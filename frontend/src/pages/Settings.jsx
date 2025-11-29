import { useState, useEffect } from 'react';
import api from '../lib/api';
import styles from './Settings.module.css';

export default function Settings() {
    // API Keys state
    const [apiKey, setApiKey] = useState('');
    const [apiSecret, setApiSecret] = useState('');
    const [exchange, setExchange] = useState('bybit');
    const [hasKey, setHasKey] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState('');
    const [exchanges, setExchanges] = useState([]);
    const [exchangesLoading, setExchangesLoading] = useState(true);

    // Telegram settings state
    const [telegramChatId, setTelegramChatId] = useState('');
    const [hasTelegram, setHasTelegram] = useState(false);
    const [telegramLoading, setTelegramLoading] = useState(false);
    const [telegramMessage, setTelegramMessage] = useState('');
    const [telegramMessageType, setTelegramMessageType] = useState('');

    const fetchExchanges = async () => {
        setExchangesLoading(true);
        try {
            const response = await api.get('/exchanges');
            setExchanges(response.data.exchanges || []);
        } catch (error) {
            console.error('Failed to load exchanges:', error);
            // Default exchanges if API fails
            setExchanges([
                { name: 'bybit', display_name: 'ByBit', supports_demo: true },
                { name: 'binance', display_name: 'Binance', supports_demo: true },
                { name: 'kraken', display_name: 'Kraken', supports_demo: true },
                { name: 'okx', display_name: 'OKX', supports_demo: true },
                { name: 'coinbase', display_name: 'Coinbase', supports_demo: false }
            ]);
        } finally {
            setExchangesLoading(false);
        }
    };

    useEffect(() => {
        fetchExchanges();
        checkApiKeyStatus();
        checkTelegramStatus();
    }, [exchange]);

    const checkApiKeyStatus = async () => {
        try {
            const response = await api.get(`/api-keys/${exchange}`);
            setHasKey(response.data.has_key);
        } catch (error) {
            console.error('Error checking API key status:', error);
        }
    };

    const checkTelegramStatus = async () => {
        try {
            const response = await api.get('/user/telegram');
            setHasTelegram(response.data.has_telegram);
        } catch (error) {
            console.error('Error checking Telegram status:', error);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        try {
            await api.post('/api-keys', {
                exchange,
                api_key: apiKey,
                api_secret: apiSecret
            });

            setMessage('API keys saved successfully!');
            setMessageType('success');
            setApiKey('');
            setApiSecret('');
            checkApiKeyStatus();
        } catch (error) {
            setMessage(error.response?.data?.detail || 'Failed to save API keys');
            setMessageType('error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete your API keys?')) {
            return;
        }

        setLoading(true);
        setMessage('');

        try {
            await api.delete(`/api-keys/${exchange}`);
            setMessage('API keys deleted successfully!');
            setMessageType('success');
            setHasKey(false);
        } catch (error) {
            setMessage(error.response?.data?.detail || 'Failed to delete API keys');
            setMessageType('error');
        } finally {
            setLoading(false);
        }
    };

    const handleTelegramSave = async (e) => {
        e.preventDefault();
        setTelegramLoading(true);
        setTelegramMessage('');

        try {
            await api.post('/user/telegram', {
                chat_id: telegramChatId
            });

            setTelegramMessage('Telegram settings saved successfully!');
            setTelegramMessageType('success');
            setTelegramChatId('');
            checkTelegramStatus();
        } catch (error) {
            setTelegramMessage(error.response?.data?.detail || 'Failed to save Telegram settings');
            setTelegramMessageType('error');
        } finally {
            setTelegramLoading(false);
        }
    };

    const handleTelegramDelete = async () => {
        if (!confirm('Are you sure you want to remove Telegram notifications?')) {
            return;
        }

        setTelegramLoading(true);
        setTelegramMessage('');

        try {
            await api.post('/user/telegram', {
                chat_id: null
            });
            setTelegramMessage('Telegram settings removed successfully!');
            setTelegramMessageType('success');
            setHasTelegram(false);
        } catch (error) {
            setTelegramMessage(error.response?.data?.detail || 'Failed to remove Telegram settings');
            setTelegramMessageType('error');
        } finally {
            setTelegramLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Settings</h1>

            {/* API Keys Section */}
            <div className={styles.section}>
                <h2>API Keys</h2>
                <p className={styles.description}>
                    Configure your exchange API keys to enable live trading. Your keys are encrypted and securely stored.
                </p>

                <div className={styles.form}>
                    {/* Modern Exchange Selector */}
                    <div className={styles.formGroup} style={{ marginBottom: '2rem' }}>
                        <label style={{ marginBottom: '1rem', display: 'block', fontSize: '14px', fontWeight: '600', color: '#9ca3af' }}>SELECT EXCHANGE</label>

                        {exchangesLoading ? (
                            <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>Loading exchanges...</div>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px' }}>
                                {exchanges.map((ex) => {
                                    const isActive = exchange === ex.name;
                                    return (
                                        <div
                                            key={ex.name}
                                            onClick={() => setExchange(ex.name)}
                                            style={{
                                                cursor: 'pointer',
                                                padding: '16px',
                                                borderRadius: '12px',
                                                border: isActive ? '2px solid #8b5cf6' : '2px solid rgba(255, 255, 255, 0.1)',
                                                backgroundColor: isActive ? 'rgba(139, 92, 246, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                                                transition: 'all 0.3s',
                                                position: 'relative'
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '700', color: isActive ? '#fff' : '#9ca3af' }}>
                                                    {ex.display_name}
                                                </h4>
                                                {isActive && (
                                                    <div style={{
                                                        width: '8px',
                                                        height: '8px',
                                                        borderRadius: '50%',
                                                        backgroundColor: '#8b5cf6',
                                                        boxShadow: '0 0 10px rgba(139, 92, 246, 0.6)'
                                                    }} />
                                                )}
                                            </div>
                                            {ex.supports_demo && (
                                                <div style={{ fontSize: '10px', color: '#8b5cf6', fontWeight: '500' }}>• Testnet</div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {hasKey && (
                        <div className={styles.status}>
                            <span className={styles.statusIndicator}>✓</span>
                            API keys configured for {exchanges.find(e => e.name === exchange)?.display_name || exchange}
                        </div>
                    )}

                    <form onSubmit={handleSave}>
                        <div className={styles.formGroup}>
                            <label htmlFor="apiKey">API Key</label>
                            <input
                                id="apiKey"
                                type="text"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter your API key"
                                className={styles.input}
                                required
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="apiSecret">API Secret</label>
                            <input
                                id="apiSecret"
                                type="password"
                                value={apiSecret}
                                onChange={(e) => setApiSecret(e.target.value)}
                                placeholder="Enter your API secret"
                                className={styles.input}
                                required
                            />
                        </div>

                        {message && (
                            <div className={`${styles.message} ${styles[messageType]}`}>
                                {message}
                            </div>
                        )}

                        <div className={styles.actions}>
                            <button
                                type="submit"
                                className={styles.btnPrimary}
                                disabled={loading}
                            >
                                {loading ? 'Saving...' : hasKey ? 'Update API Keys' : 'Save API Keys'}
                            </button>

                            {hasKey && (
                                <button
                                    type="button"
                                    onClick={handleDelete}
                                    className={styles.btnDanger}
                                    disabled={loading}
                                >
                                    Delete API Keys
                                </button>
                            )}
                        </div>
                    </form>
                </div>

                <div className={styles.info}>
                    <h3>⚠️ Important Security Notes:</h3>
                    <ul>
                        <li>Never share your API keys with anyone</li>
                        <li>Enable IP whitelist restrictions on your exchange account</li>
                        <li>Only grant necessary permissions (trading, reading account info)</li>
                        <li>Do not enable withdrawal permissions</li>
                        <li>Keys are encrypted using AES-256 before storage</li>
                    </ul>
                </div>
            </div>

            {/* Telegram Notifications Section */}
            <div className={styles.section}>
                <h2>📱 Telegram Notifications</h2>
                <p className={styles.description}>
                    Get real-time trading alerts and bot status updates via Telegram.
                </p>

                <div className={styles.form}>
                    {hasTelegram && (
                        <div className={styles.status}>
                            <span className={styles.statusIndicator}>✓</span>
                            Telegram notifications configured
                        </div>
                    )}

                    <form onSubmit={handleTelegramSave}>
                        <div className={styles.formGroup}>
                            <label htmlFor="chatId">Chat ID</label>
                            <input
                                id="chatId"
                                type="text"
                                value={telegramChatId}
                                onChange={(e) => setTelegramChatId(e.target.value)}
                                placeholder="123456789"
                                className={styles.input}
                                required
                            />
                        </div>

                        {telegramMessage && (
                            <div className={`${styles.message} ${styles[telegramMessageType]}`}>
                                {telegramMessage}
                            </div>
                        )}

                        <div className={styles.actions}>
                            <button
                                type="submit"
                                className={styles.btnPrimary}
                                disabled={telegramLoading}
                            >
                                {telegramLoading ? 'Saving...' : hasTelegram ? 'Update Telegram Settings' : 'Save Telegram Settings'}
                            </button>

                            {hasTelegram && (
                                <button
                                    type="button"
                                    onClick={handleTelegramDelete}
                                    className={styles.btnDanger}
                                    disabled={telegramLoading}
                                >
                                    Remove Telegram
                                </button>
                            )}
                        </div>
                    </form>
                </div>

                <div className={styles.info}>
                    <h3>📖 How to Set Up:</h3>
                    <ol>
                        <li>Search for <strong>@userinfobot</strong> in Telegram</li>
                        <li>Send any message to get your <strong>Chat ID</strong></li>
                        <li>Paste your Chat ID above and save</li>
                        <li>Make sure you have started a chat with our bot!</li>
                    </ol>
                </div>
            </div>
        </div>
    );
}
