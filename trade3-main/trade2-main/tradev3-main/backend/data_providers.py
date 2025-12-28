import yfinance as yf
import pandas as pd
from typing import Optional, Dict, List, Any
from fuzzywuzzy import fuzz, process
import aiohttp
import logging
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = "/tmp/trading_cache"
CACHE_DURATION_HOURS = 1

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Extended stock symbols for fuzzy matching (100+ popular symbols)
COMMON_SYMBOLS = [
    # Mega Cap Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL",
    # Large Cap Tech
    "ADBE", "CRM", "INTC", "CSCO", "NFLX", "AMD", "QCOM", "TXN", "INTU", "AMAT",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK", "SCHW", "USB",
    # Healthcare
    "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY",
    # Consumer
    "WMT", "HD", "MCD", "NKE", "COST", "SBUX", "TGT", "LOW", "CVS", "DIS",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Industrials
    "BA", "CAT", "HON", "UPS", "RTX", "LMT", "GE", "MMM", "DE", "EMR",
    # Telecom
    "T", "VZ", "TMUS", "CMCSA",
    # Consumer Staples
    "KO", "PEP", "PG", "PM", "MO", "CL", "EL", "KMB",
    # Special Interest
    "PYPL", "V", "MA", "SQ", "SHOP", "SPOT", "SNAP", "UBER", "LYFT", "ABNB",
    # Energy/Renewables
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
    # Healthcare Tech
    "ISRG", "VRTX", "REGN", "GILD", "BIIB", "ILMN",
    # Oil Services
    "SOC", "SOCO", "SOCL",
    # Additional popular
    "PLTR", "COIN", "RBLX", "ZM", "DOCU", "SNOW", "CRWD", "NET", "DDOG", "MDB",
    # Crypto related
    "MARA", "RIOT", "MSTR", "HOOD",
    # EV & Clean Energy
    "RIVN", "LCID", "NIO", "XPEV", "LI", "PLUG", "FCEL", "ENPH", "SEDG",
    # SPACs & Growth
    "SOFI", "DKNG", "CHPT", "CLOV", "WISH", "SPCE",
    # Biotech
    "MRNA", "BNTX", "CRSP", "EDIT", "NTLA", "BEAM",
    # Semiconductors
    "TSM", "ASML", "LRCX", "KLAC", "MRVL", "ON", "SWKS", "QRVO",
    # International
    "BABA", "JD", "PDD", "BIDU", "NIO", "TME"
]

COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc. (Class A)",
    "GOOG": "Alphabet Inc. (Class C)",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "WMT": "Walmart Inc.",
    "SOC": "Sable Offshore Corp.",
    "PYPL": "PayPal Holdings Inc.",
    "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.",
    "CRM": "Salesforce Inc.",
    "INTC": "Intel Corporation",
    "AMD": "Advanced Micro Devices Inc.",
    "QCOM": "Qualcomm Inc.",
    "CSCO": "Cisco Systems Inc.",
    "ORCL": "Oracle Corporation",
    "COIN": "Coinbase Global Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "SNOW": "Snowflake Inc.",
    "CRWD": "CrowdStrike Holdings Inc.",
    "NET": "Cloudflare Inc.",
    "DDOG": "Datadog Inc.",
    "MDB": "MongoDB Inc.",
    "MARA": "Marathon Digital Holdings",
    "RIOT": "Riot Platforms Inc.",
    "MSTR": "MicroStrategy Inc.",
    "RIVN": "Rivian Automotive Inc.",
    "LCID": "Lucid Group Inc.",
    "NIO": "NIO Inc.",
    "SOFI": "SoFi Technologies Inc.",
    "MRNA": "Moderna Inc.",
    "BNTX": "BioNTech SE",
    "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding N.V.",
    "BABA": "Alibaba Group",
    "JD": "JD.com Inc.",
    "PDD": "PDD Holdings Inc."
}

