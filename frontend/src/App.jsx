import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Optimization from './pages/Optimization';
import Backtest from './pages/Backtest';
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

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <ToastProvider>
          <ModalProvider>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/strategies" element={<Strategies />} />
                <Route path="/optimization" element={<Optimization />} />
                <Route path="/backtest" element={<Backtest />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ModalProvider>
        </ToastProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
