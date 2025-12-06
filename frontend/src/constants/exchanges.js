// Default exchange configurations
// Used as fallback when API fails to load exchanges

export const DEFAULT_EXCHANGES = [
    { name: 'bybit', display_name: 'ByBit' },
    { name: 'binance', display_name: 'Binance' },
    { name: 'kraken', display_name: 'Kraken' },
    { name: 'okx', display_name: 'OKX' },
    { name: 'coinbase', display_name: 'Coinbase' }
];

// Helper function to format exchange display name
export const formatExchangeName = (exchangeName) => {
    const exchange = DEFAULT_EXCHANGES.find(e => e.name === exchangeName);
    return exchange?.display_name || exchangeName.charAt(0).toUpperCase() + exchangeName.slice(1);
};
