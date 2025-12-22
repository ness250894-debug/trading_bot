# API Versioning Strategy

## Current State
All endpoints are under `/api/*` without version namespace.

## Recommendation for Future

When implementing breaking changes, use API versioning:

### Approach 1: URL Path Versioning (Recommended)
```
/api/v1/auth/login
/api/v2/auth/login  # New version with breaking changes
```

### Approach 2: Header Versioning
```
GET /api/auth/login
Headers: Accept: application/vnd.tradingbot.v1+json
```

## Implementation Guide

### Step 1: Create Versioned Routers
```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from . import auth, trades, strategies

router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(auth.router)
router_v1.include_router(trades.router)
router_v1.include_router(strategies.router)
```

### Step 2: Register in main.py
```python
from .api.v1 import router_v1
from .api.v2 import router_v2

app.include_router(router_v1, prefix="/api")
app.include_router(router_v2, prefix="/api")
```

### Step 3: Deprecation Strategy
1. Announce deprecation in v1 responses
2. Add `X-API-Deprecated` header
3. Set sunset date
4. Remove after 6-12 months

## When to Version

✅ **Do version when:**
- Changing response structure
- Removing fields
- Changing authentication
- Major behavioral changes

❌ **Don't version when:**
- Adding optional fields
- Bug fixes
- Performance improvements
- Internal refactoring

## Current Recommendation

**No versioning needed now** because:
- API is still evolving
- No breaking changes planned
- Limited external consumers
- Adds unnecessary complexity

**Implement versioning when:**
- Preparing for public API
- Supporting multiple client versions
- Planning breaking changes
