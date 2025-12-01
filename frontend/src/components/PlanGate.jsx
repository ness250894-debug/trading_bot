import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import './PlanGate.css';

console.log('[PlanGate] Module loaded');

/**
 * PlanGate component - Restricts access to features based on user plan
 * Shows a blurred overlay with upgrade message for Free plan users
 */
const PlanGate = ({ feature, children }) => {
    console.log('[PlanGate] Component rendered for feature:', feature);

    const [isRestricted, setIsRestricted] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        console.log('[PlanGate] useEffect triggered');
        checkPlanAccess();
    }, []);

    const checkPlanAccess = async () => {
        console.log('[PlanGate] checkPlanAccess started');
        try {
            const token = localStorage.getItem('token');
            console.log('[PlanGate] Token exists:', !!token);

            if (!token) {
                console.log('[PlanGate] No token found, restricting access');
                setIsRestricted(true);
                setLoading(false);
                return;
            }

            console.log('[PlanGate] Fetching /api/user/me...');

            // Get user info including subscription
            const response = await fetch('/api/user/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            console.log('[PlanGate] Response status:', response.status);
            console.log('[PlanGate] Response ok:', response.ok);

            if (response.ok) {
                const data = await response.json();
                console.log('[PlanGate] ===== USER DATA =====');
                console.log('[PlanGate] Full response:', JSON.stringify(data, null, 2));
                console.log('[PlanGate] Is Admin:', data.is_admin);
                console.log('[PlanGate] Subscription:', data.subscription);
                console.log('[PlanGate] ===================');

                const isAdmin = data.is_admin || false;
                const subscription = data.subscription;

                const hasActivePaidPlan = subscription &&
                    subscription.status === 'active' &&
                    subscription.plan_id &&
                    !subscription.plan_id.startsWith('free');

                console.log('[PlanGate] Calculated values:');
                console.log('[PlanGate]   - Is Admin:', isAdmin);
                console.log('[PlanGate]   - Has Active Paid Plan:', hasActivePaidPlan);
                console.log('[PlanGate]   - Will Restrict:', !isAdmin && !hasActivePaidPlan);

                setIsRestricted(!isAdmin && !hasActivePaidPlan);
            } else {
                const errorText = await response.text();
                console.error('[PlanGate] Failed to fetch user info');
                console.error('[PlanGate] Status:', response.status);
                console.error('[PlanGate] Error:', errorText);
                setIsRestricted(true);
            }
        } catch (error) {
            console.error('[PlanGate] Exception in checkPlanAccess:', error);
            console.error('[PlanGate] Error stack:', error.stack);
            setIsRestricted(true);
        } finally {
            console.log('[PlanGate] Setting loading to false');
            setLoading(false);
        }
    };

    const handleUpgradeClick = () => {
        console.log('[PlanGate] Upgrade button clicked');
        window.location.href = '/pricing';
    };

    console.log('[PlanGate] Render state - loading:', loading, 'isRestricted:', isRestricted);

    if (loading) {
        console.log('[PlanGate] Rendering loading state');
        return <div className="plan-gate-loading">{children}</div>;
    }

    if (!isRestricted) {
        console.log('[PlanGate] User has access, rendering children directly');
        return <>{children}</>;
    }

    console.log('[PlanGate] Rendering restricted overlay');
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
};

PlanGate.propTypes = {
    feature: PropTypes.string.isRequired,
    children: PropTypes.node.isRequired
};

export default PlanGate;
