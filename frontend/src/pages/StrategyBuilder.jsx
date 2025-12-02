import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Plus, Trash2, Save, Eye, CheckCircle, AlertTriangle } from 'lucide-react';
import Disclaimer from '../components/Disclaimer';
import PlanGate from '../components/PlanGate';
import { formatLabel } from '../lib/utils';

export default function StrategyBuilder() {
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);
    const [activeTab, setActiveTab] = useState('general');

    // Strategy state
    const [strategyName, setStrategyName] = useState('');
    const [strategyDescription, setStrategyDescription] = useState('');
    const [selectedIndicators, setSelectedIndicators] = useState([]);
    const [buyConditions, setBuyConditions] = useState([]);
    const [sellConditions, setSellConditions] = useState([]);
    const [indicators, setIndicators] = useState({});
    const [operators, setOperators] = useState({});


    useEffect(() => {
        fetchMetadata();
    }, []);

    const fetchMetadata = async () => {
        try {
            const [indicatorsRes, conditionsRes] = await Promise.all([
                api.get('/indicators'),
                api.get('/conditions')
            ]);

            setIndicators(indicatorsRes.data.indicators || {});
            setOperators(conditionsRes.data.operators || {});
        } catch (err) {
            // Silent fail - will use default metadata
            setMessage({ type: 'error', text: 'Failed to load metadata' });
        } finally {
            setLoading(false);
        }
    };

    const addIndicator = () => {
        setSelectedIndicators([...selectedIndicators, {
            id: `indicator_${Date.now()}`,
            type: 'rsi',
            params: { period: 14, source: 'close' }
        }]);
    };

    const updateIndicator = (index, field, value) => {
        const updated = [...selectedIndicators];
        if (field === 'type') {
            updated[index].type = value;
            // Reset params based on new type
            const indicatorMeta = indicators[value];
            const defaultParams = {};
            if (indicatorMeta?.params) {
                Object.entries(indicatorMeta.params).forEach(([key, meta]) => {
                    defaultParams[key] = meta.default;
                });
            }
            updated[index].params = defaultParams;
        } else {
            updated[index].params[field] = value;
        }
        setSelectedIndicators(updated);
    };

    const removeIndicator = (index) => {
        setSelectedIndicators(selectedIndicators.filter((_, i) => i !== index));
    };

    const addCondition = (type) => {
        const condition = {
            id: `condition_${Date.now()}`,
            left: 'close',
            operator: '>',
            right: 50
        };

        if (type === 'buy') {
            setBuyConditions([...buyConditions, condition]);
        } else {
            setSellConditions([...sellConditions, condition]);
        }
    };

    const updateCondition = (type, index, field, value) => {
        const conditions = type === 'buy' ? [...buyConditions] : [...sellConditions];
        conditions[index][field] = value;

        if (type === 'buy') {
            setBuyConditions(conditions);
        } else {
            setSellConditions(conditions);
        }
    };

    const removeCondition = (type, index) => {
        if (type === 'buy') {
            setBuyConditions(buyConditions.filter((_, i) => i !== index));
        } else {
            setSellConditions(sellConditions.filter((_, i) => i !== index));
        }
    };

    const buildJSON = () => {
        return {
            name: strategyName,
            description: strategyDescription,
            version: '1.0.0',
            indicators: selectedIndicators.map(ind => ({
                id: ind.id,
                type: ind.type,
                params: ind.params
            })),
            conditions: {
                buy: {
                    operator: 'AND',
                    rules: buyConditions.map(c => ({
                        left: c.left,
                        operator: c.operator,
                        right: isNaN(c.right) ? c.right : parseFloat(c.right)
                    }))
                },
                sell: {
                    operator: 'AND',
                    rules: sellConditions.map(c => ({
                        left: c.left,
                        operator: c.operator,
                        right: isNaN(c.right) ? c.right : parseFloat(c.right)
                    }))
                }
            }
        };
    };

    const handleSave = async () => {
        if (!strategyName) {
            setMessage({ type: 'error', text: 'Please enter a strategy name' });
            return;
        }

        if (selectedIndicators.length === 0) {
            setMessage({ type: 'error', text: 'Please add at least one indicator' });
            return;
        }

        try {
            const jsonConfig = buildJSON();

            // Validate first
            const validateRes = await api.post('/visual-strategies/validate', {
                name: strategyName,
                description: strategyDescription,
                json_config: jsonConfig
            });

            if (!validateRes.data.valid) {
                setMessage({ type: 'error', text: validateRes.data.message });
                return;
            }

            // Save strategy
            await api.post('/visual-strategies', {
                name: strategyName,
                description: strategyDescription,
                json_config: jsonConfig
            });

            setMessage({ type: 'success', text: 'Strategy saved successfully!' });

            // Reset form after 2 seconds
            setTimeout(() => {
                setStrategyName('');
                setStrategyDescription('');
                setSelectedIndicators([]);
                setBuyConditions([]);
                setSellConditions([]);
                setMessage(null);
            }, 2000);

        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to save strategy' });
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const tabs = [
        { id: 'general', label: 'General', icon: Save },
        { id: 'indicators', label: 'Indicators', icon: Eye },
        { id: 'buy', label: 'Buy Rules', icon: CheckCircle },
        { id: 'sell', label: 'Sell Rules', icon: AlertTriangle },
    ];

    return (
        <PlanGate feature="Strategy Builder">
            <div className="max-w-6xl mx-auto space-y-8">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Strategy Builder
                    </h2>
                    <p className="text-muted-foreground mt-1">Create custom trading strategies without coding</p>
                </div>

                <Disclaimer compact />

                {message && (
                    <div className={`p-4 rounded-xl flex items-center gap-3 border ${message.type === 'success'
                        ? 'bg-green-500/10 border-green-500/20 text-green-400'
                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                        }`}>
                        {message.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                        {message.text}
                    </div>
                )}

                <div className="flex flex-col md:flex-row gap-8">
                    {/* Sidebar Navigation */}
                    <div className="w-full md:w-64 flex-shrink-0">
                        <div className="glass rounded-xl p-2 space-y-1">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                                        ? 'bg-primary text-white shadow-lg shadow-primary/25'
                                        : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                                        }`}
                                >
                                    <tab.icon size={18} />
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 space-y-6">
                        {/* General Tab */}
                        {activeTab === 'general' && (
                            <div className="glass rounded-2xl p-8 space-y-6">
                                <h3 className="font-semibold text-lg">Strategy Information</h3>

                                <div className="space-y-4">
                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Strategy Name</label>
                                        <input
                                            type="text"
                                            value={strategyName}
                                            onChange={(e) => setStrategyName(e.target.value)}
                                            placeholder="My Custom Strategy"
                                            className="w-full mt-2 bg-black/20 border border-white/10 rounded-lg p-3 text-foreground focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-muted-foreground">Description (Optional)</label>
                                        <textarea
                                            value={strategyDescription}
                                            onChange={(e) => setStrategyDescription(e.target.value)}
                                            placeholder="Describe your strategy..."
                                            rows={3}
                                            className="w-full mt-2 bg-black/20 border border-white/10 rounded-lg p-3 text-foreground focus:border-primary/50 outline-none resize-none"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-white/10">
                                    <button
                                        onClick={handleSave}
                                        className="w-full flex items-center justify-center gap-2 px-8 py-3 bg-primary hover:bg-primary/90 text-white rounded-xl font-bold transition-all shadow-lg shadow-primary/25"
                                    >
                                        <Save size={20} />
                                        Save Strategy
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Indicators Tab */}
                        {activeTab === 'indicators' && (
                            <div className="glass rounded-2xl p-8 space-y-6">
                                <div className="flex justify-between items-center">
                                    <h3 className="font-semibold text-lg">Indicators</h3>
                                    <button
                                        onClick={addIndicator}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-all"
                                    >
                                        <Plus size={18} />
                                        Add Indicator
                                    </button>
                                </div>

                                {selectedIndicators.map((indicator, index) => (
                                    <div key={indicator.id} className="bg-white/5 rounded-xl p-6 space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h4 className="font-medium">Indicator #{index + 1}</h4>
                                            <button
                                                onClick={() => removeIndicator(index)}
                                                className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm text-muted-foreground">Type</label>
                                                <div className="relative">
                                                    <select
                                                        value={indicator.type}
                                                        onChange={(e) => updateIndicator(index, 'type', e.target.value)}
                                                        className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground appearance-none cursor-pointer hover:bg-black/30 transition-all outline-none focus:border-primary/50"
                                                    >
                                                        {Object.entries(indicators).map(([key, meta]) => (
                                                            <option key={key} value={key}>{meta.name}</option>
                                                        ))}
                                                    </select>
                                                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none mt-0.5">
                                                        <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                        </svg>
                                                    </div>
                                                </div>
                                            </div>

                                            {indicators[indicator.type]?.params && Object.entries(indicators[indicator.type].params).map(([paramKey, paramMeta]) => (
                                                <div key={paramKey}>
                                                    <label className="text-sm text-muted-foreground capitalize">{formatLabel(paramKey)}</label>
                                                    {paramMeta.type === 'select' ? (
                                                        <div className="relative">
                                                            <select
                                                                value={indicator.params[paramKey]}
                                                                onChange={(e) => updateIndicator(index, paramKey, e.target.value)}
                                                                className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-foreground appearance-none cursor-pointer hover:bg-black/30 transition-all outline-none focus:border-primary/50"
                                                            >
                                                                {paramMeta.options.map(opt => (
                                                                    <option key={opt} value={opt}>{opt}</option>
                                                                ))}
                                                            </select>
                                                            <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none mt-0.5">
                                                                <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                                </svg>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <input
                                                            type="number"
                                                            value={indicator.params[paramKey]}
                                                            onChange={(e) => updateIndicator(index, paramKey, parseFloat(e.target.value))}
                                                            min={paramMeta.min}
                                                            max={paramMeta.max}
                                                            step={paramMeta.step || 1}
                                                            className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 text-foreground"
                                                        />
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}

                                {selectedIndicators.length === 0 && (
                                    <div className="text-center py-12 text-muted-foreground">
                                        No indicators added yet. Click "Add Indicator" to get started.
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Buy Conditions Tab */}
                        {activeTab === 'buy' && (
                            <div className="glass rounded-2xl p-8 space-y-6">
                                <div className="flex justify-between items-center">
                                    <h3 className="font-semibold text-lg text-green-400">Buy Conditions</h3>
                                    <button
                                        onClick={() => addCondition('buy')}
                                        className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all"
                                    >
                                        <Plus size={18} />
                                        Add Buy Condition
                                    </button>
                                </div>

                                {buyConditions.map((condition, index) => (
                                    <ConditionRow
                                        key={condition.id}
                                        condition={condition}
                                        index={index}
                                        type="buy"
                                        selectedIndicators={selectedIndicators}
                                        operators={operators}
                                        onUpdate={updateCondition}
                                        onRemove={removeCondition}
                                    />
                                ))}
                                {buyConditions.length === 0 && (
                                    <div className="text-center py-12 text-muted-foreground">
                                        No buy conditions added yet.
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Sell Conditions Tab */}
                        {activeTab === 'sell' && (
                            <div className="glass rounded-2xl p-8 space-y-6">
                                <div className="flex justify-between items-center">
                                    <h3 className="font-semibold text-lg text-red-400">Sell Conditions</h3>
                                    <button
                                        onClick={() => addCondition('sell')}
                                        className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-all"
                                    >
                                        <Plus size={18} />
                                        Add Sell Condition
                                    </button>
                                </div>

                                {sellConditions.map((condition, index) => (
                                    <ConditionRow
                                        key={condition.id}
                                        condition={condition}
                                        index={index}
                                        type="sell"
                                        selectedIndicators={selectedIndicators}
                                        operators={operators}
                                        onUpdate={updateCondition}
                                        onRemove={removeCondition}
                                    />
                                ))}
                                {sellConditions.length === 0 && (
                                    <div className="text-center py-12 text-muted-foreground">
                                        No sell conditions added yet.
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </PlanGate>
    );
}

// Condition Row Component
function ConditionRow({ condition, index, type, selectedIndicators, operators, onUpdate, onRemove }) {
    const comparisonOps = operators.comparison || {};
    const crossOps = operators.crosses || {};
    const allOps = { ...comparisonOps, ...crossOps };

    return (
        <div className="bg-white/5 rounded-xl p-4 flex items-center gap-4">
            <div className="flex-1 grid grid-cols-3 gap-4">
                <div>
                    <label className="text-xs text-muted-foreground">Left Value</label>
                    <div className="relative">
                        <select
                            value={condition.left}
                            onChange={(e) => onUpdate(type, index, 'left', e.target.value)}
                            className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-sm text-foreground appearance-none cursor-pointer hover:bg-black/30 transition-all outline-none focus:border-primary/50"
                        >
                            <option value="close">Close Price</option>
                            <option value="open">Open Price</option>
                            <option value="high">High Price</option>
                            <option value="low">Low Price</option>
                            {selectedIndicators.map(ind => (
                                <option key={ind.id} value={ind.id}>{ind.id}</option>
                            ))}
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none mt-0.5">
                            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>
                </div>

                <div>
                    <label className="text-xs text-muted-foreground">Operator</label>
                    <div className="relative">
                        <select
                            value={condition.operator}
                            onChange={(e) => onUpdate(type, index, 'operator', e.target.value)}
                            className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 pr-8 text-sm text-foreground appearance-none cursor-pointer hover:bg-black/30 transition-all outline-none focus:border-primary/50"
                        >
                            {Object.entries(allOps).map(([key, meta]) => (
                                <option key={key} value={key}>{meta.symbol} {meta.name}</option>
                            ))}
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none mt-0.5">
                            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                        </div>
                    </div>
                </div>

                <div>
                    <label className="text-xs text-muted-foreground">Right Value</label>
                    <input
                        type="text"
                        value={condition.right}
                        onChange={(e) => onUpdate(type, index, 'right', e.target.value)}
                        placeholder="Value or indicator"
                        className="w-full mt-1 bg-black/20 border border-white/10 rounded-lg p-2 text-sm text-foreground"
                    />
                </div>
            </div>

            <button
                onClick={() => onRemove(type, index)}
                className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
            >
                <Trash2 size={18} />
            </button>
        </div>
    );
}
