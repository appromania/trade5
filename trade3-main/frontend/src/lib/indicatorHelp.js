export const INDICATOR_HELP = {
  ADX: {
    name: "Average Directional Index",
    description: "Măsoară puterea trendului, indiferent de direcție",
    interpretation: {
      below_20: "Piață laterală (RANGING) - Evitați semnalele de trend",
      between_20_25: "Trend slab sau în formare",
      above_25: "Trend puternic - Semnalele sunt mai fiabile",
      above_50: "Trend foarte puternic"
    },
    action: "ADX NU indică direcția, doar puterea. Folosiți împreună cu +DI și -DI."
  },
  RSI: {
    name: "Relative Strength Index",
    description: "Măsoară momentum-ul și identifică zone de supracumpărare/supravânzare",
    interpretation: {
      below_30: "Supravândut - Posibilă revenire (BUY opportunity)",
      between_30_70: "Zona normală - Fără semnal clar",
      above_70: "Supracumpărat - Risc de corecție (SELL/WAIT)"
    },
    action: "În trend puternic, RSI poate rămâne >70 (bullish) sau <30 (bearish) mult timp."
  },
  STOCH_RSI: {
    name: "Stochastic RSI",
    description: "Versiune mai sensibilă a RSI, excelentă pentru timing precis",
    interpretation: {
      below_20: "Supravândut extrem - Punct bun de intrare",
      between_20_80: "Zona echilibrată",
      above_80: "Supracumpărat extrem - NU CUMPĂRA! Așteaptă corecție"
    },
    action: "Foarte reactiv - folosește pentru timing exact al intrării/ieșirii."
  },
  ATR: {
    name: "Average True Range",
    description: "Măsoară volatilitatea pieței (cât de mult se mișcă prețul)",
    interpretation: {
      low: "Volatilitate scăzută - Mișcări mici de preț, SL strâns",
      medium: "Volatilitate normală",
      high: "Volatilitate ridicată - Mișcări mari, SL mai larg"
    },
    action: "Folosit pentru calculul Stop Loss: SL = Entry - (ATR * 1.5-2)"
  },
  MACD: {
    name: "Moving Average Convergence Divergence",
    description: "Identifică schimbări în momentum și direcția trendului",
    interpretation: {
      histogram_positive: "Momentum bullish - MACD peste Signal line",
      histogram_negative: "Momentum bearish - MACD sub Signal line",
      crossover_up: "Bullish crossover - Posibil semnal BUY",
      crossover_down: "Bearish crossover - Posibil semnal SELL"
    },
    action: "Cel mai bun în trend. În piață laterală generează semnale false."
  },
  VOLUME: {
    name: "Volume Analysis",
    description: "Confirmă puterea unei mișcări de preț",
    interpretation: {
      high_with_price_up: "Creștere validată - Sănătos",
      low_with_price_up: "Creștere slabă - Posibilă capcană (Volume Exhaustion)",
      high_with_price_down: "Scădere validată - Pressure puternic",
      low_with_price_down: "Scădere slabă - Posibilă revenire"
    },
    action: "NICIODATĂ nu cumpăra când volumul este < 0.8x media (risc de reversare)."
  },
  EMA: {
    name: "Exponential Moving Average",
    description: "Media mobilă care reacționează mai rapid la schimbări de preț",
    interpretation: {
      price_above_ema20: "Short-term bullish",
      price_above_ema50: "Medium-term bullish - Trend confirmat",
      price_above_ema200: "Long-term bullish - Bull market",
      price_below_all: "Bearish pe toate timeframe-urile"
    },
    action: "EMA 50 este cel mai important - definește trendul principal."
  },
  SUPPORT_RESISTANCE: {
    name: "Suport & Rezistență",
    description: "Niveluri psihologice unde prețul tinde să se oprească sau să se întoarcă",
    interpretation: {
      at_support: "Zona de cumpărare - SL sub suport",
      at_resistance: "Zona de vânzare - Sau așteaptă breakout",
      between: "Zona neutră",
      breakout_resistance: "Breakout bullish - Vechea rezistență devine suport nou"
    },
    action: "NU cumpăra NICIODATĂ la rezistență. Așteaptă pullback sau breakout confirmat."
  }
};

export function getIndicatorHelp(indicator) {
  return INDICATOR_HELP[indicator] || null;
}
