const [stats, setStats] = useState({
    totalTrades: 12847,
    successRate: 73.4,
    activeUsers: 1243,
    totalProfit: 284567
});

// Check if user is already logged in
useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
        navigate('/dashboard');
    }
}, [navigate]);

// Animated counter effect
useEffect(() => {
    const interval = setInterval(() => {
        setStats(prev => ({
            totalTrades: prev.totalTrades + Math.floor(Math.random() * 3),
            successRate: prev.successRate + (Math.random() - 0.5) * 0.1,
            activeUsers: prev.activeUsers + Math.floor(Math.random() * 2),
            totalProfit: prev.totalProfit + Math.floor(Math.random() * 100)
        }));
    }, 3000);
    return () => clearInterval(interval);
}, []);

const features = [
    {
        icon: Zap,
        title: "Lightning Fast Execution",
        description: "Execute trades in milliseconds with our optimized infrastructure and direct exchange connections."
    },
    {
        icon: Shield,
        title: "Advanced Risk Management",
        description: "Protect your capital with customizable stop-loss, take-profit, and position sizing rules."
    },
    {
        icon: BarChart2,
        title: "Strategy Optimization",
        description: "Fine-tune your strategies with our powerful backtesting and optimization engine."
    },
    {
        icon: Activity,
        title: "Real-Time Monitoring",
        description: "Track every trade, metric, and market movement with our comprehensive dashboard."
    },
    {
        icon: Target,
        title: "Multiple Strategies",
        description: "Choose from SMA Crossover, RSI, MACD, Mean Reversion, and more proven strategies."
    },
    {
        icon: Clock,
        title: "24/7 Automated Trading",
        description: "Never miss an opportunity. Your bot trades around the clock, even while you sleep."
    }
];

const benefits = [
    "No coding required - Easy visual configuration",
    "Backtesting with historical data",
    "Paper trading for risk-free testing",
    "Multi-exchange support",
    "Telegram notifications",
    "Advanced analytics & reporting"
];

const testimonials = [
    {
        name: "Alex Thompson",
        role: "Day Trader",
        content: "This bot has completely transformed my trading. The optimization tools helped me find strategies that consistently beat the market.",
        rating: 5
    },
    {
        name: "Sarah Chen",
        role: "Crypto Investor",
        content: "I was skeptical at first, but the backtesting results convinced me. Now I'm seeing real profits every week.",
        rating: 5
    },
    {
        name: "Michael Rodriguez",
        role: "Professional Trader",
        content: "The risk management features are top-notch. I can sleep well knowing my positions are protected.",
        rating: 5
    }
];

