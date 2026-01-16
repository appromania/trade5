import { useState } from 'react';
import { X, TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

export default function SimulateTradeModal({ isOpen, onClose, analysis, riskData }) {
  const [capital, setCapital] = useState(1000);
  const [customSL, setCustomSL] = useState(riskData?.stop_loss || 0);
  const [customTP, setCustomTP] = useState(riskData?.take_profit || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update SL/TP when modal opens or riskData changes
  useState(() => {
    if (riskData) {
      setCustomSL(riskData.stop_loss);
      setCustomTP(riskData.take_profit);
    }
  }, [riskData]);

  if (!isOpen) return null;

  const entryPrice = riskData?.entry_price || analysis?.current_price || 0;
  
  // Calculate position size (number of shares)
  const positionSize = Math.floor(capital / entryPrice);
  
  // Calculate P/L
  const profitAmount = (customTP - entryPrice) * positionSize;
  const lossAmount = (customSL - entryPrice) * positionSize;
  const profitPercent = ((customTP - entryPrice) / entryPrice) * 100;
  const lossPercent = ((customSL - entryPrice) / entryPrice) * 100;
  
  // Calculate Risk/Reward ratio
  const riskAmount = Math.abs(entryPrice - customSL);
  const rewardAmount = Math.abs(customTP - entryPrice);
  const rrRatio = riskAmount > 0 ? (rewardAmount / riskAmount).toFixed(1) : '0.0';

  const handleSimulate = async () => {
    setIsSubmitting(true);
    try {
      // First, create simulation
      const response = await axios.post(`${API_URL}/simulate-trade`, {
        symbol: analysis.symbol,
        entry_price: entryPrice,
        stop_loss: customSL,
        take_profit: customTP,
        position_size: positionSize,
        strategy: 'manual',
        notes: `Simulare cu capital $${capital} - R/R ${rrRatio}:1`
      });

      if (response.data.success) {
        // Then, add to watchlist/portfolio
        try {
          await axios.post(`${API_URL}/watchlist/add`, {
            symbol: analysis.symbol,
            ideal_entry_price: entryPrice,
            current_price: analysis.current_price,
            stop_loss: customSL,
            take_profit: customTP,
            confidence_score: analysis.confidence_score,
            notes: `Simulare - Capital: $${capital}`
          });

          toast.success('Tranzacție salvată!', {
            description: `${analysis.symbol} adăugat în Strategy Tester și Portfolio`,
            duration: 5000
          });
        } catch (watchlistError) {
          console.error('Watchlist add error:', watchlistError);
          // Show success even if watchlist fails
          toast.success('Tranzacție simulată creată!', {
            description: `${analysis.symbol} adăugat în Strategy Tester`,
            duration: 5000
          });
        }

        onClose();
      }
    } catch (error) {
      console.error('Simulate trade error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Eroare necunoscută';
      toast.error('Eroare la crearea simulării', {
        description: errorMsg,
        duration: 5000
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 glass-card border-b border-white/10 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <span className="text-xl">🧪</span>
            </div>
            <div>
              <h2 className="font-heading text-xl font-bold">Simulate Trade</h2>
              <p className="text-sm text-muted-foreground">{analysis?.symbol} - Testează strategia fără risc</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Capital Input */}
          <div className="glass-card p-5 border border-violet-500/30 rounded-lg">
            <label className="block text-sm font-bold mb-3 uppercase tracking-wider text-violet-400">
              <DollarSign className="inline h-4 w-4 mr-1" />
              Capital de Investit
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl font-bold text-muted-foreground">$</span>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(parseFloat(e.target.value) || 1000)}
                className="w-full bg-black/30 border border-white/20 rounded-lg pl-10 pr-4 py-3 text-2xl font-mono font-bold focus:outline-none focus:border-violet-500 transition-colors"
                min="100"
                step="100"
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Position size: <span className="font-bold text-violet-400">{positionSize} shares</span> @ ${entryPrice.toFixed(2)}
            </p>
          </div>

          {/* SL/TP Adjustments */}
          <div className="grid grid-cols-2 gap-4">
            {/* Stop Loss */}
            <div className="glass-card p-4 border border-red-500/30 rounded-lg">
              <label className="block text-xs font-bold mb-2 uppercase tracking-wider text-red-400">
                <TrendingDown className="inline h-3 w-3 mr-1" />
                Stop Loss
              </label>
              <input
                type="number"
                value={customSL}
                onChange={(e) => setCustomSL(parseFloat(e.target.value) || riskData?.stop_loss)}
                className="w-full bg-black/30 border border-red-500/20 rounded px-3 py-2 text-lg font-mono focus:outline-none focus:border-red-500 transition-colors"
                step="0.01"
              />
              <div className="mt-2 text-xs">
                <div className="text-red-400 font-bold">${lossAmount.toFixed(2)}</div>
                <div className="text-muted-foreground">{lossPercent.toFixed(2)}%</div>
              </div>
            </div>

            {/* Take Profit */}
            <div className="glass-card p-4 border border-green-500/30 rounded-lg">
              <label className="block text-xs font-bold mb-2 uppercase tracking-wider text-green-400">
                <TrendingUp className="inline h-3 w-3 mr-1" />
                Take Profit
              </label>
              <input
                type="number"
                value={customTP}
                onChange={(e) => setCustomTP(parseFloat(e.target.value) || riskData?.take_profit)}
                className="w-full bg-black/30 border border-green-500/20 rounded px-3 py-2 text-lg font-mono focus:outline-none focus:border-green-500 transition-colors"
                step="0.01"
              />
              <div className="mt-2 text-xs">
                <div className="text-green-400 font-bold">+${profitAmount.toFixed(2)}</div>
                <div className="text-muted-foreground">+{profitPercent.toFixed(2)}%</div>
              </div>
            </div>
          </div>

          {/* R/R Display */}
          <div className="glass-card p-5 bg-gradient-to-br from-violet-500/10 to-purple-500/10 border border-violet-500/30 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold uppercase tracking-wider text-violet-400">
                <Percent className="inline h-4 w-4 mr-1" />
                Raport Risc/Recompensă
              </span>
              <span className={`font-mono text-3xl font-bold ${parseFloat(rrRatio) >= 2.0 ? 'text-green-400' : parseFloat(rrRatio) >= 1.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                1:{rrRatio}
              </span>
            </div>
            <div className="w-full bg-black/30 rounded-full h-3 overflow-hidden">
              <div
                className={`h-full rounded-full ${parseFloat(rrRatio) >= 2.0 ? 'bg-green-500' : parseFloat(rrRatio) >= 1.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${Math.min(parseFloat(rrRatio) * 25, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Profit/Loss Scenarios */}
          <div className="grid grid-cols-2 gap-4">
            {/* Win Scenario */}
            <div className="glass-card p-5 border border-green-500/30 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">✅</span>
                <h3 className="font-bold text-green-400">Success (TP Hit)</h3>
              </div>
              <div className="font-mono text-3xl font-bold text-green-400 mb-1">
                +${profitAmount.toFixed(2)}
              </div>
              <p className="text-xs text-muted-foreground">
                Capital final: <span className="font-bold text-green-400">${(capital + profitAmount).toFixed(2)}</span>
              </p>
            </div>

            {/* Loss Scenario */}
            <div className="glass-card p-5 border border-red-500/30 bg-gradient-to-br from-red-500/10 to-rose-500/10 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">❌</span>
                <h3 className="font-bold text-red-400">Failure (SL Hit)</h3>
              </div>
              <div className="font-mono text-3xl font-bold text-red-400 mb-1">
                {lossAmount.toFixed(2)}
              </div>
              <p className="text-xs text-muted-foreground">
                Capital final: <span className="font-bold text-red-400">${(capital + lossAmount).toFixed(2)}</span>
              </p>
            </div>
          </div>

          {/* Warning for bad R/R */}
          {parseFloat(rrRatio) < 1.5 && (
            <div className="glass-card-red p-4 border border-red-500/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">⚠️</span>
                <h3 className="font-bold text-red-400">Avertisment Setup Nefavorabil</h3>
              </div>
              <p className="text-sm text-red-300">
                Raportul Risc/Recompensă este sub 1.5:1. Acest setup NU este recomandat. 
                Ajustați Stop Loss sau Take Profit pentru un raport mai bun.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 p-6 space-y-3">
          <button
            onClick={handleSimulate}
            disabled={isSubmitting || parseFloat(rrRatio) < 1.0}
            className={`w-full py-3 rounded-lg font-bold uppercase tracking-wider transition-all ${
              parseFloat(rrRatio) >= 1.5
                ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700'
                : 'bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700'
            } ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Se creează simularea...
              </span>
            ) : (
              '🧪 Creează Simulare'
            )}
          </button>
          <button
            onClick={onClose}
            className="w-full console-btn py-3"
          >
            Anulează
          </button>
        </div>
      </div>
    </div>
  );
}
