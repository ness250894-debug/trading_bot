import React, { useState, useEffect } from 'react';
import { ExternalLink } from 'lucide-react';
import { useTokenPrices } from '../hooks/useTokenPrices';

// Exchange configuration with branding - ALL 5 EXCHANGES
const EXCHANGES = [
    {
        name: 'Binance',
        url: 'https://www.binance.com/activity/referral-entry/CPA?ref=CPA_00UQ3VVI77',
        colors: {
            bg: 'bg-black',
            text: 'text-[#F3BA2F]',
            border: 'border-[#F3BA2F]/30',
            hover: 'hover:border-[#F3BA2F]/60'
        }
    },
    {
        name: 'Bybit',
        url: 'https://www.bybit.com/invite?ref=QONQNG',
        colors: {
            bg: 'bg-[#1C1C28]',
            text: 'text-[#F7A600]',
            border: 'border-[#F7A600]/30',
            hover: 'hover:border-[#F7A600]/60'
        }
    },
    {
        name: 'OKX',
        url: 'https://okx.com/join/66004268',
        colors: {
            bg: 'bg-black',
            text: 'text-blue-400',
            border: 'border-blue-400/30',
            hover: 'hover:border-blue-400/60'
        }
    },
    {
        name: 'Coinbase',
        url: 'https://www.coinbase.com/join/YOUR_COINBASE_REF_CODE',
        colors: {
            bg: 'bg-[#0052FF]',
            text: 'text-white',
            border: 'border-white/20',
            hover: 'hover:border-white/40'
        }
    },
    {
        name: 'Kraken',
        url: 'https://www.kraken.com/',
        colors: {
            bg: 'bg-[#5741D9]',
            text: 'text-white',
            border: 'border-white/20',
            hover: 'hover:border-white/40'
        }
    }
];

const ExchangeLink = ({ exchange, currentToken, showPrices }) => {
    const { name, url, colors } = exchange;

    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
                group flex flex-col items-center justify-center gap-0.5 px-2 py-1.5 rounded-lg border transition-all duration-300
                ${colors.bg} ${colors.border} ${colors.hover}
            `}
        >
            <div className="flex items-center gap-1">
                <span className={`text-[10px] font-bold ${colors.text}`}>{name}</span>
                <ExternalLink size={8} className={`${colors.text} opacity-60 group-hover:opacity-100 transition-opacity`} />
            </div>

            {showPrices && currentToken && (
                <div className="flex items-center gap-1 text-[9px]">
                    <span className="text-white/60 font-mono">{currentToken.symbol}</span>
                    <span className="text-white/90 font-mono font-semibold">
                        ${currentToken.price > 1000 ? currentToken.price.toLocaleString('en-US', { maximumFractionDigits: 0 }) : currentToken.price.toFixed(2)}
                    </span>
                    <span className={`font-mono font-medium ${currentToken.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {currentToken.change24h >= 0 ? '+' : ''}{currentToken.change24h.toFixed(1)}%
                    </span>
                </div>
            )}
        </a>
    );
};

export default function ExchangeLinks() {
    const { tokens, loading, error } = useTokenPrices();
    const [currentTokenIndex, setCurrentTokenIndex] = useState(0);

    // Rotate through tokens every 3 seconds
    useEffect(() => {
        if (!tokens || tokens.length === 0) return;

        const interval = setInterval(() => {
            setCurrentTokenIndex(prev => (prev + 1) % tokens.length);
        }, 3000);

        return () => clearInterval(interval);
    }, [tokens]);

    // Silently handle errors - don't break the page
    if (error) {
        console.error('Token price error:', error);
    }

    const currentToken = tokens && tokens.length > 0 ? tokens[currentTokenIndex] : null;
    const showPrices = !loading && !error && currentToken;

    return (
        <div className="hidden md:flex items-center gap-1.5">
            {EXCHANGES.map((exchange) => (
                <ExchangeLink
                    key={exchange.name}
                    exchange={exchange}
                    currentToken={currentToken}
                    showPrices={showPrices}
                />
            ))}
        </div>
    );
}
