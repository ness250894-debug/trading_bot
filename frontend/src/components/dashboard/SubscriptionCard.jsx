import React from 'react';
import { Shield, CheckCircle, XCircle, Calendar, TrendingUp } from 'lucide-react';
import { formatPlanName } from '../../lib/utils';

const SubscriptionCard = ({ subscription }) => {
    return (
        <div className="glass p-6 rounded-2xl h-full">
            <div className="flex items-center gap-2 mb-4">
                <Shield size={20} className="text-primary" />
                <h2 className="text-xl font-bold">Subscription Details</h2>
            </div>
            <div className="space-y-4">
                <div className="flex justify-between items-center">
                    <div>
                        <p className="text-sm text-muted-foreground mb-1">Current Plan</p>
                        <p className="text-lg font-semibold text-foreground">
                            {formatPlanName(subscription?.plan) || 'Free Plan'}
                        </p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground mb-1">Status</p>
                        <div className="flex items-center justify-end gap-2">
                            {subscription?.status === 'active' ? (
                                <>
                                    <CheckCircle size={16} className="text-green-400" />
                                    <span className="text-sm font-semibold text-green-400">Active</span>
                                </>
                            ) : (
                                <>
                                    <XCircle size={16} className="text-red-400" />
                                    <span className="text-sm font-semibold text-red-400">
                                        {subscription?.status?.toUpperCase() || 'Inactive'}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {subscription?.expires_at && (
                    <div className="pt-4 border-t border-white/10">
                        <p className="text-sm text-muted-foreground mb-1">Expires</p>
                        <div className="flex items-center gap-2">
                            <Calendar size={16} className="text-primary" />
                            <p className="text-sm font-medium text-foreground">
                                {new Date(subscription.expires_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                )}

                <div className="pt-4 border-t border-white/10">
                    <a
                        href="/pricing"
                        className="w-full justify-center text-primary hover:text-primary/80 font-medium inline-flex items-center gap-1 p-2 bg-primary/10 rounded-lg transition-colors border border-primary/20 hover:bg-primary/20"
                    >
                        Upgrade Plan <TrendingUp size={14} />
                    </a>
                </div>
            </div>
        </div>
    );
};

export default SubscriptionCard;
