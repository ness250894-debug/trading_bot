import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import {
    TrendingUp, TrendingDown, Minus, RefreshCw,
    Activity, Zap, MessageSquare, ChevronDown, ChevronUp
} from 'lucide-react';


export default function CombinedSentimentWidget({ symbol = 'BTC' }) {
    const [simpleData, setSimpleData] = useState(null);
    const [advancedData, setAdvancedData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [advancedLoading, setAdvancedLoading] = useState(false);
    const [error, setError] = useState(null);
    const [expanded, setExpanded] = useState(false);

    // Fetch simple sentiment (always available)
    const fetchSimpleSentiment = async () => {
        try {
            const response = await api.get(`/sentiment/${symbol}/simple`);
            setSimpleData(response.data);
        } catch (err) {
            console.error('Failed to load simple sentiment:', err);
            throw err;
        }
    };

    // Fetch advanced sentiment (on demand or when expanded)
    const fetchAdvancedSentiment = async () => {
        setAdvancedLoading(true);
        try {
            const response = await api.get(`/sentiment/${symbol}/advanced`);
            setAdvancedData(response.data);
        } catch (err) {
            // Advanced might be locked for free users - that's okay
            console.error('Failed to load advanced sentiment:', err);
        } finally {
            setAdvancedLoading(false);
        }
    };

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            await fetchSimpleSentiment();
            if (expanded) {
                await fetchAdvancedSentiment();
            }
        } catch (err) {
            setError('Failed to load sentiment');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Refresh every 60 minutes to stay within 50 daily calls limit
        // (24 calls/day automatically)
        const interval = setInterval(fetchSimpleSentiment, 60 * 60 * 1000);
        return () => clearInterval(interval);
    }, [symbol]);

    // Fetch advanced data when expanded
    useEffect(() => {
        if (expanded && !advancedData && !advancedLoading) {
            fetchAdvancedSentiment();
        }
    }, [expanded]);

    const getSentimentColor = (score) => {
        if (score >= 60) return 'text-green-400';
        if (score >= 40) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getSentimentBgColor = (score) => {
        if (score >= 60) return 'bg-green-400';
        if (score >= 40) return 'bg-yellow-400';
        return 'bg-red-400';
    };

    const getSentimentIcon = (score) => {
        if (score >= 60) return <TrendingUp className="text-green-400" size={20} />;
        if (score >= 40) return <Minus className="text-yellow-400" size={20} />;
        return <TrendingDown className="text-red-400" size={20} />;
    };

    const getSignalColor = (strength) => {
        switch (strength?.toLowerCase()) {
            case 'strong': return 'text-green-400';
            case 'moderate': return 'text-yellow-400';
            case 'weak': return 'text-gray-400';
            default: return 'text-gray-400';
        }
    };

    return (
        <div className="glass rounded-xl p-6 h-full flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                    <Activity size={18} className="text-primary" />
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider">
                        AI Sentiment & Analysis
                    </h3>
                </div>
                {/* Auto-refresh indicator (no button) */}
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground" title="Updates automatically every hour">
                    <div className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-primary animate-pulse' : 'bg-green-500/50'}`} />
                    <span>{loading ? 'Updating...' : 'Live'}</span>
                </div>
            </div>

            {loading && !simpleData ? (
                <div className="flex-1 flex flex-col items-center justify-center animate-pulse space-y-4">
                    <div className="h-4 bg-white/10 rounded w-1/2"></div>
                    <div className="h-8 bg-white/10 rounded w-full"></div>
                    <div className="h-20 bg-white/10 rounded w-full"></div>
                </div>
            ) : (error || !simpleData) ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center border border-red-500/20 rounded-lg p-4">
                    <Activity size={32} className="text-red-500/50 mb-3" />
                    <p className="text-red-400 text-sm">{error || 'No data available'}</p>
                    <p className="text-xs text-muted-foreground mt-2">Next update in ~60m</p>
                </div>
            ) : (
                <>
                    {/* Simple Sentiment Section */}
                    <div className="flex items-center gap-4 mb-4">
                        {getSentimentIcon(simpleData.score)}
                        <div className="flex-1">
                            <div className="flex justify-between items-baseline mb-2">
                                <span className={`text-2xl font-bold ${getSentimentColor(simpleData.score)}`}>
                                    {simpleData.emoji}
                                </span>
                                <span className="text-sm text-muted-foreground">
                                    {simpleData.confidence}% confident
                                </span>
                            </div>

                            <div className="relative w-full h-2 bg-black/30 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-500 ${getSentimentBgColor(simpleData.score)}`}
                                    style={{ width: `${simpleData.score}%` }}
                                />
                            </div>

                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                <span>Bearish</span>
                                <span className="font-medium">{simpleData.score}/100</span>
                                <span>Bullish</span>
                            </div>
                        </div>
                    </div>

                    <div className="text-xs text-muted-foreground capitalize mb-4">
                        Market: {simpleData.sentiment}
                    </div>

                    {/* Expand/Collapse for Advanced Analysis */}
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="flex items-center justify-center gap-2 w-full py-2 border-t border-white/10 text-xs text-muted-foreground hover:text-primary transition-colors"
                    >
                        {expanded ? (
                            <>
                                <ChevronUp size={14} />
                                Hide Advanced Analysis
                            </>
                        ) : (
                            <>
                                <ChevronDown size={14} />
                                Show Advanced Analysis
                            </>
                        )}
                    </button>

                    {/* Advanced Analysis Section (Expandable) */}
                    {expanded && (
                        <div className={`mt-4 space-y-4 flex-1 overflow-y-auto custom-scrollbar transition-all duration-300 ${advancedLoading ? 'opacity-50' : ''}`}>
                            {advancedLoading ? (
                                <div className="flex items-center justify-center py-8">
                                    <RefreshCw size={24} className="animate-spin text-primary" />
                                </div>
                            ) : advancedData ? (
                                <>
                                    {/* AI Summary */}
                                    <div className="bg-white/5 rounded-xl p-4 border border-white/5">
                                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
                                            <MessageSquare size={14} /> AI Summary
                                        </h4>
                                        <p className="text-sm leading-relaxed text-gray-300">
                                            {advancedData.summary}
                                        </p>
                                    </div>

                                    {/* Metrics Grid */}
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                                            <div className="text-xs text-muted-foreground mb-1">Signal Strength</div>
                                            <div className={`text-lg font-bold capitalize ${getSignalColor(advancedData.signal_strength)}`}>
                                                {advancedData.signal_strength}
                                            </div>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                                            <div className="text-xs text-muted-foreground mb-1">Confidence</div>
                                            <div className="text-lg font-bold text-white">
                                                {advancedData.confidence}%
                                            </div>
                                        </div>
                                    </div>

                                    {/* Key Topics */}
                                    <div>
                                        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                                            <Zap size={14} /> Key Drivers
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {advancedData.topics && advancedData.topics.length > 0 ? (
                                                advancedData.topics.map((topic, i) => (
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

                                    {/* Footer */}
                                    <div className="pt-4 border-t border-white/5 text-[10px] text-muted-foreground text-center">
                                        Powered by Gemini AI • Updated {new Date(advancedData.analyzed_at).toLocaleTimeString()}
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-8 text-muted-foreground text-sm">
                                    <Activity size={32} className="mx-auto mb-2 opacity-50" />
                                    <p>Advanced analysis unavailable</p>
                                    <p className="text-xs mt-1">Upgrade to access detailed AI insights</p>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
