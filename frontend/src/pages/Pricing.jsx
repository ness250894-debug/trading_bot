import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '../lib/api';
import secureStorage from '../lib/secureStorage';
import { useStaticData } from '../lib/swr';
import styles from './Pricing.module.css';
import { CheckCircle, Zap, Shield, TrendingUp, Crown } from 'lucide-react';


const PLAN_METADATA = {
    free: { color: 'gray', icon: Shield, cta: 'Current Plan', order: 0 },
    basic: { color: 'blue', icon: Zap, cta: 'Start Basic', order: 1 },
    pro: { color: 'purple', icon: TrendingUp, cta: 'Go Pro', order: 2, featured: true },
    elite: { color: 'gold', icon: Crown, cta: 'Get Elite', order: 3 }
};

export default function Pricing() {
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
            const token = secureStorage.getToken();
            const promises = [api.get('/billing/plans')];

            if (token) {
                promises.push(api.get('/billing/status'));
            }

            const results = await Promise.allSettled(promises);
            const plansRes = results[0];
            const statusRes = token ? results[1] : null;

            if (plansRes.status === 'fulfilled' && plansRes.value?.data) {
                processPlans(plansRes.value.data);
            }

            if (statusRes.status === 'fulfilled' && statusRes.value?.data?.plan) {
                setCurrentPlan(String(statusRes.value.data.plan));
            }
        } catch (error) {
            // Silent fail - will show default plans
            setMessage({ type: 'error', text: 'Failed to load pricing plans.' });
        } finally {
            setLoading(false);
        }
    };

    const processPlans = (apiPlans) => {
        if (!Array.isArray(apiPlans)) {
            // Validation warning - data structure mismatch
            return;
        }

        const grouped = {};

        apiPlans.forEach(plan => {
            if (!plan || typeof plan !== 'object') return;

            // Safely extract tier and cycle from plan ID
            const planId = String(plan.id || '');
            const parts = planId.split('_');
            const tier = parts[0] || 'unknown';
            const cycle = parts[1] || 'monthly';

            // Skip if no metadata for this tier
            if (!PLAN_METADATA[tier]) return;

            // Initialize grouped plan if it doesn't exist
            if (!grouped[tier]) {
                const planName = String(plan.name || tier);
                grouped[tier] = {
                    id: tier,
                    name: planName.replace(/ Monthly$/i, '').replace(/ Yearly$/i, ''),
                    price: { monthly: 0, yearly: 0 },
                    features: [],
                    ...PLAN_METADATA[tier]
                };
            }

            // Safely parse price as number
            const priceValue = parseFloat(plan.price);
            grouped[tier].price[cycle] = isNaN(priceValue) ? 0 : priceValue;

            // Set features (prefer monthly)
            if (Array.isArray(plan.features) && plan.features.length > 0) {
                if (cycle === 'monthly' || !grouped[tier].features.length) {
                    grouped[tier].features = plan.features.map(f => String(f));
                }
            }
        });

        // Sort and set plans
        const sortedPlans = Object.values(grouped)
            .filter(p => p && p.id)
            .sort((a, b) => (a.order || 0) - (b.order || 0));

        setPlans(sortedPlans);
    };

    const handleUpgrade = async (basePlanId) => {
        const token = secureStorage.getToken();
        if (!token) {
            openSignupModal();
            return;
        }

        if (basePlanId === 'free') return;

        const planId = `${basePlanId}_${billingCycle}`;

        if (currentPlan && currentPlan.startsWith(basePlanId)) return;

        setLoading(true);
        setMessage(null);

        try {
            const response = await api.post('/billing/charge', { plan_id: planId });
            if (response?.data?.hosted_url) {
                window.location.href = response.data.hosted_url;
            }
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
                <h1 className={styles.title}>
                    Choose Your Plan
                </h1>
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
                    if (!plan || !plan.id) return null;

                    const isCurrent = currentPlan && String(currentPlan).startsWith(String(plan.id));
                    const Icon = plan.icon || Shield;
                    const planColor = plan.color || 'gray';
                    const planName = String(plan.name || plan.id);
                    const priceValue = typeof plan.price?.[billingCycle] === 'number'
                        ? plan.price[billingCycle]
                        : 0;

                    return (
                        <div
                            key={plan.id}
                            className={`${styles.planCard} ${styles[planColor]} ${plan.featured ? styles.featured : ''} ${isCurrent ? styles.current : ''}`}
                        >
                            {plan.featured && (
                                <div className={styles.badge}>Most Popular</div>
                            )}

                            <div className={styles.planHeader}>
                                <div className={`${styles.iconWrapper} ${styles[planColor]}`}>
                                    <Icon size={32} />
                                </div>
                                <h3 className={styles.planName}>{planName}</h3>

                                <div className={styles.pricing}>
                                    {priceValue === 0 ? (
                                        <div className={styles.free}>Free</div>
                                    ) : (
                                        <>
                                            <span className={styles.currency}>$</span>
                                            <span className={styles.price}>{Math.round(priceValue)}</span>
                                            <span className={styles.period}>/{billingCycle === 'monthly' ? 'mo' : 'yr'}</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            <ul className={styles.features}>
                                {Array.isArray(plan.features) && plan.features.map((feature, idx) => (
                                    <li key={idx} className={styles.feature}>
                                        <CheckCircle size={18} className={`${styles.checkIcon} ${styles[planColor]}`} />
                                        <span>{String(feature)}</span>
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={`${styles.ctaButton} ${styles[planColor]} ${isCurrent ? styles.ctaCurrent : ''}`}
                                onClick={() => handleUpgrade(plan.id)}
                                disabled={loading || isCurrent}
                            >
                                {isCurrent ? 'Current Plan' : (plan.cta || 'Get Started')}
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
