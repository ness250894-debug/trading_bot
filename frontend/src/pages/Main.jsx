import React, { useEffect } from 'react';
import CombinedSentimentWidget from '../components/CombinedSentimentWidget';
import BotInstancesTable from '../components/BotInstancesTable';
import WatchlistWidget from '../components/WatchlistWidget';
import PriceAlertsWidget from '../components/PriceAlertsWidget';
import BalanceCard from '../components/dashboard/BalanceCard';
import BotLogs from '../components/BotLogs';
import PlanGate from '../components/PlanGate';

import DashboardHeader from '../components/dashboard/DashboardHeader';
import SubscriptionCard from '../components/dashboard/SubscriptionCard';
import NewsFeed from '../components/dashboard/NewsFeed';
import TradingGoalsWidget from '../components/TradingGoalsWidget';

import { useDashboardData } from '../hooks/useDashboardData';

export default function Main() {
    const {
        user,
        subscription,
        isPracticeMode,
        loading,
        refreshing,
        botStatus,
        botConfigs,
        startingBots,
        exchangeBalances,
        exchangeBalancesLoading,
        refreshingBalance,
        newsItems,
        newsLoading,
        handlePracticeModeToggle,
        handleRefresh,
        handleRefreshBalance,
        handleStartStop,
        isBotRunning,
        handleRemoveBot,
        handleBulkRemove,
        handleQuickScalp,
        handleStartBot,
        handleStopBot,
        fetchNews
    } = useDashboardData();

    // Scroll main container to top on mount
    useEffect(() => {
        const mainContainer = document.querySelector('main');
        if (mainContainer) {
            mainContainer.scrollTo({ top: 0, behavior: 'instant' });
        } else {
            window.scrollTo(0, 0);
        }
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-muted-foreground animate-pulse">Loading your profile...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header Section */}
            <DashboardHeader
                user={user}
                isPracticeMode={isPracticeMode}
                subscription={subscription}
                handlePracticeModeToggle={handlePracticeModeToggle}
                handleRefresh={handleRefresh}
                refreshing={refreshing}
            />

            {/* Bot Instances Table - Moved to Top */}
            <div id="bot-instances-table">
                <BotInstancesTable
                    instances={botStatus?.instances || {}}
                    botConfigs={botConfigs}
                    onRemoveBot={handleRemoveBot}
                    onBulkRemove={handleBulkRemove}
                    onStart={handleStartBot}
                    onStop={handleStopBot}
                    onStopAll={() => handleStartStop()}
                    loading={loading}
                    subscription={subscription}
                    startingBots={startingBots}
                    isBotRunning={isBotRunning}
                    onQuickScalp={handleQuickScalp}
                />
            </div>

            {/* Live Bot Logs */}
            {botStatus?.is_running && (
                <div className="mb-8">
                    <BotLogs
                        logs={Object.values(botStatus?.instances || {})[0]?.logs || []}
                        isRunning={botStatus?.is_running}
                    />
                </div>
            )}

            {/* Account Info Grid */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Subscription Details Card */}
                <SubscriptionCard subscription={subscription} />

                {/* Balance Card */}
                <div className="h-full">
                    <BalanceCard
                        status={botStatus}
                        onRefreshBalance={handleRefreshBalance}
                        refreshing={refreshingBalance}
                        trades={[]}
                        exchangeBalances={exchangeBalances}
                        exchangeBalancesLoading={exchangeBalancesLoading}
                        isPracticeMode={isPracticeMode}
                    />
                </div>
            </div>

            {/* Market Tools Grid */}
            <div className="grid md:grid-cols-2 gap-6">
                {/* Watchlist */}
                <div className="h-[500px]">
                    <WatchlistWidget />
                </div>

                {/* Price Alerts */}
                <div className="h-[500px]">
                    <PriceAlertsWidget />
                </div>
            </div>

            {/* Trading Goals */}
            <div>
                <TradingGoalsWidget />
            </div>

            {/* AI Sentiment & Analysis - Combined Widget */}
            <div>
                <PlanGate feature="AI Sentiment & Analysis" explanation="Get real-time market sentiment analysis powered by AI with advanced metrics and key market drivers.">
                    <CombinedSentimentWidget />
                </PlanGate>
            </div>

            {/* News Feed */}
            <NewsFeed
                newsItems={newsItems}
                loading={newsLoading}
                onRefresh={fetchNews}
            />
        </div>
    );
}