# Dynamic symbols cache (populated on-demand)
DYNAMIC_SYMBOLS = {}


def get_cache_path(symbol: str, data_type: str) -> str:
    """Get cache file path for a symbol"""
    return os.path.join(CACHE_DIR, f"{symbol}_{data_type}.json")


def is_cache_valid(cache_path: str) -> bool:
    """Check if cache file is still valid (less than 1 hour old)"""
    if not os.path.exists(cache_path):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
    return datetime.now() - file_time < timedelta(hours=CACHE_DURATION_HOURS)


def read_cache(symbol: str, data_type: str) -> Optional[Dict]:
    """Read data from cache"""
    cache_path = get_cache_path(symbol, data_type)
    if is_cache_valid(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
    return None


def write_cache(symbol: str, data_type: str, data: Dict):
    """Write data to cache"""
    cache_path = get_cache_path(symbol, data_type)
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Cache write error: {e}")


def fuzzy_search_symbol(query: str, limit: int = 10) -> List[Dict]:
    """Enhanced fuzzy search for stock symbols - searches both symbols and company names"""
    query_upper = query.upper().replace("-", "").replace(" ", "")
    query_lower = query.lower()
    
    results = []
    
    # Try exact match first
    if query_upper in COMMON_SYMBOLS:
        return [{
            "symbol": query_upper,
            "name": COMPANY_NAMES.get(query_upper, query_upper),
            "match_score": 100,
            "source": "known"
        }]
    
    # Check dynamic symbols cache
    if query_upper in DYNAMIC_SYMBOLS:
        return [{
            "symbol": query_upper,
            "name": DYNAMIC_SYMBOLS[query_upper].get("name", query_upper),
            "match_score": 100,
            "source": "dynamic"
        }]
    
    # Fuzzy matching on symbols
    symbol_matches = process.extract(query_upper, COMMON_SYMBOLS, scorer=fuzz.ratio, limit=limit)
    
    for symbol, score in symbol_matches:
        if score > 40:
            results.append({
                "symbol": symbol,
                "name": COMPANY_NAMES.get(symbol, symbol),
                "match_score": score,
                "source": "symbol_match"
            })
    
    # Fuzzy matching on company names
    name_to_symbol = {v.lower(): k for k, v in COMPANY_NAMES.items()}
    company_names = list(name_to_symbol.keys())
    
    name_matches = process.extract(query_lower, company_names, scorer=fuzz.partial_ratio, limit=limit)
    
    for name, score in name_matches:
        if score > 50:
            symbol = name_to_symbol[name]
            # Avoid duplicates
            existing = next((r for r in results if r["symbol"] == symbol), None)
            if existing:
                existing["match_score"] = max(existing["match_score"], score)
            else:
                results.append({
                    "symbol": symbol,
                    "name": COMPANY_NAMES.get(symbol, symbol),
                    "match_score": score,
                    "source": "name_match"
                })
    
    # Sort by score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    
    return results[:limit]


async def fetch_symbol_on_demand(symbol: str) -> Dict[str, Any]:
    """
    Fetch data for a new/unknown symbol directly from Yahoo Finance.
    Returns data and caches it for 1 hour.
    """
    symbol = symbol.upper().strip()
    
    # Check cache first
    cached = read_cache(symbol, "ondemand")
    if cached:
        logger.info(f"Returning cached data for {symbol}")
        return cached
    
    logger.info(f"Fetching on-demand data for {symbol}")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get basic info
        info = ticker.info
        
        if not info or info.get('regularMarketPrice') is None:
            # Try to get historical data as fallback
            hist = ticker.history(period="5d")
            if hist.empty:
                return {
                    "success": False,
                    "error": f"Simbolul {symbol} nu există pe nicio bursă. Vă rugăm verificați ortografia.",
                    "symbol": symbol
                }
        
        # Get company name
        company_name = info.get('longName') or info.get('shortName') or symbol
        
        # Store in dynamic symbols cache
        DYNAMIC_SYMBOLS[symbol] = {
            "name": company_name,
            "fetched_at": datetime.now().isoformat()
        }
        
        # Add to COMMON_SYMBOLS for future searches
        if symbol not in COMMON_SYMBOLS:
            COMMON_SYMBOLS.append(symbol)
            COMPANY_NAMES[symbol] = company_name
        
        result = {
            "success": True,
            "symbol": symbol,
            "name": company_name,
            "fetched_at": datetime.now().isoformat(),
            "info": {
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange')
            }
        }
        
        # Cache the result
        write_cache(symbol, "ondemand", result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching on-demand data for {symbol}: {e}")
        return {
            "success": False,
            "error": f"Eroare la preluarea datelor pentru {symbol}: {str(e)}",
            "symbol": symbol
        }


class BaseProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    async def get_ohlc_data(
        self,
        symbol: str,
        period: str = "6mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        raise NotImplementedError

    async def get_current_price(self, symbol: str) -> Dict:
        raise NotImplementedError


class YahooFinanceProvider(BaseProvider):
    """Yahoo Finance data provider with caching"""
    
    async def get_ohlc_data(
        self,
        symbol: str,
        period: str = "1y",  # Changed to 1 year for more data
        interval: str = "1d"
    ) -> pd.DataFrame:
        try:
            # Check cache first
            cache_key = f"{period}_{interval}"
            cached = read_cache(symbol, f"ohlc_{cache_key}")
            
            if cached:
                logger.info(f"Using cached OHLC data for {symbol}")
                df = pd.DataFrame(cached['data'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            
            logger.info(f"Fetching fresh OHLC data for {symbol}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            df = df.reset_index()
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            if 'date' not in df.columns and 'datetime' in df.columns:
                df = df.rename(columns={'datetime': 'date'})
            
            # Cache the data
            cache_data = {
                'data': df.to_dict('records'),
                'cached_at': datetime.now().isoformat()
            }
            # Convert datetime to string for JSON serialization
            for record in cache_data['data']:
                if 'date' in record and hasattr(record['date'], 'isoformat'):
                    record['date'] = record['date'].isoformat()
            
            write_cache(symbol, f"ohlc_{cache_key}", cache_data)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return pd.DataFrame()

    async def get_current_price(self, symbol: str) -> Dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', info.get('currentPrice', 0)),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'high': info.get('regularMarketDayHigh', 0),
                'low': info.get('regularMarketDayLow', 0),
                'open': info.get('regularMarketOpen', 0),
                'previous_close': info.get('regularMarketPreviousClose', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return {'symbol': symbol, 'price': 0, 'error': str(e)}

    async def get_fundamentals(self, symbol: str) -> Dict:
        """Get fundamental data with caching"""
        try:
            # Check cache
            cached = read_cache(symbol, "fundamentals")
            if cached:
                logger.info(f"Using cached fundamentals for {symbol}")
                return cached
            
            logger.info(f"Fetching fresh fundamentals for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            fundamentals = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'profit_margin': info.get('profitMargins', 0),
                'revenue': info.get('totalRevenue', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'gross_profit': info.get('grossProfits', 0),
                'ebitda': info.get('ebitda', 0),
                'free_cash_flow': info.get('freeCashflow', 0),
                'total_debt': info.get('totalDebt', 0),
                'total_cash': info.get('totalCash', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'return_on_assets': info.get('returnOnAssets', 0),
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'average_volume': info.get('averageVolume', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'earnings_date': str(info.get('earningsTimestamp', 'N/A')),
                'currency': info.get('currency', 'USD')
            }
            
            # Cache the data
            write_cache(symbol, "fundamentals", fundamentals)
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}


def get_provider(name: str, api_key: Optional[str] = None) -> BaseProvider:
    providers = {
        'yahoo': YahooFinanceProvider,
    }
    
    provider_class = providers.get(name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {name}")
    
    return provider_class(api_key)
