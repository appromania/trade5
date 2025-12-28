"""
After-Hours Momentum Scanner
Identifică "Top Movers" în timpul after-hours (16:00-20:00 ET) și pre-market (4:00-9:30 ET)
"""
import yfinance as yf
import logging
from typing import List, Dict, Any
from datetime import datetime, time
import pandas as pd

logger = logging.getLogger(__name__)

# S&P 500 top movers candidates (liquid stocks)
AH_WATCHLIST = [
    # Mega Cap Tech (lichiditate garantată)
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    # Large Cap Tech
    "AMD", "INTC", "NFLX", "ADBE", "CRM", "ORCL", "QCOM",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS",
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "MRK",
    # Consumer
    "WMT", "HD", "MCD", "DIS", "COST",
    # Energy
    "XOM", "CVX",
    # Hot Growth
    "COIN", "PLTR", "SNOW", "CRWD", "NET", "DDOG",
    # Volatile (penny stocks alternative)
    "MARA", "RIOT", "RIVN", "LCID", "SOFI"
]


class AfterHoursScanner:
    """
    Scanner pentru identificarea mișcărilor after-hours
    """
    
    def __init__(self):
        self.min_volume_ah = 50000  # Volum minim after-hours
        self.min_volume_ratio = 0.20  # 20% din volumul mediu zilnic
        self.min_price_change = 3.0  # ±3% mișcare minimă
        
    def scan_after_hours(
        self,
        symbols: List[str] = None,
        min_change_percent: float = None,
        min_volume: int = None
    ) -> List[Dict[str, Any]]:
        """
        Scanează simboluri pentru mișcări after-hours
        
        Returns:
            List of movers with details
        """
        if symbols is None:
            symbols = AH_WATCHLIST
        
        if min_change_percent is None:
            min_change_percent = self.min_price_change
        
        if min_volume is None:
            min_volume = self.min_volume_ah
        
        movers = []
        
        logger.info(f"🌙 Scanning {len(symbols)} symbols for after-hours movers...")
        
        for symbol in symbols:
            try:
                mover_data = self._analyze_symbol_ah(
                    symbol, 
                    min_change_percent, 
                    min_volume
                )
                
                if mover_data:
                    movers.append(mover_data)
                    logger.info(f"✅ Found mover: {symbol} ({mover_data['change_percent']:+.2f}%)")
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Sort by absolute change percent (descending)
        movers.sort(key=lambda x: abs(x['change_percent']), reverse=True)
        
        logger.info(f"🌙 Found {len(movers)} after-hours movers")
        return movers
    
    def _analyze_symbol_ah(
        self, 
        symbol: str, 
        min_change_percent: float, 
        min_volume: int
    ) -> Dict[str, Any]:
        """
        Analizează un singur simbol pentru mișcare after-hours
        """
        ticker = yf.Ticker(symbol)
        
        # Get info
        info = ticker.info
        
        if not info:
            return None
        
        # Extract prices
        regular_close = info.get('regularMarketPreviousClose', 0)
        post_market_price = info.get('postMarketPrice', None)
        pre_market_price = info.get('preMarketPrice', None)
        
        # Determine which price to use (post-market or pre-market)
        ah_price = post_market_price or pre_market_price
        
        if not ah_price or not regular_close or regular_close == 0:
            return None
        
        # Calculate change
        change_percent = ((ah_price - regular_close) / regular_close) * 100
        change_absolute = ah_price - regular_close
        
        # Check if meets criteria
        if abs(change_percent) < min_change_percent:
            return None
        
        # Extract volume
        post_volume = info.get('postMarketVolume', 0) or 0
        pre_volume = info.get('preMarketVolume', 0) or 0
        ah_volume = post_volume + pre_volume
        
        # Get average volume
        avg_volume = info.get('averageVolume', 0) or info.get('averageDailyVolume10Day', 0) or 0
        
        # Check volume criteria
        if ah_volume < min_volume:
            return None
        
        if avg_volume > 0:
            volume_ratio = ah_volume / avg_volume
            if volume_ratio < self.min_volume_ratio:
                return None
        else:
            volume_ratio = 0
        
        # Determine market phase
        if post_market_price:
            market_phase = "After-Hours"
            ah_time = info.get('postMarketTime', 'N/A')
        else:
            market_phase = "Pre-Market"
            ah_time = info.get('preMarketTime', 'N/A')
        
        # Get company name
        company_name = info.get('longName', symbol)
        
        # Calculate market cap
        market_cap = info.get('marketCap', 0)
        
        # Assess risk level
        risk_level = self._assess_ah_risk(
            change_percent, 
            volume_ratio, 
            market_cap
        )
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'regular_close': round(regular_close, 2),
            'ah_price': round(ah_price, 2),
            'change_absolute': round(change_absolute, 2),
            'change_percent': round(change_percent, 2),
            'ah_volume': ah_volume,
            'avg_volume': avg_volume,
            'volume_ratio': round(volume_ratio, 2),
            'market_phase': market_phase,
            'ah_time': str(ah_time),
            'market_cap': market_cap,
            'risk_level': risk_level,
            'direction': 'up' if change_percent > 0 else 'down',
            'alert_type': self._generate_alert_type(change_percent, volume_ratio)
        }
    
    def _assess_ah_risk(
        self, 
        change_percent: float, 
        volume_ratio: float, 
        market_cap: int
    ) -> str:
        """
        Evaluează nivelul de risc pentru o mișcare after-hours
        """
        # High risk factors
        risk_score = 0
        
        # Extreme price move
        if abs(change_percent) > 10:
            risk_score += 3
        elif abs(change_percent) > 5:
            risk_score += 2
        else:
            risk_score += 1
        
        # Low volume
        if volume_ratio < 0.3:
            risk_score += 2
        
        # Small cap (more volatile)
        if market_cap < 1e9:  # < $1B
            risk_score += 2
        elif market_cap < 10e9:  # < $10B
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 6:
            return "EXTREM"
        elif risk_score >= 4:
            return "RIDICAT"
        elif risk_score >= 2:
            return "MODERAT"
        else:
            return "SCĂZUT"
    
    def _generate_alert_type(self, change_percent: float, volume_ratio: float) -> str:
        """
        Generează tipul de alertă bazat pe caracteristicile mișcării
        """
        if abs(change_percent) > 10 and volume_ratio > 0.5:
            return "BREAKOUT_MAJOR"
        elif abs(change_percent) > 5 and volume_ratio > 0.3:
            return "MOMENTUM_STRONG"
        elif volume_ratio < 0.3:
            return "LOW_VOLUME_WARNING"
        else:
            return "STANDARD_MOVE"


# Global instance
after_hours_scanner = AfterHoursScanner()


def scan_after_hours_movers(
    symbols: List[str] = None,
    min_change: float = 3.0,
    min_volume: int = 50000
) -> List[Dict[str, Any]]:
    """
    Helper function pentru scanare rapidă
    """
    return after_hours_scanner.scan_after_hours(
        symbols=symbols,
        min_change_percent=min_change,
        min_volume=min_volume
    )
