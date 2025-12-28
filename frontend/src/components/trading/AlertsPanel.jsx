import { AlertTriangle, TrendingUp, Volume2, Activity } from 'lucide-react';

export default function AlertsPanel({ alerts, marketContext }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="terminal-card p-4">
        <h3 className="indicator-label mb-4">Alerte și Avertizări</h3>
        <p className="text-sm text-muted-foreground">Nu există alerte active</p>
      </div>
    );
  }

  const getSeverityClass = (severity) => {
    if (severity === 'high') return 'alert-high';
    if (severity === 'medium') return 'alert-medium';
    return 'alert-low';
  };

  const getIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'volatilitate':
      case 'earnings':
        return <AlertTriangle className="h-4 w-4" />;
      case 'volum':
        return <Volume2 className="h-4 w-4" />;
      case 'supracumpărat':
      case 'rezistență':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-4" data-testid="alerts-panel">
      <div className="terminal-card p-4">
        <h3 className="indicator-label mb-4">Alerte și Avertizări</h3>
        <div className="space-y-2">
          {alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-3 ${getSeverityClass(alert.severity)} rounded-sm`}
              data-testid={`alert-${alert.severity}`}
            >
              <div className="flex items-start gap-2">
                <div className="mt-0.5">{getIcon(alert.type)}</div>
                <div className="flex-1">
                  <div className="font-mono text-xs uppercase tracking-wider font-bold mb-1">
                    {alert.type}
                  </div>
                  <div className="text-sm leading-relaxed">{alert.message}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Market Context */}
      {marketContext && (
        <div className="terminal-card p-4">
          <h3 className="indicator-label mb-4">Context Piață Globală</h3>
          <div className="space-y-3">
            {/* VIX */}
            {marketContext.vix && marketContext.vix.value && (
              <div className="indicator-card" data-testid="market-vix">
                <div className="indicator-label">VIX (Volatilitate)</div>
                <div className="indicator-value text-base">{marketContext.vix.value}</div>
                <div className={`indicator-status ${
                  marketContext.vix.high_volatility ? 'text-bear' : 'text-bull'
                }`}>
                  {marketContext.vix.level}
                </div>
              </div>
            )}

            {/* S&P 500 */}
            {marketContext.sp500 && (
              <div className="indicator-card" data-testid="market-sp500">
                <div className="indicator-label">S&P 500 Trend</div>
                <div className={`indicator-value text-base ${
                  marketContext.sp500.trend === 'BULLISH' ? 'text-bull' : 'text-bear'
                }`}>
                  {marketContext.sp500.trend}
                </div>
                <div className="indicator-status mono-data">
                  {marketContext.sp500.change_percent > 0 ? '+' : ''}{marketContext.sp500.change_percent}%
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}