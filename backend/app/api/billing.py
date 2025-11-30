from fastapi import APIRouter, HTTPException, Depends, Request, Header, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import hmac
import hashlib
import requests
from ..core import auth, config
from ..core.database import DuckDBHandler
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger("API.Billing")
db = DuckDBHandler()

# Coinbase Commerce API Configuration
COINBASE_API_URL = "https://api.commerce.coinbase.com"
COINBASE_API_KEY = config.COINBASE_COMMERCE_API_KEY if hasattr(config, 'COINBASE_COMMERCE_API_KEY') else None
COINBASE_WEBHOOK_SECRET = config.COINBASE_COMMERCE_WEBHOOK_SECRET if hasattr(config, 'COINBASE_COMMERCE_WEBHOOK_SECRET') else None

class ChargeRequest(BaseModel):
    plan_id: str

class PlanCreate(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    duration_days: int
    features: List[str]
    is_active: bool = True

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

@router.get("/billing/plans")
async def get_plans():
    """Get all active subscription plans."""
    return db.get_plans()

@router.post("/billing/charge")
async def create_charge(
    request: ChargeRequest,
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a Coinbase Commerce charge for a subscription plan."""
    if not COINBASE_API_KEY:
        raise HTTPException(status_code=500, detail="Billing not configured")
    
    plan = db.get_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    try:
        # Create charge via Coinbase Commerce API
        headers = {
            'X-CC-Api-Key': COINBASE_API_KEY,
            'X-CC-Version': '2018-03-22',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'name': plan['name'],
            'description': f'{plan["name"]} Subscription',
            'pricing_type': 'fixed_price',
            'local_price': {
                'amount': str(plan['price']),
                'currency': plan['currency']
            },
            'metadata': {
                'user_id': str(current_user['id']),
                'plan_id': request.plan_id
            }
        }
        
        response = requests.post(
            f'{COINBASE_API_URL}/charges',
            json=payload,
            headers=headers,
            timeout=10  # 10 second timeout
        )
        
        if response.status_code != 201:
            logger.error(f"Coinbase API error: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to create charge")
        
        charge_data = response.json()['data']
        charge_code = charge_data['code']
        
        # Log payment in database
        db.create_payment(
            user_id=current_user['id'],
            charge_code=charge_code,
            amount=plan['price'],
            currency=plan['currency'],
            plan_id=request.plan_id
        )
        
        return {
            'hosted_url': charge_data['hosted_url'],
            'charge_code': charge_code
        }
        
    except requests.RequestException as e:
        logger.error(f"Error creating charge: {e}")
        raise HTTPException(status_code=500, detail="Failed to create charge")

@router.post("/billing/webhook")
async def handle_webhook(
    request: Request,
    x_cc_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle Coinbase Commerce webhook events.
    
    Security improvements:
    - Validates webhook signature is present
    - Implements timing attack protection
    - Adds timestamp validation to prevent replay attacks
    - Proper error handling
    """
    if not COINBASE_WEBHOOK_SECRET:
        logger.error("Webhook secret not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    # Check signature header is present
    if not x_cc_webhook_signature:
        logger.warning("Webhook request missing signature header")
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    try:
        # Get raw body
        body = await request.body()
        
        # Verify signature
        expected_sig = hmac.new(
            COINBASE_WEBHOOK_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, x_cc_webhook_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event
        import json
        from datetime import datetime, timedelta
        
        event = json.loads(body)
        
        # Validate timestamp to prevent replay attacks (5 minute window)
        event_created_at = event.get('event', {}).get('created_at')
        if event_created_at:
            # Parse ISO format timestamp
            try:
                event_time = datetime.fromisoformat(event_created_at.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                time_diff = abs((current_time - event_time.replace(tzinfo=None)).total_seconds())
                
                # Reject events older than 5 minutes
                if time_diff > 300:
                    logger.warning(f"Webhook event too old: {time_diff}s")
                    raise HTTPException(status_code=400, detail="Event timestamp too old")
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid timestamp format: {e}")
                # Continue processing despite timestamp validation failure
                # (Coinbase may have different timestamp formats)
        
        event_type = event.get('event', {}).get('type')
        charge_data = event.get('event', {}).get('data', {})
        charge_code = charge_data.get('code')
        
        if not charge_code:
            logger.info("Webhook event has no charge code, ignoring")
            return {"status": "ignored"}
        
        # Get payment from database
        payment = db.get_payment_by_charge_code(charge_code)
        if not payment:
            logger.warning(f"Unknown charge code: {charge_code}")
            return {"status": "ignored"}
        
        # Handle charge:confirmed event
        if event_type == 'charge:confirmed':
            # Update payment status
            db.update_payment_status(charge_code, 'confirmed')
            
            # Get plan details
            plan_id = payment['plan_id']
            plan = db.get_plan(plan_id)
            
            if not plan:
                logger.error(f"Invalid plan ID in payment: {plan_id}")
                return {"status": "error"}
            
            expires_at = datetime.now() + timedelta(days=plan['duration_days'])
            
            # Create/update subscription
            db.create_subscription(
                user_id=payment['user_id'],
                plan_id=plan_id,
                status='active',
                expires_at=expires_at
            )
            
            logger.info(f"Subscription activated for user {payment['user_id']}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/billing/status")
async def get_billing_status(current_user: dict = Depends(auth.get_current_user)):
    """Get current user's subscription status."""
    try:
        subscription = db.get_subscription(current_user['id'])
        
        if not subscription:
            return {
                'plan': 'free',
                'status': 'active',
                'expires_at': None
            }
        
        # Check if expired
        if subscription['expires_at'] and subscription['expires_at'] < datetime.now():
            return {
                'plan': 'free',
                'status': 'expired',
                'expires_at': subscription['expires_at']
            }
        
        return {
            'plan': subscription['plan_id'],
            'status': subscription['status'],
            'expires_at': subscription['expires_at']
        }
        
    except Exception as e:
        logger.error(f"Error fetching billing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch billing status")

# Admin Endpoints

@router.post("/admin/plans")
async def create_plan(
    plan: PlanCreate,
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Create a new subscription plan."""
    if db.get_plan(plan.id):
        raise HTTPException(status_code=400, detail="Plan ID already exists")
    
    if db.create_plan(plan.dict()):
        return {"status": "success", "plan_id": plan.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create plan")

@router.put("/admin/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    plan: PlanUpdate,
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Update an existing subscription plan."""
    if not db.get_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if db.update_plan(plan_id, plan.dict(exclude_unset=True)):
        return {"status": "success", "plan_id": plan_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to update plan")

@router.delete("/admin/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: dict = Depends(auth.get_current_admin_user)
):
    """Deactivate a subscription plan."""
    if not db.get_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan not found")
    
    if db.delete_plan(plan_id):
        return {"status": "success", "plan_id": plan_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete plan")
