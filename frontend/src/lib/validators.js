import { z } from 'zod';

/**
 * Validation schemas for form inputs across the application
 */

// API Key Validation
export const apiKeySchema = z.object({
    exchange: z.enum(['bybit', 'binance', 'okx'], {
        errorMap: () => ({ message: 'Please select a valid exchange' })
    }),
    apiKey: z.string()
        .min(10, 'API key is too short (minimum 10 characters)')
        .max(100, 'API key is too long (maximum 100 characters)')
        .trim(),
    apiSecret: z.string()
        .min(10, 'API secret is too short (minimum 10 characters)')
        .max(100, 'API secret is too long (maximum 100 characters)')
        .trim(),
});

// Strategy Configuration Validation
export const strategyConfigSchema = z.object({
    symbol: z.string()
        .regex(/^[A-Z]+\/[A-Z]+$/, 'Invalid symbol format (e.g., BTC/USDT)')
        .trim(),
    timeframe: z.enum(['1m', '5m', '15m', '1h', '4h', '1d'], {
        errorMap: () => ({ message: 'Please select a valid timeframe' })
    }),
    strategy: z.string().min(1, 'Strategy is required'),
    amount_usdt: z.number()
        .positive('Amount must be positive')
        .max(1000000, 'Amount cannot exceed 1,000,000 USDT'),
    leverage: z.number()
        .int('Leverage must be a whole number')
        .min(1, 'Leverage must be at least 1x')
        .max(125, 'Leverage cannot exceed 125x'),
    take_profit_pct: z.number()
        .positive('Take profit must be positive')
        .max(100, 'Take profit cannot exceed 100%'),
    stop_loss_pct: z.number()
        .positive('Stop loss must be positive')
        .max(100, 'Stop loss cannot exceed 100%'),
});

// Authentication Validation
export const emailSchema = z.string()
    .email('Invalid email address')
    .trim()
    .toLowerCase();

export const passwordSchema = z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password is too long');

export const signupSchema = z.object({
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
    nickname: z.string().max(50, 'Nickname is too long').optional(),
}).refine(data => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
});

export const loginSchema = z.object({
    email: emailSchema,
    password: z.string().min(1, 'Password is required'),
});

// Backtest Validation
export const backtestSchema = z.object({
    symbol: z.string().regex(/^[A-Z]+\/[A-Z]+$/, 'Invalid symbol format'),
    timeframe: z.enum(['1m', '5m', '15m', '1h', '4h', '1d']),
    strategy: z.string().min(1, 'Strategy is required'),
    days: z.number()
        .int('Days must be a whole number')
        .positive('Days must be positive')
        .max(30, 'Cannot backtest more than 30 days'),
    leverage: z.number()
        .positive('Leverage must be positive')
        .max(125, 'Leverage cannot exceed 125x'),
});

// Optimization Validation
export const optimizationSchema = backtestSchema.extend({
    n_trials: z.number()
        .int('Trials must be a whole number')
        .positive('Trials must be positive')
        .max(1000, 'Cannot exceed 1000 trials')
        .optional(),
});
