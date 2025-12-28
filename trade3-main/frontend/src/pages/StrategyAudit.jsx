import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, ArrowLeft, RefreshCw, CheckCircle, XCircle, Clock, Beaker } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

export default function StrategyAudit() {
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);
  const [stats, setStats] = useState(null);

  // Fetch simulations
  const fetchSimulations = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/simulations`);
      if (response.data.success) {
        setSimulations(response.data.trades);
      }
    } catch (error) {
      console.error('Fetch simulations error:', error);
      toast.error('Eroare la încărcarea simulărilor');
    } finally {
      setLoading(false);
    }
  };

  // Audit all active simulations
  const handleAudit = async () => {
    setAuditing(true);
    try {
      const response = await axios.post(`${API_URL}/simulations/audit`);
      if (response.data.success) {
        setStats(response.data.statistics);
        toast.success(`Audit complet! ${response.data.updated} tranzacții actualizate`);
        await fetchSimulations();
      }
    } catch (error) {
      console.error('Audit error:', error);
      toast.error('Eroare la audit');
    } finally {
      setAuditing(false);
    }
  };

  useEffect(() => {
    fetchSimulations();
  }, []);

  // Calculate stats from simulations
  useEffect(() => {
    if (simulations.length > 0) {
      const success = simulations.filter(s => s.status === 'success').length;
      const failed = simulations.filter(s => s.status === 'failed').length;
      const active = simulations.filter(s => s.status === 'active').length;
      const successRate = (success + failed) > 0 ? (success / (success + failed) * 100) : 0;
      
      setStats({
        total_trades: simulations.length,
        successful_trades: success,
        failed_trades: failed,
        active_trades: active,
        success_rate: successRate.toFixed(1)
      });
    }
  }, [simulations]);

  const getStatusIcon = (status) => {
    switch(status) {
      case 'success': return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'failed': return <XCircle className="h-5 w-5 text-red-400" />;
      case 'active': return <Clock className="h-5 w-5 text-yellow-400" />;
      default: return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'success': return 'bg-green-500/10 border-green-500/30 text-green-400';
      case 'failed': return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'active': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
      default: return 'bg-white/5 border-white/10 text-muted-foreground';
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-[#262626] bg-[#0A0A0A]">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="p-2 hover:bg-white/5 rounded transition-colors">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 bg-purple-500/20 rounded flex items-center justify-center">
                  <Beaker className="h-6 w-6 text-purple-400" />
                </div>
                <div>
                  <h1 className="font-heading text-xl font-black uppercase tracking-tight">
                    Strategy Audit
                  </h1>
                  <p className="text-xs text-muted-foreground uppercase tracking-widest">
                    Paper Trading Tester
                  </p>
                </div>
              </div>
            </div>
            
            <button
              onClick={handleAudit}
              disabled={auditing || loading}
              className="console-btn flex items-center gap-2"
            >
              {auditing ? (
                <>
                  <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                  Verificare...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Verifică Status
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="glass-card p-4">
              <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Total Trades</div>
              <div className="text-3xl font-bold font-mono">{stats.total_trades}</div>
            </div>
            <div className="glass-card p-4 border-green-500/20">
              <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Succesful</div>
              <div className="text-3xl font-bold font-mono text-green-400">{stats.successful_trades}</div>
            </div>
            <div className="glass-card p-4 border-red-500/20">
              <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Failed</div>
              <div className="text-3xl font-bold font-mono text-red-400">{stats.failed_trades}</div>
            </div>
            <div className="glass-card p-4 border-yellow-500/20">
              <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Active</div>
              <div className="text-3xl font-bold font-mono text-yellow-400">{stats.active_trades}</div>
            </div>
            <div className="glass-card p-4 border-primary/20">
              <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Success Rate</div>
              <div className={`text-3xl font-bold font-mono ${
                parseFloat(stats.success_rate) >= 70 ? 'text-green-400' : 
                parseFloat(stats.success_rate) >= 50 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {stats.success_rate}%
              </div>
            </div>
          </div>
        )}

        {/* Simulations Table */}
        <div className="glass-card p-6">
          <h2 className="indicator-label mb-4">Toate Simulările</h2>
          
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground font-mono">Se încarcă simulările...</p>
              </div>
            </div>
          ) : simulations.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Beaker className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">Nu există simulări</p>
              <p className="text-sm">Creați o simulare folosind butonul 🧪 Simulate Trade din Dashboard</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted-foreground text-xs border-b border-white/10">
                    <th className="text-left py-3 px-2">Status</th>
                    <th className="text-left py-3 px-2">Symbol</th>
                    <th className="text-right py-3 px-2">Entry</th>
                    <th className="text-right py-3 px-2">Current/Exit</th>
                    <th className="text-right py-3 px-2">SL</th>
                    <th className="text-right py-3 px-2">TP</th>
                    <th className="text-right py-3 px-2">P/L %</th>
                    <th className="text-right py-3 px-2">P/L $</th>
                    <th className="text-left py-3 px-2">Date</th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {simulations.map((sim) => (
                    <tr key={sim.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="py-3 px-2">
                        <div className={`flex items-center gap-2 px-2 py-1 rounded border ${getStatusColor(sim.status)}`}>
                          {getStatusIcon(sim.status)}
                          <span className="text-[10px] uppercase font-bold">{sim.status}</span>
                        </div>
                      </td>
                      <td className="py-3 px-2 font-bold">{sim.symbol}</td>
                      <td className="py-3 px-2 text-right">${sim.entry_price.toFixed(2)}</td>
                      <td className="py-3 px-2 text-right">
                        ${(sim.exit_price || sim.current_price || sim.entry_price).toFixed(2)}
                      </td>
                      <td className="py-3 px-2 text-right text-red-400">${sim.stop_loss.toFixed(2)}</td>
                      <td className="py-3 px-2 text-right text-green-400">${sim.take_profit.toFixed(2)}</td>
                      <td className={`py-3 px-2 text-right font-bold ${
                        sim.pnl_percent > 0 ? 'text-green-400' : 
                        sim.pnl_percent < 0 ? 'text-red-400' : 'text-muted-foreground'
                      }`}>
                        {sim.pnl_percent > 0 ? '+' : ''}{sim.pnl_percent?.toFixed(2)}%
                      </td>
                      <td className={`py-3 px-2 text-right font-bold ${
                        sim.pnl_amount > 0 ? 'text-green-400' : 
                        sim.pnl_amount < 0 ? 'text-red-400' : 'text-muted-foreground'
                      }`}>
                        {sim.pnl_amount > 0 ? '+' : ''}${sim.pnl_amount?.toFixed(2)}
                      </td>
                      <td className="py-3 px-2 text-xs text-muted-foreground">
                        {new Date(sim.entry_date).toLocaleDateString('ro-RO')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
