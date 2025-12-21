import React, { useState, useEffect } from 'react';
import { Plus, Trash2, TrendingUp, TrendingDown, Star } from 'lucide-react';
import api from '../lib/api';
import { useToast } from './ToastContext';
import { POPULAR_SYMBOLS } from '../constants/symbols';

import Combobox from './Combobox';

export default function WatchlistWidget() {
    const [watchlist, setWatchlist] = useState([]);
    const [newSymbol, setNewSymbol] = useState('');
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);
    const toast = useToast();

    const [prices, setPrices] = useState({});
    const [availableSymbols, setAvailableSymbols] = useState([]); // Dynamic list

    useEffect(() => {
        fetchWatchlist();
        fetchSupportedSymbols();
    }, []);

    const fetchSupportedSymbols = async () => {
        try {
            const res = await api.get('/exchanges/all-symbols');
            if (res.data.symbols && res.data.symbols.length > 0) {
                setAvailableSymbols(res.data.symbols);
            } else {
                // Fallback to popular if empty (e.g., first run before sync)
                setAvailableSymbols(POPULAR_SYMBOLS);
            }
        } catch (err) {
            console.error("Failed to fetch symbols", err);
            setAvailableSymbols(POPULAR_SYMBOLS);
        }
    };


    useEffect(() => {
        if (watchlist.length === 0) return;

        const fetchPrices = async () => {
            try {
                const symbols = watchlist.map(w => w.symbol).join(',');
                const res = await api.get('/exchanges/tickers', { params: { symbols } });
                if (res.data.tickers) {
                    setPrices(res.data.tickers);
                }
            } catch (err) {
                console.error("Failed to fetch prices", err);
            }
        };

        fetchPrices();
        const interval = setInterval(fetchPrices, 10000); // 10s polling
        return () => clearInterval(interval);
    }, [watchlist]);

    const fetchWatchlist = async () => {
        try {
            const response = await api.get('/watchlist');
            setWatchlist(response.data.watchlist || []);
        } catch (error) {
            console.error('Failed to fetch watchlist:', error);
            toast.error('Failed to load watchlist');
        } finally {
            setLoading(false);
        }
    };



    const handleAddSymbol = async (e) => {
        e.preventDefault();
        if (!newSymbol) return;

        const symbolToAdd = newSymbol.trim().toUpperCase();

        // Check if already in watchlist
        if (watchlist.some(item => item.symbol === symbolToAdd)) {
            toast.error(`Symbol ${symbolToAdd} is already in your watchlist`);
            setNewSymbol('');
            return;
        }

        setAdding(true);
        try {
            await api.post('/watchlist', { symbol: symbolToAdd });
            setNewSymbol('');
            fetchWatchlist();
            toast.success('Symbol added to watchlist');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to add symbol');
        } finally {
            setAdding(false);
        }
    };

    const handleRemoveSymbol = async (symbol) => {
        try {
            await api.delete('/watchlist/remove', { params: { symbol } });
            setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
            toast.success('Symbol removed from watchlist');
        } catch (error) {
            toast.error('Failed to remove symbol');
        }
    };

    if (loading) {
        return <div className="animate-pulse h-48 bg-white/5 rounded-xl"></div>;
    }

    return (
        <div className="glass p-6 rounded-xl h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Star size={20} className="text-yellow-500" />
                    Watchlist
                </h3>
                <span className="text-xs text-muted-foreground">{watchlist.length} pairs</span>
            </div>

            <form onSubmit={handleAddSymbol} className="flex gap-2 mb-4">
                <Combobox
                    options={availableSymbols}
                    value={newSymbol}
                    onChange={setNewSymbol}
                    placeholder="Symbol (e.g. BTC/USDT)"
                    className="flex-1"
                />
                <button
                    type="submit"
                    disabled={adding || !newSymbol}
                    className="bg-primary/10 hover:bg-primary/20 text-primary p-2 rounded-lg transition-colors disabled:opacity-50"
                >
                    <Plus size={18} />
                </button>
            </form>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {watchlist.length === 0 ? (
                    <div className="text-center text-muted-foreground text-sm py-8">
                        No symbols watched
                    </div>
                ) : (
                    watchlist.map((item) => (
                        <div key={item.symbol} className="flex items-center justify-between p-3 bg-white/5 rounded-lg group hover:bg-white/10 transition-all">
                            <div>
                                <div className="font-bold text-sm">{item.symbol}</div>
                                <div className="text-xs text-muted-foreground">
                                    {prices[item.symbol] ? (
                                        <span className={prices[item.symbol].change_24h >= 0 ? "text-green-500" : "text-red-500"}>
                                            ${prices[item.symbol].price} ({prices[item.symbol].change_24h?.toFixed(2)}%)
                                        </span>
                                    ) : (
                                        <span className="text-muted-foreground text-[10px]">-</span>
                                    )}
                                </div>
                            </div>
                            <button
                                onClick={() => handleRemoveSymbol(item.symbol)}
                                className="opacity-0 group-hover:opacity-100 p-1.5 text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
