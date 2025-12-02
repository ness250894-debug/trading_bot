import { useState, useEffect } from 'react';

/**
 * Custom hook to fetch and manage top cryptocurrency prices from CoinGecko API
 * Updates every 60 seconds to stay within free tier rate limits (30 calls/min)
 */
export const useTokenPrices = () => {
    const [tokens, setTokens] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchTokenPrices = async () => {
            try {
                const response = await fetch(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=10&page=1&sparkline=false&price_change_percentage=24h'
                );

                if (!response.ok) {
                    throw new Error('Failed to fetch token prices');
                }

                const data = await response.json();

                const formattedTokens = data.map(coin => ({
                    symbol: coin.symbol.toUpperCase(),
                    name: coin.name,
                    price: coin.current_price,
                    change24h: coin.price_change_percentage_24h || 0,
                    image: coin.image
                }));

                setTokens(formattedTokens);
                setError(null);
            } catch (err) {
                console.error('Error fetching token prices:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        // Initial fetch
        fetchTokenPrices();

        // Refresh every 60 seconds (within free tier limits)
        const interval = setInterval(fetchTokenPrices, 60000);

        return () => clearInterval(interval);
    }, []);

    return { tokens, loading, error };
};
