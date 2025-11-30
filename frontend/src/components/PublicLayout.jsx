import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import LoginModal from './LoginModal';
import SignupModal from './SignupModal';

export default function PublicLayout() {
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [showSignupModal, setShowSignupModal] = useState(false);

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

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Header onLoginClick={handleLoginClick} onSignupClick={handleSignupClick} />

            <main className="flex-grow">
                {/* Pass the modal handlers to the children via context if needed, 
                    but for now Landing has its own buttons that might need these.
                    We can use Outlet context. */}
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
