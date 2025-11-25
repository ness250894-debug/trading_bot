import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FlaskConical, BrainCircuit, Settings, Activity, Zap, Wallet } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Backtest from './pages/Backtest';
import Strategies from './pages/Strategies';
import Optimization from './pages/Optimization';
import { useState, useEffect } from 'react';
import axios from 'axios';

function BalanceDisplay() {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBalance = async () => {
    try {
      const res = await axios.get('/api/balance');
      setBalance(res.data);
    } catch (err) {
      console.error("Failed to fetch balance", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
    const interval = setInterval(fetchBalance, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="animate-pulse h-12 bg-muted rounded-lg"></div>;
  if (!balance) return null;

  const totalUSDT = balance.total?.USDT || 0;
  const freeUSDT = balance.free?.USDT || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-3 shadow-sm">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        <Wallet size={14} />
        <span className="text-xs font-medium uppercase tracking-wider">Wallet Balance</span>
      </div>
      <div className="text-lg font-bold text-foreground">
        ${totalUSDT.toFixed(2)}
      </div>
      <div className="text-xs text-muted-foreground mt-1 flex justify-between">
        <span>Available:</span>
        <span className="text-primary font-medium">${freeUSDT.toFixed(2)}</span>
      </div>
    </div>
  );
}

function NavItem({ to, icon: Icon, label }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link to={to} className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}>
      <Icon size={20} />
      <span className="font-medium">{label}</span>
    </Link>
  );
}

function Layout({ children }) {
  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <div className="w-64 border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Activity className="text-primary" />
            TradingBot
          </h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />
          <NavItem to="/backtest" icon={FlaskConical} label="Backtest Lab" />
          <NavItem to="/optimize" icon={Zap} label="Optimization" />
          <NavItem to="/strategies" icon={BrainCircuit} label="Strategies" />
          <NavItem to="/settings" icon={Settings} label="Settings" />
        </nav>

        {/* Balance Display */}
        <div className="px-6 py-4 border-t border-border bg-muted/10">
          <BalanceDisplay />
        </div>

        <div className="px-6 py-2 pb-4 text-xs text-muted-foreground flex justify-between items-center">
          <span>v1.0.0</span>
          <span className="flex items-center gap-1 text-green-500"><div className="w-2 h-2 rounded-full bg-green-500"></div> Connected</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/optimize" element={<Optimization />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/settings" element={<div className="p-8">Settings (Coming Soon)</div>} />
        </Routes>
      </Layout>
    </Router>
  );
}
