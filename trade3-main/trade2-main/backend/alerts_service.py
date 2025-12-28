"""
Alerts and Paper Trading Service
Handles price alerts, watchlist management, and simulated trades
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from models import PriceAlert, WatchlistEntry, PaperTrade, StrategyStats

logger = logging.getLogger(__name__)


class AlertsService:
    """Service for managing price alerts"""
    
    def __init__(self, db):
        self.db = db
        self.alerts_collection = db.price_alerts
        
    async def create_alert(
        self,
        symbol: str,
        target_price: float,
        alert_type: str,
        current_price: float,
        user_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new price alert"""
        
        alert = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'target_price': target_price,
            'alert_type': alert_type,
            'current_price': current_price,
            'created_at': datetime.now(),
            'triggered': False,
            'triggered_at': None,
            'user_note': user_note
        }
        
        await self.alerts_collection.insert_one(alert)
        
        logger.info(f"✅ Created alert: {symbol} @ ${target_price} ({alert_type})")
        
        return alert
    
    async def get_active_alerts(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all active (non-triggered) alerts"""
        
        query = {'triggered': False}
        if symbol:
            query['symbol'] = symbol
        
        alerts = await self.alerts_collection.find(query).sort('created_at', -1).to_list(100)
        return alerts
    
    async def check_and_trigger_alerts(self, symbol: str, current_price: float) -> List[Dict]:
        """Check if any alerts should be triggered"""
        
        triggered_alerts = []
        
        # Get active alerts for this symbol
        alerts = await self.get_active_alerts(symbol)
        
        for alert in alerts:
            target_price = alert['target_price']
            alert_type = alert['alert_type']
            
            # Check if price crossed the target
            should_trigger = False
            
            if alert_type == 'take_profit':
                # Trigger if current price >= target
                should_trigger = current_price >= target_price
            elif alert_type == 'stop_loss':
                # Trigger if current price <= target
                should_trigger = current_price <= target_price
            elif alert_type == 'ideal_entry':
                # Trigger if price is within 0.5% of target
                diff_percent = abs((current_price - target_price) / target_price) * 100
                should_trigger = diff_percent <= 0.5
            
            if should_trigger:
                # Update alert as triggered
                await self.alerts_collection.update_one(
                    {'id': alert['id']},
                    {
                        '$set': {
                            'triggered': True,
                            'triggered_at': datetime.now()
                        }
                    }
                )
                
                triggered_alerts.append(alert)
                logger.info(f"🔔 Alert triggered: {symbol} @ ${current_price} ({alert_type})")
        
        return triggered_alerts


class WatchlistService:
    """Service for managing potential investments watchlist"""
    
    def __init__(self, db):
        self.db = db
        self.watchlist_collection = db.watchlist
        
    async def add_to_watchlist(
        self,
        symbol: str,
        ideal_entry_price: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add symbol to watchlist"""
        
        # Calculate initial P/L
        pnl_percent = ((current_price - ideal_entry_price) / ideal_entry_price) * 100
        
        # Determine status
        status = 'pending'
        if current_price <= ideal_entry_price * 1.01:  # Within 1% of entry
            status = 'triggered'
        
        entry = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'ideal_entry_price': ideal_entry_price,
            'current_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence_score': confidence_score,
            'added_at': datetime.now(),
            'pnl_percent': pnl_percent,
            'status': status,
            'notes': notes
        }
        
        await self.watchlist_collection.insert_one(entry)
        
        logger.info(f"✅ Added to watchlist: {symbol} @ ${ideal_entry_price}")
        
        return entry
    
    async def get_watchlist(self, status: Optional[str] = None) -> List[Dict]:
        """Get watchlist entries"""
        
        query = {}
        if status:
            query['status'] = status
        
        entries = await self.watchlist_collection.find(query).sort('added_at', -1).to_list(100)
        return entries
    
    async def update_watchlist_prices(self, symbol: str, current_price: float):
        """Update current prices and P/L for watchlist entries"""
        
        entries = await self.watchlist_collection.find({'symbol': symbol, 'status': 'pending'}).to_list(100)
        
        for entry in entries:
            ideal_entry = entry['ideal_entry_price']
            pnl_percent = ((current_price - ideal_entry) / ideal_entry) * 100
            
            # Check if triggered
            status = entry['status']
            if current_price <= ideal_entry * 1.01:
                status = 'triggered'
            
            await self.watchlist_collection.update_one(
                {'id': entry['id']},
                {
                    '$set': {
                        'current_price': current_price,
                        'pnl_percent': pnl_percent,
                        'status': status
                    }
                }
            )


