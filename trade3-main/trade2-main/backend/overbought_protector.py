"""
Modul Overbought Assets (REAL) - Protecție pentru Active Supracumpărate
Implementare conform specificațiilor pentru gestionarea zonelor de risc extrem
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OverboughtProtector:
    """
    Protector pentru active în zone de supracumpărare extremă
    """
    
    def __init__(self):
        self.rsi_threshold = 70
        self.stoch_rsi_threshold = 90
        self.volume_ratio_min = 0.5
        self.min_rr_ratio = 1.0
        self.earnings_protect_days = 5
        
    def check_sell_trigger(
        self,
        rsi: float,
        stoch_rsi_k: float,
        volume_ratio: float
    ) -> Optional[Dict[str, Any]]:
        """
        SELL_TRIGGER Automat:
        - Activare: RSI > 70 ȘI Stoch RSI > 90% ȘI Volum Ratio < 0.5x
        - Acțiune: Înlocuiește semnalul cu 'SELL (Take Profit Now)'
        """
        
        trigger_active = (
            rsi > self.rsi_threshold and
            stoch_rsi_k > self.stoch_rsi_threshold and
            volume_ratio < self.volume_ratio_min
        )
        
        if trigger_active:
            trigger = {
                'type': 'SELL_TRIGGER',
                'severity': 'critical',
                'rsi': rsi,
                'stoch_rsi_k': stoch_rsi_k,
                'volume_ratio': volume_ratio,
                'message': (
                    f"🔴 SELL_TRIGGER ACTIVAT: Zone de OVERBOUGHT EXTREM! "
                    f"RSI={rsi:.1f} (>{self.rsi_threshold}), "
                    f"Stoch RSI={stoch_rsi_k:.1f}% (>{self.stoch_rsi_threshold}%), "
                    f"Volum={volume_ratio:.2f}x (<{self.volume_ratio_min}x). "
                    f"Combinația este TOXICĂ: Supracumpărare + Lipsă de cumpărători noi. "
                    f"🎯 ACȚIUNE: TAKE PROFIT NOW - SELL înainte de corecție."
                ),
                'action': 'SELL - Take Profit acum',
                'forced_signal': 'SELL',
                'forced_confidence': 85,
                'force_override': True
            }
            
            logger.critical(
                f"🔴 SELL_TRIGGER activated: RSI={rsi:.1f}, StochRSI={stoch_rsi_k:.1f}%, "
                f"Vol={volume_ratio:.2f}x"
            )
            return trigger
        
        return None
    
    def check_entry_block(
        self,
        risk_reward_ratio: float
    ) -> Optional[Dict[str, Any]]:
        """
        Blocare Intrări Noi:
        - Dacă R/R < 1.0: Blocare automată intrări noi
        """
        
        if risk_reward_ratio < self.min_rr_ratio:
            block = {
                'type': 'ENTRY_BLOCK',
                'severity': 'high',
                'rr_ratio': risk_reward_ratio,
                'message': (
                    f"🛑 BLOCAT: Raport R/R subunitar ({risk_reward_ratio:.2f}). "
                    f"Risc mai mare decât recompensa potențială. "
                    f"Setup tehnic NEFAVORABIL - Nu intra în poziție."
                ),
                'action': 'NU CUMPĂRA - Așteptați setup mai bun',
                'entry_blocked': True
            }
            
            logger.warning(f"🛑 Entry blocked: R/R={risk_reward_ratio:.2f} < {self.min_rr_ratio}")
            return block
        
        return None
    
    def calculate_trailing_stop(
        self,
        current_price: float,
        atr: float
    ) -> Dict[str, Any]:
        """
        Optimizarea Trailing Stop:
        - Trailing Stop = Preț - (2 * ATR)
        - Auto-execute (nu doar sugestie)
        """
        
        trailing_stop = current_price - (2 * atr)
        
        result = {
            'trailing_stop': trailing_stop,
            'formula': 'Preț - (2 * ATR)',
            'atr': atr,
            'distance_percent': ((current_price - trailing_stop) / current_price) * 100,
            'message': (
                f"📍 TRAILING STOP: ${trailing_stop:.2f} "
                f"(Distanță: {((current_price - trailing_stop) / current_price) * 100:.1f}%). "
                f"Bazat pe volatilitatea pieței (2*ATR = ${2*atr:.2f}). "
                f"Actualizează automat când prețul crește."
            ),
            'auto_execute': True
        }
        
        logger.info(f"📍 Trailing Stop calculated: ${trailing_stop:.2f} (2*ATR)")
        return result
    
    def earnings_auto_protect(
        self,
        days_until_earnings: Optional[int],
        entry_price: float,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Earnings Auto-Protect:
        - Dacă Earnings < 5 zile ȘI poziție pe profit:
          - Mută SL la breakeven (preț de intrare)
          - Pop-up: 'Scoateți 50% din poziție'
        """
        
        if days_until_earnings is None or days_until_earnings > self.earnings_protect_days:
            return None
        
        # Verifică dacă e pe profit
        is_profitable = current_price > entry_price
        
        if not is_profitable:
            return None
        
        # PROTECȚIE AUTOMATĂ
        protect = {
            'type': 'EARNINGS_AUTO_PROTECT',
            'severity': 'high',
            'days_until': days_until_earnings,
            'breakeven_sl': entry_price,
            'current_profit_percent': ((current_price - entry_price) / entry_price) * 100,
            'message': (
                f"🛡️ EARNINGS AUTO-PROTECT: Raport în {days_until_earnings} zile! "
                f"Poziție pe profit: +{((current_price - entry_price) / entry_price) * 100:.1f}%. "
                f"🔒 ACȚIUNE AUTOMATĂ: Mutăm Stop Loss la BREAKEVEN (${entry_price:.2f}) "
                f"pentru protecție în caz de gap negativ. "
                f"💡 RECOMANDARE: Scoateți 50% din poziție ACUM și lăsați restul să ruleze."
            ),
            'action_auto': f'SL mutat automat la ${entry_price:.2f} (breakeven)',
            'action_manual': 'Scoateți 50% din poziție pentru siguranță',
            'new_stop_loss': entry_price,
            'auto_adjusted': True
        }
        
        logger.info(
            f"🛡️ Earnings Auto-Protect: {days_until_earnings}d, "
            f"SL moved to breakeven ${entry_price:.2f}"
        )
        return protect
    
    def assess_final_risk(
        self,
        rsi: float,
        stoch_rsi_k: float,
        volume_ratio: float,
        days_until_earnings: Optional[int]
    ) -> Dict[str, str]:
        """
        Evaluarea Riscului Final:
        - Înlocuiește 'RIDICAT' cu 'EXTREM DE RIDICAT (Overbought/Earnings Risk)'
        """
        
        # Check overbought
        is_overbought = rsi > self.rsi_threshold and stoch_rsi_k > self.stoch_rsi_threshold
        
        # Check earnings risk
        earnings_risk = days_until_earnings is not None and days_until_earnings <= 7
        
        # Check volume weakness
        volume_weak = volume_ratio < self.volume_ratio_min
        
        # Assess risk
        if is_overbought and (earnings_risk or volume_weak):
            risk_level = "EXTREM DE RIDICAT"
            risk_factors = []
            
            if is_overbought:
                risk_factors.append("Overbought Extrem")
            if earnings_risk:
                risk_factors.append("Earnings Risk")
            if volume_weak:
                risk_factors.append("Volum Scăzut")
            
            return {
                'level': risk_level,
                'factors': ', '.join(risk_factors),
                'message': f"🔴 {risk_level} ({', '.join(risk_factors)})",
                'color': 'red',
                'severity': 'extreme'
            }
        elif is_overbought or earnings_risk:
            return {
                'level': 'RIDICAT',
                'factors': 'Overbought sau Earnings' if is_overbought else 'Earnings',
                'message': f"🟡 RIDICAT ({'Overbought' if is_overbought else 'Earnings'})",
                'color': 'yellow',
                'severity': 'high'
            }
        else:
            return {
                'level': 'MODERAT',
                'factors': 'Normal',
                'message': '🟢 MODERAT (Condiții normale)',
                'color': 'green',
                'severity': 'moderate'
            }


# Global instance
overbought_protector = OverboughtProtector()
