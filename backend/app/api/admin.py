from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from ..core import auth
from ..core.database import DuckDBHandler
from ..core.rate_limit import limiter

router = APIRouter()
db = DuckDBHandler()

class UserUpdate(BaseModel):
    plan_id: str
    status: str

@router.get("/admin/users")
@limiter.limit("20/minute")
async def get_all_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Get all users with pagination (Admin only)."""
    return db.get_all_users(skip=skip, limit=limit)

@router.put("/admin/users/{user_id}/subscription")
@limiter.limit("10/minute")
async def update_user_subscription(
    request: Request,
    user_id: str,  # Changed to str to support BIGINT
    update: UserUpdate,
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Update user subscription (Admin only)."""
    # Verify plan exists first
    plan = db.get_plan(update.plan_id)
    if not plan and not update.plan_id.startswith('free'):
        # Allow 'free' as a special case if needed, or check if 'free' is in plans table. 
        # Usually 'free' might be hardcoded or seeded. 
        # If the user says "only those plans that are available(were created by me on Plans tab)", 
        # then we should strict check against db.get_plan().
        raise HTTPException(status_code=400, detail=f"Invalid plan ID: {update.plan_id}")

    success = db.update_user_subscription(int(user_id), update.plan_id, update.status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update subscription")
    return {"status": "success"}

@router.delete("/admin/users/{user_id}")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: str,  # Changed to str to support BIGINT
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Delete user (Admin only)."""
    if int(user_id) == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    success = db.delete_user(int(user_id))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    return {"status": "success"}

@router.post("/admin/users/{user_id}/make_admin")
async def make_admin(
    user_id: str,  # Changed to str to support BIGINT
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Make a user an admin (Admin only)."""
    success = db.set_admin_status(int(user_id), True)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update admin status")
    return {"status": "success"}

class AdminSetupRequest(BaseModel):
    """Request model for admin setup."""
    email: str
    password: str

def validate_password_strength(password: str) -> None:
    """
    Validate password meets security requirements.
    Raises HTTPException if password is weak.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )
    
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one digit"
        )

@router.post("/admin/setup")
async def setup_initial_admin(request: AdminSetupRequest):
    """
    Create the first admin user. 
    Only works if no admin users exist yet.
    
    Security improvements:
    - Uses request body instead of query parameters
    - Validates password strength
    - Checks admin doesn't already exist
    """
    # Validate password strength
    validate_password_strength(request.password)
    
    # Check if any admin exists
    all_users = db.get_all_users()
    has_admin = any(user.get('is_admin') for user in all_users)
    
    if has_admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin already exists. Use the admin panel to manage users."
        )
    
    # Validate email format (basic check)
    if '@' not in request.email or '.' not in request.email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    # Check if user exists
    user = db.get_user_by_email(request.email)
    
    if not user:
        # Create user
        from ..core.auth import get_password_hash
        hashed_password = get_password_hash(request.password)
        success = db.create_user(request.email, hashed_password)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user")
        user = db.get_user_by_email(request.email)
    
    # Make admin
    success = db.set_admin_status(user['id'], True)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set admin status")
    
    return {
        "status": "success",
        "message": f"Admin user {request.email} created successfully"
    }

@router.delete("/admin/clear-users")
async def clear_all_users(current_user: dict = Depends(auth.get_current_admin_user)):
    """
    Clear all users and related data (Admin only).
    WARNING: This is destructive and cannot be undone.
    """
    try:
        # Delete all related data
        db.conn.execute("DELETE FROM subscriptions")
        db.conn.execute("DELETE FROM user_strategies")
        db.conn.execute("DELETE FROM api_keys")
        db.conn.execute("DELETE FROM trades")
        db.conn.execute("DELETE FROM backtest_results")
        db.conn.execute("DELETE FROM payments")
        db.conn.execute("DELETE FROM visual_strategies")
        db.conn.execute("DELETE FROM public_strategies")
        db.conn.execute("DELETE FROM strategy_clones")
        db.conn.execute("DELETE FROM audit_log")
        
        # Delete all users
        db.conn.execute("DELETE FROM users")
        
        return {
            "status": "success",
            "message": "All users and related data deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear users: {str(e)}")
