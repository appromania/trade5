from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import numpy as np
import pandas as pd

from data_providers import (
    YahooFinanceProvider,
    fuzzy_search_symbol,
    fetch_symbol_on_demand
)
from technical_analysis import TechnicalAnalyzer
from risk_calculator import RiskCalculator
from ai_analyzer import AIAnalyzer
from market_context import MarketContext
from reality_check import reality_check, get_live_market_data
from after_hours_scanner import scan_after_hours_movers
from cache_manager import clear_all_cache, clear_symbol_cache, get_cache_stats
from optimize_entry import EntryOptimizer
from price_validator import PriceValidator
from models import PriceAlert, WatchlistEntry, PaperTrade, StrategyStats
import uuid


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def format_price(value):
    """Format price to 2 decimal places"""
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def format_percentage(value):
    """Format percentage to 2 decimal places"""
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def clean_analysis_response(data):
    """Clean and format all numerical values in analysis response"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # Skip formatting for nested objects like 'price', 'indicators', etc
            if key in ['price', 'indicators', 'risk_management', 'market_context', 'chart_levels', 'pivots', 'volume', 'rsi', 'stoch_rsi', 'adx', 'atr', 'macd', 'heikin_ashi', 'trend', 'gaps', 'vix', 'sp500']:
                if isinstance(value, dict):
                    cleaned[key] = clean_analysis_response(value)
                elif isinstance(value, list):
                    cleaned[key] = [clean_analysis_response(item) for item in value]
                else:
                    cleaned[key] = convert_numpy_types(value)
            elif key in ['current_price', 'entry_price', 'stop_loss', 'take_profit', 'trailing_stop'] or (isinstance(key, str) and 'price' in key.lower() and key != 'price'):
                cleaned[key] = format_price(value)
            elif key in ['price_change_percent', 'stop_loss_percent'] or (isinstance(key, str) and 'percent' in key.lower()):
                cleaned[key] = format_percentage(value)
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_analysis_response(value)
            else:
                cleaned[key] = convert_numpy_types(value)
        return cleaned
    elif isinstance(data, list):
        return [clean_analysis_response(item) for item in data]
    else:
        return convert_numpy_types(data)


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Initialize services (only stateless ones)
provider = YahooFinanceProvider()
ai_analyzer = AIAnalyzer()
market_context = MarketContext()

# Services that need db will be initialized later
# alerts_service, watchlist_service, paper_trading_service will be created on-demand


class ProviderConfig(BaseModel):
    name: str
    enabled: bool
    api_key: Optional[str] = None


class UserSettings(BaseModel):
    user_id: str = "default"
    providers: List[ProviderConfig]
    default_timeframe: str = "1d"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SymbolSearchRequest(BaseModel):
    query: str


class AnalyzeRequest(BaseModel):
    symbol: str
    provider: str = "yahoo"
    timeframe: str = "1d"  # 1h, 4h, 1d, 1w
    period: str = "6mo"
    lookback: int = 60
    use_heikin_ashi: bool = False


class AnalysisResponse(BaseModel):
    symbol: str
    company_name: Optional[str]
    current_price: float
    price_change_percent: float
    signal: str
    confidence_score: int
    indicators: Dict[str, Any]
    risk_management: Dict[str, Any]
    market_context: Dict[str, Any]
    alerts: List[Dict[str, str]]
    ai_analysis: str
    chart_data: Optional[List[Dict[str, Any]]] = []
    override_reason: Optional[str] = None
    chart_levels: Optional[Dict[str, Any]] = {}
    donchian_channel: Optional[Dict[str, Any]] = {}
    williams_fractals: Optional[Dict[str, Any]] = {}
    trend_alignment: Optional[Dict[str, Any]] = {}
    timestamp: str


@api_router.get("/")
async def root():
    return {"message": "Expert Trading System API", "version": "2025"}


@api_router.get("/providers")
async def get_providers():
    """Return list of available data providers"""
    return {
        "providers": [
            {
                "id": "yahoo",
                "name": "Yahoo Finance",
                "free": True,
                "description": "Date gratuite, fără limită"
            },
            {
                "id": "alphavantage",
                "name": "Alpha Vantage",
                "free": True,
                "description": "Gratuit cu limită (5 cereri/minut, 25/zi)",
                "requires_key": True
            },
            {
                "id": "twelvedata",
                "name": "Twelve Data",
                "free": True,
                "description": "Freemium (800 cereri/zi gratuit)",
                "requires_key": True
            }
        ]
    }


@api_router.post("/symbols/search")
async def search_symbols(request: SymbolSearchRequest):
    """Fuzzy search for stock symbols"""
    try:
        results = fuzzy_search_symbol(request.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OnDemandFetchRequest(BaseModel):
    symbol: str


@api_router.post("/symbols/fetch-on-demand")
async def fetch_symbol_data_on_demand(request: OnDemandFetchRequest):
    """
    Fetch data for an unknown symbol on-demand from Yahoo Finance.
    This is used when a user searches for a symbol not in our database.
    """
    try:
        result = await fetch_symbol_on_demand(request.symbol)
        return result
    except Exception as e:
        logger.error(f"On-demand fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_symbol(request: AnalyzeRequest):
    """Complete technical analysis of a symbol"""
    try:
        # Step 1: Get user settings to determine provider credentials
        settings = await db.user_settings.find_one({"user_id": "default"})
        api_keys = {}
        if settings:
            for provider in settings.get("providers", []):
                if provider.get("api_key"):
                    api_keys[provider["name"]] = provider["api_key"]

        # Step 2: Initialize provider (using Yahoo Finance for all)
        provider = YahooFinanceProvider()

        # Step 3: Fetch OHLC data
        data = await provider.get_ohlc_data(
            request.symbol,
            period=request.period,
            interval=request.timeframe
        )
        
        if data is None or len(data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Simbol inexistent sau date insuficiente pentru {request.symbol}"
            )

        # Step 4: Technical Analysis
        analyzer = TechnicalAnalyzer(data)
        indicators_raw = analyzer.calculate_all_indicators()
        indicators = convert_numpy_types(indicators_raw)
        
        # Step 4.5: Check for massive drops and validate entry
        massive_drop = PriceValidator.detect_massive_drop(data)
        gap_reversal = PriceValidator.detect_gap_reversal(data)
        
        # Add to alerts if detected
        if massive_drop:
            alerts_raw = alerts_raw if 'alerts_raw' in locals() else []
            alerts_raw.insert(0, {
                'type': 'MASSIVE_DROP',
                'severity': 'critical',
                'message': massive_drop['warning'],
                'action': massive_drop['action'],
                'drop_percent': massive_drop['drop_percent'],
                'volume_spike': massive_drop['volume_spike']
            })
        
        if gap_reversal:
            alerts_raw = alerts_raw if 'alerts_raw' in locals() else []
            alerts_raw.insert(0, {
                'type': 'GAP_REVERSAL',
                'severity': 'info',
                'message': gap_reversal['message'],
                'action': gap_reversal['action'],
                'recovery_percent': gap_reversal['recovery_percent']
            })
        
        # Step 5: Risk Calculation
        risk_calc = RiskCalculator(data, indicators_raw)
        risk_data_raw = risk_calc.calculate_risk_reward(
            lookback_days=request.lookback
        )
        risk_data = convert_numpy_types(risk_data_raw)
        
        # Step 6: Market Context (VIX, S&P 500)
        context_data_raw = await market_context.get_context()
        context_data = convert_numpy_types(context_data_raw)
        
        # Step 6.5: Fetch fundamentals (needed for signal generation)
        try:
            fundamentals = await provider.get_fundamentals(request.symbol)
        except:
            fundamentals = None
        
        # Step 6.9: Calculate price change BEFORE signal generation (CRITICAL)
        current_price = float(data['close'].iloc[-1])
        prev_price = float(data['close'].iloc[-2])
        price_change = ((current_price - prev_price) / prev_price) * 100
        
        # Step 7: Generate signal and confidence (PASS price_change for drop penalty)
        signal_data_raw = analyzer.generate_signal(
            indicators_raw, 
            context_data_raw,
            risk_data,
            earnings_days=None,  # TODO: Calculate from earnings calendar
            fundamentals=fundamentals,  # Pass fundamentals for financial health check
            price_change_percent=price_change  # NEW: Pass for daily drop penalty
        )
        signal_data = convert_numpy_types(signal_data_raw)
        
        # Step 8: Check for alerts (earnings, volatility)
        alerts_raw = await market_context.check_alerts(
            request.symbol,
            indicators_raw,
            context_data_raw
        )
        alerts = convert_numpy_types(alerts_raw)
        
        # Step 9: AI Analysis with fundamentals AND price change
        ai_summary = await ai_analyzer.analyze(
            symbol=request.symbol,
            indicators=indicators,
            risk_data=risk_data,
            signal=signal_data["signal"],
            context=context_data,
            alerts=alerts,
            fundamentals=fundamentals,
            price_change_percent=price_change  # NEW: Pass for crash detection
        )
        
        # Step 10: Build response (price_change already calculated above)
        
        # 🔥 REALITY CHECK: Validate price against LIVE data
        price_validation = reality_check.validate_price(request.symbol, current_price)
        
        if not price_validation['valid']:
            # Price mismatch detected - use LIVE price instead
            logger.warning(f"⚠️ Price mismatch for {request.symbol}: Using LIVE price")
            current_price = price_validation['live_price']
            
            # Add warning to alerts
            alerts.insert(0, {
                'type': 'REALITY_CHECK',
                'severity': 'high',
                'message': f"⚠️ Diferență de preț detectată ({price_validation['diff_percent']:.1f}%). Folosim prețul LIVE: ${current_price:.2f}"
            })
        
        # Prepare historical OHLC data for chart (last 300 candles for zoom capability)
        chart_data = []
        seen_times = set()  # Track seen timestamps to avoid duplicates
        
        for idx in range(max(0, len(data) - 300), len(data)):
            row = data.iloc[idx]
            
            # Format time based on interval
            if request.timeframe in ['1h', '4h', '30m', '15m', '5m']:
                # For intraday: use Unix timestamp (seconds)
                if hasattr(row['date'], 'timestamp'):
                    time_value = int(row['date'].timestamp())
                else:
                    # Fallback: try to parse
                    try:
                        dt = pd.to_datetime(row['date'])
                        time_value = int(dt.timestamp())
                    except:
                        time_value = str(row['date'])
            else:
                # For daily/weekly: use YYYY-MM-DD string
                time_value = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            
            # Skip duplicates (important for 1h/4h where Yahoo can have duplicates)
            if time_value in seen_times:
                logger.warning(f"Skipping duplicate timestamp: {time_value}")
                continue
            
            seen_times.add(time_value)
            
            chart_data.append({
                'time': time_value,
                'open': format_price(row['open']),
                'high': format_price(row['high']),
                'low': format_price(row['low']),
                'close': format_price(row['close']),
                'volume': int(row['volume']) if not pd.isna(row['volume']) else 0
            })
        
        response_dict = {
            'symbol': request.symbol.upper(),
            'company_name': None,
            'current_price': format_price(current_price),
            'price_change_percent': format_percentage(price_change),
            'signal': signal_data["signal"],
            'confidence_score': int(signal_data["confidence"]),
            'indicators': indicators,
            'risk_management': risk_data,
            'market_context': context_data,
            'alerts': alerts,
            'ai_analysis': ai_summary,
            'chart_data': chart_data,
            'override_reason': signal_data.get('override_reason'),
            'chart_levels': {
                'support': format_price(indicators['pivots']['support']),
                'resistance': format_price(indicators['pivots']['resistance']),
                'stop_loss': format_price(risk_data['stop_loss']),
                'take_profit': format_price(risk_data['take_profit']),
                'entry': format_price(risk_data['entry_price'])
            },
            'donchian_channel': indicators.get('donchian', {}),
            'williams_fractals': indicators.get('fractals', {}),
            'trend_alignment': indicators.get('trend_alignment', {}),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Clean all numerical values
        cleaned_response = clean_analysis_response(response_dict)
        
        response = AnalysisResponse(**cleaned_response)
        
        # Cache the analysis (without chart_data to save space)
        cache_dict = {k: v for k, v in cleaned_response.items() if k != 'chart_data'}
        await db.analysis_cache.insert_one(cache_dict)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare de analiză: {str(e)}")


@api_router.get("/market-context")
async def get_market_context_endpoint():
    """Get global market context"""
    try:
        context = await market_context.get_context()
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/fundamentals/{symbol}")
async def get_fundamentals(symbol: str):
    """Get fundamental data for a symbol"""
    try:
        provider = YahooFinanceProvider()
        fundamentals = await provider.get_fundamentals(symbol)
        
        if not fundamentals:
            raise HTTPException(status_code=404, detail="Fundamentals not available")
        
        return fundamentals
    except Exception as e:
        logger.error(f"Fundamentals error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/settings")
async def save_settings(settings: UserSettings):
    """Save user settings"""
    try:
        settings_dict = settings.model_dump()
        settings_dict["created_at"] = settings_dict["created_at"].isoformat()
        
        await db.user_settings.update_one(
            {"user_id": settings.user_id},
            {"$set": settings_dict},
            upsert=True
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/settings")
async def get_settings():
    """Get user settings"""
    try:
        settings = await db.user_settings.find_one(
            {"user_id": "default"},
            {"_id": 0}
        )
        
        if not settings:
            # Return default settings
            return {
                "user_id": "default",
                "providers": [
                    {"name": "yahoo", "enabled": True, "api_key": None},
                    {"name": "alphavantage", "enabled": False, "api_key": None},
                    {"name": "twelvedata", "enabled": False, "api_key": None}
                ],
                "default_timeframe": "1d"
            }
        
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/live-price/{symbol}")
async def get_live_price(symbol: str):
    """
    Reality Check Module - Obține prețul LIVE (cache 1 minut)
    """
    try:
        live_data = get_live_market_data(symbol)
        
        if not live_data:
            raise HTTPException(
                status_code=404,
                detail=f"Nu se poate obține prețul LIVE pentru {symbol}"
            )
        
        return live_data
    except Exception as e:
        logger.error(f"Live price error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/validate-price")
async def validate_price_endpoint(request: dict):
    """
    Reality Check Module - Validează un preț față de prețul LIVE
    Request: {"symbol": "AAPL", "cached_price": 150.00}
    """
    try:
        symbol = request.get('symbol')
        cached_price = request.get('cached_price')
        
        if not symbol or cached_price is None:
            raise HTTPException(status_code=400, detail="Missing symbol or cached_price")
        
        validation = reality_check.validate_price(symbol, float(cached_price))
        
        return validation
    except Exception as e:
        logger.error(f"Price validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scan-after-hours")
async def scan_after_hours():
    """
    After-Hours Momentum Scanner
    Scanează Top Movers după închiderea pieței
    Query params:
    - min_change: Minimum price change % (default: 3.0)
    - min_volume: Minimum volume (default: 50000)
    """
    try:
        # Get query params
        from fastapi import Query
        
        min_change = 3.0  # Default
        min_volume = 50000  # Default
        
        logger.info("🌙 Starting after-hours scan...")
        
        movers = scan_after_hours_movers(
            symbols=None,  # Use default watchlist
            min_change=min_change,
            min_volume=min_volume
        )
        
        return {
            'success': True,
            'scan_time': datetime.now(timezone.utc).isoformat(),
            'total_scanned': len([]),  # Will be set by scanner
            'movers_found': len(movers),
            'movers': movers,
            'filters': {
                'min_change_percent': min_change,
                'min_volume': min_volume
            }
        }
        
    except Exception as e:
        logger.error(f"After-hours scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW ENDPOINTS: OPTIMIZE ENTRY ====================

class OptimizeEntryRequest(BaseModel):
    symbol: str
    current_price: float
    ema_20: float
    ema_50: float
    support: float
    resistance: float
    atr: float
    current_rr: float


@api_router.post("/optimize-entry")
async def optimize_entry(request: OptimizeEntryRequest):
    """
    Optimize entry price for better Risk/Reward ratio (target: R/R >= 2.0)
    Recalculates entry at closest support (EMA 20/50 or pivot)
    """
    try:
        optimizer = EntryOptimizer(target_rr=2.0)
        
        result = optimizer.optimize_entry(
            current_price=request.current_price,
            ema_20=request.ema_20,
            ema_50=request.ema_50,
            support=request.support,
            resistance=request.resistance,
            atr=request.atr,
            current_rr=request.current_rr
        )
        
        return {
            'success': True,
            'optimization': result
        }
        
    except Exception as e:
        logger.error(f"Optimize entry error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW ENDPOINTS: PAPER TRADING ====================

class SimulateTradeRequest(BaseModel):
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int = 100
    strategy: Optional[str] = "manual"
    notes: Optional[str] = None


@api_router.post("/simulate-trade")
async def simulate_trade(request: SimulateTradeRequest):
    """
    Create a simulated paper trade for strategy testing
    """
    try:
        trade_id = str(uuid.uuid4())
        
        trade = {
            'id': trade_id,
            'symbol': request.symbol.upper(),
            'entry_price': request.entry_price,
            'stop_loss': request.stop_loss,
            'take_profit': request.take_profit,
            'position_size': request.position_size,
            'entry_date': datetime.now(timezone.utc),
            'current_price': request.entry_price,
            'status': 'active',
            'strategy': request.strategy,
            'notes': request.notes,
            'pnl_percent': 0.0,
            'pnl_amount': 0.0
        }
        
        await db.simulated_trades.insert_one(trade)
        
        # Remove MongoDB's _id before returning (not JSON serializable)
        trade.pop('_id', None)
        
        return {
            'success': True,
            'trade_id': trade_id,
            'message': f'Tranzacție simulată creată pentru {request.symbol}',
            'trade': trade
        }
        
    except Exception as e:
        logger.error(f"Simulate trade error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/simulations")
async def get_simulations(status: Optional[str] = None):
    """
    Get all simulated trades (optionally filtered by status)
    """
    try:
        query = {}
        if status:
            query['status'] = status
        
        trades = await db.simulated_trades.find(query).sort('entry_date', -1).to_list(100)
        
        # Remove MongoDB _id
        for trade in trades:
            trade.pop('_id', None)
        
        return {
            'success': True,
            'total': len(trades),
            'trades': trades
        }
        
    except Exception as e:
        logger.error(f"Get simulations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/simulations/audit")
async def audit_simulations():
    """
    Audit all active simulations - check current price and update status
    Returns success/failure statistics
    """
    try:
        active_trades = await db.simulated_trades.find({'status': 'active'}).to_list(100)
        
        provider = YahooFinanceProvider()
        updated_count = 0
        
        for trade in active_trades:
            symbol = trade['symbol']
            
            # Fetch current price
            try:
                data = await provider.get_ohlc_data(symbol, period='1d', interval='1d')
                if data is not None and len(data) > 0:
                    current_price = float(data['close'].iloc[-1])
                    
                    # Check if TP or SL hit
                    if current_price >= trade['take_profit']:
                        # Success - TP hit
                        pnl_percent = ((trade['take_profit'] - trade['entry_price']) / trade['entry_price']) * 100
                        pnl_amount = (trade['take_profit'] - trade['entry_price']) * trade['position_size']
                        
                        await db.simulated_trades.update_one(
                            {'id': trade['id']},
                            {
                                '$set': {
                                    'status': 'success',
                                    'exit_price': current_price,
                                    'exit_date': datetime.now(timezone.utc),
                                    'current_price': current_price,
                                    'pnl_percent': round(pnl_percent, 2),
                                    'pnl_amount': round(pnl_amount, 2)
                                }
                            }
                        )
                        updated_count += 1
                        
                    elif current_price <= trade['stop_loss']:
                        # Failure - SL hit
                        pnl_percent = ((trade['stop_loss'] - trade['entry_price']) / trade['entry_price']) * 100
                        pnl_amount = (trade['stop_loss'] - trade['entry_price']) * trade['position_size']
                        
                        await db.simulated_trades.update_one(
                            {'id': trade['id']},
                            {
                                '$set': {
                                    'status': 'failed',
                                    'exit_price': current_price,
                                    'exit_date': datetime.now(timezone.utc),
                                    'current_price': current_price,
                                    'pnl_percent': round(pnl_percent, 2),
                                    'pnl_amount': round(pnl_amount, 2)
                                }
                            }
                        )
                        updated_count += 1
                    else:
                        # Still active - update current price and unrealized P/L
                        pnl_percent = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
                        pnl_amount = (current_price - trade['entry_price']) * trade['position_size']
                        
                        await db.simulated_trades.update_one(
                            {'id': trade['id']},
                            {
                                '$set': {
                                    'current_price': current_price,
                                    'pnl_percent': round(pnl_percent, 2),
                                    'pnl_amount': round(pnl_amount, 2)
                                }
                            }
                        )
            except Exception as e:
                logger.error(f"Error auditing trade {symbol}: {str(e)}")
                continue
        
        # Calculate statistics
        all_trades = await db.simulated_trades.find({}).to_list(1000)
        total = len(all_trades)
        success = len([t for t in all_trades if t['status'] == 'success'])
        failed = len([t for t in all_trades if t['status'] == 'failed'])
        active = len([t for t in all_trades if t['status'] == 'active'])
        
        success_rate = (success / (success + failed) * 100) if (success + failed) > 0 else 0
        
        return {
            'success': True,
            'audited': len(active_trades),
            'updated': updated_count,
            'statistics': {
                'total_trades': total,
                'successful_trades': success,
                'failed_trades': failed,
                'active_trades': active,
                'success_rate': round(success_rate, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Audit simulations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW ENDPOINTS: ALERTS ====================

class SetAlertRequest(BaseModel):
    symbol: str
    target_price: float
    alert_type: str  # 'take_profit', 'stop_loss', 'ideal_entry'
    current_price: float
    user_note: Optional[str] = None


@api_router.post("/alerts/set")
async def set_alert(request: SetAlertRequest):
    """
    Set a price alert for a symbol
    """
    try:
        alert_id = str(uuid.uuid4())
        
        alert = {
            'id': alert_id,
            'symbol': request.symbol.upper(),
            'target_price': request.target_price,
            'alert_type': request.alert_type,
            'current_price': request.current_price,
            'created_at': datetime.now(timezone.utc),
            'triggered': False,
            'user_note': request.user_note,
            'status': 'active'
        }
        
        await db.alerts.insert_one(alert)
        
        # Remove MongoDB's _id before returning
        alert.pop('_id', None)
        
        return {
            'success': True,
            'alert_id': alert_id,
            'message': f'Alertă setată pentru {request.symbol} la ${request.target_price}',
            'alert': alert
        }
        
    except Exception as e:
        logger.error(f"Set alert error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/alerts")
async def get_alerts(status: Optional[str] = 'active'):
    """
    Get all alerts (default: active only)
    """
    try:
        query = {'status': status} if status else {}
        
        alerts = await db.alerts.find(query).sort('created_at', -1).to_list(100)
        
        # Remove MongoDB _id
        for alert in alerts:
            alert.pop('_id', None)
        
        return {
            'success': True,
            'total': len(alerts),
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Get alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/alerts/check")
async def check_alerts():
    """
    Check all active alerts against current prices
    Returns triggered alerts
    """
    try:
        active_alerts = await db.alerts.find({'status': 'active', 'triggered': False}).to_list(100)
        
        provider = YahooFinanceProvider()
        triggered_alerts = []
        
        for alert in active_alerts:
            symbol = alert['symbol']
            
            try:
                data = await provider.get_ohlc_data(symbol, period='1d', interval='1d')
                if data is not None and len(data) > 0:
                    current_price = float(data['close'].iloc[-1])
                    
                    # Check if alert triggered
                    triggered = False
                    
                    if alert['alert_type'] == 'ideal_entry':
                        # Trigger if price drops to or below target (buying opportunity)
                        if current_price <= alert['target_price'] * 1.02:  # 2% tolerance
                            triggered = True
                    elif alert['alert_type'] == 'take_profit':
                        # Trigger if price rises to or above target
                        if current_price >= alert['target_price'] * 0.98:  # 2% tolerance
                            triggered = True
                    elif alert['alert_type'] == 'stop_loss':
                        # Trigger if price drops to or below target
                        if current_price <= alert['target_price'] * 1.02:  # 2% tolerance
                            triggered = True
                    
                    if triggered:
                        await db.alerts.update_one(
                            {'id': alert['id']},
                            {
                                '$set': {
                                    'triggered': True,
                                    'triggered_at': datetime.now(timezone.utc),
                                    'trigger_price': current_price
                                }
                            }
                        )
                        
                        alert['current_price'] = current_price
                        triggered_alerts.append(alert)
                        
            except Exception as e:
                logger.error(f"Error checking alert for {symbol}: {str(e)}")
                continue
        
        return {
            'success': True,
            'checked': len(active_alerts),
            'triggered': len(triggered_alerts),
            'alerts': triggered_alerts
        }
        
    except Exception as e:
        logger.error(f"Check alerts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """
    Delete or deactivate an alert
    """
    try:
        result = await db.alerts.update_one(
            {'id': alert_id},
            {'$set': {'status': 'deleted'}}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'message': 'Alertă ștearsă'}
        else:
            raise HTTPException(status_code=404, detail='Alertă negăsită')
        
    except Exception as e:
        logger.error(f"Delete alert error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW ENDPOINTS: WATCHLIST (POTENTIAL PORTFOLIO) ====================

class AddToWatchlistRequest(BaseModel):
    symbol: str
    ideal_entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    confidence_score: int
    notes: Optional[str] = None


@api_router.post("/watchlist/add")
async def add_to_watchlist(request: AddToWatchlistRequest):
    """
    Add symbol to Potential Portfolio (Smart Watchlist)
    """
    try:
        entry_id = str(uuid.uuid4())
        
        entry = {
            'id': entry_id,
            'symbol': request.symbol.upper(),
            'ideal_entry_price': request.ideal_entry_price,
            'current_price': request.current_price,
            'stop_loss': request.stop_loss,
            'take_profit': request.take_profit,
            'confidence_score': request.confidence_score,
            'added_at': datetime.now(timezone.utc),
            'pnl_percent': 0.0,
            'status': 'pending',
            'notes': request.notes
        }
        
        await db.watchlist.insert_one(entry)
        
        # Remove MongoDB's _id before returning
        entry.pop('_id', None)
        
        return {
            'success': True,
            'entry_id': entry_id,
            'message': f'{request.symbol} adăugat în Potential Portfolio',
            'entry': entry
        }
        
    except Exception as e:
        logger.error(f"Add to watchlist error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/watchlist")
async def get_watchlist():
    """
    Get Potential Portfolio (Smart Watchlist)
    Updates P/L for each entry
    """
    try:
        entries = await db.watchlist.find({'status': {'$ne': 'removed'}}).sort('added_at', -1).to_list(100)
        
        provider = YahooFinanceProvider()
        
        for entry in entries:
            try:
                data = await provider.get_ohlc_data(entry['symbol'], period='1d', interval='1d')
                if data is not None and len(data) > 0:
                    current_price = float(data['close'].iloc[-1])
                    
                    # Calculate unrealized P/L
                    if current_price <= entry['ideal_entry_price'] * 1.02:
                        # Entry triggered or close
                        entry['status'] = 'triggered'
                        pnl_percent = ((current_price - entry['ideal_entry_price']) / entry['ideal_entry_price']) * 100
                    else:
                        # Still waiting
                        entry['status'] = 'pending'
                        pnl_percent = ((current_price - entry['ideal_entry_price']) / entry['ideal_entry_price']) * 100
                    
                    entry['current_price'] = round(current_price, 2)
                    entry['pnl_percent'] = round(pnl_percent, 2)
                    
                    # Update in database
                    await db.watchlist.update_one(
                        {'id': entry['id']},
                        {
                            '$set': {
                                'current_price': current_price,
                                'pnl_percent': pnl_percent,
                                'status': entry['status']
                            }
                        }
                    )
            except Exception as e:
                logger.error(f"Error updating watchlist entry {entry['symbol']}: {str(e)}")
                continue
            
            entry.pop('_id', None)
        
        return {
            'success': True,
            'total': len(entries),
            'entries': entries
        }
        
    except Exception as e:
        logger.error(f"Get watchlist error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/watchlist/{entry_id}")
async def remove_from_watchlist(entry_id: str):
    """
    Remove entry from watchlist
    """
    try:
        result = await db.watchlist.update_one(
            {'id': entry_id},
            {'$set': {'status': 'removed'}}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'message': 'Intrare eliminată din watchlist'}
        else:
            raise HTTPException(status_code=404, detail='Intrare negăsită')
        
    except Exception as e:
        logger.error(f"Remove from watchlist error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include router
app.include_router(api_router)

# CORS - Configured for Vercel deployment
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in cors_origins.split(',')]
    # Add Vercel domains
    allowed_origins.extend([
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
