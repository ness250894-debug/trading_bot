from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..core import auth
from ..core.database import DuckDBHandler
from pydantic import BaseModel
from ..core.rate_limit import limiter
from ..core.email_service import EmailService

email_service = EmailService()

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

@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint.
    Since we use stateless JWTs, the backend doesn't need to do much,
    but this endpoint allows the frontend to clear its state gracefully.
    """
    return {"status": "success", "message": "Logged out successfully"}

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
        # Use centralized deletion logic
        if db.delete_user(user_id):
            return {"status": "success", "message": "Account deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete account")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    """
    Initiates password reset flow.
    Sends an email with a reset token if the email exists.
    Always returns success to prevent email enumeration.
    """
    user = db.get_user_by_email(body.email)
    if user:
        token = db.create_reset_token(user['id'])
        if token:
            # Construct reset link (assuming frontend is at origin)
            origin = request.headers.get('origin', 'http://localhost:5173')
            reset_links = f"{origin}/reset-password?token={token}"
            
            # Send email (async in background would be better, but simple for now)
            email_service.send_reset_email(user['email'], reset_links)
            
    return {"status": "success", "message": "If this email is registered, you will receive a reset link."}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8: raise ValueError('Password too short')
        if not any(c.isupper() for c in v): raise ValueError('Missing uppercase')
        if not any(c.islower() for c in v): raise ValueError('Missing lowercase')
        if not any(c.isdigit() for c in v): raise ValueError('Missing digit')
        return v

@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest):
    """
    Verifies token and resets password.
    """
    user_id = db.verify_reset_token(body.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    hashed_password = auth.get_password_hash(body.new_password)
    
    # Update password
    # We need a direct method in UserRepository or via generic update.
    # Currently we lack 'update_password', so we'll access raw query via repo connection or add method.
    # Ideally add method to UserRepository. For now, let's assume we can add it or execute raw.
    # Checking UserRepository... we don't have update_password exposed in Database delegates yet.
    # Let's check repository files.
    
    # Actually, we should check if we can update it. 
    # Since I cannot modify UserRepository in this chunk easily, I will use raw execution if needed
    # BUT clean code prefers a method. I will add 'update_password' to UserRepository in a separate step?
    # No, I should add it here if possible or use db.conn directly if exposed.
    # db is DuckDBHandler, which has .conn.
    
    try:
        db.conn.execute("UPDATE users SET hashed_password = ? WHERE id = ?", [hashed_password, user_id])
        db.consume_reset_token(body.token)
        return {"status": "success", "message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to reset password")
