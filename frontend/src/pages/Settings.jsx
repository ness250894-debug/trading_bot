import React, { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { useStaticData } from '../lib/swr';

import {
    User, Key, Bell, Settings as SettingsIcon, Shield,
    LogOut, Moon, Sun, DollarSign, Globe, CheckCircle,
    AlertTriangle, Trash2, Save, Copy, Plus
} from 'lucide-react';
import { useToast } from '../components/ToastContext';
import { useModal } from '../components/Modal';
import { DEFAULT_EXCHANGES } from '../constants/exchanges';
import EditableText from '../components/constructor/EditableText';

export default function Settings() {
    const [activeTab, setActiveTab] = useState('profile');
    const toast = useToast();
    const modal = useModal();

    // API Keys state
    const [apiKey, setApiKey] = useState('');
    const [apiSecret, setApiSecret] = useState('');
    const [exchange, setExchange] = useState('bybit');
    const [hasKey, setHasKey] = useState(false);
    const [loading, setLoading] = useState(false);
    const [exchanges, setExchanges] = useState([]);
    const [savedApiKeys, setSavedApiKeys] = useState([]);
    const [selectedApis, setSelectedApis] = useState(new Set());

    // Telegram settings state
    const [telegramChatId, setTelegramChatId] = useState('');
    const [hasTelegram, setHasTelegram] = useState(false);
    const [telegramLoading, setTelegramLoading] = useState(false);
    const [savedTelegramIds, setSavedTelegramIds] = useState([]);

    // User info state
    const [userInfo, setUserInfo] = useState(null);

    // Risk Profile state
    const [riskProfile, setRiskProfile] = useState({
        max_daily_loss: '',
        max_drawdown: '',
        max_position_size: '',
        max_open_positions: '',
        stop_trading_on_breach: true
    });
    const [riskLoading, setRiskLoading] = useState(false);
    const [savedRiskRules, setSavedRiskRules] = useState([]);

    // Helper function to mask API keys
    const maskApiKey = (key) => {
        if (!key || key.length < 8) return '••••••••';
        return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4);
    };


    const checkApiKeyStatus = useCallback(async () => {
        try {
            const response = await api.get(`/api-keys/${exchange}`);
            setHasKey(response.data.has_key);
        } catch (error) {
            // Silent fail - will show "no key" state
        }
    }, [exchange]);

    const checkTelegramStatus = useCallback(async () => {
        try {
            const response = await api.get('/user/telegram');
            setHasTelegram(response.data.has_telegram);
            // Also get the chat ID if exists
            if (response.data.chat_id) {
                setSavedTelegramIds([{ chat_id: response.data.chat_id }]);
            }
        } catch (error) {
            // Silent fail - will show "not configured" state
        }
    }, []);

    // Load all saved API keys
    const loadSavedApiKeys = useCallback(async () => {
        try {
            const response = await api.get('/api-keys');
            setSavedApiKeys(response.data.keys || []);
        } catch (error) {
            // Silent fail
        }
    }, []);

    // Use SWR for caching exchanges and user info (rarely changes)
    const { data: exchangesData, isLoading: exchangesLoading } = useStaticData('/exchanges');
    const { data: userInfoData, isLoading: userInfoLoading, mutate: mutateUserInfo } = useStaticData('/auth/me');

    // Set state from SWR data
    React.useEffect(() => {
        if (exchangesData?.exchanges) {
            setExchanges(exchangesData.exchanges);
        } else if (exchangesData === undefined && !exchangesLoading) {
            // Fallback if API fails
            setExchanges(DEFAULT_EXCHANGES);
        }
    }, [exchangesData, exchangesLoading]);

    React.useEffect(() => {
        if (userInfoData) {
            setUserInfo(userInfoData);
        }
    }, [userInfoData]);

    // Load preferences 
    const loadPreferences = useCallback(async () => {
        try {
            const response = await api.get('/preferences');
            const prefs = response.data.preferences;
            setTheme(prefs.theme || 'dark');
            if (prefs.widgets_enabled) {
                setWidgetsEnabled(prefs.widgets_enabled);
            }
        } catch (error) {
            // Silent fail - use defaults
        }
    }, []);

    const loadRiskProfile = useCallback(async () => {
        try {
            const response = await api.get('/risk-profile');
            if (response.data.profile) {
                setRiskProfile(response.data.profile);
            }
        } catch (error) {
            // Silent fail
        }
    }, []);

    useEffect(() => {
        checkApiKeyStatus();
        checkTelegramStatus();
        loadPreferences();
        loadRiskProfile();
        loadSavedApiKeys();
    }, [exchange, checkApiKeyStatus, checkTelegramStatus, loadPreferences, loadRiskProfile, loadSavedApiKeys]);

    const handleSaveKeys = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post('/api-keys', {
                exchange,
                api_key: apiKey,
                api_secret: apiSecret
            });
            toast.success('API keys saved successfully!');
            setApiKey('');
            setApiSecret('');
            checkApiKeyStatus();
            loadSavedApiKeys(); // Refresh the saved APIs table
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to save API keys');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteKeys = () => {
        modal.confirm({
            title: 'Delete API Keys',
            message: 'Are you sure you want to delete your API keys? This action cannot be undone.',
            confirmText: 'Delete',
            cancelText: 'Cancel',
            type: 'danger',
            onConfirm: async () => {
                setLoading(true);
                try {
                    await api.delete(`/api-keys/${exchange}`);
                    toast.success('API keys deleted successfully!');
                    setHasKey(false);
                } catch (error) {
                    toast.error(error.response?.data?.detail || 'Failed to delete API keys');
                } finally {
                    setLoading(false);
                }
            }
        });
    };

    const handleTelegramSave = async (e) => {
        e.preventDefault();
        setTelegramLoading(true);
        try {
            await api.post('/user/telegram', { chat_id: telegramChatId });
            toast.success('Telegram settings saved successfully!');
            setTelegramChatId('');
            checkTelegramStatus();
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to save Telegram settings');
        } finally {
            setTelegramLoading(false);
        }
    };

    // Save preferences
    const handleSavePreferences = async () => {
        setPrefsLoading(true);
        try {
            await api.put('/preferences', {
                theme,
                widgets_enabled: widgetsEnabled
            });
            toast.success('Preferences saved successfully');
        } catch (error) {
            toast.error('Failed to save preferences');
        } finally {
            setPrefsLoading(false);
        }
    };

    const handleSaveRiskProfile = async (e) => {
        e.preventDefault();
        setRiskLoading(true);
        try {
            await api.put('/risk-profile', riskProfile);
            toast.success('Risk profile saved successfully');
        } catch (error) {
            toast.error('Failed to save risk profile');
        } finally {
            setRiskLoading(false);
        }
    };

    const toggleWidget = (widget) => {
        setWidgetsEnabled(prev =>
            prev.includes(widget)
                ? prev.filter(w => w !== widget)
                : [...prev, widget]
        );
    };

    const handleTelegramDelete = () => {
        modal.confirm({
            title: 'Remove Telegram Notifications',
            message: 'Are you sure you want to remove Telegram notifications? You can always set them up again later.',
            confirmText: 'Remove',
            cancelText: 'Cancel',
            type: 'danger',
            onConfirm: async () => {
                setTelegramLoading(true);
                try {
                    await api.post('/user/telegram', { chat_id: null });
                    toast.success('Telegram settings removed successfully!');
                    setHasTelegram(false);
                } catch (error) {
                    toast.error(error.response?.data?.detail || 'Failed to remove Telegram settings');
                } finally {
                    setTelegramLoading(false);
                }
            }
        });
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'trading', label: 'Trading', icon: Key },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'risk', label: 'Risk Management', icon: AlertTriangle },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    <EditableText
                        configPath="pages.settings.pageTitle"
                        defaultValue="Settings"
                    />
                </h1>
                <p className="text-muted-foreground mt-1">
                    <EditableText
                        configPath="pages.settings.subtitle"
                        defaultValue="Manage your account, trading keys, and preferences"
                    />
                </p>
            </div>

            <div className="flex flex-col md:flex-row gap-8">
                {/* Sidebar Navigation */}
                <div className="w-full md:w-64 flex-shrink-0">
                    <div className="glass rounded-xl p-2 space-y-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                                    ? 'bg-primary text-white shadow-lg shadow-primary/25'
                                    : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
                                    }`}
                            >
                                <tab.icon size={18} />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 space-y-6">
                    {/* Profile Tab */}
                    {activeTab === 'profile' && (
                        <div className="space-y-6">
                            <div className="glass rounded-xl p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <User size={20} className="text-primary" />
                                    Account Information
                                </h3>

                                {userInfoLoading ? (
                                    <div className="animate-pulse space-y-4">
                                        <div className="h-12 bg-white/5 rounded-lg w-full"></div>
                                        <div className="h-12 bg-white/5 rounded-lg w-full"></div>
                                    </div>
                                ) : (
                                    <div className="grid gap-4">
                                        <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl">
                                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Account Number</label>
                                            <div className="flex items-center justify-between mt-1">
                                                <span className="text-xl font-mono font-bold text-primary">{userInfo?.id}</span>
                                                <button
                                                    onClick={() => {
                                                        navigator.clipboard.writeText(userInfo?.id);
                                                        toast.success('Copied to clipboard');
                                                    }}
                                                    className="p-2 hover:bg-primary/10 rounded-lg text-primary transition-colors"
                                                >
                                                    <Copy size={16} />
                                                </button>
                                            </div>
                                        </div>

                                        <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email Address</label>
                                            <div className="text-lg font-medium mt-1">{userInfo?.email}</div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="glass rounded-xl p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Shield size={20} className="text-primary" />
                                    Security
                                </h3>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                                        <div>
                                            <div className="font-medium">Active Sessions</div>
                                            <div className="text-sm text-muted-foreground">Manage devices logged into your account</div>
                                        </div>
                                        <button className="px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                                            <LogOut size={16} />
                                            Logout All
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Danger Zone */}
                            <div className="glass rounded-xl p-6 border border-red-500/20">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-400">
                                    <AlertTriangle size={20} />
                                    Danger Zone
                                </h3>
                                <div className="flex items-center justify-between p-4 bg-red-500/5 rounded-xl">
                                    <div>
                                        <div className="font-medium text-red-400">Delete Account</div>
                                        <div className="text-sm text-muted-foreground">
                                            Permanently delete your account and all data. This cannot be undone.
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => {
                                            modal.confirm({
                                                title: '⚠️ Delete Account',
                                                message: 'This will permanently delete your account including all bot configurations, API keys, trade history, and settings. This action is IRREVERSIBLE. Are you absolutely sure?',
                                                confirmText: 'Delete My Account',
                                                cancelText: 'Cancel',
                                                type: 'danger',
                                                onConfirm: async () => {
                                                    try {
                                                        await api.delete('/auth/account');
                                                        toast.success('Account deleted');
                                                        localStorage.removeItem('token');
                                                        window.location.href = '/';
                                                    } catch (error) {
                                                        toast.error(error.response?.data?.detail || 'Failed to delete account');
                                                    }
                                                }
                                            });
                                        }}
                                        className="px-4 py-2 bg-red-500 text-white hover:bg-red-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                                    >
                                        <Trash2 size={16} />
                                        Delete Account
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Trading Tab */}
                    {activeTab === 'trading' && (
                        <div className="space-y-6">
                            {/* Connected Exchanges Section */}
                            <div className="glass rounded-xl p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Key size={20} className="text-primary" />
                                    Connected Exchanges
                                </h3>

                                {savedApiKeys.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground bg-white/5 rounded-xl border border-dashed border-white/10">
                                        <div className="flex justify-center mb-3">
                                            <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center">
                                                <Key size={24} className="opacity-50" />
                                            </div>
                                        </div>
                                        <p>No exchanges connected yet.</p>
                                        <p className="text-xs mt-1">Connect an exchange below to start trading.</p>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {savedApiKeys.map((apiEntry) => (
                                            <div key={apiEntry.exchange} className="p-4 bg-white/5 border border-white/10 rounded-xl relative group hover:border-primary/30 transition-all">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                                                            {apiEntry.exchange.charAt(0).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <h4 className="font-semibold capitalize text-foreground">{apiEntry.exchange}</h4>
                                                            <span className="flex items-center gap-1 text-[10px] text-green-400 font-medium bg-green-500/10 px-1.5 py-0.5 rounded w-fit">
                                                                <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                                                                Active
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => {
                                                            modal.confirm({
                                                                title: 'Disconnect Exchange',
                                                                message: `Are you sure you want to delete API keys for ${apiEntry.exchange}? This will stop any active bots on this exchange.`,
                                                                confirmText: 'Disconnect',
                                                                type: 'danger',
                                                                onConfirm: async () => {
                                                                    try {
                                                                        await api.delete(`/api-keys/${apiEntry.exchange}`);
                                                                        toast.success('Exchange disconnected');
                                                                        loadSavedApiKeys();
                                                                    } catch (e) {
                                                                        toast.error('Failed to disconnect');
                                                                    }
                                                                }
                                                            });
                                                        }}
                                                        className="p-2 hover:bg-red-500/10 text-muted-foreground hover:text-red-400 rounded-lg transition-colors"
                                                        title="Disconnect"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>

                                                <div className="space-y-1">
                                                    <label className="text-xs text-muted-foreground">API Key</label>
                                                    <div className="font-mono text-sm bg-black/20 px-3 py-2 rounded-lg text-gray-300 border border-white/5 flex items-center justify-between">
                                                        {apiEntry.api_key_masked}
                                                        <Key size={12} className="opacity-30" />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Connect New Exchange Section */}
                            <div className="glass rounded-xl p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm font-bold">
                                        <Plus size={16} />
                                    </div>
                                    Connect New Exchange
                                </h3>

                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-muted-foreground mb-3">Select Exchange</label>
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                        {exchanges.map((ex) => {
                                            const isConnected = savedApiKeys.some(k => k.exchange === ex.name);
                                            return (
                                                <button
                                                    key={ex.name}
                                                    onClick={() => {
                                                        setExchange(ex.name);
                                                        setApiKey('');
                                                        setApiSecret('');
                                                    }}
                                                    disabled={isConnected}
                                                    className={`p-3 rounded-xl border transition-all relative text-left ${exchange === ex.name
                                                        ? 'bg-primary/10 border-primary text-foreground ring-1 ring-primary'
                                                        : isConnected
                                                            ? 'bg-white/5 border-white/5 text-muted-foreground opacity-50 cursor-not-allowed'
                                                            : 'bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10 hover:border-white/20'
                                                        }`}
                                                >
                                                    <div className="font-bold text-sm mb-1">{ex.display_name}</div>
                                                    {isConnected ? (
                                                        <div className="text-[10px] text-green-400 flex items-center gap-1">
                                                            <CheckCircle size={10} /> Connected
                                                        </div>
                                                    ) : (
                                                        ex.supports_demo && (
                                                            <div className="text-[10px] text-primary/70">Supports Testnet</div>
                                                        )
                                                    )}

                                                    {exchange === ex.name && !isConnected && (
                                                        <div className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full shadow-[0_0_8px_rgba(139,92,246,0.6)]"></div>
                                                    )}
                                                </button>
                                            )
                                        })}
                                    </div>
                                </div>

                                <form onSubmit={handleSaveKeys} className="space-y-4 max-w-2xl">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-muted-foreground mb-1">API Key</label>
                                            <input
                                                type="text"
                                                value={apiKey}
                                                onChange={(e) => setApiKey(e.target.value)}
                                                className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                                placeholder="Paste API Key"
                                                required
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-muted-foreground mb-1">API Secret</label>
                                            <input
                                                type="password"
                                                value={apiSecret}
                                                onChange={(e) => setApiSecret(e.target.value)}
                                                className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                                placeholder="Paste API Secret"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4 pt-2">
                                        <button
                                            type="submit"
                                            disabled={loading}
                                            className="px-6 py-2.5 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50 shadow-lg shadow-primary/20"
                                        >
                                            <Save size={18} />
                                            {loading ? 'Saving...' : 'Save Keys'}
                                        </button>

                                        <div className="text-xs text-muted-foreground flex items-center gap-2 bg-yellow-500/5 px-3 py-2 rounded-lg border border-yellow-500/10">
                                            <Shield size={14} className="text-yellow-500" />
                                            Keys are encrypted at rest with AES-256
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}

                    {/* Notifications Tab */}
                    {activeTab === 'notifications' && (
                        <div className="glass rounded-xl p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Bell size={20} className="text-primary" />
                                Telegram Alerts
                            </h3>

                            <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl mb-6">
                                <h4 className="text-sm font-semibold text-blue-400 mb-2">How to Setup</h4>
                                <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                                    <li>Search for <strong className="text-foreground">@userinfobot</strong> in Telegram</li>
                                    <li>Send any message to get your <strong className="text-foreground">Chat ID</strong></li>
                                    <li>Paste your Chat ID below and save</li>
                                </ol>
                            </div>

                            {hasTelegram && (
                                <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-2 text-green-400 text-sm font-medium">
                                    <CheckCircle size={16} />
                                    Telegram notifications active
                                </div>
                            )}

                            <form onSubmit={handleTelegramSave} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">Chat ID</label>
                                    <input
                                        type="text"
                                        value={telegramChatId}
                                        onChange={(e) => setTelegramChatId(e.target.value)}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                        placeholder="123456789"
                                        required
                                    />
                                </div>

                                <div className="flex gap-3 pt-2">
                                    <button
                                        type="submit"
                                        disabled={telegramLoading}
                                        className="flex-1 bg-primary hover:bg-primary/90 text-white py-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                    >
                                        <Save size={18} />
                                        {telegramLoading ? 'Saving...' : hasTelegram ? 'Update Settings' : 'Enable Notifications'}
                                    </button>
                                    {hasTelegram && (
                                        <button
                                            type="button"
                                            onClick={handleTelegramDelete}
                                            disabled={telegramLoading}
                                            className="px-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </div>
                            </form>

                            {/* Saved Telegram Chat IDs */}
                            {savedTelegramIds.length > 0 && (
                                <div className="mt-6">
                                    <h4 className="text-md font-semibold text-foreground mb-4">Saved Notifications</h4>
                                    <div className="bg-white/5 rounded-xl overflow-hidden">
                                        <table className="w-full">
                                            <thead className="bg-white/5">
                                                <tr>
                                                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Chat ID</th>
                                                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                                                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/5">
                                                {savedTelegramIds.map((entry, idx) => (
                                                    <tr key={idx} className="hover:bg-white/5">
                                                        <td className="px-4 py-3 font-mono text-sm">{entry.chat_id}</td>
                                                        <td className="px-4 py-3">
                                                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs font-medium">
                                                                <CheckCircle size={12} />
                                                                Active
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3 text-right">
                                                            <button
                                                                onClick={handleTelegramDelete}
                                                                className="px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded text-xs font-medium"
                                                            >
                                                                Remove
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}



                    {/* Risk Management Tab */}
                    {activeTab === 'risk' && (
                        <div className="glass rounded-xl p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <AlertTriangle size={20} className="text-primary" />
                                Risk Management
                            </h3>

                            <div className="p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-xl mb-6">
                                <h4 className="text-sm font-semibold text-yellow-500 mb-2">Global Risk Limits</h4>
                                <p className="text-sm text-muted-foreground">
                                    These settings apply to all your active bots. If any limit is breached, the system can automatically stop trading to protect your capital.
                                </p>
                            </div>

                            <form onSubmit={handleSaveRiskProfile} className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-1">Max Daily Loss ($)</label>
                                        <input
                                            type="number"
                                            value={riskProfile.max_daily_loss || ''}
                                            onChange={(e) => setRiskProfile({ ...riskProfile, max_daily_loss: parseFloat(e.target.value) })}
                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 outline-none"
                                            placeholder="e.g. 100.00"
                                            step="0.01"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-1">Max Drawdown (%)</label>
                                        <input
                                            type="number"
                                            value={riskProfile.max_drawdown || ''}
                                            onChange={(e) => setRiskProfile({ ...riskProfile, max_drawdown: parseFloat(e.target.value) })}
                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 outline-none"
                                            placeholder="e.g. 5.0"
                                            step="0.1"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-1">Max Position Size ($)</label>
                                        <input
                                            type="number"
                                            value={riskProfile.max_position_size || ''}
                                            onChange={(e) => setRiskProfile({ ...riskProfile, max_position_size: parseFloat(e.target.value) })}
                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 outline-none"
                                            placeholder="e.g. 1000.00"
                                            step="0.01"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-muted-foreground mb-1">Max Open Positions</label>
                                        <input
                                            type="number"
                                            value={riskProfile.max_open_positions || ''}
                                            onChange={(e) => setRiskProfile({ ...riskProfile, max_open_positions: parseInt(e.target.value) })}
                                            className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 outline-none"
                                            placeholder="e.g. 3"
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                                    <div>
                                        <div className="font-medium">Stop Trading on Breach</div>
                                        <div className="text-sm text-muted-foreground">Automatically stop all bots if any limit is reached</div>
                                    </div>
                                    <div className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="sr-only peer"
                                            checked={riskProfile.stop_trading_on_breach}
                                            onChange={(e) => setRiskProfile({ ...riskProfile, stop_trading_on_breach: e.target.checked })}
                                        />
                                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                    </div>
                                </div>

                                <div className="flex justify-end pt-2">
                                    <button
                                        type="submit"
                                        disabled={riskLoading}
                                        className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50"
                                    >
                                        <Save size={18} />
                                        {riskLoading ? 'Saving...' : 'Save Risk Profile'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* Preferences Tab */}
                    {activeTab === 'preferences' && (
                        <div className="glass rounded-xl p-6">
                            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <SettingsIcon size={20} className="text-primary" />
                                App Preferences
                            </h3>

                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                            {theme === 'dark' ? <Moon size={20} /> : <Sun size={20} />}
                                        </div>
                                        <div>
                                            <div className="font-medium">Theme</div>
                                            <div className="text-sm text-muted-foreground">Customize app appearance</div>
                                        </div>
                                    </div>
                                    <div className="flex bg-black/20 rounded-lg p-1">
                                        <button
                                            onClick={() => setTheme('light')}
                                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${theme === 'light' ? 'bg-white text-black shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                        >
                                            Light
                                        </button>
                                        <button
                                            onClick={() => setTheme('dark')}
                                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${theme === 'dark' ? 'bg-primary text-white shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                                        >
                                            Dark
                                        </button>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-green-500/10 rounded-lg text-green-500">
                                            <DollarSign size={20} />
                                        </div>
                                        <div>
                                            <div className="font-medium">Currency</div>
                                            <div className="text-sm text-muted-foreground">Display currency for PnL</div>
                                        </div>
                                    </div>
                                    <div className="relative">
                                        <select
                                            value={currency}
                                            onChange={(e) => setCurrency(e.target.value)}
                                            className="bg-black/20 border border-white/10 rounded-lg pl-3 pr-8 py-1.5 text-sm outline-none focus:border-primary/50 appearance-none cursor-pointer hover:bg-black/30 transition-all"
                                        >
                                            <option value="USD">USD ($)</option>
                                            <option value="EUR">EUR (€)</option>
                                            <option value="GBP">GBP (£)</option>
                                        </select>
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                            <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                                            <Globe size={20} />
                                        </div>
                                        <div>
                                            <div className="font-medium">Language</div>
                                            <div className="text-sm text-muted-foreground">Interface language</div>
                                        </div>
                                    </div>
                                    <div className="relative">
                                        <select
                                            className="bg-black/20 border border-white/10 rounded-lg pl-3 pr-8 py-1.5 text-sm outline-none focus:border-primary/50 appearance-none cursor-pointer hover:bg-black/30 transition-all"
                                            defaultValue="en"
                                        >
                                            <option value="en">English</option>
                                            <option value="es">Español</option>
                                            <option value="fr">Français</option>
                                        </select>
                                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                            <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </div>
                                </div>


                                <div className="p-4 bg-white/5 rounded-xl">
                                    <h4 className="font-medium mb-4">Dashboard Widgets</h4>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        {[
                                            { id: 'balance', label: 'Portfolio Balance' },
                                            { id: 'status', label: 'Bot Status' },
                                            { id: 'trades', label: 'Recent Trades' },
                                            { id: 'bots', label: 'Active Bots' },
                                            { id: 'watchlist', label: 'Watchlist' },
                                            { id: 'alerts', label: 'Price Alerts' }
                                        ].map(widget => (
                                            <label key={widget.id} className="flex items-center justify-between p-3 bg-black/20 rounded-lg cursor-pointer hover:bg-black/30 transition-all">
                                                <span className="text-sm font-medium">{widget.label}</span>
                                                <div className="relative inline-flex items-center cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        className="sr-only peer"
                                                        checked={widgetsEnabled.includes(widget.id)}
                                                        onChange={() => toggleWidget(widget.id)}
                                                    />
                                                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex justify-end pt-4">
                                    <button
                                        onClick={handleSavePreferences}
                                        disabled={prefsLoading}
                                        className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 disabled:opacity-50"
                                    >
                                        <Save size={18} />
                                        {prefsLoading ? 'Saving...' : 'Save Preferences'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
