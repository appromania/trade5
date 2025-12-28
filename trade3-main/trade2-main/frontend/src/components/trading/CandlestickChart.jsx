import { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, CrosshairMode, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';

export default function CandlestickChart({ 
  symbol, 
  chartData, 
  levels, 
  useHeikinAshi = false, 
  donchianChannel, 
  williamsFractals 
}) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  
  // Transform to Heikin Ashi if needed
  const transformToHeikinAshi = (data) => {
    const haData = [];
    
    for (let i = 0; i < data.length; i++) {
      const item = data[i];
      const open = parseFloat(item.open);
      const high = parseFloat(item.high);
      const low = parseFloat(item.low);
      const close = parseFloat(item.close);
      
      const haClose = (open + high + low + close) / 4;
      
      let haOpen;
      if (i === 0) {
        haOpen = (open + close) / 2;
      } else {
        const prevHa = haData[i - 1];
        haOpen = (prevHa.open + prevHa.close) / 2;
      }
      
      const haHigh = Math.max(high, haOpen, haClose);
      const haLow = Math.min(low, haOpen, haClose);
      
      haData.push({
        time: item.time,
        open: haOpen,
        high: haHigh,
        low: haLow,
        close: haClose,
        volume: parseFloat(item.volume)
      });
    }
    
    return haData;
  };

  // Prepare and sort data
  const processedData = useMemo(() => {
    if (!chartData || chartData.length === 0) return { candles: [], volumes: [] };
    
    const dataToUse = useHeikinAshi ? transformToHeikinAshi(chartData) : chartData;
    
    // Smart sort function that handles both string dates and Unix timestamps
    const smartSort = (a, b) => {
      // If time is a number (Unix timestamp), sort numerically
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      // If time is a string (YYYY-MM-DD), sort lexicographically
      if (typeof a.time === 'string' && typeof b.time === 'string') {
        return a.time.localeCompare(b.time);
      }
      // Fallback: convert to string and compare
      return String(a.time).localeCompare(String(b.time));
    };
    
    // Convert to lightweight-charts format with proper time format
    const candles = dataToUse.map(item => ({
      time: item.time, // Can be YYYY-MM-DD string OR Unix timestamp
      open: parseFloat(item.open),
      high: parseFloat(item.high),
      low: parseFloat(item.low),
      close: parseFloat(item.close)
    })).sort(smartSort);
    
    const volumes = dataToUse.map(item => ({
      time: item.time,
      value: parseFloat(item.volume),
      color: parseFloat(item.close) >= parseFloat(item.open) 
        ? 'rgba(34, 197, 94, 0.5)' 
        : 'rgba(248, 113, 113, 0.5)'
    })).sort(smartSort);
    
    return { candles, volumes };
  }, [chartData, useHeikinAshi]);

  // Prepare Donchian Channel data
  const donchianData = useMemo(() => {
    if (!donchianChannel?.channel_data) return { upper: [], lower: [], middle: [] };
    
    // Smart sort for channel data
    const smartSort = (a, b) => {
      if (typeof a.time === 'number' && typeof b.time === 'number') {
        return a.time - b.time;
      }
      if (typeof a.time === 'string' && typeof b.time === 'string') {
        return a.time.localeCompare(b.time);
      }
      return String(a.time).localeCompare(String(b.time));
    };
    
    const sortedData = [...donchianChannel.channel_data].sort(smartSort);
    
    return {
      upper: sortedData.map(d => ({ time: d.time, value: d.upper })),
      lower: sortedData.map(d => ({ time: d.time, value: d.lower })),
      middle: sortedData.map(d => ({ time: d.time, value: d.middle }))
    };
  }, [donchianChannel]);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || !processedData.candles.length) return;

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
        background: { type: 'solid', color: 'transparent' },
        textColor: '#a1a1aa',
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(38, 38, 38, 0.5)' },
        horzLines: { color: 'rgba(38, 38, 38, 0.5)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      handleScroll: true,
      handleScale: true,
      rightPriceScale: {
        autoScale: true,
        borderColor: 'rgba(38, 38, 38, 0.8)',
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: 'rgba(38, 38, 38, 0.8)',
        barSpacing: 10,
        rightOffset: 5,
      },
      localization: {
        locale: 'en-US',
      },
    });

    chartRef.current = chart;

    // **CRITICAL FIX**: Clean and validate data BEFORE setData()
    // Remove duplicates and ensure ascending order
    const cleanData = (data) => {
      if (!data || data.length === 0) return [];
      
      // Remove duplicates by time (keep first occurrence)
      const seen = new Set();
      const unique = data.filter(item => {
        if (seen.has(item.time)) {
          console.warn(`Duplicate timestamp detected and removed: ${item.time}`);
          return false;
        }
        seen.add(item.time);
        return true;
      });
      
      // Sort ascending by time
      const sorted = unique.sort((a, b) => {
        if (typeof a.time === 'number' && typeof b.time === 'number') {
          return a.time - b.time;
        }
        if (typeof a.time === 'string' && typeof b.time === 'string') {
          return a.time.localeCompare(b.time);
        }
        return 0;
      });
      
      console.log(`Data cleaned: ${data.length} → ${sorted.length} unique timestamps`);
      return sorted;
    };

    // Add Candlestick Series - V5 API
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#f87171',
      borderUpColor: '#22c55e',
      borderDownColor: '#f87171',
      wickUpColor: '#22c55e',
      wickDownColor: '#f87171',
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
    });
    candleSeriesRef.current = candleSeries;
    candleSeries.setData(cleanData(processedData.candles));

    // Add Volume Series - V5 API
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(cleanData(processedData.volumes));

    // Add Donchian Channel lines
    if (donchianData.upper.length > 0) {
      const upperLine = chart.addSeries(LineSeries, {
        color: 'rgba(34, 197, 94, 0.6)',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      upperLine.setData(cleanData(donchianData.upper));

      const lowerLine = chart.addSeries(LineSeries, {
        color: 'rgba(248, 113, 113, 0.6)',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      lowerLine.setData(cleanData(donchianData.lower));

      const middleLine = chart.addSeries(LineSeries, {
        color: 'rgba(156, 163, 175, 0.4)',
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      middleLine.setData(cleanData(donchianData.middle));
    }

    // Add Price Lines for levels
    if (levels) {
      if (levels.resistance) {
        candleSeries.createPriceLine({
          price: levels.resistance,
          color: '#f87171',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'R',
        });
      }
      if (levels.support) {
        candleSeries.createPriceLine({
          price: levels.support,
          color: '#22c55e',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'S',
        });
      }
      if (levels.stop_loss) {
        candleSeries.createPriceLine({
          price: levels.stop_loss,
          color: '#f59e0b',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'SL',
        });
      }
      if (levels.take_profit) {
        candleSeries.createPriceLine({
          price: levels.take_profit,
          color: '#06b6d4',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'TP',
        });
      }
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [processedData, donchianData, levels]);

  if (!chartData || chartData.length === 0) {
    return (
      <div className="glass-card p-8 flex items-center justify-center h-[500px]">
        <p className="text-muted-foreground">Introduceți un simbol pentru a vizualiza graficul</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-4" data-testid="chart-container">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="font-heading text-lg font-bold uppercase tracking-tight">{symbol}</h2>
          <p className="text-xs text-muted-foreground uppercase tracking-widest mt-1">
            {useHeikinAshi ? '🕯️ Heikin Ashi' : '📊 Candlestick'} • {chartData.length} candles • Scroll/Zoom
          </p>
        </div>
        <div className="flex gap-4 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-[#22c55e]"></div>
            <span>Donchian Up</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-[#f87171]"></div>
            <span>Down</span>
          </div>
        </div>
      </div>

      {levels && (
        <div className="flex flex-wrap gap-4 mb-3 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-[#f87171]"></div>
            <span>R: ${levels.resistance?.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-[#22c55e]"></div>
            <span>S: ${levels.support?.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-[#06b6d4]"></div>
            <span>TP: ${levels.take_profit?.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-[#f59e0b]"></div>
            <span>SL: ${levels.stop_loss?.toFixed(2)}</span>
          </div>
        </div>
      )}

      <div ref={chartContainerRef} className="w-full" style={{ minHeight: '500px' }} />

      <div className="mt-2 text-[10px] text-muted-foreground/50 text-center">
        🖱️ Scroll = zoom • Drag = pan
      </div>
    </div>
  );
}
