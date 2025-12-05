from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..core import auth
from ..core.database import DuckDBHandler
from pydantic import BaseModel
from ..core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])
db = DuckDBHandler()

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional

class UserCreate(BaseModel):
    """User creation model with comprehensive validation."""
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)
    nickname: Optional[str] = Field(None, max_length=50)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('nickname')
    def nickname_validation(cls, v):
        """Validate nickname."""
        if v is not None:
            # Remove leading/trailing whitespace
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) > 50:
                raise ValueError('Nickname must be 50 characters or less')
            # Basic XSS prevention - reject HTML-like content
            if '<' in v or '>' in v:
                raise ValueError('Nickname contains invalid characters')
        return v

@router.post("/signup", response_model=auth.Token)
@limiter.limit("5/minute")  # Max 5 signups per minute per IP
async def signup(request: Request, user: UserCreate):
    db_user = db.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    if db.create_user(user.email, hashed_password, user.nickname):
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.post("/login", response_model=auth.Token)
@limiter.limit("10/minute")  # Max 10 login attempts per minute per IP
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user_by_email(form_data.username)
    if not user or not auth.verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(auth.get_current_user)):
    """Get current user information including admin status."""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "nickname": current_user.get("nickname"),
        "is_admin": current_user.get("is_admin", False)
    }

class ProfileUpdate(BaseModel):
    nickname: str

@router.put("/update-profile")
async def update_profile(profile: ProfileUpdate, current_user: dict = Depends(auth.get_current_user)):
    """Update user profile (nickname)."""
    if db.update_user_nickname(current_user["id"], profile.nickname):
        return {"status": "success", "message": "Profile updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update profile")

@router.delete("/account")
async def delete_account(current_user: dict = Depends(auth.get_current_user)):
    """
    Permanently delete user account and all associated data.
    This action is irreversible.
    """
    user_id = current_user["id"]
    
    try:
        # Delete all user data in order (respecting foreign keys)
        # 1. Delete bot configurations
        db.conn.execute("DELETE FROM bot_configurations WHERE user_id = ?", [user_id])
        
        # 2. Delete API keys
        db.conn.execute("DELETE FROM api_keys WHERE user_id = ?", [user_id])
        
        # 3. Delete trades
        db.conn.execute("DELETE FROM trades WHERE user_id = ?", [user_id])
        
        # 4. Delete subscriptions
        db.conn.execute("DELETE FROM subscriptions WHERE user_id = ?", [user_id])
        
        # 5. Delete price alerts
        db.conn.execute("DELETE FROM price_alerts WHERE user_id = ?", [user_id])
        
        # 6. Delete watchlists
        db.conn.execute("DELETE FROM watchlists WHERE user_id = ?", [user_id])
        
        # 7. Delete risk profile
        db.conn.execute("DELETE FROM risk_profiles WHERE user_id = ?", [user_id])
        
        # 8. Delete user preferences
        db.conn.execute("DELETE FROM user_preferences WHERE user_id = ?", [user_id])
        
        # 9. Finally, delete the user
        db.conn.execute("DELETE FROM users WHERE id = ?", [user_id])
        
        return {"status": "success", "message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
