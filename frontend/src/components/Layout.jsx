import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Settings, TrendingUp, History, Zap, Menu, X, Bell, DollarSign, Shield } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import UserDropdown from './UserDropdown';

const SidebarItem = ({ to, icon: Icon, label }) => {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${isActive
                    ? 'bg-primary/20 text-primary shadow-lg shadow-primary/10 border border-primary/20'
                    : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                }`
            }
        >
            <Icon size={20} className="relative z-10" />
            <span className="font-medium relative z-10">{label}</span>
            {/* Hover Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </NavLink>
    );
};

export default function Layout({ children }) {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
    const [isAdmin, setIsAdmin] = React.useState(false);
    const [currentUser, setCurrentUser] = React.useState(null);
    const location = useLocation();
    const navigate = useNavigate();

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
                console.error('Failed to fetch user data:', error);
            }
        };
        fetchCurrentUser();
    }, []);



    return (
        <div className="h-screen flex bg-background text-foreground overflow-hidden font-sans selection:bg-primary/30">
            {/* Background Ambient Glow */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-[120px]" />
            </div>

            {/* Sidebar */}
            <aside className={`
                fixed inset-y-0 left-0 z-50 w-64 bg-card/50 backdrop-blur-xl border-r border-white/10 transform transition-transform duration-300 ease-in-out
                flex flex-col
                ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
                md:relative md:translate-x-0
            `}>
                <div className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                            <Zap size={20} className="text-white" fill="currentColor" />
                        </div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            NovaBot
                        </h1>
                    </div>
                    <button onClick={() => setIsMobileMenuOpen(false)} className="md:hidden text-muted-foreground">
                        <X size={24} />
                    </button>
                </div>

            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
                {/* Top Bar */}
                <header className="h-16 px-8 flex items-center justify-between bg-transparent z-40">
                    <button onClick={() => setIsMobileMenuOpen(true)} className="md:hidden text-foreground">
                        <Menu size={24} />
                    </button>

                    {/* Breadcrumbs / Page Title could go here */}
                    <div className="hidden md:block">
                        {/* Spacer */}
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2 rounded-full hover:bg-white/5 text-muted-foreground hover:text-foreground transition-colors relative">
                            <Bell size={20} />
                            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border border-background" />
                        </button>
                        {currentUser && <UserDropdown user={currentUser} />}
                    </div>
                </header>

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-8 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
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
                        </motion.div>
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
}
