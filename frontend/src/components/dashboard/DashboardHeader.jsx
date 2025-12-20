import React from 'react';
import { RefreshCw } from 'lucide-react';
import PracticeModeToggle from '../PracticeModeToggle';

const DashboardHeader = ({
    user,
    isPracticeMode,
    subscription,
    handlePracticeModeToggle,
    handleRefresh,
    refreshing
}) => {
    return (
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Welcome back, {user?.nickname || user?.email?.split('@')[0] || 'Trader'}!
                </h1>
                <p className="text-muted-foreground mt-1">
                    Your trading overview and account information.
                </p>
            </div>

            <div className="flex items-center gap-3">
                <PracticeModeToggle
                    isPracticeMode={isPracticeMode}
                    onToggle={handlePracticeModeToggle}
                    isFreePlan={subscription?.plan === 'free'}
                />
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="p-2 hover:bg-white/10 rounded-lg transition-all"
                    title="Refresh data"
                >
                    <RefreshCw size={20} className={`text-muted-foreground ${refreshing ? 'animate-spin' : ''}`} />
                </button>
            </div>
        </div>
    );
};

export default DashboardHeader;
