import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckSquare, Square, Play, Pause, Trash2,
    MoreHorizontal, X, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * Bulk Actions Bar Component
 * Shows when items are selected for batch operations
 */

const BulkActionsBar = ({
    selectedCount,
    onSelectAll,
    onDeselectAll,
    onAction,
    totalCount,
    allSelected = false,
    actions = ['start', 'stop', 'delete'],
    className = ""
}) => {
    const [loading, setLoading] = useState(null);

    const handleAction = async (action) => {
        setLoading(action);
        try {
            await onAction(action);
            toast.success(`${action.charAt(0).toUpperCase() + action.slice(1)} completed for ${selectedCount} items`);
        } catch (error) {
            toast.error(`Failed to ${action}: ${error.message}`);
        } finally {
            setLoading(null);
        }
    };

    const actionButtons = {
        start: {
            icon: Play,
            label: 'Start All',
            color: 'text-green-400 hover:bg-green-500/20',
            confirm: false
        },
        stop: {
            icon: Pause,
            label: 'Stop All',
            color: 'text-yellow-400 hover:bg-yellow-500/20',
            confirm: true,
            confirmMessage: `Stop ${selectedCount} bots?`
        },
        delete: {
            icon: Trash2,
            label: 'Delete',
            color: 'text-red-400 hover:bg-red-500/20',
            confirm: true,
            confirmMessage: `Delete ${selectedCount} items? This cannot be undone.`
        },
        restart: {
            icon: RefreshCw,
            label: 'Restart',
            color: 'text-blue-400 hover:bg-blue-500/20',
            confirm: false
        }
    };

    if (selectedCount === 0) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className={`
          fixed bottom-6 left-1/2 -translate-x-1/2 z-50
          glass rounded-2xl border border-primary/20 shadow-2xl
          px-4 py-3 flex items-center gap-4
          ${className}
        `}
            >
                {/* Selection info */}
                <div className="flex items-center gap-3 pr-4 border-r border-white/10">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center"
                    >
                        <span className="text-primary font-bold text-sm">{selectedCount}</span>
                    </motion.div>
                    <div className="text-sm">
                        <p className="text-foreground font-medium">
                            {selectedCount} selected
                        </p>
                        <p className="text-muted-foreground text-xs">
                            of {totalCount} items
                        </p>
                    </div>
                </div>

                {/* Select all / Deselect all */}
                <div className="flex items-center gap-2 pr-4 border-r border-white/10">
                    {!allSelected ? (
                        <button
                            onClick={onSelectAll}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                        hover:bg-white/5 text-sm text-muted-foreground 
                        hover:text-foreground transition-colors"
                        >
                            <CheckSquare size={16} />
                            Select All
                        </button>
                    ) : (
                        <button
                            onClick={onDeselectAll}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                        hover:bg-white/5 text-sm text-muted-foreground 
                        hover:text-foreground transition-colors"
                        >
                            <Square size={16} />
                            Deselect All
                        </button>
                    )}
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2">
                    {actions.map((action) => {
                        const config = actionButtons[action];
                        if (!config) return null;

                        const Icon = config.icon;
                        const isLoading = loading === action;

                        return (
                            <motion.button
                                key={action}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => handleAction(action)}
                                disabled={isLoading}
                                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl
                  text-sm font-medium transition-colors
                  ${config.color}
                  disabled:opacity-50 disabled:cursor-not-allowed
                `}
                            >
                                {isLoading ? (
                                    <RefreshCw size={16} className="animate-spin" />
                                ) : (
                                    <Icon size={16} />
                                )}
                                {config.label}
                            </motion.button>
                        );
                    })}
                </div>

                {/* Close button */}
                <button
                    onClick={onDeselectAll}
                    className="ml-2 p-2 hover:bg-white/5 rounded-lg transition-colors"
                >
                    <X size={18} className="text-muted-foreground" />
                </button>
            </motion.div>
        </AnimatePresence>
    );
};

/**
 * Selectable Row Wrapper
 */
export const SelectableRow = ({
    selected,
    onSelect,
    children,
    className = ""
}) => (
    <div className={`relative group ${className}`}>
        <div className="absolute left-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect();
                }}
                className="p-1 rounded hover:bg-white/10"
            >
                {selected ? (
                    <CheckSquare size={18} className="text-primary" />
                ) : (
                    <Square size={18} className="text-muted-foreground" />
                )}
            </button>
        </div>
        <div className={selected ? 'bg-primary/5' : ''}>
            {children}
        </div>
    </div>
);

/**
 * Hook for managing bulk selection
 */
export const useBulkSelection = (items = []) => {
    const [selectedIds, setSelectedIds] = useState(new Set());

    const toggleSelect = (id) => {
        setSelectedIds(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const selectAll = () => {
        setSelectedIds(new Set(items.map(item => item.id || item)));
    };

    const deselectAll = () => {
        setSelectedIds(new Set());
    };

    const isSelected = (id) => selectedIds.has(id);

    return {
        selectedIds: Array.from(selectedIds),
        selectedCount: selectedIds.size,
        isSelected,
        toggleSelect,
        selectAll,
        deselectAll,
        allSelected: selectedIds.size === items.length && items.length > 0
    };
};

export default BulkActionsBar;
