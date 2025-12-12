import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, ChevronDown, X } from 'lucide-react';

/**
 * Date Range Filter Component
 * Filter trades and data by date range with presets
 */

const PRESETS = [
    { label: 'Today', value: 'today', days: 0 },
    { label: 'Last 7 Days', value: '7d', days: 7 },
    { label: 'Last 30 Days', value: '30d', days: 30 },
    { label: 'Last 90 Days', value: '90d', days: 90 },
    { label: 'This Year', value: 'year', days: 365 },
    { label: 'All Time', value: 'all', days: null },
];

const DateRangeFilter = ({
    value,
    onChange,
    className = ""
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [customRange, setCustomRange] = useState({ start: '', end: '' });

    const selectedPreset = PRESETS.find(p => p.value === value) || PRESETS[5]; // Default to 'All Time'

    const handlePresetSelect = (preset) => {
        if (preset.days === null) {
            onChange({ type: 'all', start: null, end: null });
        } else if (preset.days === 0) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            onChange({
                type: 'preset',
                value: preset.value,
                start: today,
                end: new Date()
            });
        } else {
            const end = new Date();
            const start = new Date();
            start.setDate(start.getDate() - preset.days);
            start.setHours(0, 0, 0, 0);
            onChange({
                type: 'preset',
                value: preset.value,
                start,
                end
            });
        }
        setIsOpen(false);
    };

    const handleCustomApply = () => {
        if (customRange.start && customRange.end) {
            onChange({
                type: 'custom',
                value: 'custom',
                start: new Date(customRange.start),
                end: new Date(customRange.end)
            });
            setIsOpen(false);
        }
    };

    const handleClear = (e) => {
        e.stopPropagation();
        onChange({ type: 'all', start: null, end: null });
    };

    return (
        <div className={`relative ${className}`}>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl
                  bg-black/20 border border-white/10 hover:border-white/20
                  text-sm text-foreground transition-colors"
            >
                <Calendar size={16} className="text-primary" />
                <span>{selectedPreset.label}</span>
                <ChevronDown
                    size={14}
                    className={`text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`}
                />
                {value !== 'all' && (
                    <button
                        onClick={handleClear}
                        className="ml-1 p-0.5 hover:bg-white/10 rounded"
                    >
                        <X size={12} className="text-muted-foreground" />
                    </button>
                )}
            </button>

            {/* Dropdown */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <div
                            className="fixed inset-0 z-40"
                            onClick={() => setIsOpen(false)}
                        />

                        {/* Menu */}
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 mt-2 z-50 w-72
                        glass rounded-xl border border-white/10 shadow-xl
                        overflow-hidden"
                        >
                            {/* Presets */}
                            <div className="p-2">
                                <p className="text-xs text-muted-foreground font-medium px-2 py-1 mb-1">
                                    Quick Filters
                                </p>
                                <div className="grid grid-cols-2 gap-1">
                                    {PRESETS.map((preset) => (
                                        <button
                                            key={preset.value}
                                            onClick={() => handlePresetSelect(preset)}
                                            className={`
                        px-3 py-2 text-sm rounded-lg text-left transition-colors
                        ${value === preset.value
                                                    ? 'bg-primary/20 text-primary'
                                                    : 'hover:bg-white/5 text-foreground'
                                                }
                      `}
                                        >
                                            {preset.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Divider */}
                            <div className="border-t border-white/10" />

                            {/* Custom Range */}
                            <div className="p-3">
                                <p className="text-xs text-muted-foreground font-medium mb-2">
                                    Custom Range
                                </p>
                                <div className="flex gap-2 mb-3">
                                    <div className="flex-1">
                                        <label className="text-xs text-muted-foreground block mb-1">From</label>
                                        <input
                                            type="date"
                                            value={customRange.start}
                                            onChange={(e) => setCustomRange(prev => ({ ...prev, start: e.target.value }))}
                                            className="w-full px-3 py-2 bg-black/20 border border-white/10 
                                rounded-lg text-sm text-foreground
                                focus:outline-none focus:border-primary/50"
                                        />
                                    </div>
                                    <div className="flex-1">
                                        <label className="text-xs text-muted-foreground block mb-1">To</label>
                                        <input
                                            type="date"
                                            value={customRange.end}
                                            onChange={(e) => setCustomRange(prev => ({ ...prev, end: e.target.value }))}
                                            className="w-full px-3 py-2 bg-black/20 border border-white/10 
                                rounded-lg text-sm text-foreground
                                focus:outline-none focus:border-primary/50"
                                        />
                                    </div>
                                </div>
                                <button
                                    onClick={handleCustomApply}
                                    disabled={!customRange.start || !customRange.end}
                                    className="w-full py-2 rounded-lg bg-primary/20 hover:bg-primary/30
                            text-primary text-sm font-medium transition-colors
                            disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Apply Custom Range
                                </button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DateRangeFilter;
