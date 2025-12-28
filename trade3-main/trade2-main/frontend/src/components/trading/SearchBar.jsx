import { Search, Plus, AlertCircle, Loader2 } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useClickOutside } from '@/hooks/useClickOutside';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function SearchBar({ onSearch, onSymbolSelect, searchFunction }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isFetchingNew, setIsFetchingNew] = useState(false);
  const [fetchStatus, setFetchStatus] = useState(null); // { type: 'success' | 'error', message: string }
  const searchRef = useRef(null);

  // Close dropdown when clicking outside
  useClickOutside(searchRef, () => {
    setShowResults(false);
    setFetchStatus(null);
  });

  useEffect(() => {
    const searchSymbols = async () => {
      if (query.length < 1) {
        setResults([]);
        setShowResults(false);
        return;
      }

      setIsSearching(true);
      try {
        const searchResults = await searchFunction(query);
        setResults(searchResults || []);
        setShowResults(true);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    const debounce = setTimeout(searchSymbols, 300);
    return () => clearTimeout(debounce);
  }, [query, searchFunction]);

  const handleSelect = (symbol) => {
    setQuery(symbol);
    setShowResults(false);
    setFetchStatus(null);
    onSymbolSelect(symbol);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setShowResults(false);
      setFetchStatus(null);
      onSearch(query.trim().toUpperCase());
    }
  };

  // Fetch new symbol on-demand
  const handleFetchNewSymbol = async () => {
    if (!query.trim()) return;
    
    const symbol = query.trim().toUpperCase();
    setIsFetchingNew(true);
    setFetchStatus(null);
    
    try {
      const response = await fetch(`${API_URL}/api/symbols/fetch-on-demand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setFetchStatus({
          type: 'success',
          message: `✓ ${data.name} (${symbol}) găsit! Se încarcă analiza...`
        });
        
        // Auto-analyze after successful fetch
        setTimeout(() => {
          setShowResults(false);
          setFetchStatus(null);
          onSymbolSelect(symbol);
        }, 1500);
      } else {
        setFetchStatus({
          type: 'error',
          message: data.error || `❌ Simbolul ${symbol} nu există pe nicio bursă.`
        });
      }
    } catch (error) {
      console.error('Fetch on-demand error:', error);
      setFetchStatus({
        type: 'error',
        message: `Eroare la preluarea datelor. Încercați din nou.`
      });
    } finally {
      setIsFetchingNew(false);
    }
  };

  const showNoResults = query.length >= 2 && !isSearching && results.length === 0;

  return (
    <div className="search-container relative" data-testid="search-container" ref={searchRef}>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Caută simbol sau nume companie (ex: AAPL, Tesla, Microsoft)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10 bg-black/50 border-white/10 focus:border-primary rounded-sm font-mono h-12 text-lg"
            data-testid="symbol-search-input"
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        <Button
          type="submit"
          className="bg-primary hover:bg-primary/90 text-black font-mono uppercase h-12 px-6 rounded-sm"
          data-testid="analyze-button"
        >
          Analizează
        </Button>
      </form>

      {/* Results Dropdown */}
      {showResults && (
        <div className="search-results" data-testid="search-results">
          {results.length > 0 ? (
            <>
              {results.map((result, index) => (
                <div
                  key={index}
                  className="search-result-item"
                  onClick={() => handleSelect(result.symbol)}
                  data-testid={`search-result-${result.symbol}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-mono font-bold text-sm">{result.symbol}</div>
                      <div className="text-xs text-muted-foreground">{result.name}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      {result.source === 'dynamic' && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-primary/20 text-primary rounded">NOU</span>
                      )}
                      <span className="text-xs text-muted-foreground">{result.match_score}%</span>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Add new symbol option */}
              <div className="border-t border-white/10 p-3">
                <button
                  type="button"
                  onClick={handleFetchNewSymbol}
                  disabled={isFetchingNew}
                  className="w-full flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors py-2"
                >
                  {isFetchingNew ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>🚀 Preluare date noi pentru {query.toUpperCase()}...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      <span>Simbol negăsit? Caută "{query.toUpperCase()}" global</span>
                    </>
                  )}
                </button>
              </div>
            </>
          ) : showNoResults ? (
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <AlertCircle className="h-4 w-4 text-yellow-500" />
                <span>Niciun simbol găsit pentru "{query}"</span>
              </div>
              
              <button
                type="button"
                onClick={handleFetchNewSymbol}
                disabled={isFetchingNew}
                className="w-full console-btn flex items-center justify-center gap-2"
              >
                {isFetchingNew ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>🚀 Preluare date globale pentru {query.toUpperCase()}...</span>
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    <span>+ Adaugă Simbol Nou: {query.toUpperCase()}</span>
                  </>
                )}
              </button>
              
              <p className="text-[10px] text-muted-foreground/50 text-center">
                Vom căuta automat pe Yahoo Finance și vom prelua datele istorice
              </p>
            </div>
          ) : null}
          
          {/* Fetch Status Message */}
          {fetchStatus && (
            <div className={`p-3 ${
              fetchStatus.type === 'success' 
                ? 'bg-green-500/10 border-t border-green-500/30 text-green-400' 
                : 'bg-red-500/10 border-t border-red-500/30 text-red-400'
            }`}>
              <p className="text-sm">{fetchStatus.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
