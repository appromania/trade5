#!/usr/bin/env python3
"""
Test script specifically for new indicators: Donchian Channel, Williams Fractals, Trend Alignment
"""

import requests
import json

def test_new_indicators():
    """Test the new indicators added to the trading system"""
    base_url = "https://frontend-builder-12.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing New Indicators: Donchian Channel, Williams Fractals, Trend Alignment")
    print("=" * 80)
    
    # Test analysis for AAPL
    payload = {
        "symbol": "AAPL",
        "provider": "yahoo",
        "timeframe": "1d",
        "period": "6mo",
        "lookback": 60
    }
    
    try:
        response = requests.post(f"{api_url}/analyze", json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API call failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Test Donchian Channel
        print("\n📊 Testing Donchian Channel...")
        donchian = data.get('donchian_channel', {})
        if donchian:
            print(f"✅ Donchian Channel present")
            print(f"   Upper: ${donchian.get('upper', 'N/A')}")
            print(f"   Lower: ${donchian.get('lower', 'N/A')}")
            print(f"   Middle: ${donchian.get('middle', 'N/A')}")
            
            # Check if channel_data exists for chart
            channel_data = donchian.get('channel_data', [])
            print(f"   Chart data points: {len(channel_data)}")
            
            if len(channel_data) > 0:
                print(f"   Sample data: {channel_data[0]}")
        else:
            print("❌ Donchian Channel missing")
        
        # Test Williams Fractals
        print("\n🔺 Testing Williams Fractals...")
        fractals = data.get('williams_fractals', {})
        if fractals:
            print(f"✅ Williams Fractals present")
            fractal_points = fractals.get('fractals', [])
            print(f"   Fractal points: {len(fractal_points)}")
            
            if len(fractal_points) > 0:
                bullish_count = sum(1 for f in fractal_points if f.get('type') == 'bullish')
                bearish_count = sum(1 for f in fractal_points if f.get('type') == 'bearish')
                print(f"   Bullish fractals: {bullish_count}")
                print(f"   Bearish fractals: {bearish_count}")
                print(f"   Sample fractal: {fractal_points[0]}")
        else:
            print("❌ Williams Fractals missing")
        
        # Test Trend Alignment
        print("\n📈 Testing Trend Alignment...")
        trend_alignment = data.get('trend_alignment', {})
        if trend_alignment:
            print(f"✅ Trend Alignment present")
            daily = trend_alignment.get('daily', {})
            weekly = trend_alignment.get('weekly', {})
            aligned = trend_alignment.get('aligned', False)
            message = trend_alignment.get('message', '')
            
            print(f"   Daily trend: {daily.get('trend')} (EMA: ${daily.get('ema_value')})")
            print(f"   Weekly trend: {weekly.get('trend')} (EMA: ${weekly.get('ema_value')})")
            print(f"   Aligned: {aligned}")
            print(f"   Message: {message}")
        else:
            print("❌ Trend Alignment missing")
        
        # Test if indicators are also in the main indicators object
        print("\n🔧 Testing Indicators Integration...")
        indicators = data.get('indicators', {})
        
        # Check if new indicators are in the main indicators object
        donchian_in_indicators = 'donchian' in indicators
        fractals_in_indicators = 'fractals' in indicators
        trend_alignment_in_indicators = 'trend_alignment' in indicators
        
        print(f"   Donchian in indicators: {'✅' if donchian_in_indicators else '❌'}")
        print(f"   Fractals in indicators: {'✅' if fractals_in_indicators else '❌'}")
        print(f"   Trend alignment in indicators: {'✅' if trend_alignment_in_indicators else '❌'}")
        
        # Overall assessment
        all_present = bool(donchian and fractals and trend_alignment)
        print(f"\n🎯 Overall: {'✅ All new indicators working' if all_present else '❌ Some indicators missing'}")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Error testing indicators: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_new_indicators()
    exit(0 if success else 1)