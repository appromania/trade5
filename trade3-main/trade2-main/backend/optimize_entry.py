"""
Optimize Entry Module
Calculates optimal entry price for better Risk/Reward ratio (target: R/R >= 2.0)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class EntryOptimizer:
    """Optimizes entry price to achieve target R/R ratio"""
    
    def __init__(self, target_rr: float = 2.0):
        """
        Args:
            target_rr: Target Risk/Reward ratio (default 2.0)
        """
        self.target_rr = target_rr
    
    def optimize_entry(
        self,
        current_price: float,
        ema_20: float,
        ema_50: float,
        support: float,
        resistance: float,
        atr: float,
        current_rr: float
    ) -> Dict[str, Any]:
        """
        Calculate optimal entry price (pullback to support/EMA) for R/R >= target
        
        Args:
            current_price: Current market price
            ema_20: EMA 20 value (short-term support)
            ema_50: EMA 50 value (long-term support)
            support: Support level from pivots
            resistance: Resistance level (target TP)
            atr: Average True Range
            current_rr: Current Risk/Reward ratio
        
        Returns:
            Dict with optimized entry details
        """
        # If current R/R is already good, no optimization needed
        if current_rr >= self.target_rr:
            return {
                'optimized': False,
                'current_rr': round(current_rr, 2),
                'message': f'R/R actual ({current_rr:.2f}) este deja favorabil. Nu este necesară optimizare.',
                'ideal_entry': current_price,
                'ideal_sl': current_price - (atr * 1.5),
                'ideal_tp': resistance,
                'ideal_rr': current_rr
            }
        
        # Find closest support level (EMA 20, EMA 50, or pivot support)
        potential_entries = []
        
        # Option 1: EMA 20 (most recent support)
        if ema_20 < current_price * 0.98:  # Only if at least 2% below
            potential_entries.append({
                'level': 'EMA 20',
                'price': ema_20,
                'distance_percent': ((current_price - ema_20) / current_price) * 100
            })
        
        # Option 2: EMA 50 (stronger support)
        if ema_50 < current_price * 0.95:  # Only if at least 5% below
            potential_entries.append({
                'level': 'EMA 50',
                'price': ema_50,
                'distance_percent': ((current_price - ema_50) / current_price) * 100
            })
        
        # Option 3: Pivot support
        if support < current_price * 0.97:  # Only if at least 3% below
            potential_entries.append({
                'level': 'Support Pivot',
                'price': support,
                'distance_percent': ((current_price - support) / current_price) * 100
            })
        
        # If no potential entries, price is already at/below support
        if not potential_entries:
            return {
                'optimized': False,
                'current_rr': round(current_rr, 2),
                'message': 'Prețul este deja la niveluri de suport. Așteptați confirmare înainte de intrare.',
                'warning': 'Risc de continuare a scăderii. Așteptați stabilizare 24-48h.',
                'ideal_entry': current_price,
                'ideal_sl': support - (atr * 0.5),
                'ideal_tp': resistance,
                'ideal_rr': current_rr
            }
        
        # Sort by closest to current price (most realistic pullback)
        potential_entries.sort(key=lambda x: x['distance_percent'])
        
        # Try each entry level until we find one with R/R >= target
        best_entry = None
        
        for entry_option in potential_entries:
            ideal_entry = entry_option['price']
            ideal_sl = ideal_entry - (atr * 1.5)  # Standard 1.5x ATR stop
            ideal_tp = resistance  # Target is resistance
            
            # Ensure SL is positive
            if ideal_sl <= 0.01:
                ideal_sl = ideal_entry * 0.97  # 3% stop as fallback
            
            # Calculate R/R
            risk = ideal_entry - ideal_sl
            reward = ideal_tp - ideal_entry
            
            if risk > 0:
                ideal_rr = reward / risk
                
                if ideal_rr >= self.target_rr:
                    best_entry = {
                        'level': entry_option['level'],
                        'price': ideal_entry,
                        'distance_percent': entry_option['distance_percent'],
                        'sl': ideal_sl,
                        'tp': ideal_tp,
                        'rr': ideal_rr
                    }
                    break
        
        # If no entry achieves target R/R, use the closest one and warn
        if not best_entry:
            closest = potential_entries[0]
            ideal_entry = closest['price']
            ideal_sl = ideal_entry - (atr * 1.5)
            ideal_tp = resistance
            risk = ideal_entry - ideal_sl
            reward = ideal_tp - ideal_entry
            ideal_rr = reward / risk if risk > 0 else 0
            
            return {
                'optimized': True,
                'current_rr': round(current_rr, 2),
                'ideal_entry': round(ideal_entry, 2),
                'ideal_sl': round(ideal_sl, 2),
                'ideal_tp': round(ideal_tp, 2),
                'ideal_rr': round(ideal_rr, 2),
                'entry_level': closest['level'],
                'pullback_distance': round(closest['distance_percent'], 1),
                'message': f'Intrare Optimizată la {closest["level"]} (${ideal_entry:.2f}) - pullback {closest["distance_percent"]:.1f}%',
                'warning': f'R/R îmbunătățit la {ideal_rr:.2f} dar încă sub target {self.target_rr}. Rezistența este prea apropiată.',
                'action': f'Setați Limit Order la ${ideal_entry:.2f} și așteptați retragerea.'
            }
        
        # Success: Found entry with R/R >= target
        return {
            'optimized': True,
            'current_rr': round(current_rr, 2),
            'ideal_entry': round(best_entry['price'], 2),
            'ideal_sl': round(best_entry['sl'], 2),
            'ideal_tp': round(best_entry['tp'], 2),
            'ideal_rr': round(best_entry['rr'], 2),
            'entry_level': best_entry['level'],
            'pullback_distance': round(best_entry['distance_percent'], 1),
            'message': f'Intrare Optimă la {best_entry["level"]} (${best_entry["price"]:.2f}) - pullback {best_entry["distance_percent"]:.1f}%',
            'success': True,
            'action': f'Setați Limit Order la ${best_entry["price"]:.2f}. R/R devine {best_entry["rr"]:.2f}:1 ✅'
        }