class PaperTradingService:
    """Service for simulated trades"""
    
    def __init__(self, db):
        self.db = db
        self.trades_collection = db.paper_trades
        
    async def create_trade(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: int = 100,
        strategy: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a simulated trade"""
        
        trade = {
            'id': str(uuid.uuid4()),
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'entry_date': datetime.now(),
            'current_price': entry_price,
            'status': 'active',
            'exit_date': None,
            'exit_price': None,
            'pnl_percent': 0.0,
            'pnl_amount': 0.0,
            'notes': notes,
            'strategy': strategy
        }
        
        await self.trades_collection.insert_one(trade)
        
        logger.info(f"🧪 Created paper trade: {symbol} @ ${entry_price} ({position_size} shares)")
        
        return trade
    
    async def get_active_trades(self) -> List[Dict]:
        """Get all active trades"""
        
        trades = await self.trades_collection.find({'status': 'active'}).sort('entry_date', -1).to_list(100)
        return trades
    
    async def get_all_trades(self, days: int = 30) -> List[Dict]:
        """Get all trades from last X days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        trades = await self.trades_collection.find(
            {'entry_date': {'$gte': cutoff_date}}
        ).sort('entry_date', -1).to_list(1000)
        
        return trades
    
    async def update_trade_price(self, trade_id: str, current_price: float) -> Optional[Dict]:
        """Update trade with current price and check for exit"""
        
        trade = await self.trades_collection.find_one({'id': trade_id})
        
        if not trade or trade['status'] != 'active':
            return None
        
        entry_price = trade['entry_price']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']
        position_size = trade['position_size']
        
        # Calculate P/L
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        pnl_amount = (current_price - entry_price) * position_size
        
        # Check for exit conditions
        status = 'active'
        exit_price = None
        exit_date = None
        
        if current_price >= take_profit:
            status = 'success'
            exit_price = take_profit
            exit_date = datetime.now()
            logger.info(f"✅ Paper trade SUCCESS: {trade['symbol']} hit TP @ ${take_profit}")
        
        elif current_price <= stop_loss:
            status = 'failed'
            exit_price = stop_loss
            exit_date = datetime.now()
            logger.warning(f"❌ Paper trade FAILED: {trade['symbol']} hit SL @ ${stop_loss}")
        
        # Update trade
        await self.trades_collection.update_one(
            {'id': trade_id},
            {
                '$set': {
                    'current_price': current_price,
                    'pnl_percent': pnl_percent,
                    'pnl_amount': pnl_amount,
                    'status': status,
                    'exit_price': exit_price,
                    'exit_date': exit_date
                }
            }
        )
        
        return {**trade, 'current_price': current_price, 'pnl_percent': pnl_percent, 'status': status}
    
    async def get_strategy_stats(self, days: int = 30) -> Dict[str, Any]:
        """Calculate strategy performance statistics"""
        
        trades = await self.get_all_trades(days)
        
        total_trades = len(trades)
        successful_trades = len([t for t in trades if t['status'] == 'success'])
        failed_trades = len([t for t in trades if t['status'] == 'failed'])
        active_trades = len([t for t in trades if t['status'] == 'active'])
        
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average P/L for closed trades
        closed_trades = [t for t in trades if t['status'] in ['success', 'failed']]
        average_pnl = sum([t.get('pnl_percent', 0) for t in closed_trades]) / len(closed_trades) if closed_trades else 0
        total_pnl = sum([t.get('pnl_amount', 0) for t in closed_trades])
        
        return {
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'failed_trades': failed_trades,
            'active_trades': active_trades,
            'success_rate': round(success_rate, 2),
            'average_pnl': round(average_pnl, 2),
            'total_pnl': round(total_pnl, 2),
            'period_days': days,
            'last_updated': datetime.now()
        }
