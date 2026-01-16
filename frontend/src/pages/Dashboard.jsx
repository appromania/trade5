import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Settings, TrendingUp, BarChart3, Calculator, Bell, Wallet, Beaker } from 'lucide-react';
import SearchBar from '@/components/trading/SearchBar';
import AdvancedChart from '@/components/trading/AdvancedChart';
import CandlestickChart from '@/components/trading/CandlestickChart';
import IndicatorsPanel from '@/components/trading/IndicatorsPanel';
import RiskPanel from '@/components/trading/RiskPanel';
import AlertsPanel from '@/components/trading/AlertsPanel';
import SignalCard from '@/components/trading/SignalCard';
import FundamentalsCard from '@/components/trading/FundamentalsCard';
import TrendContext from '@/components/trading/TrendContext';
import TradePlanner from '@/components/trading/TradePlanner';
import AlertSystem, { AlertIndicator } from '@/components/trading/AlertSystem';
import PotentialPortfolio from '@/components/trading/PotentialPortfolio';
import { Button } from '@/components/ui/button';
import { useMarketData } from '@/hooks/useMarketData';

// Alerts storage key
const ALERTS_STORAGE_KEY = 'trading_alerts';

export default function Dashboard() {
  const {
    loading,
    analysis,
    providers,
    marketContext,
    analyzeSymbol,
    searchSymbols,
    fetchMarketContext
  } = useMarketData();

  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [timeframe, setTimeframe] = useState('1d');
  const [useHeikinAshi, setUseHeikinAshi] = useState(false);
  const [isTradePlannerOpen, setIsTradePlannerOpen] = useState(false);
  const [isAlertSystemOpen, setIsAlertSystemOpen] = useState(false);
  const [isPortfolioOpen, setIsPortfolioOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);

  // Load alerts from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(ALERTS_STORAGE_KEY);
    if (stored) {
      setAlerts(JSON.parse(stored));
    }
  }, []);

  // Sync alerts from AlertSystem
  useEffect(() => {
    const handleStorage = () => {
      const stored = localStorage.getItem(ALERTS_STORAGE_KEY);
      if (stored) {
        setAlerts(JSON.parse(stored));
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  useEffect(() => {
    fetchMarketContext();
  }, []);

  const handleAnalyze = async (symbol, tf = timeframe) => {
    try {
      setSelectedSymbol(symbol);
      await analyzeSymbol(symbol, 'yahoo', tf, '1y', 60); // Increased to 1 year for more candles
    } catch (error) {
      console.error('Analysis error:', error);
    }
  };

  const timeframes = [
    { value: '5m', label: '5M' },
    { value: '1h', label: '1H' },
    { value: '4h', label: '4H' },
    { value: '1d', label: '1D' },
    { value: '1wk', label: '1W' }
  ];

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-[#262626] bg-[#0A0A0A]">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-primary rounded-sm flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-black" />
              </div>
              <div>
                <h1 className="font-heading text-xl font-black uppercase tracking-tight" data-testid="app-title">
                  Expert Trading System
                </h1>
                <p className="text-xs text-muted-foreground uppercase tracking-widest">V.2025</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Alert Indicator */}
              <AlertIndicator 
                alerts={alerts}
                onClick={() => setIsAlertSystemOpen(true)}
              />
              
              {/* Potential Portfolio Button */}
              <button
                onClick={() => setIsPortfolioOpen(true)}
                className="p-2 rounded transition-colors hover:bg-white/5 text-muted-foreground hover:text-purple-400"
                title="Potential Portfolio"
              >
                <Wallet className="h-5 w-5" />
              </button>
              
              {/* Strategy Audit Link */}
              <Link to="/strategy-audit">
                <button
                  className="p-2 rounded transition-colors hover:bg-white/5 text-muted-foreground hover:text-purple-400"
                  title="Strategy Audit"
                >
                  <Beaker className="h-5 w-5" />
                </button>
              </Link>
              
              {/* Trade Planner Button */}
              <button
                onClick={() => setIsTradePlannerOpen(true)}
                disabled={!analysis}
                className={`p-2 rounded transition-colors ${
                  analysis 
                    ? 'hover:bg-white/5 text-muted-foreground hover:text-primary' 
                    : 'opacity-30 cursor-not-allowed'
                }`}
                title="Trade Planner"
              >
                <Calculator className="h-5 w-5" />
              </button>
              
              <Link to="/settings">
                <Button
                  variant="outline"
                  className="border-white/10 hover:border-primary/50 rounded-sm font-mono uppercase text-xs"
                  data-testid="settings-button"
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Setări
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Search Section */}
        <div className="mb-6">
          <SearchBar
            onSearch={(symbol) => handleAnalyze(symbol)}
            onSymbolSelect={(symbol) => handleAnalyze(symbol)}
            searchFunction={searchSymbols}
          />
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20" data-testid="loading-indicator">
            <div className="text-center">
              <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground font-mono">Se analizează {selectedSymbol}...</p>
            </div>
          </div>
        )}

        {!loading && !analysis && (
          <div className="glass-card p-12 text-center">
            <BarChart3 className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="font-heading text-2xl font-bold mb-2">Bun venit la Expert Trading System</h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              Introduceți un simbol de acțiune pentru a obține o analiză tehnică completă cu indicatori,
              risk management și recomandări AI.
            </p>
          </div>
        )}

        {!loading && analysis && (
          <div className="space-y-6">
            {/* Price Header */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-heading text-3xl font-black uppercase tracking-tight mb-2" data-testid="symbol-display">
                    {analysis.symbol}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {analysis.company_name || analysis.symbol}
                  </p>
                </div>
                <div className="text-right">
                  <div className="font-mono text-4xl font-bold" data-testid="current-price">
                    ${analysis.current_price?.toFixed(2)}
                  </div>
                  <div
                    className={`font-mono text-lg ${
                      analysis.price_change_percent >= 0 ? 'text-bull' : 'text-bear'
                    }`}
                    data-testid="price-change"
                  >
                    {analysis.price_change_percent >= 0 ? '+' : ''}{analysis.price_change_percent?.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Timeframe & Chart Type Selector - CONSOLE STYLE CENTERED */}
            <div className="flex flex-wrap items-center justify-center gap-4 glass-card p-4">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Timeframe:</span>
                <div className="flex gap-1">
                  {timeframes.map(tf => (
                    <button
                      key={tf.value}
                      onClick={() => {
                        setTimeframe(tf.value);
                        handleAnalyze(selectedSymbol, tf.value);
                      }}
                      disabled={loading}
                      className={`console-btn ${timeframe === tf.value ? 'active' : ''}`}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-6 w-px bg-white/10"></div>

              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Tip Lumânări:</span>
                <button
                  onClick={() => setUseHeikinAshi(!useHeikinAshi)}
                  disabled={loading}
                  className={`console-btn ${useHeikinAshi ? 'active' : ''}`}
                >
                  {useHeikinAshi ? '🕯️ Heikin Ashi' : '📊 Standard'}
                </button>
              </div>

              <div className="h-6 w-px bg-white/10"></div>

              {/* Quick Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsTradePlannerOpen(true)}
                  className="console-btn flex items-center gap-2"
                >
                  <Calculator className="h-3 w-3" />
                  Trade Planner
                </button>
                <button
                  onClick={() => setIsAlertSystemOpen(true)}
                  className={`console-btn flex items-center gap-2 ${
                    alerts.filter(a => a.status === 'active').length > 0 ? 'active' : ''
                  }`}
                >
                  <Bell className="h-3 w-3" />
                  Alerte
                  {alerts.filter(a => a.status === 'active').length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-yellow-500 text-black text-[9px] font-bold rounded">
                      {alerts.filter(a => a.status === 'active').length}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column - Chart & Indicators */}
              <div className="lg:col-span-8 space-y-6">
                {/* Advanced Chart with All Indicators */}
                <AdvancedChart
                  symbol={analysis.symbol}
                  chartData={analysis.chart_data}
                  indicators={analysis.indicators}
                />

                <IndicatorsPanel indicators={analysis.indicators} />

                {/* Fundamentals */}
                <FundamentalsCard symbol={analysis.symbol} />
              </div>

              {/* Right Column - Signal, Risk, Alerts */}
              <div className="lg:col-span-4 space-y-6">
                {/* Trend Alignment Widget */}
                <TrendContext trendAlignment={analysis.trend_alignment} />

                <SignalCard
                  signal={analysis.signal}
                  confidence={analysis.confidence_score}
                  reasons={[]}
                  warnings={[]}
                  overrideReason={analysis.override_reason}
                  rrRatio={analysis.risk_management?.risk_reward_ratio || 0}
                />

                <RiskPanel 
                  riskData={analysis.risk_management}
                  analysis={analysis}
                  onOptimizeComplete={(opt) => console.log('Optimized:', opt)}
                  onAlertSet={(alert) => console.log('Alert set:', alert)}
                  onSimulationCreated={(trade) => console.log('Simulation:', trade)}
                />

                <AlertsPanel
                  alerts={analysis.alerts}
                  marketContext={analysis.market_context}
                />
              </div>
            </div>

            {/* AI Analysis - 4 Column Layout */}
            {analysis.ai_analysis && (
              <div className="glass-card p-6" data-testid="ai-analysis">
                <h3 className="indicator-label mb-4 flex items-center gap-2">
                  <span className="icon-pulse">🤖</span>
                  Analiză AI
                </h3>
                <AIAnalysisLayout analysis={analysis.ai_analysis} />
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#262626] bg-[#0A0A0A] mt-12 py-6">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>Expert Trading System V.2025 | Analiză tehnică profesională pentru traderi</p>
          <p className="mt-2">⚠️ Această aplicație este doar pentru scopuri educaționale. Nu constituie sfaturi de investiții.</p>
        </div>
      </footer>

      {/* Trade Planner Sidebar */}
      <TradePlanner 
        analysis={analysis}
        isOpen={isTradePlannerOpen}
        onClose={() => setIsTradePlannerOpen(false)}
      />

      {/* Alert System Popup */}
      <AlertSystem
        analysis={analysis}
        isOpen={isAlertSystemOpen}
        onClose={() => {
          setIsAlertSystemOpen(false);
          // Refresh alerts from storage
          const stored = localStorage.getItem(ALERTS_STORAGE_KEY);
          if (stored) {
            setAlerts(JSON.parse(stored));
          }
        }}
      />

      {/* Potential Portfolio Popup */}
      <PotentialPortfolio
        isOpen={isPortfolioOpen}
        onClose={() => setIsPortfolioOpen(false)}
      />
    </div>
  );
}

// AI Analysis Layout Component - Parses text and displays in structured columns
function AIAnalysisLayout({ analysis }) {
  // Simply display the analysis with proper formatting
  // No complex parsing - AI already formats it well
  
  return (
    <div className="prose prose-invert max-w-none">
      <div className="text-sm leading-relaxed space-y-3">
        {analysis.split('\n').filter(line => line.trim()).map((line, idx) => {
          // Detect if line starts with emoji (technical, fundamentals, risks, recommendation)
          const isBulletPoint = line.trim().startsWith('•');
          const isActionPlan = line.includes('💡') || line.includes('🚀') || line.includes('📊') || line.includes('⚠️');
          
          if (isBulletPoint) {
            return (
              <div key={idx} className="flex items-start gap-2 p-2 rounded bg-white/5">
                <span className="text-lg flex-shrink-0">{line.split(' ')[0]}</span>
                <span className="flex-1">{line.substring(line.indexOf(' ') + 1)}</span>
              </div>
            );
          } else if (isActionPlan) {
            return (
              <div key={idx} className="p-3 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                <p className="text-sm font-medium">{line}</p>
              </div>
            );
          } else {
            return <p key={idx} className="text-sm text-gray-300">{line}</p>;
          }
        })}
      </div>
    </div>
  );
}

// Orphaned code removed - AIAnalysisLayout function above handles the display
