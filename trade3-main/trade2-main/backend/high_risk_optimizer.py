"""
Modul High-Risk Assets (SOC) - Optimizări pentru Protecția Capitalului
Implementare conform specificațiilor pentru gestionarea activelor cu volatilitate ridicată
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HighRiskOptimizer:
    """
    Optimizator pentru active high-risk (ex: SOC, penny stocks, volatilitate ridicată)
    """
    
    def __init__(self):
        self.volume_threshold = 0.8  # Volume Ratio minim acceptabil
        self.debt_to_equity_max = 200  # Debt/Equity max pentru BUY
        self.earnings_warning_days = 7  # Alerta cu X zile înainte de earnings
        
    def calculate_dynamic_take_profit(
        self,
        current_price: float,
        ema_50: float,
        ema_200: Optional[float],
        donchian_upper: float,
        atr: float
    ) -> Dict[str, Any]:
        """
        Ierarhizare Rezistențelor Dinamice:
        - Dacă preț < EMA 50 sau EMA 200: TP = EMA - 2% (rezistență intermediară)
        - Altfel: TP = Donchian Upper (rezistență istorică)
        """
        
        # Verifică dacă prețul este sub mediile mobile
        below_ema_50 = current_price < ema_50
        below_ema_200 = ema_200 is not None and current_price < ema_200
        
        if below_ema_50 or below_ema_200:
            # Preț sub EMA - folosește rezistență intermediară
            if below_ema_50:
                reference_ema = ema_50
                ema_type = "EMA 50"
            else:
                reference_ema = ema_200
                ema_type = "EMA 200"
            
            # TP = EMA - 2% pentru confirmare
            take_profit = reference_ema * 0.98
            
            reason = (
                f"⚠️ REZISTENȚĂ INTERMEDIARĂ: Preț sub {ema_type} (${reference_ema:.2f}). "
                f"TP ajustat la ${take_profit:.2f} (2% sub {ema_type}) pentru confirmare termen scurt."
            )
            
            return {
                'take_profit': take_profit,
                'type': 'intermediate_resistance',
                'reference_level': reference_ema,
                'reason': reason,
                'adjusted': True
            }
        else:
            # Preț peste EMA - folosește rezistență istorică (Donchian)
            take_profit = donchian_upper
            
            reason = (
                f"✅ REZISTENȚĂ ISTORICĂ: Preț peste EMA 50/200. "
                f"TP la Donchian Upper ${take_profit:.2f}."
            )
            
            return {
                'take_profit': take_profit,
                'type': 'historical_resistance',
                'reference_level': donchian_upper,
                'reason': reason,
                'adjusted': False
            }
    
    def check_volume_divergence(
        self,
        volume_ratio: float,
        price_change_percent: float
    ) -> Optional[Dict[str, Any]]:
        """
        Corelarea Volumului cu Validitatea Trendului:
        - Dacă Volume Ratio < 0.8x ȘI preț crește: AVERTISMENT CRITIC
        """
        
        if volume_ratio < self.volume_threshold and price_change_percent > 0:
            warning = {
                'type': 'VOLUME_DIVERGENCE',
                'severity': 'critical',
                'volume_ratio': volume_ratio,
                'price_change': price_change_percent,
                'message': (
                    f"🚨 DIVERGENȚĂ DE VOLUM: Creștere speculativă fără suport de cumpărare! "
                    f"Volum {volume_ratio:.2f}x (sub {self.volume_threshold}x) în timp ce prețul crește cu {price_change_percent:.1f}%. "
                    f"Acest tip de mișcare este nesustenabilă și poate fi o capcană."
                ),
                'action': 'NU CUMPĂRA - Așteptați confirmare cu volum mare',
                'confidence_penalty': 30  # Scade Confidence Score cu 30%
            }
            
            logger.warning(f"⚠️ Volume divergence detected: {volume_ratio:.2f}x, price +{price_change_percent:.1f}%")
            return warning
        
        return None
    
    def check_financial_health_block(
        self,
        fundamentals: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Integrarea Sănătății Financiare în Semnalul Tehnic:
        - Dacă Free Cash Flow < 0 ȘI Debt/Equity > 200%: BLOCARE BUY/HOLD
        """
        
        if fundamentals is None:
            return None
        
        free_cash_flow = fundamentals.get('free_cash_flow', 0)
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        
        # Conversie pentru verificare (uneori pot fi None)
        try:
            fcf = float(free_cash_flow) if free_cash_flow else 0
            dte = float(debt_to_equity) if debt_to_equity else 0
        except (ValueError, TypeError):
            return None
        
        # BLOCARE CRITICĂ
        if fcf < 0 and dte > self.debt_to_equity_max:
            block = {
                'type': 'FINANCIAL_HEALTH_BLOCK',
                'severity': 'critical',
                'free_cash_flow': fcf,
                'debt_to_equity': dte,
                'message': (
                    f"🛑 BLOCARE: SĂNĂTATE FINANCIARĂ DEZASTRUOASĂ! "
                    f"Free Cash Flow negativ (${fcf:,.0f}) ȘI Debt/Equity > 200% ({dte:.0f}%). "
                    f"Compania arde bani și este supraleviată. "
                    f"FORȚAT NEUTRAL/LIQUIDATE indiferent de indicatori tehnici."
                ),
                'action': 'BLOCARE BUY/HOLD - Forțat NEUTRAL sau LIQUIDATE',
                'forced_signal': 'LIQUIDATE' if fcf < -1000000000 else 'NEUTRAL'  # -1B FCF = LIQUIDATE
            }
            
            logger.critical(f"🛑 Financial health block triggered: FCF={fcf}, D/E={dte}")
            return block
        
        return None
    
    def calculate_atr_based_stop_loss(
        self,
        current_price: float,
        atr: float,
        support: float
    ) -> Dict[str, Any]:
        """
        Optimizarea Stop-Loss bazată pe ATR:
        - SL = Preț curent - (1.5 * ATR)
        - Verificare: SL nu trebuie să fie deasupra suportului major
        """
        
        # Calculare SL bazat pe ATR
        sl_atr = current_price - (1.5 * atr)
        
        # Verificare vs suport major
        if sl_atr > support:
            warning = {
                'type': 'STOP_LOSS_WARNING',
                'severity': 'medium',
                'sl_atr_based': sl_atr,
                'support_level': support,
                'message': (
                    f"⚠️ Stop Loss prea strâns: SL calculat (${sl_atr:.2f}) este deasupra "
                    f"suportului major (${support:.2f}). Risc ridicat de lichidare prin zgomot de piață. "
                    f"Recomandăm SL sub suport: ${support * 0.98:.2f}"
                ),
                'recommended_sl': support * 0.98  # 2% sub suport
            }
            
            logger.warning(f"⚠️ SL too tight: ${sl_atr:.2f} above support ${support:.2f}")
            return {
                'stop_loss': warning['recommended_sl'],
                'warning': warning,
                'adjusted': True
            }
        
        # SL OK
        return {
            'stop_loss': sl_atr,
            'warning': None,
            'adjusted': False,
            'reason': f"SL bazat pe ATR: Preț - (1.5 * ATR) = ${sl_atr:.2f}"
        }
    
    def check_earnings_proximity(
        self,
        earnings_date: Optional[str],
        days_until_earnings: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Alertă de Proximitate Earnings:
        - Cu 7 zile înainte: Transform orice semnal în 'High Volatility Warning'
        - Sugestie: Reducere expunere 50%
        """
        
        if days_until_earnings is not None and days_until_earnings <= self.earnings_warning_days:
            alert = {
                'type': 'EARNINGS_WARNING',
                'severity': 'critical',
                'days_until': days_until_earnings,
                'earnings_date': earnings_date,
                'message': (
                    f"📊 EARNINGS ALERT: Raport financiar în {days_until_earnings} zile! "
                    f"Risc de VOLATILITATE EXTREMĂ. Gap-uri de ±5-15% sunt posibile overnight. "
                    f"🚨 TRANSFORMARE SEMNAL în 'HIGH VOLATILITY WARNING'."
                ),
                'action': 'Reducere expunere cu 50% ÎNAINTE de earnings',
                'forced_signal_override': True,
                'forced_signal': 'WAIT',  # Force WAIT
                'forced_confidence': 20
            }
            
            logger.critical(f"📊 Earnings in {days_until_earnings} days - forcing WAIT signal")
            return alert
        
        return None
    
    def calculate_smart_exit(
        self,
        entry_price: float,
        current_price: float,
        confidence_score: int
    ) -> Optional[Dict[str, Any]]:
        """
        Verdict de 'Smart Exit':
        - Dacă profit > 80% ȘI Confidence Score < 30%: SECURIZEAZĂ PROFITUL
        """
        
        if entry_price <= 0:
            return None
        
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        
        if profit_percent > 80 and confidence_score < 30:
            verdict = {
                'type': 'SMART_EXIT',
                'severity': 'high',
                'profit_percent': profit_percent,
                'confidence_score': confidence_score,
                'message': (
                    f"💰 SMART EXIT: Profit nerealizat de {profit_percent:.1f}% cu Confidence scăzută ({confidence_score}%). "
                    f"🎯 VERDICT: Securizează profitul ACUM (SELL 70%). "
                    f"Nu lăsa un trade câștigător să devină pierzător din cauza lăcomiei! "
                    f"Lăcomia distrue mai mulți traderi decât pierderile."
                ),
                'action': 'SELL 70% din poziție la preț curent',
                'sell_price': current_price,
                'keep_percentage': 30,
                'recommended_signal': 'SELL'
            }
            
            logger.info(f"💰 Smart Exit triggered: {profit_percent:.1f}% profit, {confidence_score}% confidence")
            return verdict
        
        return None


# Global instance
high_risk_optimizer = HighRiskOptimizer()
