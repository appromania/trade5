"""
Price Validation Module
Ensures all prices are valid (no negative values, no extreme drops without validation)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PriceValidator:
    """Validates price data and protects against invalid calculations"""
    
    @staticmethod
    def validate_price(price: float, min_price: float = 0.01) -> float:
        """
        Ensure price is never negative or zero
        Args:
            price: Price to validate
            min_price: Minimum acceptable price (default 0.01)
        Returns:
            Valid price (>= min_price)
        """
        if pd.isna(price) or price is None:
            return min_price
        
        return max(min_price, float(price))
    
    @staticmethod
    def validate_stop_loss(stop_loss: float, current_price: float, atr: float) -> float:
        """
        Ensure Stop Loss is valid (below entry, not negative)
        Args:
            stop_loss: Calculated SL
            current_price: Current market price
            atr: Average True Range
        Returns:
            Valid SL below current price
        """
        # Ensure SL is positive
        stop_loss = PriceValidator.validate_price(stop_loss)
        
        # Ensure SL is below current price (at least 1% below)
        if stop_loss >= current_price * 0.99:
            stop_loss = current_price - (atr * 1.5)
        
        # Final check
        stop_loss = PriceValidator.validate_price(stop_loss)
        
        return stop_loss
    
    @staticmethod
    def validate_take_profit(take_profit: float, current_price: float, atr: float) -> float:
        """
        Ensure Take Profit is valid (above entry)
        Args:
            take_profit: Calculated TP
            current_price: Current market price
            atr: Average True Range
        Returns:
            Valid TP above current price
        """
        # Ensure TP is positive
        take_profit = PriceValidator.validate_price(take_profit)
        
        # Ensure TP is above current price (at least 2% above)
        if take_profit <= current_price * 1.02:
            take_profit = current_price + (atr * 2)
        
        return take_profit
    
    @staticmethod
    def detect_massive_drop(df: pd.DataFrame, threshold: float = 8.0) -> Optional[Dict[str, Any]]:
        """
        Detect massive price drops (>8% in single session)
        Args:
            df: OHLC DataFrame
            threshold: Drop threshold percentage (default 8%)
        Returns:
            Dict with drop details or None
        """
        if len(df) < 2:
            return None
        
        # Calculate today's change
        last_close = df['close'].iloc[-2]
        current_close = df['close'].iloc[-1]
        drop_percent = ((current_close - last_close) / last_close) * 100
        
        if drop_percent < -threshold:
            # Massive drop detected
            volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1] if len(df) >= 20 else 1.0
            
            return {
                'drop_detected': True,
                'drop_percent': round(drop_percent, 2),
                'previous_close': round(float(last_close), 2),
                'current_close': round(float(current_close), 2),
                'volume_spike': volume_ratio > 1.5,
                'volume_ratio': round(float(volume_ratio), 2),
                'warning': f'Scădere Masivă Detectată: {abs(drop_percent):.1f}% într-o sesiune',
                'action': 'WAIT 24-48h pentru stabilizare înainte de orice intrare'
            }
        
        return None
    
    @staticmethod
    def detect_gap_reversal(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect gap down with intraday recovery (potential reversal)
        Args:
            df: OHLC DataFrame
        Returns:
            Dict with gap reversal details or None
        """
        if len(df) < 2:
            return None
        
        prev_close = df['close'].iloc[-2]
        current_open = df['open'].iloc[-1]
        current_close = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # Check for gap down
        gap_percent = ((current_open - prev_close) / prev_close) * 100
        
        if gap_percent < -3:  # Gap down >3%
            # Check if price recovered during the day
            red_candle_size = abs(prev_close - current_low)
            recovery_size = current_close - current_low
            recovery_percent = (recovery_size / red_candle_size) * 100 if red_candle_size > 0 else 0
            
            # Check volume
            volume_ratio = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1] if len(df) >= 20 else 1.0
            
            if recovery_percent > 50 and volume_ratio > 1.2:
                return {
                    'gap_reversal_detected': True,
                    'gap_percent': round(gap_percent, 2),
                    'recovery_percent': round(recovery_percent, 2),
                    'volume_ratio': round(float(volume_ratio), 2),
                    'signal': 'POTENTIAL_REVERSAL',
                    'message': f'Gap Reversal Detectat: Gap {abs(gap_percent):.1f}% recuperat {recovery_percent:.0f}% pe volum mare',
                    'action': 'Acesta este un setup favorabil de tip "Falling Knife" recuperat. Monitorizați confirmarea.'
                }
        
        return None
    
    @staticmethod
    def cap_risk_reward_ratio(rr_ratio: float, max_rr: float = 10.0) -> Dict[str, Any]:
        """
        Cap displayed R/R ratio to avoid unrealistic displays
        Args:
            rr_ratio: Calculated R/R ratio
            max_rr: Maximum display ratio (default 10.0)
        Returns:
            Dict with capped ratio and warning if applicable
        """
        if rr_ratio > max_rr:
            return {
                'rr_ratio': max_rr,
                'actual_rr': round(rr_ratio, 2),
                'capped': True,
                'message': f'Raport R/R efectiv ({rr_ratio:.1f}:1) este nerealistic. Afișat: {max_rr}:1',
                'warning': 'Take Profit setat prea agresiv la o rezistență îndepărtată.'
            }
        
        return {
            'rr_ratio': round(rr_ratio, 2),
            'actual_rr': round(rr_ratio, 2),
            'capped': False
        }
