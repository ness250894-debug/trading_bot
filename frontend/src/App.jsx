import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import StrategyBuilder from './pages/StrategyBuilder';
import Marketplace from './pages/Marketplace';
import Optimization from './pages/Optimization';
import Backtest from './pages/Backtest';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Settings from './pages/Settings';
import Pricing from './pages/Pricing';
import AdminDashboard from './pages/AdminDashboard';
import { ToastProvider } from './components/Toast';
import { ModalProvider } from './components/Modal';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-8">
          <div className="max-w-2xl w-full bg-gray-800 rounded-xl p-8 border border-red-500/30">
            <h1 className="text-2xl font-bold text-red-500 mb-4">Something went wrong</h1>
            <p className="text-gray-300 mb-4">The application crashed. Here is the error details:</p>
            <pre className="bg-black/50 p-4 rounded-lg overflow-auto text-xs font-mono text-red-300 mb-4">
              {this.state.error && this.state.error.toString()}
            </pre>
            <details className="text-xs text-gray-500">
              <summary className="cursor-pointer hover:text-gray-300">Component Stack</summary>
              <pre className="mt-2 whitespace-pre-wrap">
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <ToastProvider>
          <ModalProvider>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />

              {/* Protected Routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/strategies" element={
                <ProtectedRoute>
                  <Layout>
                    <Strategies />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/strategy-builder" element={
                <ProtectedRoute>
                  <Layout>
                    <StrategyBuilder />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/marketplace" element={
                <ProtectedRoute>
                  <Layout>
                    <Marketplace />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/optimization" element={
                <ProtectedRoute>
                  <Layout>
                    <Optimization />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/backtest" element={
                <ProtectedRoute>
                  <Layout>
                    <Backtest />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/settings" element={
                <ProtectedRoute>
                  <Layout>
                    <Settings />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/pricing" element={
                <ProtectedRoute>
                  <Layout>
                    <Pricing />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/admin" element={
                <ProtectedRoute>
                  <Layout>
                    <AdminDashboard />
                  </Layout>
                </ProtectedRoute>
              } />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ModalProvider>
        </ToastProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
