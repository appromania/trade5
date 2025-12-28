import yfinance as yf
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketContext:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    async def get_context(self) -> Dict[str, Any]:
        """Get global market context (VIX, S&P 500)"""
        try:
            # Check cache
            if 'context' in self.cache:
                cached_time = self.cache.get('timestamp', datetime.min)
                if (datetime.now() - cached_time).seconds < self.cache_duration:
                    return self.cache['context']
            
            # Fetch VIX
            vix_data = self._get_vix()
            
            # Fetch S&P 500
            sp500_data = self._get_sp500()
            
            context = {
                'vix': vix_data,
                'sp500': sp500_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update cache
            self.cache['context'] = context
            self.cache['timestamp'] = datetime.now()
            
            return context
            
        except Exception as e:
            logger.error(f"Error fetching market context: {str(e)}")
            return {
                'vix': {'value': None, 'level': 'unknown', 'high_volatility': False},
                'sp500': {'trend': 'unknown', 'change_percent': 0}
            }
    
    def _get_vix(self) -> Dict[str, Any]:
        """Get VIX (Volatility Index)"""
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="1d")
            
            if hist.empty:
                return {'value': None, 'level': 'unknown', 'high_volatility': False}
            
            vix_value = float(hist['Close'].iloc[-1])
            
            # VIX interpretation
            if vix_value < 15:
                level = "SCĂZUTĂ"
                high_vol = False
            elif vix_value < 20:
                level = "NORMALĂ"
                high_vol = False
            elif vix_value < 30:
                level = "RIDICATĂ"
                high_vol = True
            else:
                level = "FOARTE RIDICATĂ"
                high_vol = True
            
            return {
                'value': round(vix_value, 2),
                'level': level,
                'high_volatility': high_vol
            }
        except Exception as e:
            logger.error(f"VIX fetch error: {str(e)}")
            return {'value': None, 'level': 'unknown', 'high_volatility': False}
    
    def _get_sp500(self) -> Dict[str, Any]:
        """Get S&P 500 trend"""
        try:
            sp500 = yf.Ticker("^GSPC")
            hist = sp500.history(period="5d")
            
            if len(hist) < 2:
                return {'trend': 'unknown', 'change_percent': 0}
            
            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2])
            
            change_percent = ((current_price - prev_price) / prev_price) * 100
            
            trend = "BULLISH" if change_percent > 0 else "BEARISH"
            
            return {
                'trend': trend,
                'change_percent': round(change_percent, 2),
                'current_price': round(current_price, 2)
            }
        except Exception as e:
            logger.error(f"S&P 500 fetch error: {str(e)}")
            return {'trend': 'unknown', 'change_percent': 0}
    
    async def check_alerts(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Check for various alerts"""
        alerts = []
        
        # Volatility alert
        if context.get('vix', {}).get('high_volatility'):
            alerts.append({
                'type': 'VOLATILITATE',
                'severity': 'high',
                'message': f"Volatilitate ridicată pe piață (VIX: {context['vix']['value']}). Prudență!"
            })
        
        # Volume exhaustion
        if indicators['volume']['exhaustion']:
            alerts.append({
                'type': 'VOLUM',
                'severity': 'medium',
                'message': 'Volum scăzut - Creșterea pe volum scăzut poate fi o capcană'
            })
        
        # Stoch RSI extreme
        if indicators['stoch_rsi']['k'] > 85:
            alerts.append({
                'type': 'SUPRACUMPĂRAT',
                'severity': 'high',
                'message': f"Stoch RSI extrem de ridicat ({indicators['stoch_rsi']['k']}%). NU cumpăra aici!"
            })
        
        # Price vs resistance
        current_price = indicators['price']['current']
        resistance = indicators['pivots']['resistance']
        
        if current_price >= resistance * 0.98:
            alerts.append({
                'type': 'REZISTENȚĂ',
                'severity': 'medium',
                'message': f'Preț aproape de rezistență ({resistance}). Posibil rejection sau breakout.'
            })
        
        # Gaps
        if indicators['gaps']:
            recent_gap = indicators['gaps'][-1]
            if abs(recent_gap['gap_size']) > 3:
                alerts.append({
                    'type': 'GAP',
                    'severity': 'medium',
                    'message': f"Gap neacoperit de {recent_gap['gap_size']}% la ${recent_gap['gap_price']}"
                })
        
        # Ranging market
        if indicators['adx']['regime'] == 'RANGING':
            alerts.append({
                'type': 'PIAȚĂ LATERALĂ',
                'severity': 'medium',
                'message': f"ADX sub 20 ({indicators['adx']['value']}) - Piață laterală, semnale nesigure"
            })
        
        # Earnings check (simplified - would need external API for real data)
        # This is a placeholder
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            if calendar is not None and 'Earnings Date' in calendar:
                alerts.append({
                    'type': 'EARNINGS',
                    'severity': 'high',
                    'message': 'Raport financiar programat în curând. Risc de volatilitate mare!'
                })
        except:
            pass
        
        return alerts