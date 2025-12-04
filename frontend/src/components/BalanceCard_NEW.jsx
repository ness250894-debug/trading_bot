const BalanceCard = ({ status, onRefreshBalance, refreshing, trades }) => {
    const isPracticeMode = status?.config?.dry_run;
    const hasApiConnected = status?.balance?.total !== undefined && status?.balance?.total !== null;

    return (
        <div className="glass p-8 rounded-2xl relative overflow-hidden group col-span-1">

            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                        <DollarSign size={24} />
                    </div>
                    <h3 className="text-base font-medium text-muted-foreground">Balance Management</h3>
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
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                        <div>
                            <div className="text-sm text-muted-foreground mb-2">Balance</div>
                            <div className="text-4xl font-bold text-foreground tracking-tight mb-1">
                                ${status?.balance?.total?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-muted-foreground">USDT on wallet</div>
                        </div>

                        <div>
                            <div className="text-sm text-muted-foreground mb-2">Practice Balance</div>
                            <div className="text-4xl font-bold text-yellow-400 tracking-tight mb-1">
                                ${status?.balance?.free?.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-yellow-400/70">⚠️ Not real money</div>
                        </div>
                    </div>

                    {/* PnL Stats */}
                    {trades && trades.length > 0 && (
                        <div className="mt-6 pt-4 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-4 relative z-10">
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">Total PnL</div>
                                <div className="text-2xl font-bold" style={{ color: (status?.total_pnl || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                    ${(status?.total_pnl || 0).toFixed(2)}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">Win Rate</div>
                                <div className="text-2xl font-bold text-green-400">
                                    {((trades.filter(t => (t.pnl !== undefined ? t.pnl : t.profit_loss) > 0).length / trades.length * 100).toFixed(1))}%
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-muted-foreground mb-1">Total Trades</div>
                                <div className="text-2xl font-bold text-foreground">
                                    {trades.length}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between relative z-10">
                        <div className="flex items-center gap-4 text-sm">
                            <div>
                                <span className="text-muted-foreground">In Orders: </span>
                                <span className="font-semibold">${((status?.balance?.total || 0) - (status?.balance?.free || 0)).toFixed(2)}</span>
                            </div>
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
