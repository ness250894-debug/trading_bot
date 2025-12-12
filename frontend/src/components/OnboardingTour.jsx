import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X, ChevronRight, ChevronLeft, Check,
    Bot, BarChart3, Settings, TrendingUp, Sparkles,
    Play
} from 'lucide-react';

/**
 * Onboarding Tour Component
 * Step-by-step guide for new users
 */

const TOUR_STEPS = [
    {
        id: 'welcome',
        title: "Welcome to TradingBot! 🚀",
        description: "Let's take a quick tour to help you get started with automated crypto trading.",
        icon: Sparkles,
        position: 'center'
    },
    {
        id: 'dashboard',
        title: "Your Dashboard",
        description: "This is your command center. View your balance, active bots, performance charts, and market sentiment all in one place.",
        icon: TrendingUp,
        target: '[data-tour="dashboard"]',
        position: 'bottom'
    },
    {
        id: 'bots',
        title: "Trading Bots",
        description: "Create and manage your automated trading bots. Each bot can run a different strategy on different trading pairs.",
        icon: Bot,
        target: '[data-tour="bots"]',
        position: 'bottom'
    },
    {
        id: 'backtest',
        title: "Backtesting",
        description: "Test your strategies on historical data before risking real money. See how they would have performed.",
        icon: BarChart3,
        target: '[data-tour="backtest"]',
        position: 'bottom'
    },
    {
        id: 'settings',
        title: "Settings",
        description: "Configure your API keys, notification preferences, and account settings.",
        icon: Settings,
        target: '[data-tour="settings"]',
        position: 'bottom'
    },
    {
        id: 'complete',
        title: "You're all set! 🎉",
        description: "Start by adding your exchange API keys in Settings, then create your first bot or run a backtest to explore strategies.",
        icon: Check,
        position: 'center'
    }
];

const STORAGE_KEY = 'tradingbot_onboarding_completed';

const OnboardingTour = ({ onComplete, forceShow = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [highlighted, setHighlighted] = useState(null);

    useEffect(() => {
        // Check if tour was already completed
        const completed = localStorage.getItem(STORAGE_KEY);
        if (!completed || forceShow) {
            // Delay to let the page render first
            const timer = setTimeout(() => setIsOpen(true), 1000);
            return () => clearTimeout(timer);
        }
    }, [forceShow]);

    useEffect(() => {
        // Highlight current step's target element
        const step = TOUR_STEPS[currentStep];
        if (step.target) {
            const element = document.querySelector(step.target);
            if (element) {
                setHighlighted(element.getBoundingClientRect());
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            setHighlighted(null);
        }
    }, [currentStep]);

    const handleNext = () => {
        if (currentStep < TOUR_STEPS.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleComplete();
        }
    };

    const handlePrev = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleSkip = () => {
        handleComplete();
    };

    const handleComplete = () => {
        localStorage.setItem(STORAGE_KEY, 'true');
        setIsOpen(false);
        if (onComplete) onComplete();
    };

    const step = TOUR_STEPS[currentStep];
    const Icon = step.icon;
    const isFirstStep = currentStep === 0;
    const isLastStep = currentStep === TOUR_STEPS.length - 1;

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/70 z-[200]"
            >
                {/* Highlight hole for target element */}
                {highlighted && (
                    <div
                        className="absolute bg-transparent"
                        style={{
                            top: highlighted.top - 8,
                            left: highlighted.left - 8,
                            width: highlighted.width + 16,
                            height: highlighted.height + 16,
                            boxShadow: '0 0 0 9999px rgba(0,0,0,0.7)',
                            borderRadius: '12px',
                            border: '2px solid rgba(139, 92, 246, 0.5)'
                        }}
                    />
                )}
            </motion.div>

            {/* Tour card */}
            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className={`
          fixed z-[201] w-full max-w-md p-6 
          glass rounded-2xl border border-primary/20 shadow-2xl
          ${step.position === 'center'
                        ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2'
                        : 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 md:top-auto md:bottom-8 md:translate-y-0'
                    }
        `}
            >
                {/* Close button */}
                <button
                    onClick={handleSkip}
                    className="absolute top-4 right-4 p-2 text-muted-foreground 
                    hover:text-foreground hover:bg-white/5 rounded-lg transition-colors"
                >
                    <X size={18} />
                </button>

                {/* Icon */}
                <div className="flex justify-center mb-4">
                    <motion.div
                        key={currentStep}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="p-4 rounded-2xl bg-gradient-to-br from-primary/30 to-purple-500/30"
                    >
                        <Icon size={32} className="text-primary" />
                    </motion.div>
                </div>

                {/* Content */}
                <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-center mb-6"
                >
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                        {step.title}
                    </h3>
                    <p className="text-muted-foreground">
                        {step.description}
                    </p>
                </motion.div>

                {/* Progress dots */}
                <div className="flex justify-center gap-2 mb-6">
                    {TOUR_STEPS.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => setCurrentStep(index)}
                            className={`w-2 h-2 rounded-full transition-all ${index === currentStep
                                    ? 'bg-primary w-6'
                                    : index < currentStep
                                        ? 'bg-primary/50'
                                        : 'bg-white/20'
                                }`}
                        />
                    ))}
                </div>

                {/* Navigation */}
                <div className="flex gap-3">
                    {!isFirstStep && (
                        <button
                            onClick={handlePrev}
                            className="flex-1 py-3 px-4 rounded-xl border border-white/10 
                        text-foreground hover:bg-white/5 transition-colors
                        flex items-center justify-center gap-2"
                        >
                            <ChevronLeft size={18} />
                            Back
                        </button>
                    )}

                    {isFirstStep && (
                        <button
                            onClick={handleSkip}
                            className="flex-1 py-3 px-4 rounded-xl border border-white/10 
                        text-muted-foreground hover:bg-white/5 transition-colors"
                        >
                            Skip Tour
                        </button>
                    )}

                    <button
                        onClick={handleNext}
                        className="flex-1 py-3 px-4 rounded-xl bg-primary hover:bg-primary/90
                      text-white font-medium transition-colors
                      flex items-center justify-center gap-2"
                    >
                        {isLastStep ? (
                            <>
                                <Play size={18} />
                                Get Started
                            </>
                        ) : (
                            <>
                                Next
                                <ChevronRight size={18} />
                            </>
                        )}
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

/**
 * Hook to control the tour
 */
export const useOnboardingTour = () => {
    const [showTour, setShowTour] = useState(false);

    const startTour = () => {
        localStorage.removeItem(STORAGE_KEY);
        setShowTour(true);
    };

    const resetTour = () => {
        localStorage.removeItem(STORAGE_KEY);
    };

    return {
        showTour,
        startTour,
        resetTour,
        TourComponent: () => showTour ? <OnboardingTour forceShow onComplete={() => setShowTour(false)} /> : null
    };
};

export default OnboardingTour;
