-- Add Supported Symbols Table
CREATE TABLE IF NOT EXISTS supported_symbols (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL DEFAULT 'bybit',
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange)
);
CREATE SEQUENCE IF NOT EXISTS seq_supported_symbol_id START 1;

CREATE INDEX IF NOT EXISTS idx_supported_symbols_lookup ON supported_symbols(symbol, exchange, is_active);