return (
    <div className="min-h-screen bg-background">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-8 h-8 text-primary" />
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                            TradingBot
                        </span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link
                            to="/pricing"
                            className="text-muted-foreground hover:text-foreground transition-colors hidden sm:block"
                        >
                            Pricing
                        </Link>
                        <button
                            onClick={() => setShowLoginModal(true)}
                            className="text-muted-foreground hover:text-foreground transition-colors"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => setShowSignupModal(true)}
                            className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-primary/25"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-6 animate-in fade-in slide-in-from-top-4 duration-1000">
                        <Rocket size={16} />
                        <span>Automate Your Trading Journey</span>
                    </div>
                    <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 animate-in fade-in slide-in-from-top-8 duration-1000 delay-100">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-400">
                            Trade Smarter with
                        </span>
                        <br />
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-400 to-pink-400">
                            AI-Powered Automation
                        </span>
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-10 animate-in fade-in slide-in-from-top-12 duration-1000 delay-200">
                        Execute winning strategies 24/7. Optimize performance with advanced backtesting.
                        Manage risk automatically. Join thousands of traders maximizing their profits.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center animate-in fade-in slide-in-from-top-16 duration-1000 delay-300">
                        <button
                            onClick={() => setShowSignupModal(true)}
                            className="group bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-105 flex items-center justify-center gap-2"
                        >
                            Start Trading Now
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                        <Link
                            to="/pricing"
                            className="bg-white/5 hover:bg-white/10 text-foreground px-8 py-4 rounded-xl font-bold text-lg transition-all border border-white/10 hover:border-white/20 flex items-center justify-center gap-2"
                        >
                            View Pricing
                        </Link>
                    </div>
                </div>

                {/* Live Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto">
                    <div className="glass p-6 rounded-xl border border-white/10 hover:border-primary/20 transition-all hover:scale-105">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-blue-500/10 rounded-lg">
                                <Activity className="w-5 h-5 text-blue-400" />
                            </div>
                            <div className="text-sm text-muted-foreground">Total Trades</div>
                        </div>
                        <div className="text-3xl font-bold text-foreground">
                            {stats.totalTrades.toLocaleString()}
                        </div>
                    </div>
                    <div className="glass p-6 rounded-xl border border-white/10 hover:border-primary/20 transition-all hover:scale-105">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-green-500/10 rounded-lg">
                                <TrendingUp className="w-5 h-5 text-green-400" />
                            </div>
                            <div className="text-sm text-muted-foreground">Success Rate</div>
                        </div>
                        <div className="text-3xl font-bold text-green-400">
                            {stats.successRate.toFixed(1)}%
                        </div>
                    </div>
                    <div className="glass p-6 rounded-xl border border-white/10 hover:border-primary/20 transition-all hover:scale-105">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-purple-500/10 rounded-lg">
                                <Users className="w-5 h-5 text-purple-400" />
                            </div>
                            <div className="text-sm text-muted-foreground">Active Users</div>
                        </div>
                        <div className="text-3xl font-bold text-foreground">
                            {stats.activeUsers.toLocaleString()}
                        </div>
                    </div>
                    <div className="glass p-6 rounded-xl border border-white/10 hover:border-primary/20 transition-all hover:scale-105">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-yellow-500/10 rounded-lg">
                                <DollarSign className="w-5 h-5 text-yellow-400" />
                            </div>
                            <div className="text-sm text-muted-foreground">Total Profit</div>
                        </div>
                        <div className="text-3xl font-bold text-yellow-400">
                            ${(stats.totalProfit / 1000).toFixed(0)}K
                        </div>
                    </div>
                </div>
            </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-4xl sm:text-5xl font-bold mb-4">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Powerful Features
                        </span>
                    </h2>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Everything you need to succeed in automated trading
                    </p>
                </div>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {features.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <div
                                key={index}
                                className="glass p-8 rounded-2xl border border-white/10 hover:border-primary/20 transition-all hover:scale-105 group"
                            >
                                <div className="p-3 bg-primary/10 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform">
                                    <Icon className="w-6 h-6 text-primary" />
                                </div>
                                <h3 className="text-xl font-bold mb-2 text-foreground">{feature.title}</h3>
                                <p className="text-muted-foreground">{feature.description}</p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>

        {/* Benefits Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    <div>
                        <h2 className="text-4xl sm:text-5xl font-bold mb-6">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                                Why Choose TradingBot?
                            </span>
                        </h2>
                        <p className="text-xl text-muted-foreground mb-8">
                            Built by traders, for traders. Our platform combines cutting-edge technology
                            with battle-tested strategies to give you the edge in the market.
                        </p>
                        <ul className="space-y-4">
                            {benefits.map((benefit, index) => (
                                <li key={index} className="flex items-start gap-3">
                                    <div className="p-1 bg-green-500/10 rounded-full mt-0.5">
                                        <CheckCircle className="w-5 h-5 text-green-400" />
                                    </div>
                                    <span className="text-foreground text-lg">{benefit}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="relative">
                        <div className="glass p-8 rounded-2xl border border-white/10">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 bg-green-500/10 rounded-xl border border-green-500/20">
                                    <div>
                                        <div className="text-sm text-green-400 mb-1">BTC/USDT</div>
                                        <div className="text-2xl font-bold text-green-400">+2.47%</div>
                                    </div>
                                    <TrendingUp className="w-8 h-8 text-green-400" />
                                </div>
                                <div className="flex items-center justify-between p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                                    <div>
                                        <div className="text-sm text-blue-400 mb-1">ETH/USDT</div>
                                        <div className="text-2xl font-bold text-blue-400">+1.83%</div>
                                    </div>
                                    <Activity className="w-8 h-8 text-blue-400" />
                                </div>
                                <div className="flex items-center justify-between p-4 bg-purple-500/10 rounded-xl border border-purple-500/20">
                                    <div>
                                        <div className="text-sm text-purple-400 mb-1">SOL/USDT</div>
                                        <div className="text-2xl font-bold text-purple-400">+3.21%</div>
                                    </div>
                                    <TrendingUp className="w-8 h-8 text-purple-400" />
                                </div>
                            </div>
                        </div>
                        <div className="absolute -top-4 -right-4 w-24 h-24 bg-primary/20 rounded-full blur-3xl"></div>
                        <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl"></div>
                    </div>
                </div>
            </div>
        </section>

        {/* Testimonials */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-4xl sm:text-5xl font-bold mb-4">
                        <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Trusted by Traders
                        </span>
                    </h2>
                    <p className="text-xl text-muted-foreground">
                        See what our community has to say
                    </p>
                </div>
                <div className="grid md:grid-cols-3 gap-6">
                    {testimonials.map((testimonial, index) => (
                        <div key={index} className="glass p-6 rounded-2xl border border-white/10">
                            <div className="flex gap-1 mb-4">
                                {[...Array(testimonial.rating)].map((_, i) => (
                                    <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                                ))}
                            </div>
                            <p className="text-foreground mb-4 italic">"{testimonial.content}"</p>
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                                    {testimonial.name[0]}
                                </div>
                                <div>
                                    <div className="text-sm font-medium text-foreground">{testimonial.name}</div>
                                    <div className="text-xs text-muted-foreground">{testimonial.role}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <div className="glass p-12 rounded-3xl border border-white/10 text-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-purple-500/10 to-pink-500/10"></div>
                    <div className="relative z-10">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/20 border border-primary/30 text-primary text-sm font-medium mb-6">
                            <Award size={16} />
                            <span>Limited Time Offer</span>
                        </div>
                        <h2 className="text-4xl sm:text-5xl font-bold mb-4">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-300">
                                Ready to Start Trading?
                            </span>
                        </h2>
                        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                            Join thousands of successful traders using our platform.
                            Start your free trial today - no credit card required.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <button
                                onClick={() => setShowSignupModal(true)}
                                className="group bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-105 flex items-center justify-center gap-2"
                            >
                                Get Started Free
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </button>
                            <button
                                onClick={() => setShowLoginModal(true)}
                                className="bg-white/5 hover:bg-white/10 text-foreground px-8 py-4 rounded-xl font-bold text-lg transition-all border border-white/10 hover:border-white/20"
                            >
                                Sign In
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        {/* Footer */}
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

        {/* Modals */}
        <LoginModal
            isOpen={showLoginModal}
            onClose={() => setShowLoginModal(false)}
            onSwitchToSignup={() => {
                setShowLoginModal(false);
                setShowSignupModal(true);
            }}
        />
        <SignupModal
            isOpen={showSignupModal}
            onClose={() => setShowSignupModal(false)}
            onSwitchToLogin={() => {
                setShowSignupModal(false);
                setShowLoginModal(true);
            }}
        />
    </div>
);
}
