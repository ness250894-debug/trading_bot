import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Trophy, TrendingUp, Copy, Star, Users, ArrowUp } from 'lucide-react';
import Disclaimer from '../components/Disclaimer';
import PlanGate from '../components/PlanGate';

export default function Marketplace() {
    const [strategies, setStrategies] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState('rating');
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchMarketplace();
        fetchLeaderboard();
    }, [sortBy]);

    const fetchMarketplace = async () => {
        try {
            const response = await api.get(`/marketplace/strategies?sort_by=${sortBy}&limit=20`);
            setStrategies(response.data.strategies || []);
        } catch (err) {
            // Silent fail - show empty state
        } finally {
            setLoading(false);
        }
    };

    const fetchLeaderboard = async () => {
        try {
            const response = await api.get('/leaderboard?period=all&limit=10');
            setLeaderboard(response.data.leaderboard || []);
        } catch (err) {
            // Silent fail - show empty state
        }
    };

    const handleClone = async (strategyId, strategyName) => {
        try {
            await api.post(`/marketplace/clone/${strategyId}`);
            setMessage({ type: 'success', text: `Successfully cloned "${strategyName}"!` });
            fetchMarketplace(); // Refresh to update clone counts
            setTimeout(() => setMessage(null), 3000);
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to clone strategy' });
        }
    };

    const getRankColor = (rank) => {
        if (rank === 1) return 'text-yellow-400';
        if (rank === 2) return 'text-gray-300';
        if (rank === 3) return 'text-orange-400';
        return 'text-muted-foreground';
    };

    const getRankEmoji = (rank) => {
        if (rank === 1) return '🥇';
        if (rank === 2) return '🥈';
        if (rank === 3) return '🥉';
        return `#${rank}`;
    };

    return (
        <PlanGate feature="Social Trading" explanation="Copy top-performing strategies from other traders and automate your profits.">
            <div className="space-y-8">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Strategy Marketplace
                    </h2>
                    <p className="text-muted-foreground mt-1">Browse and clone successful trading strategies</p>
                </div>

                <Disclaimer compact />

                {message && (
                    <div className={`p-4 rounded-xl ${message.type === 'success'
                        ? 'bg-green-500/10 border border-green-500/20 text-green-400'
                        : 'bg-red-500/10 border border-red-500/20 text-red-400'
                        }`}>
                        {message.text}
                    </div>
                )}

                {/* Leaderboard */}
                <div className="glass rounded-2xl p-8">
                    <div className="flex items-center gap-3 mb-6">
                        <Trophy className="text-yellow-400" size={24} />
                        <h3 className="text-xl font-bold">Top Performers</h3>
                    </div>

                    <div className="space-y-3">
                        {leaderboard.map((item) => (
                            <div key={item.strategy_id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-all">
                                <div className="flex items-center gap-4 flex-1">
                                    <span className={`text-2xl font-bold w-12 text-center ${getRankColor(item.rank)}`}>
                                        {getRankEmoji(item.rank)}
                                    </span>
                                    <div className="flex-1">
                                        <div className="font-semibold">{item.name}</div>
                                        <div className="text-sm text-muted-foreground">by {item.author}</div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-6">
                                    <div className="text-right">
                                        <div className={`font-bold ${item.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            ${item.total_pnl.toLocaleString()}
                                        </div>
                                        <div className="text-sm text-muted-foreground">{item.win_rate}% Win Rate</div>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Users size={16} />
                                        {item.clones}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Filter Bar */}
                <div className="flex gap-2">
                    {[
                        { value: 'rating', label: 'Top Rated', icon: Star },
                        { value: 'pnl', label: 'Most Profitable', icon: TrendingUp },
                        { value: 'clones', label: 'Most Cloned', icon: Users },
                        { value: 'recent', label: 'Recently Added', icon: ArrowUp }
                    ].map((item) => (
                        <button
                            key={item.value}
                            onClick={() => setSortBy(item.value)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${sortBy === item.value
                                ? 'bg-primary text-white'
                                : 'bg-white/5 text-muted-foreground hover:bg-white/10'
                                }`}
                        >
                            <item.icon size={16} />
                            {item.label}
                        </button>
                    ))}
                </div>

                {/* Strategy Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                        Array(6).fill(0).map((_, i) => (
                            <div key={i} className="glass rounded-xl p-6 animate-pulse">
                                <div className="h-4 bg-white/10 rounded w-3/4 mb-4"></div>
                                <div className="h-3 bg-white/10 rounded w-full mb-2"></div>
                                <div className="h-3 bg-white/10 rounded w-2/3"></div>
                            </div>
                        ))
                    ) : strategies.length === 0 ? (
                        <div className="col-span-full text-center py-12 text-muted-foreground">
                            No strategies found
                        </div>
                    ) : (
                        strategies.map((strategy) => (
                            <div key={strategy.id} className="glass rounded-xl p-6 space-y-4 hover:border-primary/30 transition-all">
                                <div>
                                    <h4 className="font-bold text-lg mb-1">{strategy.name}</h4>
                                    <p className="text-sm text-muted-foreground">by {strategy.author}</p>
                                </div>

                                <p className="text-sm line-clamp-2">{strategy.description || 'No description provided'}</p>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-muted-foreground">PnL</div>
                                        <div className={`font-bold ${strategy.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            ${strategy.total_pnl.toLocaleString()}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground">Win Rate</div>
                                        <div className="font-bold">{strategy.win_rate}%</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground">Trades</div>
                                        <div className="font-bold">{strategy.total_trades}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground">Rating</div>
                                        <div className="flex items-center gap-1">
                                            <Star size={14} className="text-yellow-400 fill-yellow-400" />
                                            <span className="font-bold">{strategy.rating.toFixed(1)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                                        <Users size={14} />
                                        {strategy.clones_count} clones
                                    </div>
                                    <button
                                        onClick={() => handleClone(strategy.id, strategy.name)}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-all"
                                    >
                                        <Copy size={16} />
                                        Clone
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </PlanGate>
    );
}
