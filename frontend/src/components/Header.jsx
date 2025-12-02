import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';

export default function Header({ onLoginClick, onSignupClick }) {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16 gap-2">
                    <Link to="/" className="flex items-center gap-2 flex-shrink-0">
                        <TrendingUp className="w-8 h-8 text-primary" />
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                            TradingBot
                        </span>
                    </Link>

                    <div className="flex items-center gap-3 flex-shrink-0">
                        <Link
                            to="/pricing"
                            className="text-muted-foreground hover:text-foreground transition-colors hidden sm:block text-sm"
                        >
                            Pricing
                        </Link>

                        {/* CTA */}
                        <div className="hidden lg:flex flex-col items-end">
                            <button
                                onClick={onLoginClick}
                                className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Sign In
                            </button>
                            <button
                                onClick={onSignupClick}
                                className="text-[10px] text-primary hover:text-primary/80 transition-colors"
                            >
                                Don't have an account? Register here
                            </button>
                        </div>

                        {/* Mobile buttons */}
                        <div className="flex lg:hidden items-center gap-2">
                            <button
                                onClick={onLoginClick}
                                className="text-muted-foreground hover:text-foreground transition-colors text-sm"
                            >
                                Sign In
                            </button>
                            <button
                                onClick={onSignupClick}
                                className="bg-primary hover:bg-primary/90 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-all shadow-lg shadow-primary/25"
                            >
                                Register
                            </button>
                        </div>

                        {/* Desktop button */}
                        <button
                            onClick={onSignupClick}
                            className="hidden lg:block bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-primary/25"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}
