import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Disclaimer from '../components/Disclaimer';
import LoginModal from '../components/LoginModal';
import SignupModal from '../components/SignupModal';
import api from '../lib/api';
import styles from './Pricing.module.css';
import { CheckCircle, Zap, Shield, TrendingUp } from 'lucide-react';

const PLANS = [
    {
        id: 'free',
        name: 'Free',
        price: 0,
        period: 'forever',
        features: [
            '1 Active Bot',
            'Basic Strategies',
            'Paper Trading Only',
            'Community Support'
        ],
        cta: 'Current Plan',
        featured: false
    },
    {
        id: 'pro_monthly',
        name: 'Pro Monthly',
        price: 29.99,
        period: 'per month',
        features: [
            'Unlimited Bots',
            'All Strategies',
            'Live Trading',
            'Priority Support',
            'Advanced Analytics',
            'API Access'
        ],
        cta: 'Upgrade Now',
        featured: true
    },
    {
        id: 'pro_yearly',
        name: 'Pro Yearly',
        price: 299.99,
        period: 'per year',
        savings: 'Save $60/year',
        features: [
            'Everything in Pro Monthly',
            '2 Months Free',
            'Dedicated Support',
            'Early Access to Features'
        ],
        cta: 'Best Value',
        featured: false
    }
];

export default function Pricing() {
    const navigate = useNavigate();
    const [currentPlan, setCurrentPlan] = useState('free');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [showSignupModal, setShowSignupModal] = useState(false);
    const [pendingPlanId, setPendingPlanId] = useState(null);

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

    const handleUpgrade = async (planId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            setPendingPlanId(planId);
            setShowSignupModal(true);
            return;
        }

        if (planId === 'free' || planId === currentPlan) return;

        setLoading(true);
        setMessage(null);

        try {
            const response = await api.post('/billing/charge', { plan_id: planId });

            // Redirect to Coinbase Commerce checkout
            window.location.href = response.data.hosted_url;
        } catch (error) {
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || 'Failed to create checkout'
            });
            setLoading(false);
        }
    };

    const handleAuthSuccess = () => {
        setShowLoginModal(false);
        setShowSignupModal(false);
        if (pendingPlanId) {
            handleUpgrade(pendingPlanId);
            setPendingPlanId(null);
        }
        fetchBillingStatus();
    };

    return (
        <div className={styles.container}>
            <Link to="/" style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: '#a1a1aa',
                textDecoration: 'none',
                marginBottom: '2rem',
                fontSize: '0.9rem'
            }}>
                ← Back to Home
            </Link>
            <div className={styles.header}>
                <h1 className={styles.title}>Choose Your Plan</h1>
                <p className={styles.subtitle}>
                    Unlock the full power of automated trading
                </p>
            </div>

            {message && (
                <div className={`${styles.message} ${styles[message.type]}`}>
                    {message.text}
                </div>
            )}

            <div className={styles.plansGrid}>
                {PLANS.map((plan) => {
                    const isCurrent = plan.id === currentPlan;
                    const Icon = plan.id === 'free' ? Shield : plan.id === 'pro_monthly' ? Zap : TrendingUp;

                    return (
                        <div
                            key={plan.id}
                            className={`${styles.planCard} ${plan.featured ? styles.featured : ''} ${isCurrent ? styles.current : ''}`}
                        >
                            {plan.featured && (
                                <div className={styles.badge}>Most Popular</div>
                            )}

                            <div className={styles.planHeader}>
                                <Icon size={32} className={styles.planIcon} />
                                <h3 className={styles.planName}>{plan.name}</h3>

                                <div className={styles.pricing}>
                                    {plan.price === 0 ? (
                                        <div className={styles.free}>Free</div>
                                    ) : (
                                        <>
                                            <span className={styles.currency}>$</span>
                                            <span className={styles.price}>{plan.price}</span>
                                            <span className={styles.period}>/ {plan.period.replace('per ', '')}</span>
                                        </>
                                    )}
                                </div>

                                {plan.savings && (
                                    <div className={styles.savings}>{plan.savings}</div>
                                )}
                            </div>

                            <ul className={styles.features}>
                                {plan.features.map((feature, idx) => (
                                    <li key={idx} className={styles.feature}>
                                        <CheckCircle size={18} className={styles.checkIcon} />
                                        <span>{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={`${styles.ctaButton} ${plan.featured ? styles.ctaFeatured : ''} ${isCurrent ? styles.ctaCurrent : ''}`}
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
            <div style={{ marginTop: '4rem' }}>
                <Disclaimer />
            </div>

            {/* Modals */}
            <LoginModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
                onSwitchToSignup={() => {
                    setShowLoginModal(false);
                    setShowSignupModal(true);
                }}
                onSuccess={handleAuthSuccess}
            />
            <SignupModal
                isOpen={showSignupModal}
                onClose={() => setShowSignupModal(false)}
                onSwitchToLogin={() => {
                    setShowSignupModal(false);
                    setShowLoginModal(true);
                }}
                onSuccess={handleAuthSuccess}
            />
        </div>
    );
}
