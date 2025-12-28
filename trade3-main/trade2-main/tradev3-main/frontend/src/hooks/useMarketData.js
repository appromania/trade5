import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const useMarketData = () => {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [providers, setProviders] = useState([]);
  const [marketContext, setMarketContext] = useState(null);

  // Fetch available providers
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await axios.get(`${API}/providers`);
        setProviders(response.data.providers);
      } catch (err) {
        console.error('Error fetching providers:', err);
      }
    };
    fetchProviders();
  }, []);

  // Fetch market context
  const fetchMarketContext = async () => {
    try {
      const response = await axios.get(`${API}/market-context`);
      setMarketContext(response.data);
      return response.data;
    } catch (err) {
      console.error('Error fetching market context:', err);
      return null;
    }
  };

  // Analyze symbol
  const analyzeSymbol = async (symbol, provider = 'yahoo', timeframe = '1d', period = '6mo', lookback = 60) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await axios.post(`${API}/analyze`, {
        symbol: symbol.toUpperCase(),
        provider,
        timeframe,
        period,
        lookback
      });

      setAnalysis(response.data);
      toast.success(`Analiză completă pentru ${symbol.toUpperCase()}`);
      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Eroare la analiza simbolului';
      setError(errorMsg);
      toast.error(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Search symbols
  const searchSymbols = async (query) => {
    try {
      const response = await axios.post(`${API}/symbols/search`, { query });
      return response.data.results;
    } catch (err) {
      console.error('Error searching symbols:', err);
      return [];
    }
  };

  return {
    loading,
    analysis,
    error,
    providers,
    marketContext,
    analyzeSymbol,
    searchSymbols,
    fetchMarketContext
  };
};