import { useState, useMemo } from 'react';
import { Calculator, Target, TrendingUp, TrendingDown, AlertTriangle, X } from 'lucide-react';

export default function TradePlanner({ 
  analysis, 
  isOpen, 
  onClose 
}) {
  const [targetRR, setTargetRR] = useState(2.0);

  // Calculate optimal pullback entry for desired R/R
  const tradePlan = useMemo(() => {
    if (!analysis?.risk_management || !analysis?.indicators?.pivots) return null;

    const currentPrice = parseFloat(analysis.current_price);
    const atr = parseFloat(analysis.indicators?.atr?.value || 0);
    const support = parseFloat(analysis.indicators.pivots.support);
    const resistance = parseFloat(analysis.indicators.pivots.resistance);
    
    // Current levels
    const currentSL = parseFloat(analysis.risk_management.stop_loss);
    const currentTP = parseFloat(analysis.risk_management.take_profit);
    const currentEntry = currentPrice;
    
    // Calculate current R/R
    const currentRisk = currentEntry - currentSL;
    const currentReward = currentTP - currentEntry;
    const currentRR = currentRisk > 0 ? (currentReward / currentRisk) : 0;

    // Calculate optimal pullback entry for target R/R
    // R/R = (TP - Entry) / (Entry - SL)
    // targetRR = (currentTP - optimalEntry) / (optimalEntry - currentSL)
    // targetRR * (optimalEntry - currentSL) = currentTP - optimalEntry
    // targetRR * optimalEntry - targetRR * currentSL = currentTP - optimalEntry
    // targetRR * optimalEntry + optimalEntry = currentTP + targetRR * currentSL
    // optimalEntry * (targetRR + 1) = currentTP + targetRR * currentSL
    // optimalEntry = (currentTP + targetRR * currentSL) / (targetRR + 1)
    
    const optimalEntry = (currentTP + targetRR * currentSL) / (targetRR + 1);
    const pullbackPercent = ((currentPrice - optimalEntry) / currentPrice) * 100;
    
    // ATR-based zones
    const atrZoneHigh = currentPrice - (atr * 0.5);
    const atrZoneLow = currentPrice - (atr * 1.0);
    const atrZoneDeep = currentPrice - (atr * 1.5);

    // Is pullback realistic?
    const isRealistic = optimalEntry > currentSL && optimalEntry < currentPrice;
    const isPriceNearOptimal = Math.abs(currentPrice - optimalEntry) / currentPrice < 0.02;

    return {
      currentPrice,
      currentEntry,
      currentSL,
      currentTP,
      currentRR: currentRR.toFixed(2),
      currentRisk: currentRisk.toFixed(2),
      currentReward: currentReward.toFixed(2),
      optimalEntry: optimalEntry.toFixed(2),
      pullbackPercent: pullbackPercent.toFixed(2),
      targetRR,
      atr: atr.toFixed(2),
      atrZoneHigh: atrZoneHigh.toFixed(2),
      atrZoneLow: atrZoneLow.toFixed(2),
      atrZoneDeep: atrZoneDeep.toFixed(2),
      support: support.toFixed(2),
      resistance: resistance.toFixed(2),
      isRealistic,
      isPriceNearOptimal,
    };
  }, [analysis, targetRR]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Sidebar Panel */}
      <div className="relative w-full max-w-md h-full bg-[#0a0a0a] border-l border-[#262626] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#0a0a0a] border-b border-[#262626] p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-primary/20 rounded flex items-center justify-center">
              <Calculator className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h2 className="font-bold text-sm uppercase tracking-wider">Trade Planner</h2>
              <p className="text-[10px] text-muted-foreground">{analysis?.symbol}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {!tradePlan ? (
          <div className="p-8 text-center text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Selectați un simbol pentru a genera planul de tranzacționare</p>
          </div>
        ) : (
          <div className="p-4 space-y-6">
            {/* Current Position Summary */}
            <div className="glass-card p-4">
              <h3 className="indicator-label mb-3 flex items-center gap-2">
                <span>📊</span> Situația Curentă
              </h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground text-xs">Preț Curent</span>
                  <p className="font-mono font-bold">${tradePlan.currentPrice.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">R/R Actual</span>
                  <p className={`font-mono font-bold ${parseFloat(tradePlan.currentRR) >= 2 ? 'text-green-400' : parseFloat(tradePlan.currentRR) >= 1.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {tradePlan.currentRR}:1
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">ATR (14)</span>
                  <p className="font-mono">${tradePlan.atr}</p>
                </div>
                <div>
                  <span className="text-muted-foreground text-xs">Risk/Reward</span>
                  <p className="font-mono text-xs">${tradePlan.currentRisk} / ${tradePlan.currentReward}</p>
                </div>
              </div>
            </div>

            {/* R/R Target Selector */}
            <div className="glass-card p-4">
              <h3 className="indicator-label mb-3 flex items-center gap-2">
                <Target className="h-3 w-3" />
                Obiectiv R/R
              </h3>
              <div className="flex gap-2">
                {[1.5, 2.0, 2.5, 3.0].map(rr => (
                  <button
                    key={rr}
                    onClick={() => setTargetRR(rr)}
                    className={`console-btn flex-1 ${targetRR === rr ? 'active' : ''}`}
                  >
                    {rr}:1
                  </button>
                ))}
              </div>
            </div>

            {/* Optimal Entry Calculation */}
            <div className={`p-4 rounded-lg border ${tradePlan.isRealistic ? 'glass-card border-primary/30' : 'bg-red-500/10 border-red-500/30'}`}>
              <h3 className="indicator-label mb-3 flex items-center gap-2">
                <TrendingDown className="h-3 w-3" />
                Pullback Entry (R/R = {targetRR}:1)
              </h3>
              
              {tradePlan.isRealistic ? (
                <div className="space-y-3">
                  <div className="bg-black/30 p-3 rounded border border-primary/20">
                    <span className="text-xs text-muted-foreground">Entry Optim (Pullback)</span>
                    <p className="font-mono text-2xl font-bold text-primary">
                      ${tradePlan.optimalEntry}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Necesită pullback de <span className="text-yellow-400">{tradePlan.pullbackPercent}%</span>
                    </p>
                  </div>
                  
                  {tradePlan.isPriceNearOptimal && (
                    <div className="bg-green-500/20 border border-green-500/50 p-3 rounded text-sm text-green-400 flex items-center gap-2">
                      <span className="icon-pulse">🎯</span>
                      Prețul este aproape de zona optimă!
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-red-500/10 p-3 rounded border border-red-500/30">
                  <p className="text-sm text-red-400">
                    ⚠️ R/R {targetRR}:1 nu este realizabil cu nivelurile actuale SL/TP.
                  </p>
                </div>
              )}
            </div>

            {/* Limit Order Plan Table */}
            <div className="glass-card p-4">
              <h3 className="indicator-label mb-3">📋 Plan Limit Order</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted-foreground text-xs border-b border-white/10">
                    <th className="text-left py-2">Nivel</th>
                    <th className="text-right py-2">Preț</th>
                    <th className="text-right py-2">Distanță</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  <tr className="border-b border-white/5">
                    <td className="py-2 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                      Take Profit
                    </td>
                    <td className="text-right text-cyan-400">${tradePlan.currentTP.toFixed(2)}</td>
                    <td className="text-right text-xs text-muted-foreground">
                      +{((tradePlan.currentTP - parseFloat(tradePlan.optimalEntry)) / parseFloat(tradePlan.optimalEntry) * 100).toFixed(2)}%
                    </td>
                  </tr>
                  <tr className="border-b border-white/5 bg-primary/5">
                    <td className="py-2 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-primary"></span>
                      Entry (Limit)
                    </td>
                    <td className="text-right text-primary font-bold">${tradePlan.optimalEntry}</td>
                    <td className="text-right text-xs text-muted-foreground">—</td>
                  </tr>
                  <tr>
                    <td className="py-2 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-orange-400"></span>
                      Stop Loss
                    </td>
                    <td className="text-right text-orange-400">${tradePlan.currentSL.toFixed(2)}</td>
                    <td className="text-right text-xs text-muted-foreground">
                      -{((parseFloat(tradePlan.optimalEntry) - tradePlan.currentSL) / parseFloat(tradePlan.optimalEntry) * 100).toFixed(2)}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* ATR Zones */}
            <div className="glass-card p-4">
              <h3 className="indicator-label mb-3">📏 Zone ATR (Volatilitate)</h3>
              <div className="space-y-2 text-sm font-mono">
                <div className="flex justify-between items-center p-2 rounded bg-green-500/10 border border-green-500/20">
                  <span className="text-green-400">0.5x ATR</span>
                  <span>${tradePlan.atrZoneHigh}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded bg-yellow-500/10 border border-yellow-500/20">
                  <span className="text-yellow-400">1.0x ATR</span>
                  <span>${tradePlan.atrZoneLow}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded bg-red-500/10 border border-red-500/20">
                  <span className="text-red-400">1.5x ATR (Deep)</span>
                  <span>${tradePlan.atrZoneDeep}</span>
                </div>
              </div>
            </div>

            {/* Key Levels */}
            <div className="glass-card p-4">
              <h3 className="indicator-label mb-3">🎯 Niveluri Cheie</h3>
              <div className="grid grid-cols-2 gap-3 text-sm font-mono">
                <div className="p-2 rounded bg-red-500/10 border border-red-500/20">
                  <span className="text-xs text-muted-foreground">Rezistență</span>
                  <p className="text-red-400">${tradePlan.resistance}</p>
                </div>
                <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
                  <span className="text-xs text-muted-foreground">Suport</span>
                  <p className="text-green-400">${tradePlan.support}</p>
                </div>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="text-[10px] text-muted-foreground/50 text-center p-4 border-t border-white/5">
              ⚠️ Acest plan este generat automat și nu constituie recomandări de investiții.
              Verificați întotdeauna condițiile pieței înainte de a plasa ordine.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
