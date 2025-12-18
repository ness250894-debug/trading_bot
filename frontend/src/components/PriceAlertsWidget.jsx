import React, { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, ArrowUp, ArrowDown } from 'lucide-react';
import api from '../lib/api';
import { useToast } from './ToastContext';
import { POPULAR_SYMBOLS } from '../constants/symbols';

import Combobox from './Combobox';

export default function PriceAlertsWidget() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);

    // Form state
    const [symbol, setSymbol] = useState('');
    const [condition, setCondition] = useState('above');
    const [price, setPrice] = useState('');

    const toast = useToast();

    useEffect(() => {
        fetchAlerts();
    }, []);

    const fetchAlerts = async () => {
        try {
            const response = await api.get('/alerts');
            setAlerts(response.data.alerts || []);
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddAlert = async (e) => {
        e.preventDefault();
        if (!symbol || !price) return;

        setAdding(true);
        try {
            await api.post('/alerts', {
                symbol: symbol.toUpperCase(),
                condition,
                price_target: parseFloat(price)
            });

            // Reset form
            setSymbol('');
            setPrice('');
            setCondition('above');

            fetchAlerts();
            toast.success('Price alert created');
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to create alert');
        } finally {
            setAdding(false);
        }
    };

    const handleDeleteAlert = async (alertId) => {
        try {
            await api.delete(`/alerts/${alertId}`);
            setAlerts(prev => prev.filter(a => a.id !== alertId));
            toast.success('Alert deleted');
        } catch (error) {
            toast.error('Failed to delete alert');
        }
    };

    if (loading) {
        return <div className="animate-pulse h-48 bg-white/5 rounded-xl"></div>;
    }

    return (
        <div className="glass p-6 rounded-xl h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Bell size={20} className="text-primary" />
                    Price Alerts
                </h3>
                <span className="text-xs text-muted-foreground">{alerts.length} active</span>
            </div>

            <form onSubmit={handleAddAlert} className="space-y-2 mb-4">
                <div className="flex gap-2">
                    <Combobox
                        options={POPULAR_SYMBOLS}
                        value={symbol}
                        onChange={setSymbol}
                        placeholder="Symbol"
                        className="w-1/3"
                    />
                    <select
                        value={condition}
                        onChange={(e) => setCondition(e.target.value)}
                        className="w-1/3 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:border-primary/50 outline-none appearance-none cursor-pointer"
                    >
                        <option value="above">Above (&gt;)</option>
                        <option value="below">Below (&lt;)</option>
                    </select>
                    <input
                        type="number"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        placeholder="Price"
                        step="any"
                        className="w-1/3 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:border-primary/50 outline-none"
                    />
                </div>
                <button
                    type="submit"
                    disabled={adding || !symbol || !price}
                    className="w-full bg-primary/10 hover:bg-primary/20 text-primary py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                    <Plus size={16} /> Create Alert
                </button>
            </form>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar max-h-[200px]">
                {alerts.length === 0 ? (
                    <div className="text-center text-muted-foreground text-sm py-8">
                        No active alerts
                    </div>
                ) : (
                    alerts.map((alert) => (
                        <div key={alert.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg group hover:bg-white/10 transition-all">
                            <div className="flex items-center gap-3">
                                <div className={`p-1.5 rounded-md ${alert.condition === 'above' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                    {alert.condition === 'above' ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
                                </div>
                                <div>
                                    <div className="font-bold text-sm">{alert.symbol}</div>
                                    <div className="text-xs text-muted-foreground">
                                        Target: <span className="text-foreground font-medium">${alert.price_target}</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDeleteAlert(alert.id)}
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
