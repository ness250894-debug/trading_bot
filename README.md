# Trading Bot - Production System

A high-performance, multi-tenant cryptocurrency trading platform featuring advanced strategy formulation, vectorized backtesting, and a robust subscription management system. Built with FastAPI, DuckDB, and React.

## 🚀 Key Features

### 🤖 Advanced Trading Engine
- **Multi-Strategy Support**: Mean Reversion, SMA Crossover, MACD, RSI, Bollinger Breakout, Momentum, DCA Dip.
- **Visual Strategy Builder**: Create complex strategies using a drag-and-drop interface without coding.
- **Paper Trading**: Simulate trading with virtual funds before going live.
- **Real-Time Execution**: Low-latency trade execution via CCXT.

### 📊 Backtesting & Optimization
- **Vectorized Backtester**: High-speed, Pandas-based backtesting engine.
- **Hyperopt Optimization**: Automated parameter tuning to maximize strategy performance.
- **Detailed Analytics**: Win rate, drawdown, Sharpe ratio, and visual equity curves.

### 🏢 Enterprise-Grade Architecture
- **Multi-Tenant**: Secure isolation of user data and bot instances.
- **Subscription System**: Built-in tier management (Free, Basic, Pro, Elite) with granular feature gating.
- **Singleton Database**: Robust, single-file DuckDB architecture for data consistency (`data/trading_bot.duckdb`).
- **Security**: AES-256 encryption for API keys, JWT authentication, and strict rate limiting.

### 🛠️ Admin & Management
- **Admin Dashboard**: User management, plan configuration, and system monitoring.
- **Audit Logging**: Comprehensive tracking of all user actions and system events.
- **Health Monitoring**: Detailed system health endpoints for uptime monitoring.

---

## 🏁 Project Requirements

This project is a specification for a high-performance, multi-tenant cryptocurrency trading platform.

### Core Requirements

1.  **Trading Engine**: Support for multiple strategies (Mean Reversion, SMA, MACD, etc.) with real-time execution.
2.  **Backtesting**: Vectorized backtesting engine with Hyperopt optimization.
3.  **Architecture**: Multi-tenant system with isolated user data and bot instances.
4.  **Security**: AES-256 for API keys, strict JWT authentication.

### Deliverables

The development team is expected to build the system according to the specifications in the `docs/` folder:

*   **API Specification**: `docs/api_documentation.md`
*   **Security Protocols**: `docs/SECURITY.md`
*   **Database Schema**: `docs/STORAGE_PATTERNS.md`
*   **Reliability**: `docs/FAILSAFE_ANALYSIS.md`

### Environment

The application should be configured using key-value pairs as defined in `.env.example`.
