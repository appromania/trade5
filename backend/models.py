"""
Alerts and Paper Trading Models
MongoDB schemas for price alerts, watchlist, and simulated trades
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class PriceAlert(BaseModel):
    """Price alert for specific symbol and target price"""
    id: Optional[str] = None
    symbol: str
    target_price: float
    alert_type: str  # 'take_profit', 'stop_loss', 'ideal_entry'
    current_price: float
    created_at: datetime = Field(default_factory=datetime.now)
    triggered: bool = False
    triggered_at: Optional[datetime] = None
    user_note: Optional[str] = None


class WatchlistEntry(BaseModel):
    """Potential investment entry in watchlist"""
    id: Optional[str] = None
    symbol: str
    ideal_entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    confidence_score: int
    added_at: datetime = Field(default_factory=datetime.now)
    pnl_percent: Optional[float] = None  # Unrealized P/L
    status: str = 'pending'  # 'pending', 'triggered', 'missed'
    notes: Optional[str] = None


class PaperTrade(BaseModel):
    """Simulated trade for strategy testing"""
    id: Optional[str] = None
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: int = 100  # Number of shares
    entry_date: datetime = Field(default_factory=datetime.now)
    current_price: Optional[float] = None
    status: str = 'active'  # 'active', 'success', 'failed'
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl_percent: Optional[float] = None
    pnl_amount: Optional[float] = None
    notes: Optional[str] = None
    strategy: Optional[str] = None  # 'buy_the_dip', 'breakout', etc.


class StrategyStats(BaseModel):
    """Overall strategy performance statistics"""
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    active_trades: int = 0
    success_rate: float = 0.0
    average_pnl: float = 0.0
    total_pnl: float = 0.0
    period_days: int = 30
    last_updated: datetime = Field(default_factory=datetime.now)
