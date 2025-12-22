# Storage Patterns Documentation

## Overview

This document outlines the standardized storage patterns used in the trading bot application after the localStorage centralization effort (Issue #7).

## Storage Architecture

### Two-Tier Storage System

1. **`secureStorage`** - For sensitive authentication data
2. **`useAppState`** - For application state with automatic persistence

---

## 1. Secure Storage (`secureStorage`)

**Location**: `frontend/src/lib/secureStorage.js`

**Purpose**: Handle authentication tokens securely using `sessionStorage` instead of `localStorage`.

### Why sessionStorage?

- ✅ **Auto-expires** when browser tab closes
- ✅ **Reduced XSS risk** - shorter exposure window
- ✅ **Better security** for sensitive tokens

### API

```javascript
import { secureStorage } from '@/lib/secureStorage';

// Store token
secureStorage.setToken(token);

// Retrieve token
const token = secureStorage.getToken();

// Clear token
secureStorage.clearToken();

// Store app state (uses localStorage)
secureStorage.setAppState(STORAGE_KEYS.SYMBOL, 'BTC/USDT');

// Retrieve app state
const symbol = secureStorage.getAppState(STORAGE_KEYS.SYMBOL);

// Clear app state
secureStorage.clearAppState(STORAGE_KEYS.SYMBOL);

// Clear everything
secureStorage.clearAll();
```

### Usage Example

```javascript
// In Signup.jsx
const handleSignup = async () => {
  const response = await api.post('/auth/signup', data);
  secureStorage.setToken(response.data.access_token);
  navigate('/dashboard');
};

// In api.js
const token = secureStorage.getToken();
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}
```

---

## 2. Application State Hook (`useAppState`)

**Location**: `frontend/src/hooks/useAppState.js`

**Purpose**: Manage application state with automatic persistence to `localStorage`.

### Benefits

✅ **Automatic persistence** - No manual `useEffect` needed  
✅ **Type-safe keys** - Uses `STORAGE_KEYS` constants  
✅ **Cleaner code** - Replaces 10+ lines with 1 line  
✅ **Consistent API** - Same as `useState`

### API

```javascript
import { useAppState } from '@/hooks/useAppState';
import { STORAGE_KEYS } from '@/constants/storageKeys';

// Just like useState, but auto-persisted!
const [symbol, setSymbol] = useAppState(STORAGE_KEYS.SYMBOL, 'BTC/USDT');
```

### Before vs After

**❌ OLD Pattern** (Manual localStorage + useEffect):
```javascript
const [symbol, setSymbol] = useState(() => 
  localStorage.getItem('symbol') || 'BTC/USDT'
);

useEffect(() => {
  localStorage.setItem('symbol', symbol);
}, [symbol]);
```

**✅ NEW Pattern** (useAppState):
```javascript
const [symbol, setSymbol] = useAppState(STORAGE_KEYS.SYMBOL, 'BTC/USDT');
```

### Usage Examples

**Optimization.jsx**:
```javascript
const [strategy, setStrategy] = useAppState(STORAGE_KEYS.STRATEGY, 'Mean Reversion');
const [symbol, setSymbol] = useAppState(STORAGE_KEYS.SYMBOL, 'BTC/USDT');
const [timeframe, setTimeframe] = useAppState(STORAGE_KEYS.TIMEFRAME, '1h');
const [leverage, setLeverage] = useAppState(STORAGE_KEYS.LEVERAGE, 10);
```

**Backtest.jsx**:
```javascript
const [symbol, setSymbol] = useAppState(STORAGE_KEYS.BACKTEST_SYMBOL, 'BTC/USDT');

// Reading one-time values
const suggestion = secureStorage.getAppState(STORAGE_KEYS.BACKTEST_PARAMS);
if (suggestion) {
  setSymbol(suggestion.symbol);
  secureStorage.clearAppState(STORAGE_KEYS.BACKTEST_PARAMS);
}
```

---

## 3. Storage Keys (`STORAGE_KEYS`)

**Location**: `frontend/src/constants/storageKeys.js`

**Purpose**: Centralized, type-safe storage key definitions.

### Benefits

✅ **No typos** - Autocomplete prevents errors  
✅ **Easy refactoring** - Change in one place  
✅ **Self-documenting** - Clear naming conventions

### Structure

```javascript
export const STORAGE_KEYS = {
  // Authentication
  TOKEN: 'auth_token',
  
  // Optimization State
  STRATEGY: 'optimization_strategy',
  SYMBOL: 'optimization_symbol',
  TIMEFRAME: 'optimization_timeframe',
  LEVERAGE: 'optimization_leverage',
  RANGES: 'optimization_ranges',
  
  // Ultimate Optimization
  ULTIMATE_SYMBOL: 'ultimate_symbol',
  ULTIMATE_RESULTS: 'ultimate_optimization_results',
  
  // Backtest State
  BACKTEST_SYMBOL: 'backtest_symbol',
  BACKTEST_PARAMS: 'backtest_params_suggestion',
  SUGGESTED_STRATEGY_PARAMS: 'suggested_strategy_params'
};
```

### Naming Convention

Format: `{feature}_{purpose}`

Examples:
- `optimization_symbol` - Symbol for optimization page
- `backtest_params` - Parameters passed to backtest
- `ultimate_results` - Results from ultimate optimization

---

## 4. Migration Checklist

When adding new persistent state:

### ✅ DO:

1. Add key to `STORAGE_KEYS` with descriptive name
2. Use `useAppState(STORAGE_KEYS.YOUR_KEY, defaultValue)`
3. Use `secureStorage` for tokens ONLY
4. Document the key's purpose in `storageKeys.js`

### ❌ DON'T:

1. ❌ Use `localStorage` directly
2. ❌ Use `sessionStorage` directly (except via secureStorage)
3. ❌ Hardcode string keys like `'myKey'`
4. ❌ Store tokens in localStorage

---

## 5. Common Patterns

### Pattern 1: Simple Persistent State

```javascript
const [value, setValue] = useAppState(STORAGE_KEYS.MY_KEY, defaultValue);
```

### Pattern 2: One-Time Data Transfer (Navigation)

**Sender (Optimization.jsx)**:
```javascript
const applyToBacktest = (result) => {
  secureStorage.setAppState(STORAGE_KEYS.BACKTEST_PARAMS, {
    symbol: result.symbol,
    strategy: result.strategy,
    params: result.params
  });
  navigate('/backtest');
};
```

**Receiver (Backtest.jsx)**:
```javascript
useEffect(() => {
  const params = secureStorage.getAppState(STORAGE_KEYS.BACKTEST_PARAMS);
  if (params) {
    applyParameters(params);
    secureStorage.clearAppState(STORAGE_KEYS.BACKTEST_PARAMS); // Clear after use
  }
}, []);
```

### Pattern 3: Conditional Persistence

```javascript
// Only persist if user is logged in
const [settings, setSettings] = useAppState(
  STORAGE_KEYS.USER_SETTINGS, 
  defaultSettings
);
```

---

## 6. Security Considerations

### Token Storage

**Always use `secureStorage.setToken()`** for authentication tokens:
- ✅ Stored in `sessionStorage` (expires on tab close)
- ✅ Cleared on logout
- ✅ HttpOnly alternative not available in SPA

### Sensitive Data

**Do NOT store** in localStorage:
- ❌ API keys
- ❌ Passwords
- ❌ Personal information
- ❌ Payment details

**OK to store** in localStorage:
- ✅ UI preferences (theme, layout)
- ✅ Form state (symbol, timeframe)
- ✅ Non-sensitive configuration

---

## 7. Testing

### Testing Components with useAppState

```javascript
import { render } from '@testing-library/react';

// Mock localStorage
beforeEach(() => {
  localStorage.clear();
});

test('persists state', () => {
  const { rerender } = render(<MyComponent />);
  // Component uses useAppState internally
  // Check localStorage was updated
  expect(localStorage.getItem('my_key')).toBe('expected_value');
});
```

---

## 8. Troubleshooting

### State Not Persisting?

1. Check you're using `useAppState` not `useState`
2. Verify key is in `STORAGE_KEYS`
3. Check browser DevTools → Application → Local Storage

### Token Not Working?

1. Verify using `secureStorage.setToken()`
2. Check Session Storage (not Local Storage!)
3. Token expires when tab closes (expected behavior)

### Clear All Storage

```javascript
// Development/debugging only
secureStorage.clearAll();
```

---

## Summary

| Storage Type | Use Case | Location | Expires |
|-------------|----------|----------|---------|
| `secureStorage.setToken()` | Auth tokens | Session Storage | Tab close |
| `useAppState()` | App state | Local Storage | Never |
| `secureStorage.setAppState()` | One-time data | Local Storage | Manual clear |

**Migration Status**: ✅ **100% Complete** - All `localStorage` calls migrated to these patterns.
