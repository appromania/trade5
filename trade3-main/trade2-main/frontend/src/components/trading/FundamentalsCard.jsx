import { Building2, DollarSign, TrendingUp, Users, HelpCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { getFundamentalsHelp } from '@/lib/fundamentalsHelp';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function FundamentalTooltip({ helpKey }) {
  const [showModal, setShowModal] = useState(false);
  const help = getFundamentalsHelp(helpKey);

  if (!help) return null;

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="ml-1 text-muted-foreground hover:text-primary transition-colors"
      >
        <HelpCircle className="h-3 w-3" />
      </button>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setShowModal(false)}>
          <div className="terminal-card p-6 max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-heading text-lg font-bold">{help.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{help.description}</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                ×
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">Interpretare</h4>
                <div className="space-y-1.5">
                  {Object.entries(help.interpretation).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2 text-xs">
                      <span className="text-primary">•</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-3 bg-primary/10 border border-primary/30 rounded-sm">
                <h4 className="text-xs font-bold uppercase tracking-wider text-primary mb-1">Acțiune</h4>
                <p className="text-xs">{help.action}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function FundamentalsCard({ symbol }) {
  const [fundamentals, setFundamentals] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!symbol) return;

    const fetchFundamentals = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/fundamentals/${symbol}`);
        setFundamentals(response.data);
      } catch (error) {
        console.error('Fundamentals error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFundamentals();
  }, [symbol]);

  if (loading) {
    return (
      <div className="terminal-card p-6">
        <h3 className="indicator-label mb-4">📊 Fundamente Companie</h3>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-white/10 rounded w-3/4"></div>
          <div className="h-4 bg-white/10 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!fundamentals) return null;

  const formatLargeNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toFixed(2)}`;
  };

  const safeToFixed = (num, decimals = 2) => {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    return num.toFixed(decimals);
  };

  const getPERating = (pe) => {
    if (pe > 50) return { text: 'RIDICAT', color: 'text-bear' };
    if (pe > 25) return { text: 'MODERAT', color: 'text-yellow-500' };
    return { text: 'NORMAL', color: 'text-bull' };
  };

  const peRating = getPERating(fundamentals.pe_ratio);

  return (
    <div className="terminal-card p-6" data-testid="fundamentals-card">
      <h3 className="indicator-label mb-4 flex items-center gap-2">
        <Building2 className="h-4 w-4" />
        Fundamente Companie
      </h3>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="indicator-card">
            <div className="indicator-label flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Market Cap
              <FundamentalTooltip helpKey="MARKET_CAP" />
            </div>
            <div className="indicator-value text-base mono-data">
              {formatLargeNumber(fundamentals.market_cap)}
            </div>
            <div className="indicator-status text-xs">{fundamentals.sector}</div>
          </div>

          <div className="indicator-card">
            <div className="indicator-label flex items-center">
              P/E Ratio
              <FundamentalTooltip helpKey="PE_RATIO" />
            </div>
            <div className={`indicator-value text-base ${peRating.color}`}>
              {fundamentals.pe_ratio > 0 ? safeToFixed(fundamentals.pe_ratio) : 'N/A'}
            </div>
            <div className={`indicator-status text-xs ${peRating.color}`}>{peRating.text}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="indicator-card">
            <div className="indicator-label flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              Revenue (TTM)
              <FundamentalTooltip helpKey="REVENUE" />
            </div>
            <div className="indicator-value text-sm mono-data">
              {formatLargeNumber(fundamentals.revenue_ttm)}
            </div>
          </div>

          <div className="indicator-card">
            <div className="indicator-label flex items-center">
              Free Cash Flow
              <FundamentalTooltip helpKey="FREE_CASH_FLOW" />
            </div>
            <div className="indicator-value text-sm mono-data">
              {formatLargeNumber(fundamentals.free_cash_flow)}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="indicator-card">
            <div className="indicator-label flex items-center">
              Total Debt
              <FundamentalTooltip helpKey="DEBT" />
            </div>
            <div className="indicator-value text-sm mono-data">
              {formatLargeNumber(fundamentals.total_debt)}
            </div>
            <div className="indicator-status text-xs">
              D/E: {safeToFixed(fundamentals.debt_to_equity)}
            </div>
          </div>

          <div className="indicator-card">
            <div className="indicator-label flex items-center">
              Profit Margin
              <FundamentalTooltip helpKey="PROFIT_MARGIN" />
            </div>
            <div className="indicator-value text-sm">
              {fundamentals.profit_margins ? (fundamentals.profit_margins * 100).toFixed(2) + '%' : 'N/A'}
            </div>
          </div>
        </div>

        {fundamentals.pe_ratio && fundamentals.pe_ratio > 50 && (
          <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-sm">
            <p className="text-xs text-yellow-500">
              ⚠️ P/E Ratio ridicat ({safeToFixed(fundamentals.pe_ratio)}) - evaluare fundamentală ridicată. 
              Combinat cu risc tehnic, sugerează prudență pe termen scurt.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
