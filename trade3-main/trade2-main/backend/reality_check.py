"""
Reality Check Module - Validare Date Live și Sincronizare Obligatorie
Implementat conform specificațiilor pentru prevenirea halucinațiilor de preț
"""
import yfinance as yf
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# Cache pentru validare live (1 minut)
LIVE_CACHE_DIR = "/tmp/live_price_cache"
LIVE_CACHE_DURATION_MINUTES = 1
os.makedirs(LIVE_CACHE_DIR, exist_ok=True)


class RealityCheckModule:
    """
    Modulul Reality Check asigură că datele folosite sunt REALE și ACTUALE
    """
    
    def __init__(self):
        self.max_price_diff_percent = 5.0  # 5% diferență maximă acceptabilă
        
    def get_live_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obține prețul LIVE direct de la Yahoo Finance (cache 1 minut)
        """
        try:
            # Check cache (1 minut)
            cache_path = os.path.join(LIVE_CACHE_DIR, f"{symbol}_live.json")
            
            if os.path.exists(cache_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
                if datetime.now() - file_time < timedelta(minutes=LIVE_CACHE_DURATION_MINUTES):
                    with open(cache_path, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"✅ Using cached LIVE price for {symbol} (age: {(datetime.now() - file_time).seconds}s)")
                        return cached_data
            
            # Fetch fresh live data
            logger.info(f"🔄 Fetching FRESH live price for {symbol}...")
            ticker = yf.Ticker(symbol)
            
            # Get current price
            info = ticker.info
            
            # Try multiple price fields (Yahoo Finance can be inconsistent)
            current_price = None
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    current_price = float(info[field])
                    break
            
            if current_price is None:
                # Fallback: try historical data (last close)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            
            if current_price is None:
                logger.error(f"❌ Cannot fetch live price for {symbol}")
                return None
            
            live_data = {
                'symbol': symbol,
                'price': current_price,
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo_finance_live',
                'market_open': info.get('regularMarketOpen', None),
                'market_high': info.get('regularMarketDayHigh', None),
                'market_low': info.get('regularMarketDayLow', None),
                'volume': info.get('regularMarketVolume', 0),
                'previous_close': info.get('regularMarketPreviousClose', current_price)
            }
            
            # Cache the data
            with open(cache_path, 'w') as f:
                json.dump(live_data, f)
            
            logger.info(f"✅ LIVE price for {symbol}: ${current_price:.2f}")
            return live_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching live price for {symbol}: {e}")
            return None
    
    def validate_price(self, symbol: str, cached_price: float) -> Dict[str, Any]:
        """
        Validează prețul cached față de prețul LIVE
        Returnează: {valid: bool, live_price: float, diff_percent: float, error: str}
        """
        live_data = self.get_live_price(symbol)
        
        if live_data is None:
            return {
                'valid': False,
                'error': f"Nu se poate obține prețul LIVE pentru {symbol}",
                'cached_price': cached_price,
                'live_price': None,
                'diff_percent': None,
                'status': 'ERROR'
            }
        
        live_price = live_data['price']
        diff_percent = abs((cached_price - live_price) / live_price * 100)
        
        is_valid = diff_percent <= self.max_price_diff_percent
        
        result = {
            'valid': is_valid,
            'cached_price': cached_price,
            'live_price': live_price,
            'diff_percent': round(diff_percent, 2),
            'timestamp': live_data['timestamp'],
            'error': None,
            'status': 'OK' if is_valid else 'PRICE_MISMATCH'
        }
        
        if not is_valid:
            result['error'] = (
                f"⚠️ EROARE SINCRONIZARE: Prețul din cache (${cached_price:.2f}) "
                f"diferă cu {diff_percent:.1f}% față de prețul LIVE (${live_price:.2f})"
            )
            logger.warning(result['error'])
        else:
            logger.info(f"✅ Price validation OK for {symbol}: diff = {diff_percent:.2f}%")
        
        return result
    
    def validate_analysis_data(self, symbol: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validează toate datele unei analize față de datele LIVE
        Returnează: validation_report cu status, warnings, errors
        """
        validation_report = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'status': 'VALID',
            'warnings': [],
            'errors': [],
            'live_data': None,
            'price_validation': None
        }
        
        # Validare preț
        cached_price = analysis_data.get('current_price', 0)
        price_validation = self.validate_price(symbol, cached_price)
        validation_report['price_validation'] = price_validation
        
        if not price_validation['valid']:
            validation_report['status'] = 'INVALID'
            validation_report['errors'].append(price_validation['error'])
        
        # Validare vârstă date
        timestamp_str = analysis_data.get('timestamp')
        if timestamp_str:
            try:
                data_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age_minutes = (datetime.now() - data_time.replace(tzinfo=None)).total_seconds() / 60
                
                if age_minutes > 60:
                    validation_report['warnings'].append(
                        f"⚠️ Datele au {age_minutes:.0f} minute vechime. Recomandăm reîncărcare."
                    )
            except:
                pass
        
        # Adaugă datele LIVE
        live_data = self.get_live_price(symbol)
        if live_data:
            validation_report['live_data'] = live_data
        
        return validation_report


# Global instance
reality_check = RealityCheckModule()


def validate_symbol_price(symbol: str, cached_price: float) -> Dict[str, Any]:
    """
    Helper function pentru validare rapidă
    """
    return reality_check.validate_price(symbol, cached_price)


def get_live_market_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Helper function pentru obținere date live
    """
    return reality_check.get_live_price(symbol)
