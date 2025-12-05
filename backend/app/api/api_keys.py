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


