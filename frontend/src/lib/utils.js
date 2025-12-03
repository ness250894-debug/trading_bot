// Utility functions for text formatting

/**
 * Formats technical text to user-friendly display text
 * Examples:
 * - "basic_tier" -> "Basic"
 * - "premium_tier" -> "Premium"
 * - "dry_run" -> "Practice Mode"
 * - "active_trades" -> "Active Positions"
 */
export const formatLabel = (text) => {
    if (!text) return '';

    const labelMap = {
        'dry_run': 'Practice Mode',
        'active_trades': 'Active Positions',
        'bot_status': 'Bot Status',
        'user_id': 'Account Number',
    };

    // Check if we have a specific mapping
    if (labelMap[text.toLowerCase()]) {
        return labelMap[text.toLowerCase()];
    }

    // Remove underscores and convert to title case
    return text
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
        .replace(/\s+tier$/i, '') // Remove "Tier" suffix
        .replace(/\s+plan$/i, '') // Remove "Plan" suffix
        .replace(/\s+monthly$/i, '') // Remove "Monthly" suffix
        .replace(/\s+yearly$/i, ''); // Remove "Yearly" suffix
};

/**
 * Formats plan names for display
 * Examples:
 * - "basic_tier" -> "Basic"
 * - "admin" -> "Admin"
 */
export const formatPlanName = (plan) => {
    if (!plan) return 'Free';

    return formatLabel(plan);
};

/**
 * Formats strategy names for display
 * Examples:
 * - "sma_crossover" -> "SMA Crossover"
 * - "rsi_strategy" -> "RSI Strategy"
 */
export const formatStrategyName = (strategy) => {
    if (!strategy) return 'None';

    return formatLabel(strategy);
};
