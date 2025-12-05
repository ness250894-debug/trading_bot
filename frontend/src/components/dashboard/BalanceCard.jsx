import React from 'react';
import { DollarSign } from 'lucide-react';

const BalanceCard = ({ status, onRefreshBalance, refreshing, trades, exchangeBalances, exchangeBalancesLoading }) => {
    const isPracticeMode = status?.config?.dry_run;
    const hasApiConnected = exchangeBalances?.has_keys || (status?.balance?.total !== undefined && status?.balance?.total !== null);

    // Exchange display names
    const exchangeNames = {
        'bybit': 'Bybit',
        'binance': 'Binance',
        'okx': 'OKX',
        'kraken': 'Kraken',
        'coinbase': 'Coinbase'
    };

    return (
        <div className="glass p-6 rounded-2xl relative overflow-hidden group col-span-1 h-full">

            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                        <DollarSign size={24} />
                    </div>
                    <h3 className="text-base font-medium text-muted-foreground">Exchange Balances</h3>
                </div>
                {isPracticeMode && hasApiConnected && (
                    <button
                        onClick={onRefreshBalance}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors text-sm disabled:opacity-50 relative z-20"
                        title="Reset practice balance to $1,000"
                    >
                        {refreshing ? (
                            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
                            </svg>
                        )}
                        Reset
                    </button>
                )}
            </div>

            {!hasApiConnected ? (
                <div className="py-8 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted-foreground/10 flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                    </div>
                    <h4 className="text-lg font-semibold mb-2">Connect Your API Keys</h4>
                    <p className="text-muted-foreground text-sm max-w-md mx-auto">
                        To view your account balance and start trading, please connect your exchange API keys in Settings.
                    </p>
                </div>
            ) : exchangeBalancesLoading ? (
                <div className="py-8 text-center">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-muted-foreground text-sm">Fetching balances from exchanges...</p>
                </div>
            ) : (
                <>
                    {/* Total Balance */}
                    <div className="relative z-10 mb-6">
                        <div className="text-sm text-muted-foreground mb-2">Total Balance (All Exchanges)</div>
                        <div className="text-4xl font-bold text-foreground tracking-tight mb-1">
                            ${exchangeBalances?.total_usdt?.toFixed(2) || '0.00'}
                        </div>
                        <div className="text-xs text-muted-foreground">USDT across {exchangeBalances?.exchanges?.length || 0} exchange(s)</div>
                    </div>

                    {/* Per-Exchange Breakdown */}
                    {exchangeBalances?.exchanges?.length > 0 && (
                        <div className="space-y-3 mb-4">
                            <div className="text-sm text-muted-foreground font-medium">Balance by Exchange</div>
                            {exchangeBalances.exchanges.map((ex, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${ex.status === 'connected' ? 'bg-green-400' : 'bg-red-400'}`} />
                                        <span className="font-medium capitalize">{exchangeNames[ex.exchange] || ex.exchange}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold">${ex.usdt_total?.toFixed(2) || '0.00'}</div>
                                        {ex.usdt_free !== undefined && ex.usdt_free !== ex.usdt_total && (
                                            <div className="text-xs text-muted-foreground">
                                                Available: ${ex.usdt_free?.toFixed(2)}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="pt-4 border-t border-white/10 flex items-center justify-between relative z-10">
                        <div className="flex items-center gap-4 text-sm">
                            {isPracticeMode && (
                                <div className="px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                    <p className="text-xs text-yellow-400 flex items-center gap-1">
                                        <span>⚠️</span>
                                        <span>Practice Mode Active</span>
                                    </p>
                                </div>
                            )}
                        </div>
                        {!isPracticeMode && (
                            <div className="px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg">
                                <p className="text-xs text-green-400 flex items-center gap-1">
                                    <span>🚀</span>
                                    <span>Live Trading Active</span>
                                </p>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default BalanceCard;
