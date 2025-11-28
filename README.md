# Trading Bot - Production System

Multi-tenant cryptocurrency trading bot with support for multiple strategies and risk management.

## Features

- ✅ Multi-tenant architecture (per-user bot instances)
- ✅ Encrypted API key storage
- ✅ JWT authentication
- ✅ Multiple trading strategies (Mean Reversion, SMA Crossover, MACD, RSI, Combined)
- ✅ Risk management (Take Profit, Stop Loss)
- ✅ Backtesting and optimization
- ✅ Real-time WebSocket logs
- ✅ Paper trading mode
- ✅ Rate limiting and audit logging

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# Required
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: Exchange keys (users can add their own via API)
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
BYBIT_DEMO=True

# Optional: Telegram notifications
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

Generate secrets:
```bash
python generate_jwt_secret.py
```

### 3. Migrate Existing Data (if upgrading)

```bash
python migrate_database.py
```

### 4. Start Server

```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

## Usage

### 1. Create Account
- Navigate to `/signup`
- Create user account

### 2. Add API Keys
- Go to Settings
- Add your exchange API keys (encrypted storage)

### 3. Configure Strategy
- Navigate to Strategies
- Select strategy and parameters
- Set risk management (TP/SL)

### 4. Start Bot
- Go to Dashboard
- Click "Start Bot"
- Monitor performance in real-time

## API Documentation

See [API Documentation](./docs/api_documentation.md) for detailed endpoint reference.

## Architecture

### Backend Structure
```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core bot logic
│   │   ├── bot.py              # Main bot loop
│   │   ├── bot_manager.py      # Multi-user bot manager
│   │   ├── client_manager.py   # Exchange client caching
│   │   ├── database.py         # DuckDB handler
│   │   ├── encryption.py       # API key encryption
│   │   └── strategies/         # Trading strategies
│   └── main.py       # FastAPI application
```

### Key Components

- **BotManager**: Manages multiple bot instances per user
- **ClientManager**: Caches exchange connections
- **DuckDB**: Stores users, strategies, trades, API keys
- **JWT Auth**: Secure user authentication
- **Rate Limiter**: 100 req/min per user

## Migration from Single-User

If upgrading from the old single-user system:

1. Run `python migrate_database.py`
2. Existing trades will be assigned to user ID 1
3. `config.json` will be imported to database
4. Bot no longer auto-starts (manual start required)

## Security Features

- ✅ JWT tokens from environment
- ✅ Configurable CORS
- ✅ Encrypted API keys (per-user)
- ✅ Sanitized error messages
- ✅ Request timeouts (10s)
- ✅ Rate limiting
- ✅ Audit logging

## Production Deployment

1. Set strong `JWT_SECRET_KEY`
2. Configure `CORS_ORIGINS` for your domain
3. Use HTTPS (reverse proxy recommended)
4. Set up monitoring for `/api/health/detailed`
5. Configure log rotation (automatic, 10MB files)

## Health Monitoring

```bash
curl http://your-domain/api/health/detailed
```

Returns status of:
- Database
- Exchange connectivity
- Telegram configuration
- Active bot instances

## Support

- API Documentation: `/docs/api_documentation.md`
- Completion Report: See artifacts for full implementation details

## License

MIT
