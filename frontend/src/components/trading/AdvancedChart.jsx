import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { TrendingUp, Eye, EyeOff } from 'lucide-react';

export default function AdvancedChart({ 
  symbol, 
  chartData, 
  indicators 
}) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRef = useRef({});

  // Indicator visibility state
  const [visibleIndicators, setVisibleIndicators] = useState({
    sma20: true,
    sma200: true,
    vwap: true,
    atr: false,
    ema20: false,
    ema50: false
  });

  // Toggle indicator visibility
  const toggleIndicator = (name) => {
    setVisibleIndicators(prev => ({
      ...prev,
      [name]: !prev[name]
    }));
  };

  // Process data
  const processedData = chartData && chartData.length > 0 ? 
    chartData.map(item => ({
      time: item.time,
      open: parseFloat(item.open),
      high: parseFloat(item.high),
      low: parseFloat(item.low),
      close: parseFloat(item.close),
      volume: parseFloat(item.volume)
    })).sort((a, b) => {
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      return String(a.time).localeCompare(String(b.time));
    }) : [];

  const volumeData = processedData.map(item => ({
    time: item.time,
    value: item.volume,
    color: item.close >= item.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(248, 113, 113, 0.5)'
  }));

  useEffect(() => {
    if (!chartContainerRef.current || processedData.length === 0) return;

    // Clear previous chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#0a0a0a' },
        textColor: '#a1a1aa'
      },
      grid: {
        vertLines: { color: '#1a1a1a' },
        horzLines: { color: '#1a1a1a' }
      },
      crosshair: {
        mode: 1
      },
      timeScale: {
        borderColor: '#262626',
        timeVisible: true,
        secondsVisible: false
      },
      rightPriceScale: {
        borderColor: '#262626'
      }
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444'
    });
    candleSeries.setData(processedData);
    candleSeriesRef.current = candleSeries;

    // Add volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume'
      },
      priceScaleId: 'volume',
      scaleMargins: {
        top: 0.8,
        bottom: 0
      }
    });
    volumeSeries.setData(volumeData);
    volumeSeriesRef.current = volumeSeries;

    // Auto-scale
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [chartData]);

  // Update indicators when visibility changes
  useEffect(() => {
    if (!chartRef.current || !indicators) return;

    // Remove all indicator series
    Object.values(indicatorSeriesRef.current).forEach(series => {
      if (series) {
        chartRef.current.removeSeries(series);
      }
    });
    indicatorSeriesRef.current = {};

    // Add visible indicators
    if (visibleIndicators.sma20 && indicators.sma_series?.sma_20) {
      const sma20Series = chartRef.current.addLineSeries({
        color: '#3b82f6',
        lineWidth: 2,
        title: 'SMA 20'
      });
      sma20Series.setData(indicators.sma_series.sma_20);
      indicatorSeriesRef.current.sma20 = sma20Series;
    }

    if (visibleIndicators.sma200 && indicators.sma_series?.sma_200 && indicators.sma_series.sma_200.length > 0) {
      const sma200Series = chartRef.current.addLineSeries({
        color: '#8b5cf6',
        lineWidth: 2,
        title: 'SMA 200'
      });
      sma200Series.setData(indicators.sma_series.sma_200);
      indicatorSeriesRef.current.sma200 = sma200Series;
    }

    if (visibleIndicators.vwap && indicators.vwap_series) {
      const vwapSeries = chartRef.current.addLineSeries({
        color: '#f59e0b',
        lineWidth: 2,
        title: 'VWAP',
        lineStyle: 2 // Dashed
      });
      vwapSeries.setData(indicators.vwap_series);
      indicatorSeriesRef.current.vwap = vwapSeries;
    }

    if (visibleIndicators.atr && indicators.atr?.series) {
      const atrSeries = chartRef.current.addLineSeries({
        color: '#ec4899',
        lineWidth: 1,
        title: 'ATR',
        priceScaleId: 'right'
      });
      atrSeries.setData(indicators.atr.series);
      indicatorSeriesRef.current.atr = atrSeries;
    }

    // EMA 20
    if (visibleIndicators.ema20 && chartData && chartData.length >= 20) {
      // Calculate EMA 20 from chartData
      const ema20Data = calculateEMA(processedData.map(d => d.close), 20);
      const ema20Series = chartRef.current.addLineSeries({
        color: '#10b981',
        lineWidth: 2,
        title: 'EMA 20'
      });
      ema20Series.setData(processedData.map((d, i) => ({
        time: d.time,
        value: ema20Data[i]
      })).filter(d => d.value !== null));
      indicatorSeriesRef.current.ema20 = ema20Series;
    }

    // EMA 50
    if (visibleIndicators.ema50 && chartData && chartData.length >= 50) {
      const ema50Data = calculateEMA(processedData.map(d => d.close), 50);
      const ema50Series = chartRef.current.addLineSeries({
        color: '#06b6d4',
        lineWidth: 2,
        title: 'EMA 50'
      });
      ema50Series.setData(processedData.map((d, i) => ({
        time: d.time,
        value: ema50Data[i]
      })).filter(d => d.value !== null));
      indicatorSeriesRef.current.ema50 = ema50Series;
    }

  }, [visibleIndicators, indicators, chartData]);

  // Simple EMA calculation
  const calculateEMA = (data, period) => {
    const k = 2 / (period + 1);
    const emaData = new Array(data.length).fill(null);
    
    // Calculate initial SMA
    let sum = 0;
    for (let i = 0; i < period; i++) {
      sum += data[i];
    }
    emaData[period - 1] = sum / period;
    
    // Calculate EMA
    for (let i = period; i < data.length; i++) {
      emaData[i] = data[i] * k + emaData[i - 1] * (1 - k);
    }
    
    return emaData;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="glass-card p-8 flex items-center justify-center h-[500px]">
        <p className="text-muted-foreground">Introduceți un simbol pentru a vizualiza graficul</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-4">
      {/* Header with Symbol and Controls */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-heading text-lg font-bold uppercase tracking-tight flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            {symbol}
          </h2>
          <p className="text-xs text-muted-foreground uppercase tracking-widest mt-1">
            Advanced Chart • {chartData.length} candles
          </p>
        </div>

        {/* Indicator Toggles */}
        <div className="flex flex-wrap gap-2">
          <IndicatorToggle
            name="SMA 20"
            color="#3b82f6"
            active={visibleIndicators.sma20}
            onClick={() => toggleIndicator('sma20')}
          />
          <IndicatorToggle
            name="SMA 200"
            color="#8b5cf6"
            active={visibleIndicators.sma200}
            onClick={() => toggleIndicator('sma200')}
          />
          <IndicatorToggle
            name="VWAP"
            color="#f59e0b"
            active={visibleIndicators.vwap}
            onClick={() => toggleIndicator('vwap')}
          />
          <IndicatorToggle
            name="ATR"
            color="#ec4899"
            active={visibleIndicators.atr}
            onClick={() => toggleIndicator('atr')}
          />
          <IndicatorToggle
            name="EMA 20"
            color="#10b981"
            active={visibleIndicators.ema20}
            onClick={() => toggleIndicator('ema20')}
          />
          <IndicatorToggle
            name="EMA 50"
            color="#06b6d4"
            active={visibleIndicators.ema50}
            onClick={() => toggleIndicator('ema50')}
          />
        </div>
      </div>

      {/* Chart Container */}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}

// Indicator Toggle Component
function IndicatorToggle({ name, color, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
        active
          ? 'bg-white/10 border border-white/20'
          : 'bg-white/5 border border-white/10 opacity-50 hover:opacity-100'
      }`}
    >
      {active ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span>{name}</span>
    </button>
  );
}
