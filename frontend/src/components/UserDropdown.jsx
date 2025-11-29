import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User, ChevronDown, LogOut, LayoutDashboard, Settings, TrendingUp, History, Zap, DollarSign, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function UserDropdown({ user }) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();
    const location = useLocation();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/');
    };

    const handleNavigate = (path) => {
        navigate(path);
        setIsOpen(false);
    };

    const menuItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
        { icon: Settings, label: 'Strategies', path: '/strategies' },
        { icon: Zap, label: 'Visual Builder', path: '/strategy-builder' },
        { icon: TrendingUp, label: 'Social Trading', path: '/marketplace' },
        { icon: TrendingUp, label: 'Optimization', path: '/optimization' },
        { icon: History, label: 'Backtest', path: '/backtest' },
        { icon: DollarSign, label: 'Pricing', path: '/pricing' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    if (user?.is_admin) {
        menuItems.push({ icon: Shield, label: 'Admin Panel', path: '/admin' });
    }

    const displayName = user?.nickname || user?.email?.split('@')[0] || 'User';
    const initials = displayName.substring(0, 2).toUpperCase();

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
            >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-primary to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                    {initials}
                </div>
                <div className="hidden md:block text-left">
                    <p className="text-sm font-medium text-foreground">{displayName}</p>
                    <p className="text-xs text-muted-foreground">ID: {user?.id}</p>
                </div>
                <ChevronDown
                    size={16}
                    className={`text-muted-foreground transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 mt-2 w-64 bg-card/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
                    >
                        {/* User Info Header */}
                        <div className="px-4 py-3 border-b border-white/10 bg-gradient-to-r from-primary/10 to-purple-500/10">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary to-purple-600 flex items-center justify-center text-white font-bold">
                                    {initials}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-foreground truncate">{displayName}</p>
                                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                                    <p className="text-xs text-muted-foreground">ID: {user?.id}</p>
                                </div>
                            </div>
                        </div>

                        {/* Navigation Items */}
                        <div className="py-2 max-h-96 overflow-y-auto">
                            {menuItems.map((item, index) => {
                                const Icon = item.icon;
                                const isActive = location.pathname === item.path;
                                return (
                                    <button
                                        key={index}
                                        onClick={() => handleNavigate(item.path)}
                                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${isActive
                                                ? 'bg-primary/20 text-primary'
                                                : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                                            }`}
                                    >
                                        <Icon size={18} />
                                        <span className="text-sm font-medium">{item.label}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Logout Button */}
                        <div className="border-t border-white/10 p-2">
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                            >
                                <LogOut size={18} />
                                <span className="text-sm font-medium">Sign Out</span>
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
