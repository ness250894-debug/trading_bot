import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import api from '../lib/api';
import styles from './Pricing.module.css';
import { CheckCircle, Zap, Shield, TrendingUp, Crown, Star } from 'lucide-react';

const PLAN_METADATA = {
    free: { color: 'gray', icon: Shield, cta: 'Current Plan', order: 0 },
    basic: { color: 'blue', icon: Zap, cta: 'Start Basic', order: 1 },
    pro: { color: 'purple', icon: TrendingUp, cta: 'Go Pro', order: 2, featured: true },
    elite: { color: 'gold', icon: Crown, cta: 'Get Elite', order: 3 }
};

export default function Pricing() {
    const navigate = useNavigate();
    const { openSignupModal } = useOutletContext();
    const [plans, setPlans] = useState([]);
    const [currentPlan, setCurrentPlan] = useState('free');
    const [billingCycle, setBillingCycle] = useState('monthly');
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [plansRes, statusRes] = await Promise.allSettled([
                api.get('/billing/plans'),
                api.get('/billing/status')
            ]);

            if (plansRes.status === 'fulfilled') {
                processPlans(plansRes.value.data);
            }

            if (statusRes.status === 'fulfilled') {
                setCurrentPlan(statusRes.value.data.plan);
            }
        } catch (error) {
            console.error('Error fetching data:', error);
            setMessage({ type: 'error', text: 'Failed to load pricing plans.' });
        } finally {
            setLoading(false);
        }
    };

    const processPlans = (apiPlans) => {
        const grouped = {};

        apiPlans.forEach(plan => {
            // Assumes id format: tier_cycle (e.g., basic_monthly)
            const parts = plan.id.split('_');
            const tier = parts[0];
            const cycle = parts[1] || 'monthly'; // Default to monthly if no cycle specified

            if (!grouped[tier]) {
                grouped[tier] = {
                    id: tier,
                    name: plan.name.replace(' Monthly', '').replace(' Yearly', ''),
                    price: { monthly: 0, yearly: 0 }, // Initialize both to prevent undefined
                    features: plan.features || [],
                    ...PLAN_METADATA[tier]
                };
            }

            // Ensure price is a number
            grouped[tier].price[cycle] = parseFloat(plan.price) || 0;

            // Prefer monthly features if available
            if (cycle === 'monthly' && plan.features) {
                grouped[tier].features = plan.features;
            }
        });

        const sortedPlans = Object.values(grouped).sort((a, b) => (a.order || 0) - (b.order || 0));
        setPlans(sortedPlans);
    };

    const handleUpgrade = async (basePlanId) => {
        const token = localStorage.getItem('token');
        if (!token) {
            openSignupModal();
            return;
        }

        if (basePlanId === 'free') return;

        const planId = `${basePlanId}_${billingCycle}`;

        // Check if already on this plan
        if (currentPlan && currentPlan.startsWith(basePlanId) && currentPlan.includes(billingCycle)) return;

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

    if (loading && plans.length === 0) {
        return <div className={styles.loading}>Loading plans...</div>;
    }

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
                {plans.map((plan) => {
                    const isCurrent = currentPlan && currentPlan.startsWith(plan.id);
                    const Icon = plan.icon || Shield;
                    const displayPrice = plan.price && plan.price[billingCycle] !== undefined
                        ? plan.price[billingCycle]
                        : 0;

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
                                    {displayPrice === 0 ? (
                                        <div className={styles.free}>Free</div>
                                    ) : (
                                        <>
                                            <span className={styles.currency}>$</span>
                                            <span className={styles.price}>{displayPrice}</span>
                                            <span className={styles.period}>/{billingCycle === 'monthly' ? 'mo' : 'yr'}</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            <ul className={styles.features}>
                                {plan.features && Array.isArray(plan.features) && plan.features.map((feature, idx) => (
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
