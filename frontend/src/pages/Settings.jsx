import React, { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import Disclaimer from '../components/Disclaimer';
import {
    User, Key, Bell, Settings as SettingsIcon, Shield,
    LogOut, Moon, Sun, DollarSign, Globe, CheckCircle,
    AlertTriangle, Trash2, Save, Copy
} from 'lucide-react';
import { useToast } from '../components/ToastContext';
import { DEFAULT_EXCHANGES } from '../constants/exchanges';

export default function Settings() {
    const [activeTab, setActiveTab] = useState('profile');
    const toast = useToast();

    // API Keys state
    const [apiKey, setApiKey] = useState('');
    const [apiSecret, setApiSecret] = useState('');
    const [exchange, setExchange] = useState('bybit');
    const [hasKey, setHasKey] = useState(false);
    const [loading, setLoading] = useState(false);
    const [exchanges, setExchanges] = useState([]);
    const [exchangesLoading, setExchangesLoading] = useState(true);

    // Telegram settings state
    const [telegramChatId, setTelegramChatId] = useState('');
    const [hasTelegram, setHasTelegram] = useState(false);
    const [telegramLoading, setTelegramLoading] = useState(false);

    // User info state
    const [userInfo, setUserInfo] = useState(null);
    const [userInfoLoading, setUserInfoLoading] = useState(true);

    // Preferences state
    const [theme, setTheme] = useState('dark');
    const [currency, setCurrency] = useState('USD');

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
        } catch (error) {
            // Silent fail - will show "not configured" state
        }
    }, []);

    const fetchExchanges = useCallback(async () => {
        setExchangesLoading(true);
        try {
            const response = await api.get('/exchanges');
            setExchanges(response.data.exchanges || []);
        } catch (error) {
            setExchanges(DEFAULT_EXCHANGES);
        } finally {
            setExchangesLoading(false);
        }
    }, []);

    const fetchUserInfo = useCallback(async () => {
        setUserInfoLoading(true);
        try {
            const response = await api.get('/auth/me');
            setUserInfo(response.data);
        } catch (error) {
            // Silent fail - non-critical
        } finally {
            setUserInfoLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchExchanges();
        fetchUserInfo();
        checkApiKeyStatus();
        checkTelegramStatus();
    }, [exchange, fetchExchanges, fetchUserInfo, checkApiKeyStatus, checkTelegramStatus]);

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
        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to save API keys');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteKeys = async () => {
        if (!confirm('Are you sure you want to delete your API keys?')) return;
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

    const handleTelegramDelete = async () => {
        if (!confirm('Are you sure you want to remove Telegram notifications?')) return;
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
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'trading', label: 'Trading', icon: Key },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'preferences', label: 'Preferences', icon: SettingsIcon },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                    Settings
                </h1>
                <p className="text-muted-foreground mt-1">Manage your account, trading keys, and preferences</p>
            </div>

            <Disclaimer compact />

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
                        </div>
                    )}

                    {/* Trading Tab */}
                    {activeTab === 'trading' && (
                        <div className="glass rounded-xl p-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Key size={20} className="text-primary" />
                                API Configuration
                            </h3>

                            <div className="mb-6">
                                <label className="block text-sm font-medium text-muted-foreground mb-3">Select Exchange</label>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                    {exchanges.map((ex) => (
                                        <button
                                            key={ex.name}
                                            onClick={() => setExchange(ex.name)}
                                            className={`p-4 rounded-xl border transition-all relative ${exchange === ex.name
                                                ? 'bg-primary/10 border-primary text-foreground'
                                                : 'bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10'
                                                }`}
                                        >
                                            <div className="font-bold text-sm">{ex.display_name}</div>
                                            {exchange === ex.name && (
                                                <div className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full shadow-[0_0_8px_rgba(139,92,246,0.6)]"></div>
                                            )}
                                            {ex.supports_demo && (
                                                <div className="text-[10px] text-primary mt-1 font-medium">Testnet</div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {hasKey && (
                                <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-2 text-green-400 text-sm font-medium">
                                    <CheckCircle size={16} />
                                    API keys configured for {exchanges.find(e => e.name === exchange)?.display_name || exchange}
                                </div>
                            )}

                            <form onSubmit={handleSaveKeys} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-muted-foreground mb-1">API Key</label>
                                    <input
                                        type="text"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-2.5 focus:border-primary/50 focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                                        placeholder="Enter your API key"
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
                                        placeholder="Enter your API secret"
                                        required
                                    />
                                </div>

                                <div className="flex gap-3 pt-2">
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="flex-1 bg-primary hover:bg-primary/90 text-white py-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                    >
                                        <Save size={18} />
                                        {loading ? 'Saving...' : hasKey ? 'Update Keys' : 'Save Keys'}
                                    </button>
                                    {hasKey && (
                                        <button
                                            type="button"
                                            onClick={handleDeleteKeys}
                                            disabled={loading}
                                            className="px-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </div>
                            </form>

                            <div className="mt-6 p-4 bg-yellow-500/5 border border-yellow-500/10 rounded-xl">
                                <h4 className="text-sm font-semibold text-yellow-500 mb-2 flex items-center gap-2">
                                    <AlertTriangle size={16} />
                                    Security Note
                                </h4>
                                <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
                                    <li>Never share your API keys with anyone</li>
                                    <li>Enable IP whitelist restrictions on your exchange</li>
                                    <li>Only grant trading permissions (no withdrawals)</li>
                                </ul>
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
                                    <select
                                        value={currency}
                                        onChange={(e) => setCurrency(e.target.value)}
                                        className="bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-primary/50"
                                    >
                                        <option value="USD">USD ($)</option>
                                        <option value="EUR">EUR (€)</option>
                                        <option value="GBP">GBP (£)</option>
                                    </select>
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
                                    <select
                                        className="bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-primary/50"
                                        defaultValue="en"
                                    >
                                        <option value="en">English</option>
                                        <option value="es">Español</option>
                                        <option value="fr">Français</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
