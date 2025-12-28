import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export default function ChartContainer({ symbol, chartData }) {
  if (!chartData || chartData.length === 0) {
    return (
      <div className="terminal-card p-8 flex items-center justify-center h-[500px]">
        <p className="text-muted-foreground">Introduceți un simbol pentru a vizualiza graficul</p>
      </div>
    );
  }

  // Prepare data for Recharts
  const priceData = chartData.map(item => ({
    date: item.time,
    price: parseFloat(item.close),
    high: parseFloat(item.high),
    low: parseFloat(item.low),
    open: parseFloat(item.open),
    volume: parseFloat(item.volume),
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="terminal-card p-3 border border-primary/30">
          <p className="text-xs text-muted-foreground mb-1">{data.date}</p>
          <p className="text-sm font-mono">
            <span className="text-bull">H:</span> ${data.high.toFixed(2)} {' '}
            <span className="text-bear">L:</span> ${data.low.toFixed(2)}
          </p>
          <p className="text-sm font-mono font-bold">
            <span className="text-primary">Close:</span> ${data.price.toFixed(2)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Vol: {(data.volume / 1000000).toFixed(2)}M
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="terminal-card p-4" data-testid="chart-container">
      <div className="mb-4">
        <h2 className="font-heading text-lg font-bold uppercase tracking-tight">{symbol}</h2>
        <p className="text-xs text-muted-foreground uppercase tracking-widest mt-1">
          Grafic de Prețuri ({chartData.length} lumânări)
        </p>
      </div>
      
      <div className="space-y-4">
        {/* Price Chart */}
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={priceData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis 
              dataKey="date" 
              stroke="#a1a1aa"
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis 
              stroke="#a1a1aa"
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
              domain={['dataMin - 5', 'dataMax + 5']}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke="#22c55e" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorPrice)" 
            />
          </AreaChart>
        </ResponsiveContainer>

        {/* Volume Chart */}
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={priceData} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis 
              dataKey="date" 
              stroke="#a1a1aa"
              tick={false}
            />
            <YAxis 
              stroke="#a1a1aa"
              tick={{ fill: '#a1a1aa', fontSize: 10 }}
              tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
            />
            <Tooltip 
              formatter={(value) => [`${(value / 1000000).toFixed(2)}M`, 'Volume']}
              contentStyle={{ 
                backgroundColor: '#121212', 
                border: '1px solid #262626',
                borderRadius: '4px',
                fontSize: '12px'
              }}
            />
            <Bar 
              dataKey="volume" 
              fill="#26a69a"
              opacity={0.7}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}