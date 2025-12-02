// Default exchange configurations
// Used as fallback when API fails to load exchanges

export const DEFAULT_EXCHANGES = [
    { name: 'bybit', display_name: 'ByBit', supports_demo: true },
    { name: 'binance', display_name: 'Binance', supports_demo: true },
    { name: 'kraken', display_name: 'Kraken', supports_demo: true },
    { name: 'okx', display_name: 'OKX', supports_demo: true },
    { name: 'coinbase', display_name: 'Coinbase', supports_demo: false }
];

// Helper function to format exchange display name
export const formatExchangeName = (exchangeName) => {
    const exchange = DEFAULT_EXCHANGES.find(e => e.name === exchangeName);
    return exchange?.display_name || exchangeName.charAt(0).toUpperCase() + exchangeName.slice(1);
};
