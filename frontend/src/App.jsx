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

// NavItem and Layout components are likely moved to ./components/Layout.js
// For the purpose of this edit, we'll assume they are no longer needed in App.js
// or are handled by the new Layout component.
// If they are still needed in App.js, they should be kept.
// Given the instruction to replace the Router structure with Layout, and the new Layout import,
// it's implied that the Layout component definition itself is moved.
// The NavItem component was a helper for the old Layout, so it's also likely moved or removed.

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/optimization" element={<Optimization />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
