export default function SignalCard({ signal, confidence, reasons, warnings, overrideReason, rrRatio }) {
  const getSignalBadgeClass = () => {
    switch (signal) {
      case 'BUY':
        return 'signal-badge-buy';
      case 'SELL':
        return 'signal-badge-sell';
      case 'HOLD':
        return 'signal-badge-hold';
      default:
        return 'signal-badge-wait';
    }
  };

  const getSignalIcon = () => {
    switch (signal) {
      case 'BUY':
        return '↑';
      case 'SELL':
        return '↓';
      case 'HOLD':
        return '↔';
      default:
        return '⏸';
    }
  };

  // Get gauge color class based on confidence
  const getGaugeClass = () => {
    if (confidence <= 40) return 'gauge-red';
    if (confidence <= 70) return 'gauge-yellow';
    return 'gauge-green';
  };

  const getConfidenceTextColor = () => {
    if (confidence <= 40) return 'text-red-400';
    if (confidence <= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  // Show override warning ONLY when R/R < 2.0 AND (NEUTRAL/WAIT with confidence < 50%)
  const shouldShowOverride = overrideReason && 
    rrRatio < 2.0 &&
    (signal === 'NEUTRAL' || signal === 'WAIT') && 
    confidence < 50;

  return (
    <div className="glass-card p-6" data-testid="signal-card">
      {/* Override Warning - ONLY when R/R < 2.0 + NEUTRAL/WAIT + low confidence */}
      {shouldShowOverride && (
        <div className="mb-6 p-4 bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/50 rounded-lg">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-10 w-10 bg-orange-500/20 rounded-full flex items-center justify-center border border-orange-500/50">
              <span className="text-2xl icon-pulse">🚫</span>
            </div>
            <h4 className="font-bold text-orange-400 uppercase tracking-wider text-sm">LOGICĂ CONSERVATOARE ACTIVATĂ</h4>
          </div>
          <p className="text-sm font-mono bg-black/30 p-3 rounded border border-orange-500/30 text-orange-300">
            {overrideReason}
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="indicator-label mb-2">Semnal de Tranzacționare</h3>
          <div className="flex items-center gap-3">
            <span className={`${getSignalBadgeClass()} px-4 py-2 rounded-sm font-mono text-2xl font-bold flex items-center gap-2`}>
              <span>{getSignalIcon()}</span>
              <span data-testid="signal-value">{signal}</span>
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="indicator-label mb-2">Confidence Score</div>
          <div className={`text-4xl font-bold font-mono ${getConfidenceTextColor()}`} data-testid="confidence-score">
            {confidence}%
          </div>
        </div>
      </div>

      {/* Confidence Gauge - Gradient Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Nivel Încredere</span>
          <div className="flex gap-3 text-[9px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>Scăzut
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500"></span>Mediu
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>Ridicat
            </span>
          </div>
        </div>
        <div className="confidence-gauge">
          <div 
            className={`confidence-gauge-fill ${getGaugeClass()}`}
            style={{ width: `${confidence}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-[9px] text-muted-foreground mt-1 font-mono">
          <span>0%</span>
          <span>40%</span>
          <span>70%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Reasons */}
      {reasons && reasons.length > 0 && (
        <div className="mb-4">
          <div className="indicator-label mb-2 flex items-center gap-2">
            <span className="icon-glow-green">🟢</span>
            Argumente
          </div>
          <ul className="space-y-1">
            {reasons.map((reason, index) => (
              <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-bull mt-1">•</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="mt-4 p-3 glass-card-red rounded-lg">
          <div className="indicator-label text-bear mb-2 flex items-center gap-2">
            <span className="icon-pulse icon-glow-red">🔴</span>
            Avertismente
          </div>
          <ul className="space-y-1">
            {warnings.map((warning, index) => (
              <li key={index} className="text-sm text-red-400/90 flex items-start gap-2">
                <span className="mt-1">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
