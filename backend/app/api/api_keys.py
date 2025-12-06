from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, validator
from typing import Optional
import logging
from ..core import auth
from ..core.database import DuckDBHandler
from ..core.encryption import EncryptionHelper
from ..core.rate_limiter import rate_limiter

router = APIRouter()
logger = logging.getLogger("API.ApiKeys")
db = DuckDBHandler()

# Initialize encryptor once at module level
try:
    encryptor = EncryptionHelper()
except ValueError as e:
    logger.error(f"Failed to initialize encryption: {e}")
    encryptor = None

class ApiKeyRequest(BaseModel):
    exchange: str  # e.g., "bybit", "binance"
    api_key: str
    api_secret: str
    
    @validator('exchange')
    def validate_exchange(cls, v):
        # Whitelist allowed exchanges
        allowed = ['bybit', 'binance', 'okx', 'kraken', 'coinbase']
        if v.lower() not in allowed:
            raise ValueError(f'Exchange must be one of: {", ".join(allowed)}')
        return v.lower()
    
    @validator('api_key', 'api_secret')
    def validate_key_length(cls, v):
        if len(v) < 10 or len(v) > 500:
            raise ValueError('API key/secret length must be between 10 and 500 characters')
        return v

class ApiKeyResponse(BaseModel):
    exchange: str
    has_key: bool

