import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from price_validator import PriceValidator

logger = logging.getLogger(__name__)


class RiskCalculator:
    def __init__(self, df: pd.DataFrame, indicators: Dict[str, Any]):
        self.df = df
        self.indicators = indicators
    
    def calculate_risk_reward(self, lookback_days: int = 60) -> Dict[str, Any]:
        """Calculate stop loss, take profit, and risk/reward ratio"""
        try:
            current_price = self.indicators['price']['current']
            atr = self.indicators['atr']['value']
            support = self.indicators['pivots']['support']
            resistance = self.indicators['pivots']['resistance']
            
            # Stop Loss calculation (ATR-based) with validation
            sl_atr_based = current_price - (atr * 1.5)
            sl_support_based = support - (atr * 0.5)
            
            # Choose the higher of the two
            stop_loss = max(sl_atr_based, sl_support_based)
            
            # Validate Stop Loss (ensure it's valid and below price)
            stop_loss = PriceValidator.validate_stop_loss(stop_loss, current_price, atr)
            
            # Calculate stop loss percentage
            sl_percent = ((current_price - stop_loss) / current_price) * 100
            
            # If SL is still unrealistic (> 10%), cap it
            if sl_percent > 10:
                stop_loss = current_price * 0.90
                sl_percent = 10.0
            
            # Take Profit calculation with validation
            if current_price >= resistance * 0.98:
                take_profit = current_price + (atr * 3)
            else:
                take_profit = resistance - (resistance * 0.002)
            
            # Validate Take Profit (ensure it's above current price)
            take_profit = PriceValidator.validate_take_profit(take_profit, current_price, atr)
            
            # Risk/Reward Ratio
            risk = current_price - stop_loss
            reward = take_profit - current_price
            
            if risk <= 0:
                risk = atr * 1.5
            
            rr_ratio = reward / risk if risk > 0 else 0
            
            # Cap R/R ratio for display (max 10:1)
            rr_display_data = PriceValidator.cap_risk_reward_ratio(rr_ratio, max_rr=10.0)
            
            # Position sizing (example: 1% risk per trade)
            account_risk_percent = 1.0
            position_size_percent = (account_risk_percent / sl_percent) * 100
            
            # Trailing stop suggestion with validation
            trailing_stop = PriceValidator.validate_price(current_price - (atr * 2))
            
            result = {
                'entry_price': round(current_price, 2),
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'stop_loss_percent': round(sl_percent, 2),
                'risk_reward_ratio': rr_display_data['rr_ratio'],
                'actual_rr_ratio': rr_display_data['actual_rr'],
                'rr_capped': rr_display_data.get('capped', False),
                'position_size_suggestion': round(min(position_size_percent, 100), 2),
                'trailing_stop': round(trailing_stop, 2),
                'atr_value': round(atr, 2),
                'favorable': rr_ratio >= 1.5,
                'risk_assessment': self._assess_risk(rr_ratio, sl_percent),
                'support': round(support, 2),
                'resistance': round(resistance, 2)
            }
            
            # Add R/R cap warning if applicable
            if rr_display_data.get('capped'):
                result['rr_warning'] = rr_display_data.get('warning')
            
            return result
            
        except Exception as e:
            logger.error(f"Risk calculation error: {str(e)}")
            raise
    
    def _assess_risk(self, rr_ratio: float, sl_percent: float) -> str:
        """Assess overall risk level"""
        if rr_ratio >= 2.5 and sl_percent <= 5:
            return "SCĂZUT - Setup favorabil"
        elif rr_ratio >= 1.5 and sl_percent <= 7:
            return "MODERAT - Acceptabil"
        elif rr_ratio < 1.5:
            return "RIDICAT - Raport R/R nefavorabil, recomand WAIT"
        else:
            return "RIDICAT - Stop Loss prea larg"
    
    def calculate_position_sizing(self, account_size: float, risk_percent: float = 1.0) -> Dict[str, Any]:
        """Calculate position sizing based on account size"""
        current_price = self.indicators['price']['current']
        sl_percent = self.calculate_risk_reward()['stop_loss_percent']
        
        risk_amount = account_size * (risk_percent / 100)
        shares = risk_amount / (current_price * (sl_percent / 100))
        
        return {
            'shares': int(shares),
            'total_cost': round(shares * current_price, 2),
            'risk_amount': round(risk_amount, 2)
        }