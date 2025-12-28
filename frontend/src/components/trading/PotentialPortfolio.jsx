import { useState, useEffect } from 'react';
import { Wallet, RefreshCw, X, TrendingUp, TrendingDown } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

export default function PotentialPortfolio({ isOpen, onClose }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch watchlist
  const fetchWatchlist = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/watchlist`);
      if (response.data.success) {
        setEntries(response.data.entries);
      }
    } catch (error) {
      console.error('Fetch watchlist error:', error);
      toast.error('Eroare la încărcarea watchlist-ului');
    } finally {
      setLoading(false);
    }
  };

  // Remove from watchlist
  const handleRemove = async (entryId) => {
    try {
      await axios.delete(`${API_URL}/watchlist/${entryId}`);
      toast.success('Intrare eliminată din Potential Portfolio');
      fetchWatchlist();
    } catch (error) {
      console.error('Remove error:', error);
      toast.error('Eroare la eliminare');
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchWatchlist();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Sidebar Panel */}
      <div className="relative w-full max-w-2xl h-full bg-[#0a0a0a] border-l border-[#262626] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#0a0a0a] border-b border-[#262626] p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-purple-500/20 rounded flex items-center justify-center">
              <Wallet className="h-4 w-4 text-purple-400" />
            </div>
            <div>
              <h2 className="font-bold text-sm uppercase tracking-wider">Potential Portfolio</h2>
              <p className="text-[10px] text-muted-foreground">{entries.length} intrări</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchWatchlist}
              disabled={loading}
              className="p-2 hover:bg-white/5 rounded transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/5 rounded transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground font-mono">Se încarcă portfolio-ul...</p>
              </div>
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <Wallet className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg mb-2">Nu există intrări în watchlist</p>
              <p className="text-sm">Adăugați simboluri folosind butoanele de alertă sau simulare</p>
            </div>
          ) : (
            <div className="space-y-4">
              {entries.map((entry) => (
                <div key={entry.id} className="glass-card p-4 hover:border-primary/30 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-mono text-xl font-bold">{entry.symbol}</h3>
                        <span className={`text-xs px-2 py-1 rounded border ${
                          entry.status === 'triggered' 
                            ? 'bg-green-500/10 border-green-500/30 text-green-400' 
                            : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                        }`}>
                          {entry.status === 'triggered' ? 'În Zonă!' : 'Așteptare'}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Adăugat: {new Date(entry.added_at).toLocaleDateString('ro-RO')}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemove(entry.id)}
                      className="p-2 hover:bg-red-500/20 rounded transition-colors"
                      title="Elimină din watchlist"
                    >
                      <X className="h-4 w-4 text-red-400" />
                    </button>
                  </div>

                  {/* Price Grid */}
                  <div className="grid grid-cols-4 gap-3 mb-3">
                    <div className="text-center">
                      <div className="text-[10px] text-muted-foreground uppercase mb-1">Entry Ideal</div>
                      <div className="font-mono text-sm text-primary font-bold">
                        ${entry.ideal_entry_price.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-muted-foreground uppercase mb-1">Curent</div>
                      <div className="font-mono text-sm font-bold">
                        ${entry.current_price.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-muted-foreground uppercase mb-1">SL</div>
                      <div className="font-mono text-sm text-red-400">
                        ${entry.stop_loss.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-[10px] text-muted-foreground uppercase mb-1">TP</div>
                      <div className="font-mono text-sm text-green-400">
                        ${entry.take_profit.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* P/L Display */}
                  <div className="flex items-center justify-between p-3 bg-black/30 rounded border border-white/10">
                    <div className="flex items-center gap-2">
                      {entry.pnl_percent >= 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-400" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-400" />
                      )}
                      <span className="text-xs text-muted-foreground">P/L Nerealizat</span>
                    </div>
                    <div className={`font-mono font-bold ${
                      entry.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {entry.pnl_percent >= 0 ? '+' : ''}{entry.pnl_percent.toFixed(2)}%
                    </div>
                  </div>

                  {/* Confidence Score */}
                  <div className="mt-3 flex items-center gap-2">
                    <div className="flex-1 h-2 bg-black/50 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          entry.confidence_score >= 70 ? 'bg-green-400' : 
                          entry.confidence_score >= 50 ? 'bg-yellow-400' : 'bg-red-400'
                        }`}
                        style={{ width: `${entry.confidence_score}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">
                      {entry.confidence_score}%
                    </span>
                  </div>

                  {/* Notes */}
                  {entry.notes && (
                    <div className="mt-3 text-xs text-muted-foreground italic">
                      {entry.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-[#262626] p-3 text-[10px] text-muted-foreground/50 text-center">
          Watchlist-ul este actualizat automat cu prețurile curente
        </div>
      </div>
    </div>
  );
}
