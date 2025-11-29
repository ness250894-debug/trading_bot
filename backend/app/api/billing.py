from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel
from typing import Optional
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

# Plan configurations
PLANS = {
    'pro_monthly': {
        'name': 'Pro Monthly',
        'price': 29.99,
        'currency': 'USD',
        'duration_days': 30
    },
    'pro_yearly': {
        'name': 'Pro Yearly',
        'price': 299.99,
        'currency': 'USD',
        'duration_days': 365
    }
}

class ChargeRequest(BaseModel):
    plan_id: str

@router.post("/billing/charge")
async def create_charge(
    request: ChargeRequest,
    current_user: dict = Depends(auth.get_current_user)
):
    """Create a Coinbase Commerce charge for a subscription plan."""
    if not COINBASE_API_KEY:
        raise HTTPException(status_code=500, detail="Billing not configured")
    
    if request.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    plan = PLANS[request.plan_id]
    
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
            headers=headers
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
    """Handle Coinbase Commerce webhook events."""
    if not COINBASE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    try:
        # Get raw body
        body = await request.body()
        
        # Verify signature
        expected_sig = hmac.new(
            COINBASE_WEBHOOK_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, x_cc_webhook_signature or ''):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event
        import json
        event = json.loads(body)
        
        event_type = event.get('event', {}).get('type')
        charge_data = event.get('event', {}).get('data', {})
        charge_code = charge_data.get('code')
        
        if not charge_code:
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
            if plan_id not in PLANS:
                logger.error(f"Invalid plan ID in payment: {plan_id}")
                return {"status": "error"}
            
            plan = PLANS[plan_id]
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
