import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import api from '../lib/api';
import styles from './Pricing.module.css';
import { CheckCircle, Zap, Shield, TrendingUp, Crown, Star } from 'lucide-react';

const PLANS = [
    {
        id: 'free',
        name: 'Free',
        price: { monthly: 0, yearly: 0 },
        features: [
            '1 Active Bot',
            'Basic Strategies',
            'Paper Trading Only',
            'Community Support'
        ],
        cta: 'Current Plan',
        color: 'gray'
    },
    {
        id: 'basic',
        name: 'Basic',
        price: { monthly: 19, yearly: 190 },
        features: [
            '3 Active Bots',
            'Standard Strategies',
            'Live Trading',
            'Email Support'
        ],
        cta: 'Start Basic',
        color: 'blue'
    },
    {
        id: 'pro',
        name: 'Pro',
        price: { monthly: 49, yearly: 490 },
        features: [
            'Unlimited Bots',
            'All Strategies',
            'Priority Support',
            'Advanced Analytics',
            'API Access'
        ],
        cta: 'Go Pro',
        featured: true,
        color: 'purple'
    },
    {
        id: 'elite',
        name: 'Elite',
        price: { monthly: 99, yearly: 990 },
        features: [
            'Everything in Pro',
            '1-on-1 Mentoring',
            'Custom Strategy Dev',
            'White Glove Support'
        ],
        cta: 'Get Elite',
        color: 'gold'
    }
];

export default function Pricing() {
    const navigate = useNavigate();
    const { openSignupModal } = useOutletContext();
    const [currentPlan, setCurrentPlan] = useState('free');
    const [billingCycle, setBillingCycle] = useState('monthly');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            fetchBillingStatus();
        }
    }, []);

    const fetchBillingStatus = async () => {
        try {
            const response = await api.get('/billing/status');
            setCurrentPlan(response.data.plan);
        } catch (error) {
            console.error('Error fetching billing status:', error);
        }
    };

    const handleUpgrade = async (basePlanId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            openSignupModal();
            return;
        }

        if (basePlanId === 'free') return;

        const planId = `${basePlanId}_${billingCycle}`;

        if (planId === currentPlan) return;

        setLoading(true);
        setMessage(null);

        try {
            const response = await api.post('/billing/charge', { plan_id: planId });
            window.location.href = response.data.hosted_url;
        } catch (error) {
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || 'Failed to create checkout'
            });
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>Choose Your Plan</h1>
                <p className={styles.subtitle}>
                    Unlock the full power of automated trading
                </p>

                <div className={styles.toggleContainer}>
                    <span className={`${styles.toggleLabel} ${billingCycle === 'monthly' ? styles.active : ''}`}>Monthly</span>
                    <button
                        className={`${styles.toggleButton} ${billingCycle === 'yearly' ? styles.toggled : ''}`}
                        onClick={() => setBillingCycle(prev => prev === 'monthly' ? 'yearly' : 'monthly')}
                    >
                        <div className={styles.toggleHandle} />
                    </button>
                    <span className={`${styles.toggleLabel} ${billingCycle === 'yearly' ? styles.active : ''}`}>
                        Yearly <span className={styles.saveBadge}>Save 20%</span>
                    </span>
                </div>
            </div>

            {message && (
                <div className={`${styles.message} ${styles[message.type]}`}>
                    {message.text}
                </div>
            )}

            <div className={styles.plansGrid}>
                {PLANS.map((plan) => {
                    const isCurrent = currentPlan && currentPlan.startsWith(plan.id);

                    let Icon = Shield;
                    if (plan.id === 'basic') Icon = Zap;
                    if (plan.id === 'pro') Icon = TrendingUp;
                    if (plan.id === 'elite') Icon = Crown;

                    return (
                        <div
                            key={plan.id}
                            className={`${styles.planCard} ${styles[plan.color]} ${plan.featured ? styles.featured : ''} ${isCurrent ? styles.current : ''}`}
                        >
                            {plan.featured && (
                                <div className={styles.badge}>Most Popular</div>
                            )}

                            <div className={styles.planHeader}>
                                <div className={`${styles.iconWrapper} ${styles[plan.color]}`}>
                                    <Icon size={32} />
                                </div>
                                <h3 className={styles.planName}>{plan.name}</h3>

                                <div className={styles.pricing}>
                                    {plan.price[billingCycle] === 0 ? (
                                        <div className={styles.free}>Free</div>
                                    ) : (
                                        <>
                                            <span className={styles.currency}>$</span>
                                            <span className={styles.price}>{plan.price[billingCycle]}</span>
                                            <span className={styles.period}>/{billingCycle === 'monthly' ? 'mo' : 'yr'}</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            <ul className={styles.features}>
                                {plan.features.map((feature, idx) => (
                                    <li key={idx} className={styles.feature}>
                                        <CheckCircle size={18} className={`${styles.checkIcon} ${styles[plan.color]}`} />
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={`${styles.ctaButton} ${styles[plan.color]} ${isCurrent ? styles.ctaCurrent : ''}`}
                                onClick={() => handleUpgrade(plan.id)}
                                disabled={loading || isCurrent}
                            >
                                {isCurrent ? 'Current Plan' : plan.cta}
                            </button>
                        </div>
                    );
                })}
            </div>

            <div className={styles.faq}>
                <h3>Frequently Asked Questions</h3>
                <div className={styles.faqGrid}>
                    <div className={styles.faqItem}>
                        <h4>How do I pay?</h4>
                        <p>We accept cryptocurrency payments via Coinbase Commerce. You can pay with Bitcoin, Ethereum, and other major cryptocurrencies.</p>
                    </div>
                    <div className={styles.faqItem}>
                        <h4>Can I cancel anytime?</h4>
                        <p>Yes! Your subscription will remain active until the end of your billing period, with no automatic renewal.</p>
                    </div>
                    <div className={styles.faqItem}>
                        <h4>What's the difference between Paper and Live Trading?</h4>
                        <p>Paper trading simulates trades without real money. Live trading executes real trades on the exchange.</p>
                    </div>
                    <div className={styles.faqItem}>
                        <h4>Is my data secure?</h4>
                        <p>Absolutely. Your API keys are encrypted with AES-256 and stored securely. We never have access to your exchange withdrawal permissions.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
