import { useState } from 'react';
import { Bell, Beaker, Target } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

export default function RiskPanel({ riskData, analysis, onOptimizeComplete, onAlertSet, onSimulationCreated }) {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  
  if (!riskData) return null;

  const getRiskColor = () => {
    if (riskData.favorable) return 'text-bull';
    return 'text-bear';
  };

  // Set alert for price level
  const handleSetAlert = async (type, price) => {
    try {
      const response = await axios.post(`${API_URL}/alerts/set`, {
        symbol: analysis.symbol,
        target_price: price,
        alert_type: type,
        current_price: analysis.current_price,
        user_note: `Alert ${type} pentru ${analysis.symbol}`
      });
      
      if (response.data.success) {
        toast.success(`Alertă setată pentru ${analysis.symbol} la $${price.toFixed(2)}`);
        if (onAlertSet) onAlertSet(response.data.alert);
      }
    } catch (error) {
      console.error('Set alert error:', error);
      toast.error('Eroare la setarea alertei');
    }
  };

  // Optimize entry for better R/R
  const handleOptimizeEntry = async () => {
    if (!analysis?.indicators) return;
    
    setIsOptimizing(true);
    try {
      const response = await axios.post(`${API_URL}/optimize-entry`, {
        symbol: analysis.symbol,
        current_price: analysis.current_price,
        ema_20: analysis.indicators.price.ema_20,
        ema_50: analysis.indicators.price.ema_50,
        support: riskData.support,
        resistance: riskData.resistance,
        atr: riskData.atr_value,
        current_rr: riskData.risk_reward_ratio
      });
      
      if (response.data.success) {
        const opt = response.data.optimization;
        toast.success(opt.message || 'Entry optimizat!', {
          description: opt.action,
          duration: 5000
        });
        if (onOptimizeComplete) onOptimizeComplete(opt);
      }
    } catch (error) {
      console.error('Optimize entry error:', error);
      toast.error('Eroare la optimizarea entry-ului');
    } finally {
      setIsOptimizing(false);
    }
  };

  // Simulate trade (paper trading)
  const handleSimulateTrade = async () => {
    setIsSimulating(true);
    try {
      const response = await axios.post(`${API_URL}/simulate-trade`, {
        symbol: analysis.symbol,
        entry_price: riskData.entry_price,
        stop_loss: riskData.stop_loss,
        take_profit: riskData.take_profit,
        position_size: 100,
        strategy: 'manual',
        notes: `Simulare pentru ${analysis.symbol} - R/R ${riskData.risk_reward_ratio}:1`
      });
      
      if (response.data.success) {
        toast.success('Tranzacție simulată creată!', {
          description: `${analysis.symbol} adăugat în Strategy Tester`,
          duration: 5000
        });
        
        // Also add to watchlist
        await axios.post(`${API_URL}/watchlist/add`, {
          symbol: analysis.symbol,
          ideal_entry_price: riskData.entry_price,
          current_price: analysis.current_price,
          stop_loss: riskData.stop_loss,
          take_profit: riskData.take_profit,
          confidence_score: analysis.confidence_score,
          notes: 'Adăugat automat din simulare'
        });
        
        if (onSimulationCreated) onSimulationCreated(response.data.trade);
      }
    } catch (error) {
      console.error('Simulate trade error:', error);
      toast.error('Eroare la crearea simulării');
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="terminal-card p-4" data-testid="risk-panel">
      <h3 className="indicator-label mb-4">Risk Management</h3>
      
      <div className="space-y-4">
        {/* Entry & Exit with Alert Buttons */}
        <div className="grid grid-cols-3 gap-3">
          <div className="indicator-card relative group">
            <div className="indicator-label text-primary">Entry</div>
            <div className="indicator-value text-base mono-data">${riskData.entry_price}</div>
            <button
              onClick={() => handleSetAlert('ideal_entry', riskData.entry_price)}
              className="absolute top-1 right-1 p-1 rounded bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-primary/20"
              title="Setează alertă"
            >
              <Bell className="h-3 w-3 text-primary" />
            </button>
          </div>
          <div className="indicator-card relative group">
            <div className="indicator-label text-bear">Stop Loss</div>
            <div className="indicator-value text-base mono-data">${riskData.stop_loss}</div>
            <div className="indicator-status text-bear">-{riskData.stop_loss_percent}%</div>
            <button
              onClick={() => handleSetAlert('stop_loss', riskData.stop_loss)}
              className="absolute top-1 right-1 p-1 rounded bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20"
              title="Setează alertă"
            >
              <Bell className="h-3 w-3 text-red-400" />
            </button>
          </div>
          <div className="indicator-card relative group">
            <div className="indicator-label text-bull">Take Profit</div>
            <div className="indicator-value text-base mono-data">${riskData.take_profit}</div>
            <button
              onClick={() => handleSetAlert('take_profit', riskData.take_profit)}
              className="absolute top-1 right-1 p-1 rounded bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-green-500/20"
              title="Setează alertă"
            >
              <Bell className="h-3 w-3 text-green-400" />
            </button>
          </div>
        </div>

        {/* R/R Ratio with Warning */}
        <div className="indicator-card">
          <div className="indicator-label">Raport Risc/Recompensă</div>
          <div className={`indicator-value ${getRiskColor()}`}>
            1:{riskData.risk_reward_ratio}
            {riskData.rr_capped && (
              <span className="text-[10px] text-yellow-400 ml-2">(capped @ 10:1)</span>
            )}
          </div>
          <div className="indicator-status">
            {riskData.favorable ? '✅ Favorabil (R/R > 1.5)' : '⚠️ Nefavorabil - Așteptați setup mai bun'}
          </div>
          {riskData.rr_warning && (
            <div className="mt-2 text-[10px] text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 p-2 rounded">
              {riskData.rr_warning}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={handleOptimizeEntry}
            disabled={isOptimizing || !analysis}
            className="console-btn flex items-center justify-center gap-2 py-2"
            title="Optimizează Entry pentru R/R >= 2.0"
          >
            {isOptimizing ? (
              <>
                <div className="h-3 w-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                Optimizează...
              </>
            ) : (
              <>
                <Target className="h-4 w-4" />
                🎯 Optimize Entry
              </>
            )}
          </button>
          
          <button
            onClick={handleSimulateTrade}
            disabled={isSimulating || !analysis}
            className="console-btn flex items-center justify-center gap-2 py-2"
            title="Simulează tranzacția (Paper Trading)"
          >
            {isSimulating ? (
              <>
                <div className="h-3 w-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                Simulează...
              </>
            ) : (
              <>
                <Beaker className="h-4 w-4" />
                🧪 Simulate Trade
              </>
            )}
          </button>
        </div>

        {/* Risk Assessment */}
        <div className="p-3 bg-black/30 border border-white/10 rounded-sm">
          <div className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Evaluare Risc</div>
          <div className="text-sm">{riskData.risk_assessment}</div>
        </div>

        {/* Trailing Stop */}
        <div className="indicator-card">
          <div className="indicator-label">Trailing Stop Sugestie</div>
          <div className="indicator-value text-base mono-data">${riskData.trailing_stop}</div>
          <div className="indicator-status text-xs">Mută SL dacă trendul continuă</div>
        </div>
      </div>
    </div>
  );
}