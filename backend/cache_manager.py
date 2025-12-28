"""
Cache Management Utilities
Clear cache for data providers and trading system
"""
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache directories
TRADING_CACHE_DIR = "/tmp/trading_cache"
LIVE_PRICE_CACHE_DIR = "/tmp/live_price_cache"


def clear_all_cache():
    """Clear all cache directories"""
    cleared = []
    
    # Clear trading cache
    if os.path.exists(TRADING_CACHE_DIR):
        try:
            shutil.rmtree(TRADING_CACHE_DIR)
            os.makedirs(TRADING_CACHE_DIR, exist_ok=True)
            cleared.append("trading_cache")
            logger.info(f"✅ Cleared trading cache: {TRADING_CACHE_DIR}")
        except Exception as e:
            logger.error(f"❌ Error clearing trading cache: {e}")
    
    # Clear live price cache
    if os.path.exists(LIVE_PRICE_CACHE_DIR):
        try:
            shutil.rmtree(LIVE_PRICE_CACHE_DIR)
            os.makedirs(LIVE_PRICE_CACHE_DIR, exist_ok=True)
            cleared.append("live_price_cache")
            logger.info(f"✅ Cleared live price cache: {LIVE_PRICE_CACHE_DIR}")
        except Exception as e:
            logger.error(f"❌ Error clearing live price cache: {e}")
    
    return cleared


def clear_symbol_cache(symbol: str):
    """Clear cache for a specific symbol"""
    cleared = []
    
    # Clear trading cache for symbol
    if os.path.exists(TRADING_CACHE_DIR):
        for file in Path(TRADING_CACHE_DIR).glob(f"{symbol}_*"):
            try:
                file.unlink()
                cleared.append(str(file.name))
                logger.info(f"✅ Cleared cache for {symbol}: {file.name}")
            except Exception as e:
                logger.error(f"❌ Error clearing {file.name}: {e}")
    
    # Clear live price cache for symbol
    if os.path.exists(LIVE_PRICE_CACHE_DIR):
        for file in Path(LIVE_PRICE_CACHE_DIR).glob(f"{symbol}_*"):
            try:
                file.unlink()
                cleared.append(str(file.name))
                logger.info(f"✅ Cleared live cache for {symbol}: {file.name}")
            except Exception as e:
                logger.error(f"❌ Error clearing {file.name}: {e}")
    
    return cleared


def get_cache_stats():
    """Get cache statistics"""
    stats = {
        'trading_cache': {
            'path': TRADING_CACHE_DIR,
            'exists': os.path.exists(TRADING_CACHE_DIR),
            'files': 0,
            'size_mb': 0
        },
        'live_price_cache': {
            'path': LIVE_PRICE_CACHE_DIR,
            'exists': os.path.exists(LIVE_PRICE_CACHE_DIR),
            'files': 0,
            'size_mb': 0
        }
    }
    
    # Trading cache stats
    if os.path.exists(TRADING_CACHE_DIR):
        files = list(Path(TRADING_CACHE_DIR).glob("*"))
        stats['trading_cache']['files'] = len(files)
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        stats['trading_cache']['size_mb'] = round(total_size / (1024 * 1024), 2)
    
    # Live price cache stats
    if os.path.exists(LIVE_PRICE_CACHE_DIR):
        files = list(Path(LIVE_PRICE_CACHE_DIR).glob("*"))
        stats['live_price_cache']['files'] = len(files)
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        stats['live_price_cache']['size_mb'] = round(total_size / (1024 * 1024), 2)
    
    return stats
