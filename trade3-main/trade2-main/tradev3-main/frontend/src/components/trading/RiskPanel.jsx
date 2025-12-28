export default function RiskPanel({ riskData }) {
  if (!riskData) return null;

  const getRiskColor = () => {
    if (riskData.favorable) return 'text-bull';
    return 'text-bear';
  };

  return (
    <div className="terminal-card p-4" data-testid="risk-panel">
      <h3 className="indicator-label mb-4">Risk Management</h3>
      
      <div className="space-y-4">
        {/* Entry & Exit */}
        <div className="grid grid-cols-3 gap-3">
          <div className="indicator-card">
            <div className="indicator-label text-primary">Entry</div>
            <div className="indicator-value text-base mono-data">${riskData.entry_price}</div>
          </div>
          <div className="indicator-card">
            <div className="indicator-label text-bear">Stop Loss</div>
            <div className="indicator-value text-base mono-data">${riskData.stop_loss}</div>
            <div className="indicator-status text-bear">-{riskData.stop_loss_percent}%</div>
          </div>
          <div className="indicator-card">
            <div className="indicator-label text-bull">Take Profit</div>
            <div className="indicator-value text-base mono-data">${riskData.take_profit}</div>
          </div>
        </div>

        {/* R/R Ratio */}
        <div className="indicator-card">
          <div className="indicator-label">Raport Risc/Recompensă</div>
          <div className={`indicator-value ${getRiskColor()}`}>
            1:{riskData.risk_reward_ratio}
          </div>
          <div className="indicator-status">
            {riskData.favorable ? '✅ Favorabil (R/R > 1.5)' : '⚠️ Nefavorabil - Așteptați setup mai bun'}
          </div>
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