import React, { useState, useEffect } from 'react';
import { Plus, Trash2, TrendingUp, TrendingDown, Star, Loader2 } from 'lucide-react';
import api from '../lib/api';
import { useToast } from './ToastContext';
import { POPULAR_SYMBOLS } from '../constants/symbols';
import Combobox from './Combobox';

export default function WatchlistWidget() {
    const [watchlist, setWatchlist] = useState([]);
    const [prices, setPrices] = useState({});
    const [availableSymbols, setAvailableSymbols] = useState([]);
    const [symbol, setSymbol] = useState('');
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const toast = useToast();

    // Initial Data Fetch
    useEffect(() => {
        const init = async () => {
            await Promise.all([fetchWatchlist(), fetchSupportedSymbols()]);
            setLoading(false);
        };
        init();

        // Poll for alerts/watchlist updates periodically
        const listInterval = setInterval(fetchWatchlist, 15000); // Poll list updates
        return () => clearInterval(listInterval);
    }, []);

    // Price Polling
    useEffect(() => {
        if (watchlist.length === 0) return;

        const fetchPrices = async () => {
            try {
                // Get unique symbols to check
                const uniqueSymbols = [...new Set(watchlist.map(w => w.symbol))].join(',');
                if (!uniqueSymbols) return;

                const res = await api.get('/exchanges/tickers', { params: { symbols: uniqueSymbols } });
                if (res.data.tickers) {
                    setPrices(res.data.tickers);
                }
            } catch (err) {
                console.error("Failed to fetch prices", err);
            }
        };

        fetchPrices();
        const interval = setInterval(fetchPrices, 10000);
        return () => clearInterval(interval);
    }, [watchlist]);

    const fetchWatchlist = async () => {
        try {
            const res = await api.get('/watchlist');
            // Backend sorts by added_at DESC
            setWatchlist(res.data.watchlist || []);
        } catch (error) {
            console.error('Failed to fetch watchlist:', error);
        }
    };

    const fetchSupportedSymbols = async () => {
        try {
            const res = await api.get('/exchanges/all-symbols');
            if (res.data.symbols?.length > 0) {
                setAvailableSymbols(res.data.symbols);
            } else {
                setAvailableSymbols(POPULAR_SYMBOLS);
            }
        } catch (err) {
            setAvailableSymbols(POPULAR_SYMBOLS);
        }
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!symbol) return;

        setSubmitting(true);
        try {
            // No duplicate check here - allow backend to handle overwrite/bump for smart ordering
            await api.post('/watchlist', { symbol: symbol.toUpperCase() });
            setSymbol('');
            // Immediate fetch to show update
            await fetchWatchlist();
            toast.success('Watchlist updated');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to add symbol');
        } finally {
            setSubmitting(false);
        }
    };

    const handleRemove = async (sym) => {
        try {
            await api.delete('/watchlist/remove', { params: { symbol: sym } });
            setWatchlist(prev => prev.filter(i => i.symbol !== sym));
            toast.success('Symbol removed');
        } catch (error) {
            toast.error('Failed to remove symbol');
        }
    };

    if (loading) {
        return <div className="animate-pulse h-full bg-white/5 rounded-xl min-h-[200px]" />;
    }

    return (
        <div className="glass p-6 rounded-xl h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Star size={20} className="text-yellow-500 fill-yellow-500/20" />
                    Watchlist
                </h3>
                <span className="text-xs text-muted-foreground">{watchlist.length} pairs</span>
            </div>

            <form onSubmit={handleAdd} className="flex gap-2 mb-4">
                <Combobox
                    options={availableSymbols}
                    value={symbol}
                    onChange={setSymbol}
                    placeholder="Search Symbol..."
                    className="flex-1"
                />
                <button
                    type="submit"
                    disabled={submitting || !symbol}
                    className="bg-primary/10 hover:bg-primary/20 text-primary p-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center min-w-[40px]"
                >
                    {submitting ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                </button>
            </form>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {watchlist.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50 space-y-2">
                        <Star size={32} />
                        <span className="text-sm">Your watchlist is empty</span>
                    </div>
                ) : (
                    watchlist.map((item) => {
                        const priceData = prices[item.symbol];
                        const isUp = priceData?.change_24h >= 0;

                        return (
                            <div key={item.symbol} className="flex items-center justify-between p-3 bg-white/5 rounded-lg group hover:bg-white/10 transition-all border border-transparent hover:border-white/5">
                                <div className="flex flex-col">
                                    <span className="font-bold text-sm tracking-wide">{item.symbol}</span>
                                    <div className="text-xs flex items-center gap-2 h-4">
                                        {priceData ? (
                                            <>
                                                <span className="font-mono">${priceData.price}</span>
                                                <span className={`flex items-center ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                                                    {isUp ? <TrendingUp size={10} className="mr-1" /> : <TrendingDown size={10} className="mr-1" />}
                                                    {Math.abs(priceData.change_24h).toFixed(2)}%
                                                </span>
                                            </>
                                        ) : (
                                            <span className="animate-pulse bg-white/10 h-3 w-16 rounded" />
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleRemove(item.symbol)}
                                    className="opacity-0 group-hover:opacity-100 p-2 text-red-400/80 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                >
                                    <Trash2 size={15} />
                                </button>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
