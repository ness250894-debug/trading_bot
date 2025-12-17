import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Settings, TrendingUp, History, Zap, Menu, X, Bell, DollarSign, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import UserDropdown from './UserDropdown';
import ExchangeLinks from './ExchangeLinks';
import Disclaimer from './Disclaimer';

export default function Layout({ children }) {
    const [isAdmin, setIsAdmin] = React.useState(false);
    const [currentUser, setCurrentUser] = React.useState(null);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
    const location = useLocation();

    React.useEffect(() => {
        const fetchCurrentUser = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;

                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const user = await response.json();
                    setCurrentUser(user);
                    setIsAdmin(user.is_admin);
                }
            } catch (error) {
                // Silent fail - not critical
            }
        };
        fetchCurrentUser();
    }, []);

    // Close mobile menu when route changes
    React.useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [location.pathname]);

    const menuItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
        { icon: Settings, label: 'Strategies', path: '/strategies' },
        { icon: Zap, label: 'Visual Builder', path: '/strategy-builder' },
        { icon: TrendingUp, label: 'Social Trading', path: '/marketplace' },
        { icon: TrendingUp, label: 'Optimization', path: '/optimization' },
        { icon: DollarSign, label: 'Pricing', path: '/pricing' },
    ];

    if (isAdmin) {
        menuItems.push({ icon: Shield, label: 'Admin Panel', path: '/admin' });
    }

    return (
        <div className="h-screen flex flex-col bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30">
            {/* Background Ambient Glow */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-[120px]" />
            </div>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsMobileMenuOpen(false)}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 md:hidden"
                        />
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                            className="fixed top-0 left-0 w-[80%] max-w-sm h-full bg-card border-r border-white/10 z-50 md:hidden p-6 shadow-2xl overflow-y-auto"
                        >
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                                        <Zap size={20} className="text-white" fill="currentColor" />
                                    </div>
                                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                                        NovaBot
                                    </span>
                                </div>
                                <button
                                    onClick={() => setIsMobileMenuOpen(false)}
                                    className="p-2 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <nav className="space-y-2">
                                <NavLink
                                    to="/main"
                                    className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive ? 'bg-primary/20 text-primary font-medium' : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'}`}
                                >
                                    <LayoutDashboard size={20} />
                                    Main Overview
                                </NavLink>

                                <div className="my-4 border-t border-white/10" />

                                {menuItems.map((item) => (
                                    <NavLink
                                        key={item.path}
                                        to={item.path}
                                        className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive ? 'bg-primary/20 text-primary font-medium' : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'}`}
                                    >
                                        <item.icon size={20} />
                                        {item.label}
                                    </NavLink>
                                ))}
                            </nav>

                            {currentUser && (
                                <div className="mt-8 pt-8 border-t border-white/10">
                                    <div className="flex items-center gap-3 px-4 mb-4">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary to-purple-600 flex items-center justify-center text-white font-bold">
                                            {currentUser.nickname ? currentUser.nickname.substring(0, 2).toUpperCase() : 'U'}
                                        </div>
                                        <div>
                                            <p className="font-medium text-foreground">{currentUser.nickname || 'User'}</p>
                                            <p className="text-xs text-muted-foreground truncate max-w-[150px]">{currentUser.email}</p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* Top Bar */}
            <header className="h-16 px-4 md:px-8 flex items-center justify-between bg-transparent z-40 border-b border-white/5">
                <div className="flex items-center gap-4">
                    {/* Mobile Hamburger */}
                    <button
                        onClick={() => setIsMobileMenuOpen(true)}
                        className="md:hidden p-2 -ml-2 hover:bg-white/10 rounded-lg text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <Menu size={24} />
                    </button>

                    <NavLink to="/main" className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                            <Zap size={20} className="text-white" fill="currentColor" />
                        </div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 hidden md:block">
                            NovaBot
                        </h1>
                    </NavLink>
                </div>

                {/* Exchange Links */}
                <ExchangeLinks />

                <div className="flex items-center gap-4 flex-shrink-0">
                    <button className="p-2 rounded-full hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors relative">
                        <Bell size={20} />
                        <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-background" />
                    </button>
                    {currentUser && <UserDropdown user={currentUser} />}
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-8 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={location.pathname}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.2 }}
                        className="max-w-7xl mx-auto pb-20"
                    >
                        {children}

                        {/* Disclaimer at bottom of all pages */}
                        <div className="mt-12">
                            <Disclaimer compact />
                        </div>
                    </motion.div>
                </AnimatePresence>
            </main>
        </div>
    );
}
