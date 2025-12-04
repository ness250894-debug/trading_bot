import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Activity, TrendingUp, TrendingDown, Minus, RefreshCw, Zap, MessageSquare } from 'lucide-react';

export default function AdvancedSentimentWidget({ symbol = 'BTC' }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get(`/sentiment/${symbol}/advanced`);
            setData(response.data);
        } catch (err) {
            setError('Failed to load advanced sentiment');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh every hour to respect rate limits
        const interval = setInterval(fetchData, 60 * 60 * 1000);
        return () => clearInterval(interval);
    }, [symbol]);

    const getSignalColor = (strength) => {
        switch (strength?.toLowerCase()) {
            case 'strong': return 'text-green-400';
            case 'moderate': return 'text-yellow-400';
            case 'weak': return 'text-gray-400';
            default: return 'text-gray-400';
        }
    };

    if (loading) {
        return (
            <div className="glass rounded-xl p-6 h-full flex flex-col animate-pulse">
                <div className="h-6 bg-white/10 rounded w-1/3 mb-6"></div>
                <div className="space-y-4 flex-1">
                    <div className="h-20 bg-white/10 rounded"></div>
                    <div className="h-20 bg-white/10 rounded"></div>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="glass rounded-xl p-6 h-full flex flex-col items-center justify-center text-center border border-red-500/20">
                <Activity size={48} className="text-red-500/50 mb-4" />
                <p className="text-red-400">{error || 'No data available'}</p>
                <button
                    onClick={fetchData}
                    className="mt-4 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm transition-colors"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="glass rounded-xl p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                    <Activity size={20} className="text-primary" />
                    <h3 className="font-bold text-lg">Advanced Analysis</h3>
                </div>
                <button
                    onClick={fetchData}
                    className="p-2 hover:bg-white/10 rounded-lg transition-all"
                    title="Refresh Analysis"
                >
                    <RefreshCw size={16} className="text-muted-foreground" />
                </button>
            </div>

            <div className="space-y-6 flex-1 overflow-y-auto custom-scrollbar pr-2">
                {/* Summary Section */}
                <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                        <MessageSquare size={14} /> AI Summary
                    </h4>
                    <p className="text-sm leading-relaxed text-gray-300">
                        {data.summary}
                    </p>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                        <div className="text-xs text-muted-foreground mb-1">Signal Strength</div>
                        <div className={`text-lg font-bold capitalize ${getSignalColor(data.signal_strength)}`}>
                            {data.signal_strength}
                        </div>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                        <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                        <div className="text-lg font-bold text-white">
                            {data.confidence}%
                        </div>
                    </div>
                </div>

                {/* Key Topics */}
                <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Zap size={14} /> Key Drivers
                    </h4>
                    <div className="flex flex-wrap gap-2">
                        {data.topics && data.topics.length > 0 ? (
                            data.topics.map((topic, i) => (
                                <span
                                    key={i}
                                    className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-xs font-medium"
                                >
                                    {topic}
                                </span>
                            ))
                        ) : (
                            <span className="text-xs text-muted-foreground italic">No specific topics identified</span>
                        )}
                    </div>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/5 text-[10px] text-muted-foreground text-center">
                Powered by Gemini AI • Updated {new Date(data.analyzed_at).toLocaleTimeString()}
            </div>
        </div>
    );
}
