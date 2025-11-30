import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import Disclaimer from './Disclaimer';

export default function Footer() {
    return (
        <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-white/5">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <Disclaimer />
                </div>
                <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-6 h-6 text-primary" />
                        <span className="font-bold text-foreground">TradingBot</span>
                    </div>
                    <div className="flex gap-6 text-sm text-muted-foreground">
                        <Link to="/pricing" className="hover:text-foreground transition-colors">Pricing</Link>
                        <a href="#" className="hover:text-foreground transition-colors">Documentation</a>
                        <a href="#" className="hover:text-foreground transition-colors">Support</a>
                    </div>
                    <div className="text-sm text-muted-foreground">
                        © 2025 TradingBot. All rights reserved.
                    </div>
                </div>
            </div>
        </footer>
    );
}