@router.post("/api-keys")
async def save_api_key(request: ApiKeyRequest, current_user: dict = Depends(auth.get_current_user), req: Request = None):
    """Save or update API keys for a specific exchange."""
    # Rate limiting: 10 requests per minute
    if not rate_limiter.is_allowed(str(current_user['id']), limit=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    if encryptor is None:
        raise HTTPException(status_code=500, detail="Encryption service unavailable")
    
    try:
        # Encrypt the keys
        api_key_encrypted = encryptor.encrypt(request.api_key)
        api_secret_encrypted = encryptor.encrypt(request.api_secret)
        
        # Save to database
        success = db.save_api_key(
            user_id=current_user['id'],
            exchange=request.exchange,
            api_key_encrypted=api_key_encrypted,
            api_secret_encrypted=api_secret_encrypted
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save API key")
        
        # Audit log
        ip_address = req.client.host if req and req.client else None
        db.log_audit(
            user_id=current_user['id'],
            action="create_or_update",
            resource_type="api_key",
            resource_id=request.exchange,
            details=f"Saved API keys for {request.exchange}",
            ip_address=ip_address
        )
        
        return {"status": "success", "message": f"API keys saved for {request.exchange}"}
    
    except ValueError as e:
        # Validation errors
        logger.warning(f"Validation error saving API key: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/api-keys")
async def list_api_keys(current_user: dict = Depends(auth.get_current_user)):
    """List all saved API keys for the user (keys are masked for security)."""
    try:
        # Get all API keys for the user
        result = db.conn.execute(
            "SELECT exchange, api_key FROM api_keys WHERE user_id = ?",
            [current_user['id']]
        ).fetchall()
        
        keys = []
        for row in result:
            exchange, encrypted_key = row
            # Decrypt and mask the key
            try:
                if encryptor:
                    decrypted = encryptor.decrypt(encrypted_key)
                    # Mask: show first 4 and last 4 chars
                    if len(decrypted) >= 8:
                        masked = decrypted[:4] + '••••••••' + decrypted[-4:]
                    else:
                        masked = '••••••••'
                else:
                    masked = '••••••••'
            except:
                masked = '••••••••'
            
            keys.append({
                'exchange': exchange,
                'api_key_masked': masked,
                'has_key': True
            })
        
        return {"keys": keys}
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.get("/exchange-balances")
async def get_exchange_balances(current_user: dict = Depends(auth.get_current_user)):
    """Fetch balances from all connected exchanges."""
    try:
        # Get all API keys for the user
        result = db.conn.execute(
            "SELECT exchange, api_key, api_secret FROM api_keys WHERE user_id = ?",
            [current_user['id']]
        ).fetchall()
        
        if not result:
            return {
                "total_usdt": 0.0,
                "exchanges": [],
                "has_keys": False
            }
        
        # Import exchange clients
        from ..core.exchange.client import ByBitClient
        from ..core.exchange.binance_client import BinanceClient
        from ..core.exchange.okx_client import OKXClient
        from ..core.exchange.kraken_client import KrakenClient
        from ..core.exchange.coinbase_client import CoinbaseClient
        
        exchange_clients = {
            'bybit': ByBitClient,
            'binance': BinanceClient,
            'okx': OKXClient,
            'kraken': KrakenClient,
            'coinbase': CoinbaseClient
        }
        
        exchange_balances = []
        total_usdt = 0.0
        
        for row in result:
            exchange_name, encrypted_key, encrypted_secret = row
            
            try:
                if not encryptor:
                    continue
                    
                # Decrypt credentials
                api_key = encryptor.decrypt(encrypted_key)
                api_secret = encryptor.decrypt(encrypted_secret)
                
                # Get the client class
                ClientClass = exchange_clients.get(exchange_name.lower())
                if not ClientClass:
                    continue
                
                # Initialize client (demo=False for live balances)
                client = ClientClass(api_key, api_secret, demo=False, timeout=15000)
                
                # Fetch balance
                balance = client.fetch_balance()
                
                if balance:
                    # Get USDT balance (most common stablecoin)
                    usdt_total = 0.0
                    usdt_free = 0.0
                    
                    # Handle different balance structures
                    if 'USDT' in balance:
                        if isinstance(balance['USDT'], dict):
                            usdt_total = float(balance['USDT'].get('total', 0) or 0)
                            usdt_free = float(balance['USDT'].get('free', 0) or 0)
                        else:
                            usdt_total = float(balance['USDT'] or 0)
                    elif 'total' in balance and 'USDT' in balance.get('total', {}):
                        usdt_total = float(balance['total'].get('USDT', 0) or 0)
                        usdt_free = float(balance.get('free', {}).get('USDT', 0) or 0)
                    
                    exchange_balances.append({
                        'exchange': exchange_name,
                        'usdt_total': usdt_total,
                        'usdt_free': usdt_free,
                        'status': 'connected'
                    })
                    
                    total_usdt += usdt_total
                else:
                    exchange_balances.append({
                        'exchange': exchange_name,
                        'usdt_total': 0.0,
                        'usdt_free': 0.0,
                        'status': 'error'
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to fetch balance from {exchange_name}: {e}")
                exchange_balances.append({
                    'exchange': exchange_name,
                    'usdt_total': 0.0,
                    'usdt_free': 0.0,
                    'status': 'error',
                    'error': str(e)[:100]  # Truncate error message
                })
        
        return {
            "total_usdt": total_usdt,
            "exchanges": exchange_balances,
            "has_keys": len(exchange_balances) > 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching exchange balances: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch exchange balances")


@router.get("/api-keys/{exchange}", response_model=ApiKeyResponse)
async def get_api_key_status(exchange: str, current_user: dict = Depends(auth.get_current_user), req: Request = None):
    """Check if user has API keys configured for a specific exchange."""
    # Rate limiting: 30 requests per minute
    if not rate_limiter.is_allowed(str(current_user['id']) + "_read", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    try:
        # Validate exchange parameter
        allowed = ['bybit', 'binance', 'okx', 'kraken', 'coinbase']
        if exchange.lower() not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid exchange: {exchange}")
        
        result = db.get_api_key(user_id=current_user['id'], exchange=exchange.lower())
        
        # Audit log
        ip_address = req.client.host if req and req.client else None
        db.log_audit(
            user_id=current_user['id'],
            action="read",
            resource_type="api_key",
            resource_id=exchange.lower(),
            details=f"Checked API key status for {exchange}",
            ip_address=ip_address
        )
        
        return ApiKeyResponse(
            exchange=exchange.lower(),
            has_key=result is not None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking API key status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/api-keys/{exchange}")
async def delete_api_key(exchange: str, current_user: dict = Depends(auth.get_current_user), req: Request = None):
    """Delete API keys for a specific exchange."""
    # Rate limiting: 10 requests per minute
    if not rate_limiter.is_allowed(str(current_user['id']), limit=10, window_seconds=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    try:
        # Validate exchange parameter
        allowed = ['bybit', 'binance', 'okx', 'kraken', 'coinbase']
        if exchange.lower() not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid exchange: {exchange}")
        
        success = db.delete_api_key(user_id=current_user['id'], exchange=exchange.lower())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete API key")
        
        # Audit log
        ip_address = req.client.host if req and req.client else None
        db.log_audit(
            user_id=current_user['id'],
            action="delete",
            resource_type="api_key",
            resource_id=exchange.lower(),
            details=f"Deleted API keys for {exchange}",
            ip_address=ip_address
        )
        
        return {"status": "success", "message": f"API keys deleted for {exchange}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


