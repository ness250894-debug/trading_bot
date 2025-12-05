import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import LoginModal from './LoginModal';
import SignupModal from './SignupModal';
import UserDropdown from './UserDropdown';
import { TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * HybridLayout - Layout that works for both authenticated and non-authenticated users
 * Shows UserDropdown if logged in, otherwise shows login/signup buttons
 */
export default function HybridLayout() {
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [showSignupModal, setShowSignupModal] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const fetchCurrentUser = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    setLoading(false);
                    return;
                }

                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const user = await response.json();
                    setCurrentUser(user);
                }
            } catch (error) {
                // Silent fail - not critical
            } finally {
                setLoading(false);
            }
        };
        fetchCurrentUser();
    }, []);

    const handleLoginClick = () => setShowLoginModal(true);
    const handleSignupClick = () => setShowSignupModal(true);

    const handleSwitchToSignup = () => {
        setShowLoginModal(false);
        setShowSignupModal(true);
    };

    const handleSwitchToLogin = () => {
        setShowSignupModal(false);
        setShowLoginModal(true);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        setCurrentUser(null);
        navigate('/');
    };

    // Check if currently on pricing page to hide duplicate link
    const isOnPricingPage = location.pathname === '/pricing';

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header - conditional based on auth state */}
            <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <Link to="/" className="flex items-center gap-2">
                            <TrendingUp className="w-8 h-8 text-primary" />
                            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                                TradingBot
                            </span>
                        </Link>
                        <div className="flex items-center gap-4">
                            {/* Hide Pricing link when already on Pricing page */}
                            {!isOnPricingPage && (
                                <Link
                                    to="/pricing"
                                    className="text-muted-foreground hover:text-foreground transition-colors hidden sm:block"
                                >
                                    Pricing
                                </Link>
                            )}

                            {loading ? (
                                <div className="w-8 h-8 animate-pulse bg-white/10 rounded-full"></div>
                            ) : currentUser ? (
                                <UserDropdown user={currentUser} onLogout={handleLogout} />
                            ) : (
                                <>
                                    <button
                                        onClick={handleLoginClick}
                                        className="text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        Sign In
                                    </button>
                                    <button
                                        onClick={handleSignupClick}
                                        className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg shadow-primary/25"
                                    >
                                        Get Started
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-grow">
                <Outlet context={{ openLoginModal: handleLoginClick, openSignupModal: handleSignupClick }} />
            </main>

            <Footer />

            <LoginModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
                onSwitchToSignup={handleSwitchToSignup}
            />
            <SignupModal
                isOpen={showSignupModal}
                onClose={() => setShowSignupModal(false)}
                onSwitchToLogin={handleSwitchToLogin}
            />
        </div>
    );
}
