python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ADAUGĂ ACEST BLOC:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite orice sursă (inclusiv Vercel-ul tău)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi import FastAPI, APIRouter, HTTPException
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

# Initialize services
ai_analyzer = AIAnalyzer()
market_context = MarketContext()


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
        
        # Step 5: Risk Calculation
        risk_calc = RiskCalculator(data, indicators_raw)
        risk_data_raw = risk_calc.calculate_risk_reward(
            lookback_days=request.lookback
        )
        risk_data = convert_numpy_types(risk_data_raw)
        
        # Step 6: Market Context (VIX, S&P 500)
        context_data_raw = await market_context.get_context()
        context_data = convert_numpy_types(context_data_raw)
        
        # Step 7: Generate signal and confidence (PASS risk_data for conservative logic)
        signal_data_raw = analyzer.generate_signal(
            indicators_raw, 
            context_data_raw,
            risk_data,
            earnings_days=None  # TODO: Calculate from earnings calendar
        )
        signal_data = convert_numpy_types(signal_data_raw)
        
        # Step 8: Check for alerts (earnings, volatility)
        alerts_raw = await market_context.check_alerts(
            request.symbol,
            indicators_raw,
            context_data_raw
        )
        alerts = convert_numpy_types(alerts_raw)
        
        # Step 9: AI Analysis with fundamentals
        try:
            # Fetch fundamentals
            fundamentals = await provider.get_fundamentals(request.symbol)
        except:
            fundamentals = None
        
        ai_summary = await ai_analyzer.analyze(
            symbol=request.symbol,
            indicators=indicators,
            risk_data=risk_data,
            signal=signal_data["signal"],
            context=context_data,
            alerts=alerts,
            fundamentals=fundamentals
        )
        
        # Step 10: Build response
        current_price = float(data['close'].iloc[-1])
        prev_price = float(data['close'].iloc[-2])
        price_change = ((current_price - prev_price) / prev_price) * 100
        
        # Prepare historical OHLC data for chart (last 300 candles for zoom capability)
        chart_data = []
        for idx in range(max(0, len(data) - 300), len(data)):
            row = data.iloc[idx]
            chart_data.append({
                'time': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
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
