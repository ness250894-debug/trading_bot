import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import ExchangeLinks from './ExchangeLinks';

export default function Header({ onLoginClick, onSignupClick }) {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16 gap-4">
                    <Link to="/" className="flex items-center gap-2 flex-shrink-0">
                        <TrendingUp className="w-8 h-8 text-primary" />
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                            TradingBot
                        </span>
                    </Link>

                    {/* Exchange Links with Live Prices */}
                    <ExchangeLinks />

                    <div className="flex items-center gap-4 flex-shrink-0">
                        <Link
                            to="/pricing"
                            className="text-muted-foreground hover:text-foreground transition-colors hidden sm:block"
                        >
                            Pricing
                        </Link>
                        <button
                            onClick={onLoginClick}
                            className="text-muted-foreground hover:text-foreground transition-colors"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={onSignupClick}
                            className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-primary/25"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}
