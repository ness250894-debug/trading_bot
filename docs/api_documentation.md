# API Documentation - Multi-Tenant Trading Bot

## Base URL
```
http://localhost:8000/api
```

---

## Authentication

### POST `/auth/signup`
Create a new user account.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=securepassword123
```

**Response:**
```json
{
  "message": "User created successfully"
}
```

---

### POST `/auth/login`
Login and receive JWT token.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=securepassword123
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## Bot Control

All bot endpoints require `Authorization: Bearer {token}` header.

### POST `/start`
Start the user's bot instance.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "status": "success",
  "message": "Bot started"
}
```

---

### POST `/stop`
Stop the user's bot instance.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "status": "success",
  "message": "Bot stopped"  
}
```

---

### GET `/status`
Get current bot status and configuration.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "status": "Active",
  "is_running": true,
  "balance": {
    "total": 1000.50,
    "free": 950.25,
    "used": 50.25
  },
  "total_pnl": 125.75,
  "active_trades": 1,
  "config": {
    "symbol": "BTC/USDT",
    "timeframe": "1m",
    "amount_usdt": 10.0,
    "strategy": "mean_reversion",
    "dry_run": true,
    "take_profit_pct": 0.01,
    "stop_loss_pct": 0.005,
    "parameters": {}
  }
}
```

---

### POST `/config`
Update bot configuration (saved to database).

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1m",
  "amount_usdt": 10.0,
  "strategy": "mean_reversion",
  "dry_run": true,
  "take_profit_pct": 0.01,
  "stop_loss_pct": 0.005,
  "parameters": {}
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Config updated and bot restarted"
}
```

---

## Migration Notes

### Breaking Changes from Single-User

1. **Bot Start**: No longer automatic, must call `/start`
2. **Config**: Saved to database, not `config.json`
3. **API Keys**: Per-user, stored encrypted
4. **Data**: Isolated per user

### Migration Steps

1. Run `migrate_database.py` to add `user_id` to existing data
2. Update frontend to use new API structure
3. Users must signup/login
4. Users must configure their bot via `/config`
5. Users must explicitly start bot via `/start`
