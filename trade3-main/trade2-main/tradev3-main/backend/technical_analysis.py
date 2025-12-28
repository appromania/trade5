import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._ensure_numeric()
    
    def _ensure_numeric(self):
        """Ensure all price columns are numeric"""
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    
    def calculate_ema(self, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return self.df['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return self.df['close'].rolling(window=period).mean()
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_stoch_rsi(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic RSI"""
        rsi = self.calculate_rsi(period)
        
        stoch_rsi = (rsi - rsi.rolling(window=period).min()) / \
                    (rsi.rolling(window=period).max() - rsi.rolling(window=period).min()) * 100
        
        k = stoch_rsi.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()
        
        return {'k': k, 'd': d, 'stoch_rsi': stoch_rsi}
    
    def calculate_adx(self, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        pos_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        neg_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        pos_di = 100 * (pos_dm.rolling(window=period).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
        adx = dx.rolling(window=period).mean()
        
        return {'adx': adx, 'pos_di': pos_di, 'neg_di': neg_di}
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        return atr
    
    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD"""
        ema_fast = self.calculate_ema(fast)
        ema_slow = self.calculate_ema(slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
    
    def calculate_heikin_ashi(self) -> pd.DataFrame:
        """Calculate Heikin Ashi candles"""
        ha_df = pd.DataFrame(index=self.df.index)
        
        ha_df['close'] = (self.df['open'] + self.df['high'] + 
                          self.df['low'] + self.df['close']) / 4
        
        ha_df['open'] = 0.0
        for i in range(len(self.df)):
            if i == 0:
                ha_df.loc[i, 'open'] = (self.df.loc[i, 'open'] + self.df.loc[i, 'close']) / 2
            else:
                ha_df.loc[i, 'open'] = (ha_df.loc[i-1, 'open'] + ha_df.loc[i-1, 'close']) / 2
        
        ha_df['high'] = self.df[['high', 'open', 'close']].max(axis=1)
        ha_df['low'] = self.df[['low', 'open', 'close']].min(axis=1)
        
        return ha_df
    
    def detect_gaps(self) -> list:
        """Detect price gaps"""
        gaps = []
        for i in range(1, len(self.df)):
            prev_close = self.df.loc[i-1, 'close']
            curr_open = self.df.loc[i, 'open']
            
            gap_size = ((curr_open - prev_close) / prev_close) * 100
            
            if abs(gap_size) > 2:
                gaps.append({
                    'index': i,
                    'date': self.df.loc[i, 'date'],
                    'gap_size': round(gap_size, 2),
                    'gap_price': round(prev_close, 2),
                    'type': 'up' if gap_size > 0 else 'down'
                })
        
        return gaps[-5:] if len(gaps) > 5 else gaps
    
    def calculate_pivot_points(self, lookback: int = 20) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        recent_data = self.df.tail(lookback)
        
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        close = recent_data['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        
        # Support levels
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        
        # Resistance levels
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        
        return {
            'support': round(float(s1), 2),
            'support2': round(float(s2), 2),
            'resistance': round(float(r1), 2),
            'resistance2': round(float(r2), 2),
            'pivot': round(float(pivot), 2)
        }
    
    def calculate_donchian_channel(self, period: int = 20) -> Dict[str, Any]:
        """Calculate Donchian Channel - Fixed for 2025"""
        high_channel = self.df['high'].rolling(window=period).max()
        low_channel = self.df['low'].rolling(window=period).min()
        
        # REPARARE: Forțăm prețul minim să fie 0.01 (nu poate fi negativ)
        low_channel = low_channel.clip(lower=0.01)
        
        middle_channel = (high_channel + low_channel) / 2
        
        # Get last N values for chart overlay
        channel_data = []
        for i in range(max(0, len(self.df) - 300), len(self.df)):
            if pd.notna(high_channel.iloc[i]) and pd.notna(low_channel.iloc[i]):
                channel_data.append({
                    'time': self.df.iloc[i]['date'].strftime('%Y-%m-%d') if hasattr(self.df.iloc[i]['date'], 'strftime') else str(self.df.iloc[i]['date']),
                    'upper': round(float(high_channel.iloc[i]), 2),
                    'lower': round(float(low_channel.iloc[i]), 2),
                    'middle': round(float(middle_channel.iloc[i]), 2)
                })
        
        return {
            'upper': round(float(high_channel.iloc[-1]), 2),
            'lower': round(float(low_channel.iloc[-1]), 2),
            'middle': round(float(middle_channel.iloc[-1]), 2),
            'channel_data': channel_data
        }
    
    def calculate_williams_fractals(self, period: int = 5) -> Dict[str, Any]:
        """Calculate Williams Fractals (Pivot points for reversals)"""
        fractals = []
        half_period = period // 2
        
        for i in range(half_period, len(self.df) - half_period):
            # Bullish fractal (low is lowest)
            is_bullish = True
            for j in range(i - half_period, i + half_period + 1):
                if j != i and self.df.iloc[j]['low'] <= self.df.iloc[i]['low']:
                    is_bullish = False
                    break
            
            # Bearish fractal (high is highest)
            is_bearish = True
            for j in range(i - half_period, i + half_period + 1):
                if j != i and self.df.iloc[j]['high'] >= self.df.iloc[i]['high']:
                    is_bearish = False
                    break
            
            if is_bullish or is_bearish:
                fractals.append({
                    'time': self.df.iloc[i]['date'].strftime('%Y-%m-%d') if hasattr(self.df.iloc[i]['date'], 'strftime') else str(self.df.iloc[i]['date']),
                    'type': 'bullish' if is_bullish else 'bearish',
                    'price': round(float(self.df.iloc[i]['low'] if is_bullish else self.df.iloc[i]['high']), 2)
                })
        
        # Return last 20 fractals for chart display
        return {
            'fractals': fractals[-20:] if len(fractals) > 20 else fractals
        }
    
    def calculate_trend_alignment(self) -> Dict[str, Any]:
        """Calculate Daily vs Weekly trend alignment based on EMAs"""
        ema_20 = self.calculate_ema(20)
        ema_50 = self.calculate_ema(50)
        
        current_price = float(self.df['close'].iloc[-1])
        
        # Daily trend based on EMA 20
        daily_trend = "BULLISH" if current_price > ema_20.iloc[-1] else "BEARISH"
        
        # Weekly trend based on EMA 50 (simulates weekly)
        weekly_trend = "BULLISH" if current_price > ema_50.iloc[-1] else "BEARISH"
        
        # Check alignment
        aligned = daily_trend == weekly_trend
        
        return {
            'daily': {
                'trend': daily_trend,
                'ema_value': round(float(ema_20.iloc[-1]), 2)
            },
            'weekly': {
                'trend': weekly_trend,
                'ema_value': round(float(ema_50.iloc[-1]), 2)
            },
            'aligned': aligned,
            'message': 'Trenduri Aliniate' if aligned else 'Divergență Timeframe - Așteptați alinierea'
        }
    
    def analyze_volume(self) -> Dict[str, Any]:
        """Analyze volume patterns"""
        volume_ma20 = self.df['volume'].rolling(window=20).mean()
        current_volume = self.df['volume'].iloc[-1]
        avg_volume = volume_ma20.iloc[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Volume trend
        recent_volumes = self.df['volume'].tail(5)
        volume_trend = "crescător" if recent_volumes.is_monotonic_increasing else \
                      "descrescător" if recent_volumes.is_monotonic_decreasing else "mixt"
        
        return {
            'current': float(current_volume),
            'average': float(avg_volume),
            'ratio': round(float(volume_ratio), 2),
            'trend': volume_trend,
            'exhaustion': volume_ratio < 0.7
        }
    
    def calculate_all_indicators(self) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        try:
            # EMAs
            ema_20 = self.calculate_ema(20)
            ema_50 = self.calculate_ema(50)
            ema_200 = self.calculate_ema(200)
            
            # RSI and Stoch RSI
            rsi = self.calculate_rsi()
            stoch_rsi = self.calculate_stoch_rsi()
            
            # ADX
            adx_data = self.calculate_adx()
            
            # ATR
            atr = self.calculate_atr()
            
            # MACD
            macd_data = self.calculate_macd()
            
            # Heikin Ashi
            ha_df = self.calculate_heikin_ashi()
            ha_last = ha_df.iloc[-1]
            ha_bullish = ha_last['close'] > ha_last['open']
            
            # Volume
            volume_data = self.analyze_volume()
            
            # Pivot Points
            pivots = self.calculate_pivot_points()
            
            # Gaps
            gaps = self.detect_gaps()
            
            # Donchian Channel
            donchian = self.calculate_donchian_channel()
            
            # Williams Fractals
            fractals = self.calculate_williams_fractals()
            
            # Trend Alignment
            trend_alignment = self.calculate_trend_alignment()
            
            # Current values
            current_price = float(self.df['close'].iloc[-1])
            
            # Trend determination
            trend = "BULLISH" if current_price > ema_50.iloc[-1] else "BEARISH"
            trend_strength = "puternic" if abs(current_price - ema_50.iloc[-1]) / ema_50.iloc[-1] > 0.05 else "slab"
            
            return {
                'price': {
                    'current': round(current_price, 2),
                    'ema_20': round(float(ema_20.iloc[-1]), 2),
                    'ema_50': round(float(ema_50.iloc[-1]), 2),
                    'ema_200': round(float(ema_200.iloc[-1]), 2) if len(self.df) >= 200 else None
                },
                'rsi': {
                    'value': round(float(rsi.iloc[-1]), 2),
                    'signal': 'supracumpărat' if rsi.iloc[-1] > 70 else 'supravândut' if rsi.iloc[-1] < 30 else 'neutru'
                },
                'stoch_rsi': {
                    'k': round(float(stoch_rsi['k'].iloc[-1]), 2),
                    'd': round(float(stoch_rsi['d'].iloc[-1]), 2),
                    'signal': 'supracumpărat' if stoch_rsi['k'].iloc[-1] > 80 else 'supravândut' if stoch_rsi['k'].iloc[-1] < 20 else 'neutru'
                },
                'adx': {
                    'value': round(float(adx_data['adx'].iloc[-1]), 2),
                    'pos_di': round(float(adx_data['pos_di'].iloc[-1]), 2),
                    'neg_di': round(float(adx_data['neg_di'].iloc[-1]), 2),
                    'regime': 'TRENDING' if adx_data['adx'].iloc[-1] > 25 else 'RANGING' if adx_data['adx'].iloc[-1] < 20 else 'NEUTRAL'
                },
                'atr': {
                    'value': round(float(atr.iloc[-1]), 2),
                    'percent': round((float(atr.iloc[-1]) / current_price) * 100, 2)
                },
                'macd': {
                    'macd': round(float(macd_data['macd'].iloc[-1]), 2),
                    'signal': round(float(macd_data['signal'].iloc[-1]), 2),
                    'histogram': round(float(macd_data['histogram'].iloc[-1]), 2),
                    'cross': 'bullish' if macd_data['histogram'].iloc[-1] > 0 else 'bearish'
                },
                'heikin_ashi': {
                    'bullish': bool(ha_bullish.item() if hasattr(ha_bullish, 'item') else ha_bullish),
                    'body_size': round(float(abs(ha_last['close'] - ha_last['open'])), 2)
                },
                'volume': volume_data,
                'pivots': pivots,
                'gaps': gaps,
                'donchian': donchian,
                'fractals': fractals,
                'trend_alignment': trend_alignment,
                'trend': {
                    'direction': trend,
                    'strength': trend_strength
                }
            }
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def generate_signal(self, indicators: Dict[str, Any], market_context: Dict[str, Any], risk_data: Dict[str, Any], earnings_days: int = None) -> Dict[str, Any]:
        """Generate trading signal based on indicators with STRICT conservative logic"""
        score = 0
        reasons = []
        warnings = []
        critical_blocks = []
        
        # CRITICAL FILTERS (Override everything)
        # 1. Risk/Reward Ratio Check
        rr_ratio = risk_data.get('risk_reward_ratio', 0)
        if rr_ratio < 1.5:
            critical_blocks.append(f"Raport R/R nefavorabil ({rr_ratio}) - sub 1.5")
            return {
                'signal': 'NEUTRAL',
                'confidence': 20,
                'reasons': ['Setup tehnic nefavorabil'],
                'warnings': critical_blocks,
                'override_reason': 'R/R < 1.5 - FORȚAT NEUTRAL'
            }
        
        # 2. Volume Exhaustion Check
        volume_ratio = indicators['volume']['ratio']
        if volume_ratio < 0.8:
            critical_blocks.append(f"Volum critic scăzut ({volume_ratio}x) - sub 0.8x media")
            return {
                'signal': 'NEUTRAL',
                'confidence': 20,
                'reasons': ['Lipsă confirmare volum'],
                'warnings': critical_blocks,
                'override_reason': 'Volum < 0.8x - FORȚAT NEUTRAL'
            }
        
        # 3. Earnings Risk Check
        if earnings_days is not None and earnings_days < 7:
            critical_blocks.append(f"Earnings în {earnings_days} zile - risc volatilitate extremă")
            return {
                'signal': 'NEUTRAL',
                'confidence': 20,
                'reasons': ['Risc eveniment major'],
                'warnings': critical_blocks,
                'override_reason': 'Earnings < 7 zile - FORȚAT NEUTRAL'
            }
        
        # Check market regime (ADX)
        adx = indicators['adx']['value']
        regime = indicators['adx']['regime']
        
        if regime == 'RANGING':
            warnings.append("Piață laterală (ADX < 20) - semnale nesigure")
            score -= 15
        
        # Trend analysis
        if indicators['trend']['direction'] == 'BULLISH':
            score += 20
            reasons.append("Trend bullish pe EMA 50")
        else:
            score -= 20
            reasons.append("Trend bearish pe EMA 50")
        
        # RSI
        if indicators['rsi']['signal'] == 'supravândut':
            score += 15
            reasons.append("RSI supravândut - posibilă revenire")
        elif indicators['rsi']['signal'] == 'supracumpărat':
            score -= 15
            warnings.append("RSI supracumpărat - risc corecție")
        
        # Stoch RSI - CRITICAL
        if indicators['stoch_rsi']['k'] > 85:
            score -= 30
            warnings.append(f"Stoch RSI EXTREM supracumpărat ({indicators['stoch_rsi']['k']}%) - NU CUMPĂRA!")
        elif indicators['stoch_rsi']['signal'] == 'supravândut':
            score += 15
            reasons.append("Stoch RSI supravândut - oportunitate")
        
        # MACD
        if indicators['macd']['cross'] == 'bullish':
            score += 10
            reasons.append("MACD bullish")
        else:
            score -= 10
        
        # VIX context
        if market_context.get('vix', {}).get('high_volatility'):
            warnings.append("Volatilitate ridicată (VIX)")
            score -= 15
        
        # Price vs levels
        current_price = indicators['price']['current']
        resistance = indicators['pivots']['resistance']
        support = indicators['pivots']['support']
        
        if current_price > resistance * 0.98:
            warnings.append(f"Preț la rezistență ({resistance})")
        
        if current_price < support * 1.02:
            warnings.append(f"Preț la suport ({support})")
        
        # Generate signal
        confidence = max(0, min(100, 50 + score))
        
        # Conservative logic
        if confidence >= 70 and regime == 'TRENDING':
            signal = "BUY"
        elif confidence <= 30:
            signal = "SELL"
        elif confidence >= 50:
            signal = "HOLD"
        else:
            signal = "WAIT"
        
        return {
            'signal': signal,
            'confidence': int(confidence),
            'reasons': reasons,
            'warnings': warnings
        }