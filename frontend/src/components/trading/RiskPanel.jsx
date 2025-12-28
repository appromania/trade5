import { useState } from 'react';
import { Bell, Beaker, Target } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import OptimizeEntryModal from './OptimizeEntryModal';
import SimulateTradeModal from './SimulateTradeModal';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

export default function RiskPanel({ riskData, analysis, onOptimizeComplete, onAlertSet, onSimulationCreated }) {
  const [isOptimizeModalOpen, setIsOptimizeModalOpen] = useState(false);
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState(false);
  
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

  return (
    <>
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

        {/* Action Buttons - NEW DESIGN with Neon Colors */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <button
            onClick={() => setIsOptimizeModalOpen(true)}
            disabled={!analysis}
            className="group relative overflow-hidden rounded-lg p-4 border border-indigo-500/30 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 hover:from-indigo-500/20 hover:to-purple-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Optimizează Entry pentru R/R >= 2.0"
          >
            <div className="flex flex-col items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Target className="h-5 w-5 text-white" />
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Optimize Entry</span>
              <span className="text-[10px] text-muted-foreground text-center">Găsește cel mai bun preț</span>
            </div>
          </button>
          
          <button
            onClick={() => setIsSimulateModalOpen(true)}
            disabled={!analysis}
            className="group relative overflow-hidden rounded-lg p-4 border border-violet-500/30 bg-gradient-to-br from-violet-500/10 to-emerald-500/10 hover:from-violet-500/20 hover:to-emerald-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Simulează tranzacția (Paper Trading)"
          >
            <div className="flex flex-col items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Beaker className="h-5 w-5 text-white" />
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-violet-400">Simulate Trade</span>
              <span className="text-[10px] text-muted-foreground text-center">Testează fără risc</span>
            </div>
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

      {/* Modals */}
      <OptimizeEntryModal
        isOpen={isOptimizeModalOpen}
        onClose={() => setIsOptimizeModalOpen(false)}
        analysis={analysis}
        riskData={riskData}
      />

      <SimulateTradeModal
        isOpen={isSimulateModalOpen}
        onClose={() => setIsSimulateModalOpen(false)}
        analysis={analysis}
        riskData={riskData}
      />
    </>
  );
}