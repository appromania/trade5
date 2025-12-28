"""
Alerts and Paper Trading API Endpoints
Additional routes for alerts, watchlist, and paper trading functionality
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create router
alerts_router = APIRouter(prefix="/api", tags=["alerts"])


# Request/Response Models
class CreateAlertRequest(BaseModel):
    symbol: str
    target_price: float
    alert_type: str  # 'take_profit', 'stop_loss', 'ideal_entry'
    current_price: float
    user_note: Optional[str] = None


class AddToWatchlistRequest(BaseModel):
    symbol: str
    ideal_entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    confidence_score: int
    notes: Optional[str] = None


class CreatePaperTradeRequest(BaseModel):
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int = 100
    strategy: Optional[str] = None
    notes: Optional[str] = None


class CalculateBuyTheDipRequest(BaseModel):
    symbol: str
    current_price: float
    support_level: float
    resistance_level: float
    atr: float


# Endpoints will be added to server.py
ENDPOINTS_CODE = """
# ===== ALERTS ENDPOINTS =====

@api_router.post("/alerts/create")
async def create_price_alert(request: CreateAlertRequest):
    '''Create a new price alert'''
    try:
        alert = await alerts_service.create_alert(
            symbol=request.symbol,
            target_price=request.target_price,
            alert_type=request.alert_type,
            current_price=request.current_price,
            user_note=request.user_note
        )
        
        return {
            'success': True,
            'alert': alert,
            'message': f'Alertă setată pentru {request.symbol} @ ${request.target_price}'
        }
    except Exception as e:
        logger.error(f'Error creating alert: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/alerts/active")
async def get_active_alerts(symbol: Optional[str] = None):
    '''Get all active alerts'''
    try:
        alerts = await alerts_service.get_active_alerts(symbol)
        return {
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        }
    except Exception as e:
        logger.error(f'Error getting alerts: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


# ===== WATCHLIST ENDPOINTS =====

@api_router.post("/watchlist/add")
async def add_to_watchlist(request: AddToWatchlistRequest):
    '''Add symbol to watchlist (Potential Investments)'''
    try:
        entry = await watchlist_service.add_to_watchlist(
            symbol=request.symbol,
            ideal_entry_price=request.ideal_entry_price,
            current_price=request.current_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            confidence_score=request.confidence_score,
            notes=request.notes
        )
        
        return {
            'success': True,
            'entry': entry,
            'message': f'{request.symbol} adăugat în Potential Investments'
        }
    except Exception as e:
        logger.error(f'Error adding to watchlist: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/watchlist")
async def get_watchlist(status: Optional[str] = None):
    '''Get watchlist entries'''
    try:
        entries = await watchlist_service.get_watchlist(status)
        return {
            'success': True,
            'count': len(entries),
            'entries': entries
        }
    except Exception as e:
        logger.error(f'Error getting watchlist: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


# ===== PAPER TRADING ENDPOINTS =====

@api_router.post("/paper-trade/create")
async def create_paper_trade(request: CreatePaperTradeRequest):
    '''Create a simulated trade (Paper Trading)'''
    try:
        trade = await paper_trading_service.create_trade(
            symbol=request.symbol,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            position_size=request.position_size,
            strategy=request.strategy,
            notes=request.notes
        )
        
        return {
            'success': True,
            'trade': trade,
            'message': f'Test trade creat pentru {request.symbol}'
        }
    except Exception as e:
        logger.error(f'Error creating paper trade: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/paper-trade/active")
async def get_active_paper_trades():
    '''Get all active paper trades'''
    try:
        trades = await paper_trading_service.get_active_trades()
        return {
            'success': True,
            'count': len(trades),
            'trades': trades
        }
    except Exception as e:
        logger.error(f'Error getting active trades: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/paper-trade/all")
async def get_all_paper_trades(days: int = 30):
    '''Get all paper trades from last X days'''
    try:
        trades = await paper_trading_service.get_all_trades(days)
        return {
            'success': True,
            'count': len(trades),
            'trades': trades,
            'period_days': days
        }
    except Exception as e:
        logger.error(f'Error getting all trades: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/paper-trade/stats")
async def get_strategy_stats(days: int = 30):
    '''Get strategy performance statistics'''
    try:
        stats = await paper_trading_service.get_strategy_stats(days)
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        logger.error(f'Error getting stats: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


# ===== BUY THE DIP CALCULATOR =====

@api_router.post("/calculate-buy-dip")
async def calculate_buy_the_dip(request: CalculateBuyTheDipRequest):
    '''Calculate optimal Buy the Dip entry with R/R >= 2.0'''
    try:
        # Calculate ideal entry at support level
        ideal_entry = request.support_level
        
        # Calculate new SL (3% below entry or 1.5*ATR, whichever is larger)
        sl_percent = ideal_entry * 0.97
        sl_atr = ideal_entry - (1.5 * request.atr)
        new_stop_loss = min(sl_percent, sl_atr)
        
        # Use existing resistance as TP
        new_take_profit = request.resistance_level
        
        # Calculate R/R
        risk = ideal_entry - new_stop_loss
        reward = new_take_profit - ideal_entry
        new_rr_ratio = reward / risk if risk > 0 else 0
        
        # If R/R < 2.0, adjust TP upward
        if new_rr_ratio < 2.0:
            # Calculate required TP for 2.0 R/R
            required_reward = risk * 2.0
            new_take_profit = ideal_entry + required_reward
        
        # Recalculate final R/R
        risk = ideal_entry - new_stop_loss
        reward = new_take_profit - ideal_entry
        final_rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'success': True,
            'original_entry': request.current_price,
            'optimized_entry': round(ideal_entry, 2),
            'stop_loss': round(new_stop_loss, 2),
            'take_profit': round(new_take_profit, 2),
            'risk_reward_ratio': round(final_rr_ratio, 2),
            'potential_gain_percent': round((reward / ideal_entry) * 100, 2),
            'potential_loss_percent': round((risk / ideal_entry) * 100, 2),
            'message': f'Intrare optimizată: ${ideal_entry:.2f} cu R/R {final_rr_ratio:.2f}:1'
        }
    except Exception as e:
        logger.error(f'Error calculating buy the dip: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
"""

# Export endpoints code to be added to server.py
print(ENDPOINTS_CODE)
