import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { TrendingUp, TrendingDown, Minus, Newspaper, RefreshCw } from 'lucide-react';

export default function SentimentWidget({ symbol = 'BTC' }) {
    const [sentiment, setSentiment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchSentiment = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.get(`/sentiment/${symbol}/simple`);
            setSentiment(response.data);
        } catch (err) {
            setError('Failed to load sentiment');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSentiment();
        // Refresh every 30 minutes
        const interval = setInterval(fetchSentiment, 30 * 60 * 1000);
        return () => clearInterval(interval);
    }, [symbol]);

    const getSentimentColor = (score) => {
        if (score >= 60) return 'text-green-400';
        if (score >= 40) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getSentimentIcon = (score) => {
        if (score >= 60) return <TrendingUp className="text-green-400" size={24} />;
        if (score >= 40) return <Minus className="text-yellow-400" size={24} />;
        return <TrendingDown className="text-red-400" size={24} />;
    };

    if (loading) {
        return (
            <div className="glass rounded-xl p-6 animate-pulse">
                <div className="h-4 bg-white/10 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-white/10 rounded"></div>
            </div>
        );
    }

    if (error || !sentiment) {
        return (
            <div className="glass rounded-xl p-6 border border-red-500/20">
                <div className="text-red-400 text-sm">{error || 'No data available'}</div>
            </div>
        );
    }

    return (
        <div className="glass rounded-xl p-6 space-y-4">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Newspaper size={18} className="text-primary" />
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                        AI Sentiment
                    </h3>
                </div>
                <button
                    onClick={fetchSentiment}
                    className="p-2 hover:bg-white/10 rounded-lg transition-all"
                    title="Refresh"
                >
                    <RefreshCw size={16} className="text-muted-foreground" />
                </button>
            </div>

            <div className="flex items-center gap-4">
                {getSentimentIcon(sentiment.score)}
                <div className="flex-1">
                    <div className="flex justify-between items-baseline mb-2">
                        <span className={`text-2xl font-bold ${getSentimentColor(sentiment.score)}`}>
                            {sentiment.emoji}
                        </span>
                        <span className="text-sm text-muted-foreground">
                            {sentiment.confidence}% confident
                        </span>
                    </div>

                    <div className="relative w-full h-2 bg-black/30 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${sentiment.score >= 60 ? 'bg-green-400' :
                                    sentiment.score >= 40 ? 'bg-yellow-400' :
                                        'bg-red-400'
                                }`}
                            style={{ width: `${sentiment.score}%` }}
                        />
                    </div>

                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>Bearish</span>
                        <span className="font-medium">{sentiment.score}/100</span>
                        <span>Bullish</span>
                    </div>
                </div>
            </div>

            <div className="text-xs text-muted-foreground capitalize">
                Market: {sentiment.sentiment}
            </div>
        </div>
    );
}
