#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Expert Trading System
Tests all APIs, indicators, risk calculations, and AI analysis
"""

import requests
import sys
import json
from datetime import datetime
import time

class TradingSystemTester:
    def __init__(self, base_url="https://frontend-builder-12.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = []

    def log_test(self, name, success, details="", severity="medium"):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            if severity == "critical":
                self.critical_failures.append(f"{name}: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "severity": severity
        })

    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f" - {data.get('message', '')}"
            self.log_test("API Health Check", success, details, "critical")
            return success
        except Exception as e:
            self.log_test("API Health Check", False, str(e), "critical")
            return False

    def test_providers_endpoint(self):
        """Test providers endpoint"""
        try:
            response = requests.get(f"{self.api_url}/providers", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                providers = data.get('providers', [])
                success = len(providers) >= 3  # Should have yahoo, alphavantage, twelvedata
                details = f"Found {len(providers)} providers"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Providers Endpoint", success, details)
            return success, data if success else None
        except Exception as e:
            self.log_test("Providers Endpoint", False, str(e))
            return False, None

    def test_symbol_search(self):
        """Test symbol search with fuzzy matching"""
        test_cases = [
            ("AAPL", "Apple"),  # Exact match
            ("APPL", "Apple"),  # Fuzzy match (APPL -> AAPL)
            ("TSLA", "Tesla"),  # Exact match
            ("TESLA", "Tesla"), # Company name search
        ]
        
        all_passed = True
        for query, expected in test_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/symbols/search",
                    json={"query": query},
                    timeout=10
                )
                success = response.status_code == 200
                if success:
                    data = response.json()
                    results = data.get('results', [])
                    # Check if we got relevant results
                    found_relevant = any(expected.lower() in result.get('name', '').lower() or 
                                       expected.upper() in result.get('symbol', '') 
                                       for result in results)
                    success = found_relevant and len(results) > 0
                    details = f"Query: {query} -> {len(results)} results"
                else:
                    details = f"Status: {response.status_code}"
                    all_passed = False
                
                self.log_test(f"Symbol Search: {query}", success, details)
            except Exception as e:
                self.log_test(f"Symbol Search: {query}", False, str(e))
                all_passed = False
        
        return all_passed

    def test_full_analysis(self, symbol="AAPL"):
        """Test complete analysis for a symbol"""
        try:
            print(f"\n🔍 Testing full analysis for {symbol}...")
            
            payload = {
                "symbol": symbol,
                "provider": "yahoo",
                "timeframe": "1d",
                "period": "6mo",
                "lookback": 60
            }
            
            response = requests.post(
                f"{self.api_url}/analyze",
                json=payload,
                timeout=30  # Analysis can take time
            )
            
            success = response.status_code == 200
            if not success:
                details = f"Status: {response.status_code} - {response.text[:200]}"
                self.log_test(f"Full Analysis ({symbol})", False, details, "critical")
                return False, None
            
            data = response.json()
            
            # Validate response structure
            required_fields = [
                'symbol', 'current_price', 'signal', 'confidence_score',
                'indicators', 'risk_management', 'market_context', 'alerts', 'ai_analysis'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                details = f"Missing fields: {missing_fields}"
                self.log_test(f"Full Analysis ({symbol})", False, details, "critical")
                return False, None
            
            # Test individual components
            self._validate_indicators(data['indicators'], symbol)
            self._validate_risk_management(data['risk_management'], symbol)
            self._validate_market_context(data['market_context'])
            self._validate_signal(data, symbol)
            
            self.log_test(f"Full Analysis ({symbol})", True, f"Signal: {data['signal']}, Confidence: {data['confidence_score']}%")
            return True, data
            
        except Exception as e:
            self.log_test(f"Full Analysis ({symbol})", False, str(e), "critical")
            return False, None

    def _validate_indicators(self, indicators, symbol):
        """Validate technical indicators"""
        required_indicators = ['price', 'rsi', 'stoch_rsi', 'adx', 'atr', 'macd', 'volume', 'trend']
        
        for indicator in required_indicators:
            if indicator not in indicators:
                self.log_test(f"Indicator {indicator} ({symbol})", False, "Missing indicator")
                continue
            
            # Validate specific indicator values
            if indicator == 'price':
                current_price = indicators[indicator].get('current')
                success = current_price and current_price > 0
                self.log_test(f"Price Indicator ({symbol})", success, f"Current: ${current_price}")
            
            elif indicator == 'rsi':
                rsi_value = indicators[indicator].get('value')
                success = rsi_value and 0 <= rsi_value <= 100
                self.log_test(f"RSI Indicator ({symbol})", success, f"RSI: {rsi_value}")
            
            elif indicator == 'adx':
                adx_value = indicators[indicator].get('value')
                regime = indicators[indicator].get('regime')
                success = adx_value and adx_value >= 0 and regime in ['TRENDING', 'RANGING', 'NEUTRAL']
                self.log_test(f"ADX Indicator ({symbol})", success, f"ADX: {adx_value} ({regime})")
            
            elif indicator == 'atr':
                atr_value = indicators[indicator].get('value')
                success = atr_value and atr_value > 0
                self.log_test(f"ATR Indicator ({symbol})", success, f"ATR: {atr_value}")

    def _validate_risk_management(self, risk_data, symbol):
        """Validate risk management calculations"""
        required_fields = ['entry_price', 'stop_loss', 'take_profit', 'risk_reward_ratio']
        
        for field in required_fields:
            if field not in risk_data:
                self.log_test(f"Risk {field} ({symbol})", False, "Missing field")
                continue
        
        # Critical validation: Stop Loss must be below entry price
        entry_price = risk_data.get('entry_price', 0)
        stop_loss = risk_data.get('stop_loss', 0)
        take_profit = risk_data.get('take_profit', 0)
        rr_ratio = risk_data.get('risk_reward_ratio', 0)
        
        # Stop Loss validation
        sl_valid = stop_loss < entry_price
        self.log_test(f"Stop Loss Validation ({symbol})", sl_valid, 
                     f"SL: ${stop_loss} vs Entry: ${entry_price}", "critical" if not sl_valid else "medium")
        
        # Take Profit validation
        tp_valid = take_profit > entry_price
        self.log_test(f"Take Profit Validation ({symbol})", tp_valid, 
                     f"TP: ${take_profit} vs Entry: ${entry_price}")
        
        # R/R Ratio validation
        rr_valid = rr_ratio > 0
        self.log_test(f"R/R Ratio Validation ({symbol})", rr_valid, f"R/R: {rr_ratio}")

    def _validate_market_context(self, market_context):
        """Validate market context data"""
        if 'vix' in market_context:
            vix_data = market_context['vix']
            vix_valid = 'value' in vix_data and 'level' in vix_data
            self.log_test("VIX Data", vix_valid, f"VIX: {vix_data.get('value')} ({vix_data.get('level')})")
        
        if 'sp500' in market_context:
            sp500_data = market_context['sp500']
            sp500_valid = 'trend' in sp500_data
            self.log_test("S&P 500 Data", sp500_valid, f"Trend: {sp500_data.get('trend')}")

    def _validate_signal(self, analysis_data, symbol):
        """Validate signal generation"""
        signal = analysis_data.get('signal')
        confidence = analysis_data.get('confidence_score')
        
        signal_valid = signal in ['BUY', 'SELL', 'HOLD', 'WAIT']
        confidence_valid = 0 <= confidence <= 100
        
        self.log_test(f"Signal Generation ({symbol})", signal_valid, f"Signal: {signal}")
        self.log_test(f"Confidence Score ({symbol})", confidence_valid, f"Confidence: {confidence}%")

    def test_ai_analysis(self, symbol="AAPL"):
        """Test AI analysis functionality"""
        try:
            # First get a full analysis
            success, data = self.test_full_analysis(symbol)
            if not success:
                self.log_test("AI Analysis", False, "Failed to get analysis data", "critical")
                return False
            
            ai_analysis = data.get('ai_analysis', '')
            
            # Check if AI analysis is present and meaningful
            ai_valid = len(ai_analysis) > 50  # Should be substantial
            has_romanian = any(word in ai_analysis.lower() for word in ['preț', 'trend', 'risc', 'recomand'])
            
            success = ai_valid and has_romanian
            details = f"Length: {len(ai_analysis)} chars, Romanian: {has_romanian}"
            
            self.log_test("AI Analysis", success, details)
            return success
            
        except Exception as e:
            self.log_test("AI Analysis", False, str(e), "critical")
            return False

    def test_settings_endpoints(self):
        """Test settings endpoints"""
        try:
            # Test GET settings
            response = requests.get(f"{self.api_url}/settings", timeout=10)
            get_success = response.status_code == 200
            
            if get_success:
                settings_data = response.json()
                self.log_test("GET Settings", True, f"Found {len(settings_data.get('providers', []))} providers")
                
                # Test POST settings (save)
                response = requests.post(f"{self.api_url}/settings", json=settings_data, timeout=10)
                post_success = response.status_code == 200
                self.log_test("POST Settings", post_success, f"Status: {response.status_code}")
                
                return get_success and post_success
            else:
                self.log_test("GET Settings", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Settings Endpoints", False, str(e))
            return False

    def test_market_context_endpoint(self):
        """Test market context endpoint"""
        try:
            response = requests.get(f"{self.api_url}/market-context", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_vix = 'vix' in data
                has_sp500 = 'sp500' in data
                details = f"VIX: {has_vix}, S&P500: {has_sp500}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Market Context Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("Market Context Endpoint", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Backend Testing for Expert Trading System")
        print("=" * 70)
        
        start_time = time.time()
        
        # Critical tests first
        if not self.test_api_health():
            print("\n❌ CRITICAL: API is not accessible. Stopping tests.")
            return self.generate_report()
        
        # Core functionality tests
        self.test_providers_endpoint()
        self.test_symbol_search()
        self.test_market_context_endpoint()
        self.test_settings_endpoints()
        
        # Main analysis tests
        print("\n📊 Testing Analysis Functionality...")
        self.test_full_analysis("AAPL")
        self.test_full_analysis("TSLA")  # Test different symbol
        
        # AI analysis test
        print("\n🤖 Testing AI Analysis...")
        self.test_ai_analysis("AAPL")
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        print(f"\n⏱️  Total test duration: {duration} seconds")
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        # Determine overall status
        if len(self.critical_failures) > 0:
            status = "CRITICAL_ISSUES"
        elif success_rate < 70:
            status = "MAJOR_ISSUES"
        elif success_rate < 90:
            status = "MINOR_ISSUES"
        else:
            status = "HEALTHY"
        
        print(f"\n🎯 Overall Status: {status}")
        
        return {
            "status": status,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": success_rate,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results
        }

def main():
    tester = TradingSystemTester()
    report = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    if report["status"] in ["CRITICAL_ISSUES", "MAJOR_ISSUES"]:
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())