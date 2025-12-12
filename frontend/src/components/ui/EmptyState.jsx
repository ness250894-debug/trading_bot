import React from 'react';
import { motion } from 'framer-motion';
import {
    Bot,
    BarChart3,
    Bell,
    History,
    TrendingUp,
    Inbox,
    Search,
    Sparkles,
    Plus,
    ArrowRight
} from 'lucide-react';

/**
 * Empty State Component
 * Friendly illustrations and messages when no data is available
 */

const EmptyState = ({
    icon: Icon = Inbox,
    title = "No data yet",
    description = "There's nothing here yet. Get started by creating something new.",
    action,
    actionText = "Get Started",
    variant = "default", // default, minimal, large
    className = ""
}) => {
    const variants = {
        default: {
            iconSize: 48,
            iconContainer: "w-20 h-20",
            titleSize: "text-lg",
            spacing: "py-12 px-6"
        },
        minimal: {
            iconSize: 32,
            iconContainer: "w-14 h-14",
            titleSize: "text-base",
            spacing: "py-8 px-4"
        },
        large: {
            iconSize: 64,
            iconContainer: "w-28 h-28",
            titleSize: "text-xl",
            spacing: "py-16 px-8"
        }
    };

    const config = variants[variant];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex flex-col items-center justify-center text-center ${config.spacing} ${className}`}
        >
            {/* Icon with gradient background */}
            <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1 }}
                className={`${config.iconContainer} rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 
                   flex items-center justify-center mb-4 border border-white/5`}
            >
                <Icon size={config.iconSize} className="text-primary/70" />
            </motion.div>

            {/* Title */}
            <h3 className={`${config.titleSize} font-semibold text-foreground mb-2`}>
                {title}
            </h3>

            {/* Description */}
            <p className="text-muted-foreground max-w-sm mb-6">
                {description}
            </p>

            {/* Action button */}
            {action && (
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={action}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl
                    bg-primary/20 hover:bg-primary/30 text-primary
                    font-medium transition-colors"
                >
                    <Plus size={18} />
                    {actionText}
                    <ArrowRight size={16} />
                </motion.button>
            )}
        </motion.div>
    );
};

/**
 * Pre-configured empty states
 */
export const NoBotsEmptyState = ({ onAction }) => (
    <EmptyState
        icon={Bot}
        title="No bots running"
        description="You don't have any active trading bots. Create your first bot to start automated trading."
        action={onAction}
        actionText="Create Bot"
    />
);

export const NoTradesEmptyState = ({ onAction }) => (
    <EmptyState
        icon={History}
        title="No trades yet"
        description="Your trade history will appear here once your bots start executing trades."
        action={onAction}
        actionText="Start Trading"
    />
);

export const NoAlertsEmptyState = ({ onAction }) => (
    <EmptyState
        icon={Bell}
        title="No price alerts"
        description="Set up price alerts to get notified when your favorite coins reach your target price."
        action={onAction}
        actionText="Create Alert"
    />
);

export const NoBacktestEmptyState = ({ onAction }) => (
    <EmptyState
        icon={BarChart3}
        title="No backtest results"
        description="Run a backtest to see how your strategy would have performed historically."
        action={onAction}
        actionText="Run Backtest"
    />
);

export const NoOptimizationEmptyState = ({ onAction }) => (
    <EmptyState
        icon={Sparkles}
        title="No optimization results"
        description="Optimize your strategy parameters to find the best configuration for your trading style."
        action={onAction}
        actionText="Start Optimization"
    />
);

export const NoSearchResultsEmptyState = ({ searchTerm }) => (
    <EmptyState
        icon={Search}
        title="No results found"
        description={`We couldn't find anything matching "${searchTerm}". Try adjusting your search.`}
        variant="minimal"
    />
);

export const NoWatchlistEmptyState = ({ onAction }) => (
    <EmptyState
        icon={TrendingUp}
        title="Watchlist is empty"
        description="Add your favorite cryptocurrencies to keep track of their prices."
        action={onAction}
        actionText="Add Symbol"
    />
);

export default EmptyState;
