import React, { useState, useEffect } from 'react';
import { Star, ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TESTIMONIALS = [
    {
        name: "Alex Thompson",
        role: "Day Trader",
        content: "This bot has completely transformed my trading. The optimization tools helped me find strategies that consistently beat the market.",
        strategy: "MACD Crossover",
        coin: "ETH/USDT",
        pnl: "+12.4%",
        profit: "$3,450"
    },
    {
        name: "Sarah Chen",
        role: "Crypto Investor",
        content: "I was skeptical at first, but the backtesting results convinced me. Now I'm seeing real profits every week.",
        strategy: "DCA Accumulation",
        coin: "BTC/USDT",
        pnl: "+8.2%",
        profit: "$1,240"
    },
    {
        name: "Michael Rodriguez",
        role: "Professional Trader",
        content: "The risk management features are top-notch. I can sleep well knowing my positions are protected.",
        strategy: "Bollinger Breakout",
        coin: "SOL/USDT",
        pnl: "+15.7%",
        profit: "$5,890"
    },
    {
        name: "David Kim",
        role: "Swing Trader",
        content: "Finally, a bot that actually works as advertised. The interface is intuitive and the execution is lightning fast.",
        strategy: "RSI Reversal",
        coin: "MATIC/USDT",
        pnl: "+9.3%",
        profit: "$890"
    },
    {
        name: "Emma Wilson",
        role: "Forex Trader",
        content: "I've tried many bots before, but this one stands out. The support team is amazing and the community is very helpful.",
        strategy: "Range Trading",
        coin: "XRP/USDT",
        pnl: "+5.1%",
        profit: "$450"
    },
    {
        name: "James Anderson",
        role: "Algo Trader",
        content: "The ability to customize strategies with such granularity is impressive. It's like having a team of developers at your fingertips.",
        strategy: "Custom Script",
        coin: "BNB/USDT",
        pnl: "+22.8%",
        profit: "$9,200"
    },
    {
        name: "Lisa Wang",
        role: "HODLer",
        content: "I used to just hold, but now I'm generating passive income with the grid trading strategy. Highly recommended!",
        strategy: "Volatility Scalping",
        coin: "DOT/USDT",
        pnl: "+4.5%",
        profit: "$320"
    },
    {
        name: "Robert Taylor",
        role: "Tech Enthusiast",
        content: "The technology behind this is solid. No downtime, no glitches. Just pure performance.",
        strategy: "Momentum",
        coin: "LINK/USDT",
        pnl: "+11.2%",
        profit: "$1,560"
    },
    {
        name: "Jennifer Martinez",
        role: "Part-time Trader",
        content: "Perfect for someone like me who has a day job. I set it up on the weekend and let it run during the week.",
        strategy: "Trend Following",
        coin: "ADA/USDT",
        pnl: "+7.8%",
        profit: "$670"
    },
    {
        name: "William Brown",
        role: "Crypto Analyst",
        content: "The analytics dashboard gives me insights I couldn't get anywhere else. It's become an essential part of my workflow.",
        strategy: "Volume Breakout",
        coin: "AVAX/USDT",
        pnl: "+14.3%",
        profit: "$2,100"
    },
    {
        name: "Sophie Patel",
        role: "DeFi User",
        content: "Integration with major exchanges is seamless. I love how easy it is to manage my portfolio across different platforms.",
        strategy: "Market Neutral",
        coin: "UNI/USDT",
        pnl: "+3.2%",
        profit: "$180"
    },
    {
        name: "Thomas Wright",
        role: "Bitcoin Maxi",
        content: "Even for a simple DCA strategy, this bot saves me so much time and emotion. It just executes the plan perfectly.",
        strategy: "Smart DCA",
        coin: "BTC/USDT",
        pnl: "+6.5%",
        profit: "$4,500"
    },
    {
        name: "Olivia Johnson",
        role: "New Trader",
        content: "As a beginner, the pre-built strategies were a lifesaver. I learned so much just by watching how the bot trades.",
        strategy: "Automated Execution",
        coin: "ETH/USDT",
        pnl: "+10.1%",
        profit: "$540"
    },
    {
        name: "Daniel Lee",
        role: "Quant Developer",
        content: "I appreciate the API access. I built my own custom indicators and they work flawlessly with the bot's engine.",
        strategy: "Technical Analysis",
        coin: "DOGE/USDT",
        pnl: "+18.9%",
        profit: "$3,200"
    },
    {
        name: "Emily Davis",
        role: "Investment Manager",
        content: "Managing client funds requires reliability. This platform delivers that and more. A game changer for my business.",
        strategy: "Dynamic Allocation",
        coin: "Mixed",
        pnl: "+8.7%",
        profit: "$12,400"
    },
    {
        name: "Ryan White",
        role: "Scalper",
        content: "For high-frequency trading, speed is everything. This bot executes faster than I ever could manually.",
        strategy: "Rapid Scalping",
        coin: "LTC/USDT",
        pnl: "+2.1%",
        profit: "$120"
    },
    {
        name: "Jessica Garcia",
        role: "Social Trader",
        content: "I love sharing my results with the community. It's great to see others succeeding with the same tools.",
        strategy: "Trend Analysis",
        coin: "SHIB/USDT",
        pnl: "+25.4%",
        profit: "$890"
    },
    {
        name: "Kevin Miller",
        role: "Blockchain Dev",
        content: "The security measures are impressive. I feel safe connecting my API keys knowing they are encrypted and stored filled.",
        strategy: "Secure HODL",
        coin: "ATOM/USDT",
        pnl: "+5.6%",
        profit: "$430"
    },
    {
        name: "Amanda Thomas",
        role: "Passive Investor",
        content: "Set it and forget it. That's my style. This bot allows me to enjoy my life while my money works for me.",
        strategy: "Compound Growth",
        coin: "CAKE/USDT",
        pnl: "+12.8%",
        profit: "$1,150"
    },
    {
        name: "Christopher Moore",
        role: "Full-time Trader",
        content: "I've replaced 3 other subscriptions with this one tool. It has everything I need in one place.",
        strategy: "Multi-Strategy",
        coin: "NEAR/USDT",
        pnl: "+16.2%",
        profit: "$2,800"
    }
];

export default function Testimonials() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isAutoPlaying, setIsAutoPlaying] = useState(true);

    useEffect(() => {
        if (!isAutoPlaying) return;

        const interval = setInterval(() => {
            nextSlide();
        }, 5000); // Rotate every 5 seconds

        return () => clearInterval(interval);
    }, [currentIndex, isAutoPlaying]);

    const nextSlide = () => {
        setCurrentIndex((prev) => (prev + 1) % TESTIMONIALS.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prev) => (prev - 1 + TESTIMONIALS.length) % TESTIMONIALS.length);
    };

    const getVisibleTestimonials = () => {
        const items = [];
        for (let i = 0; i < 3; i++) {
            const index = (currentIndex + i) % TESTIMONIALS.length;
            items.push(TESTIMONIALS[index]);
        }
        return items;
    };

    return (
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

                <div
                    className="relative"
                    onMouseEnter={() => setIsAutoPlaying(false)}
                    onMouseLeave={() => setIsAutoPlaying(true)}
                >
                    {/* Navigation Buttons */}
                    <button
                        onClick={prevSlide}
                        className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 p-2 rounded-full bg-background/80 border border-white/10 hover:bg-primary/20 hover:border-primary/50 transition-all hidden md:block"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <button
                        onClick={nextSlide}
                        className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 p-2 rounded-full bg-background/80 border border-white/10 hover:bg-primary/20 hover:border-primary/50 transition-all hidden md:block"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>

                    <div className="grid md:grid-cols-3 gap-6 overflow-hidden">
                        <AnimatePresence mode="popLayout">
                            {getVisibleTestimonials().map((testimonial, idx) => (
                                <motion.div
                                    key={`${testimonial.name}-${currentIndex + idx}`}
                                    initial={{ opacity: 0, x: 100 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -100 }}
                                    transition={{ duration: 0.5 }}
                                    className="glass p-6 rounded-2xl border border-white/10 flex flex-col h-full"
                                >
                                    <div className="flex gap-1 mb-4">
                                        {[...Array(5)].map((_, i) => (
                                            <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                                        ))}
                                    </div>

                                    <p className="text-foreground mb-6 italic flex-grow">"{testimonial.content}"</p>

                                    {/* Trading Stats Card */}
                                    <div className="bg-white/5 rounded-xl p-3 mb-4 border border-white/5">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-xs text-muted-foreground">Strategy</span>
                                            <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                                                {testimonial.strategy}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center text-sm">
                                            <div className="flex items-center gap-2">
                                                <span className="text-muted-foreground">{testimonial.coin}</span>
                                            </div>
                                            <div className="text-right">
                                                <div className="font-bold text-green-400">{testimonial.pnl}</div>
                                                <div className="text-xs text-green-400/80">+{testimonial.profit}</div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3 mt-auto">
                                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold shrink-0">
                                            {testimonial.name[0]}
                                        </div>
                                        <div>
                                            <div className="text-sm font-medium text-foreground">{testimonial.name}</div>
                                            <div className="text-xs text-muted-foreground">{testimonial.role}</div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>


                    {/* Mobile Navigation Dots */}
                    <div className="flex justify-center gap-2 mt-8 md:hidden">
                        {[...Array(5)].map((_, i) => (
                            <button
                                key={i}
                                onClick={() => setCurrentIndex(i * 4)}
                                className={`w-2 h-2 rounded-full transition-all ${Math.floor(currentIndex / 4) === i ? 'bg-primary w-4' : 'bg-white/20'
                                    }`}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
