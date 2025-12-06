import React from 'react';
import { DollarSign, Wallet, RefreshCw } from 'lucide-react';

const BalanceCard = ({ status, onRefreshBalance, refreshing, trades, exchangeBalances, exchangeBalancesLoading, isPracticeMode }) => {
    // If global practice mode is on, we treat it as practice
    // Otherwise fallback to status config (legacy) or default to false
    const showPracticeMode = isPracticeMode ?? status?.config?.dry_run;
    const hasApiConnected = exchangeBalances?.has_keys || (status?.balance?.total !== undefined && status?.balance?.total !== null);

    // Calculate PnL from trades if available
    const calculatePnL = () => {
        if (!trades || trades.length === 0) return { amount: 0, percentage: 0 };
        const pnl = trades.reduce((acc, trade) => acc + (trade.pnl || 0), 0);
        const startingBalance = 1000; // Assumed starting balance for practice
        const percentage = (pnl / startingBalance) * 100;
        return { amount: pnl, percentage };
    };

    const pnlData = calculatePnL();

    // Exchange display names
    const exchangeNames = {
        'bybit': 'Bybit',
        'binance': 'Binance',
        'okx': 'OKX',
        'kraken': 'Kraken',
        'coinbase': 'Coinbase'
    };

    return (
        <div className="glass p-8 rounded-2xl relative overflow-hidden group col-span-1 h-full flex flex-col">
            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                        {showPracticeMode ? <Wallet size={24} /> : <DollarSign size={24} />}
                    </div>
                    <h3 className="text-base font-medium text-muted-foreground">
                        {showPracticeMode ? 'Practice Balance' : 'Exchange Balances'}
                    </h3>
                </div>
                {/* Reset/Refresh Button */}
                <button
                    onClick={onRefreshBalance}
                    disabled={refreshing}
                    className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors text-sm disabled:opacity-50 relative z-20"
                    title={showPracticeMode ? "Reset practice balance to $1,000" : "Refresh exchange balances"}
                >
                    {refreshing ? (
                        <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    ) : (
                        <RefreshCw size={14} />
                    )}
                    {showPracticeMode ? 'Reset' : 'Refresh'}
                </button>
            </div>

            {/* Content Logic */}
            <div className="flex-1 flex flex-col justify-center">
                {showPracticeMode ? (
                    // PRACTICE MODE DISPLAY
                    <div className="relative z-10">
                        <div className="text-sm text-muted-foreground mb-2">Simulated USDT Balance</div>
                        <div className="text-4xl font-bold text-foreground tracking-tight mb-2">
                            ${status?.balance?.available?.toFixed(2) || '1,000.00'}
                        </div>
                        <div className="flex items-center gap-2">
                            <span className={`text-sm font-medium ${pnlData.amount >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {pnlData.amount >= 0 ? '+' : ''}{pnlData.amount.toFixed(2)} ({pnlData.percentage.toFixed(2)}%)
                            </span>
                            <span className="text-xs text-muted-foreground">Total PnL</span>
                        </div>
                        <div className="mt-4 p-3 bg-yellow-400/10 border border-yellow-400/20 rounded-lg">
                            <p className="text-xs text-yellow-400 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                                Practice Mode Active - No real money used
                            </p>
                        </div>
                    </div>
                ) : (
                    // REAL MODE DISPLAY
                    <>
                        {!hasApiConnected ? (
                            <div className="py-4 text-center">
                                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-muted-foreground/10 flex items-center justify-center">
                                    <DollarSign className="text-muted-foreground" size={24} />
                                </div>
                                <h4 className="text-base font-semibold mb-1">Connect Exchange</h4>
                                <p className="text-muted-foreground text-xs max-w-[200px] mx-auto">
                                    Connect API keys in Settings to view real balances.
                                </p>
                            </div>
                        ) : exchangeBalancesLoading ? (
                            <div className="py-8 text-center">
                                <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                                <p className="text-muted-foreground text-sm">Fetching balances...</p>
                            </div>
                        ) : (
                            <>
                                <div className="relative z-10 mb-6">
                                    <div className="text-sm text-muted-foreground mb-2">Total Balance</div>
                                    <div className="text-4xl font-bold text-foreground tracking-tight mb-1">
                                        ${exchangeBalances?.total_usdt?.toFixed(2) || '0.00'}
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        Across {exchangeBalances?.exchanges?.length || 0} connected exchange(s)
                                    </div>
                                </div>

                                {exchangeBalances?.exchanges?.length > 0 && (
                                    <div className="space-y-2 max-h-[150px] overflow-y-auto pr-2 scrollbar-thin">
                                        {exchangeBalances.exchanges.map((ex, idx) => (
                                            <div key={idx} className="flex justify-between items-center p-2 rounded-lg bg-white/5 border border-white/5">
                                                <div className="flex items-center gap-2">
                                                    <span className="capitalize text-sm font-medium">{exchangeNames[ex.name] || ex.name}</span>
                                                </div>
                                                <div className="text-sm font-semibold">${ex.usdt_total?.toFixed(2)}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </>
                        )}
                    </>
                )}
            </div>

            {/* Decorative Background Blob */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none" />
        </div>
    );
};

export default BalanceCard;
