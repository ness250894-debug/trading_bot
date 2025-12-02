import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import './PlanGate.css';

/**
 * PlanGate component - Restricts access to features based on user plan
 * Shows a blurred overlay with upgrade message for Free plan users
 */
function PlanGate({ feature, children }) {
    const [isRestricted, setIsRestricted] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkPlanAccess();
    }, []);

    const checkPlanAccess = async () => {
        try {
            const token = localStorage.getItem('token');

            if (!token) {
                setIsRestricted(true);
                setLoading(false);
                return;
            }

            const response = await fetch('/api/user/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const isAdmin = data.is_admin || false;
                const subscription = data.subscription;

                const hasActivePaidPlan = subscription &&
                    subscription.status === 'active' &&
                    subscription.plan_id &&
                    !subscription.plan_id.startsWith('free');

                setIsRestricted(!isAdmin && !hasActivePaidPlan);
            } else {
                setIsRestricted(true);
            }
        } catch (error) {
            setIsRestricted(true);
        } finally {
            setLoading(false);
        }
    };

    const handleUpgradeClick = () => {
        window.location.href = '/pricing';
    };

    if (loading) {
        return <div className="plan-gate-loading">{children}</div>;
    }

    if (!isRestricted) {
        return <div>{children}</div>;
    }

    return (
        <div className="plan-gate-container">
            <div className="plan-gate-content blurred">
                {children}
            </div>
            <div className="plan-gate-overlay">
                <div className="plan-gate-message">
                    <h2>🔒 Premium Feature</h2>
                    <p>{feature} is not available on the Free plan.</p>
                    <button className="upgrade-button" onClick={handleUpgradeClick}>
                        Upgrade to Pro
                    </button>
                </div>
            </div>
        </div>
    );
}

PlanGate.propTypes = {
    feature: PropTypes.string.isRequired,
    children: PropTypes.node.isRequired
};

export default PlanGate;
