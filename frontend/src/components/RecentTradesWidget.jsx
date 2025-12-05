import React, { useState, useEffect } from 'react';
import { FileText, Tag, Save, X, TrendingUp, TrendingDown } from 'lucide-react';
import api from '../lib/api';
import { useToast } from './ToastContext';
import EditableWidget from './constructor/EditableWidget';

export default function RecentTradesWidget() {
    const [trades, setTrades] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTrade, setSelectedTrade] = useState(null);
    const [note, setNote] = useState('');
    const [tags, setTags] = useState('');
    const [saving, setSaving] = useState(false);
    const toast = useToast();

    useEffect(() => {
        fetchTrades();
    }, []);

    const fetchTrades = async () => {
        try {
            const response = await api.get('/trades?limit=10');
            setTrades(response.data.trades || []);
        } catch (error) {
            console.error('Failed to fetch trades:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenNote = (trade) => {
        setSelectedTrade(trade);
        setNote(trade.notes || '');
        setTags(trade.tags || '');
    };

    const handleSaveNote = async (e) => {
        e.preventDefault();
        if (!selectedTrade) return;

        setSaving(true);
        try {
            await api.post(`/trades/${selectedTrade.id}/notes`, {
                notes: note,
                tags: tags
            });

            // Update local state
            setTrades(prev => prev.map(t =>
                t.id === selectedTrade.id
                    ? { ...t, notes: note, tags: tags }
                    : t
            ));

            toast.success('Trade note saved');
            setSelectedTrade(null);
        } catch (error) {
            toast.error('Failed to save note');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return <div className="animate-pulse h-48 bg-white/5 rounded-xl"></div>;
    }

    return (
        <EditableWidget
            configPath="widgets.recentTrades"
            widgetName="Recent Trades"
            editableFields={{
                title: 'Recent Trades',
                displayLimit: 10,
                emptyMessage: 'No recent trades'
            }}
            className="glass p-6 rounded-xl h-full flex flex-col"
        >
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <TrendingUp size={20} className="text-primary" />
                    Recent Trades
                </h3>
                <span className="text-xs text-muted-foreground">{trades.length} trades</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {trades.length === 0 ? (
                    <div className="text-center text-muted-foreground text-sm py-8">
                        No recent trades
                    </div>
                ) : (
                    trades.map((trade) => (
                        <div key={trade.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg group hover:bg-white/10 transition-all">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-bold text-sm">{trade.symbol}</span>
                                    <span className={`text-xs px-1.5 py-0.5 rounded ${trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                        {trade.side.toUpperCase()}
                                    </span>
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                    {new Date(trade.timestamp).toLocaleString()}
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {trade.pnl > 0 ? '+' : ''}{trade.pnl?.toFixed(2)}
                                </div>
                                <button
                                    onClick={() => handleOpenNote(trade)}
                                    className={`p-2 rounded-lg transition-colors ${trade.notes ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-primary hover:bg-white/5'}`}
                                    title={trade.notes ? "Edit Note" : "Add Note"}
                                >
                                    <FileText size={16} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Note Modal */}
            {selectedTrade && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-card border border-border p-6 rounded-xl w-full max-w-md m-4">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Trade Journal</h3>
                            <button onClick={() => setSelectedTrade(null)} className="text-muted-foreground hover:text-foreground">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="mb-4 p-3 bg-white/5 rounded-lg text-sm">
                            <div className="flex justify-between mb-1">
                                <span className="text-muted-foreground">Symbol:</span>
                                <span className="font-medium">{selectedTrade.symbol}</span>
                            </div>
                            <div className="flex justify-between mb-1">
                                <span className="text-muted-foreground">Side:</span>
                                <span className="font-medium uppercase">{selectedTrade.side}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">PnL:</span>
                                <span className={`font-medium ${selectedTrade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {selectedTrade.pnl?.toFixed(2)}
                                </span>
                            </div>
                        </div>

                        <form onSubmit={handleSaveNote}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-muted-foreground mb-1">Notes</label>
                                <textarea
                                    value={note}
                                    onChange={(e) => setNote(e.target.value)}
                                    placeholder="What was your rationale? What went right/wrong?"
                                    className="w-full h-32 bg-black/20 border border-white/10 rounded-lg px-4 py-2 focus:border-primary/50 outline-none resize-none"
                                    autoFocus
                                />
                            </div>

                            <div className="mb-6">
                                <label className="block text-sm font-medium text-muted-foreground mb-1">Tags</label>
                                <div className="relative">
                                    <Tag size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                                    <input
                                        type="text"
                                        value={tags}
                                        onChange={(e) => setTags(e.target.value)}
                                        placeholder="impulse, mistake, fomo (comma separated)"
                                        className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 pr-4 py-2 focus:border-primary/50 outline-none"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={() => setSelectedTrade(null)}
                                    className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                                >
                                    <Save size={16} />
                                    {saving ? 'Saving...' : 'Save Note'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </EditableWidget>
    );
}
