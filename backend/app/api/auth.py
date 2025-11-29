from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..core import auth
from ..core.database import DuckDBHandler
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])
db = DuckDBHandler()

class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str = None

@router.post("/signup", response_model=auth.Token)
async def signup(user: UserCreate):
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
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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
