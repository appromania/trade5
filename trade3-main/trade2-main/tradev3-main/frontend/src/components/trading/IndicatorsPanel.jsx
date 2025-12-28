import IndicatorTooltip from './IndicatorTooltip';

export default function IndicatorsPanel({ indicators }) {
  if (!indicators) {
    return (
      <div className="terminal-card p-6">
        <p className="text-muted-foreground text-center">Nu există date de afișat</p>
      </div>
    );
  }

  const getSignalColor = (signal) => {
    if (!signal) return 'text-muted-foreground';
    const s = signal.toLowerCase();
    if (s.includes('supră') || s.includes('suprac') || s === 'supracumpărat') return 'text-bear';
    if (s.includes('suprâ') || s.includes('suprav') || s === 'supravândut') return 'text-bull';
    return 'text-muted-foreground';
  };

  const getRegimeColor = (regime) => {
    if (regime === 'TRENDING') return 'text-bull';
    if (regime === 'RANGING') return 'text-bear';
    return 'text-yellow-500';
  };

  return (
    <div className="space-y-4" data-testid="indicators-panel">
      <div className="terminal-card p-4">
        <h3 className="indicator-label mb-4">Indicatori Tehnici</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {/* ADX */}
          <div className="indicator-card" data-testid="indicator-adx">
            <div className="indicator-label flex items-center">
              ADX
              <IndicatorTooltip indicator="ADX" />
            </div>
            <div className="indicator-value text-primary">{indicators.adx.value}</div>
            <div className={`indicator-status font-mono ${getRegimeColor(indicators.adx.regime)}`}>
              {indicators.adx.regime}
            </div>
          </div>

          {/* RSI */}
          <div className="indicator-card" data-testid="indicator-rsi">
            <div className="indicator-label flex items-center">
              RSI (14)
              <IndicatorTooltip indicator="RSI" />
            </div>
            <div className="indicator-value">{indicators.rsi.value}</div>
            <div className={`indicator-status ${getSignalColor(indicators.rsi.signal)}`}>
              {indicators.rsi.signal}
            </div>
          </div>

          {/* Stoch RSI */}
          <div className="indicator-card" data-testid="indicator-stoch-rsi">
            <div className="indicator-label flex items-center">
              Stoch RSI
              <IndicatorTooltip indicator="STOCH_RSI" />
            </div>
            <div className="indicator-value">{indicators.stoch_rsi.k}%</div>
            <div className={`indicator-status ${getSignalColor(indicators.stoch_rsi.signal)}`}>
              {indicators.stoch_rsi.signal}
            </div>
          </div>

          {/* ATR */}
          <div className="indicator-card" data-testid="indicator-atr">
            <div className="indicator-label flex items-center">
              ATR (14)
              <IndicatorTooltip indicator="ATR" />
            </div>
            <div className="indicator-value mono-data">${indicators.atr.value}</div>
            <div className="indicator-status">{indicators.atr.percent}% din preț</div>
          </div>

          {/* MACD */}
          <div className="indicator-card" data-testid="indicator-macd">
            <div className="indicator-label flex items-center">
              MACD
              <IndicatorTooltip indicator="MACD" />
            </div>
            <div className="indicator-value text-sm mono-data">{indicators.macd.histogram}</div>
            <div className={`indicator-status ${indicators.macd.cross === 'bullish' ? 'text-bull' : 'text-bear'}`}>
              {indicators.macd.cross}
            </div>
          </div>

          {/* Volume */}
          <div className="indicator-card" data-testid="indicator-volume">
            <div className="indicator-label flex items-center">
              Volum Ratio
              <IndicatorTooltip indicator="VOLUME" />
            </div>
            <div className="indicator-value">{indicators.volume.ratio}x</div>
            <div className="indicator-status">{indicators.volume.trend}</div>
          </div>
        </div>
      </div>

      {/* EMAs */}
      <div className="terminal-card p-4">
        <h3 className="indicator-label mb-4 flex items-center">
          Medii Mobile Exponențiale
          <IndicatorTooltip indicator="EMA" />
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="indicator-card">
            <div className="indicator-label">EMA 20</div>
            <div className="indicator-value text-sm mono-data">${indicators.price.ema_20}</div>
          </div>
          <div className="indicator-card">
            <div className="indicator-label">EMA 50</div>
            <div className="indicator-value text-sm mono-data">${indicators.price.ema_50}</div>
          </div>
          {indicators.price.ema_200 && (
            <div className="indicator-card">
              <div className="indicator-label">EMA 200</div>
              <div className="indicator-value text-sm mono-data">${indicators.price.ema_200}</div>
            </div>
          )}
        </div>
      </div>

      {/* Pivots */}
      <div className="terminal-card p-4">
        <h3 className="indicator-label mb-4 flex items-center">
          Niveluri de Suport/Rezistență
          <IndicatorTooltip indicator="SUPPORT_RESISTANCE" />
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="indicator-card">
            <div className="indicator-label text-bear">Rezistență</div>
            <div className="indicator-value text-sm mono-data">${indicators.pivots.resistance}</div>
          </div>
          <div className="indicator-card">
            <div className="indicator-label text-bull">Suport</div>
            <div className="indicator-value text-sm mono-data">${indicators.pivots.support}</div>
          </div>
        </div>
      </div>
    </div>
  );
}