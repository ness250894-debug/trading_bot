import { useState, useEffect } from 'react';
import api from '../lib/api';
import styles from './Settings.module.css';

export default function Settings() {
    const [apiKey, setApiKey] = useState('');
    const [apiSecret, setApiSecret] = useState('');
    const [exchange, setExchange] = useState('bybit');
    const [hasKey, setHasKey] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState(''); // 'success' or 'error'

    useEffect(() => {
        checkApiKeyStatus();
    }, [exchange]);

    const checkApiKeyStatus = async () => {
        try {
            const response = await api.get(`/api-keys/${exchange}`);
            setHasKey(response.data.has_key);
        } catch (error) {
            console.error('Error checking API key status:', error);
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

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Settings</h1>

            <div className={styles.section}>
                <h2>API Keys</h2>
                <p className={styles.description}>
                    Configure your exchange API keys to enable live trading. Your keys are encrypted and securely stored.
                </p>

                <div className={styles.form}>
                    <div className={styles.formGroup}>
                        <label htmlFor="exchange">Exchange</label>
                        <select
                            id="exchange"
                            value={exchange}
                            onChange={(e) => setExchange(e.target.value)}
                            className={styles.select}
                        >
                            <option value="bybit">ByBit</option>
                            <option value="binance">Binance</option>
                            <option value="okx">OKX</option>
                            <option value="kraken">Kraken</option>
                            <option value="coinbase">Coinbase</option>
                        </select>
                    </div>

                    {hasKey && (
                        <div className={styles.status}>
                            <span className={styles.statusIndicator}>✓</span>
                            API keys configured for {exchange}
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
        </div>
    );
}
