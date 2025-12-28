import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

export default function TrendContext({ trendAlignment }) {
  if (!trendAlignment) return null;

  const { daily, weekly, aligned, message } = trendAlignment;

  const TrendBadge = ({ trend, label, emaValue }) => (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`trend-badge ${trend === 'BULLISH' ? 'bullish' : 'bearish'}`}>
          {trend === 'BULLISH' ? (
            <TrendingUp className="inline w-3 h-3 mr-1" />
          ) : (
            <TrendingDown className="inline w-3 h-3 mr-1" />
          )}
          {trend}
        </span>
        <span className="text-xs text-muted-foreground font-mono">
          EMA: ${emaValue?.toFixed(2)}
        </span>
      </div>
    </div>
  );

  return (
    <div className="glass-card p-4">
      <h3 className="indicator-label mb-3 flex items-center gap-2">
        <span className="icon-pulse">📊</span>
        Trend Context
      </h3>
      
      <div className="grid grid-cols-2 gap-4 mb-3">
        <TrendBadge 
          trend={daily?.trend} 
          label="Daily (EMA 20)" 
          emaValue={daily?.ema_value} 
        />
        <TrendBadge 
          trend={weekly?.trend} 
          label="Weekly (EMA 50)" 
          emaValue={weekly?.ema_value} 
        />
      </div>

      <div className={`mt-3 p-2 rounded border flex items-center gap-2 text-xs ${
          daily?.trend === 'BULLISH' && weekly?.trend === 'BULLISH'
          ? 'bg-green-500/10 text-green-500 border-green-500/20'
          : daily?.trend === 'BEARISH' && weekly?.trend === 'BEARISH'
          ? 'bg-red-500/10 text-red-500 border-red-500/20 font-bold'
          : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
      }`}>
        {daily?.trend === 'BULLISH' && weekly?.trend === 'BULLISH' ? (
          <>
            <span className="icon-glow-green">✓</span>
            <span>Trenduri Aliniate - Semnal Mai Puternic</span>
          </>
        ) : daily?.trend === 'BEARISH' && weekly?.trend === 'BEARISH' ? (
          <>
            <span className="text-red-500">❌</span>
            <span>Confluență Bearish - Risc Extrem</span>
          </>
        ) : (
          <>
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <span>{message}</span>
          </>
        )}
      </div>
    </div>
  );
}
