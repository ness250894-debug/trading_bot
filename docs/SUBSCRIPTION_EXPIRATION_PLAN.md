# Graceful Subscription Expiration Handling

## Problem
Currently, if a user's subscription expires while they have an active position, the bot may:
- Continue trading (charge-free)
- Abruptly crash
- Leave orphaned positions

This needs graceful handling.

## Solution

### 1. Add Subscription Check Helper
**File:** `backend/app/core/database.py`

Add method to check if subscription is valid:
```python
def is_subscription_active(self, user_id):
    """Check if user has an active subscription."""
    subscription = self.get_subscription(user_id)
    if not subscription:
        return False
    
    # Check status and expiration
    if subscription['status'] != 'active':
        return False
    
    # Check expiration date
    from datetime import datetime
    expires_at = subscription['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    
    return datetime.now() < expires_at
```

### 2. Periodic Subscription Check in Bot Loop
**File:** `backend/app/core/bot.py`

Add check every N iterations (e.g., every 10th loop = ~5 minutes):

```python
subscription_check_counter = 0
SUBSCRIPTION_CHECK_INTERVAL = 10  # Check every 10 loops

while True:
    # ... existing loop code ...
    
    # Periodic subscription check
    subscription_check_counter += 1
    if subscription_check_counter >= SUBSCRIPTION_CHECK_INTERVAL:
        subscription_check_counter = 0
        
        if not db.is_subscription_active(user_id):
            logger.warning(f"⚠️ User {user_id} subscription expired!")
            
            # Check if position is open
            if position_size > 0:
                logger.info(f"📤 Closing position gracefully for user {user_id}")
                notifier.send_message(
                    f"⚠️ *Subscription Expired*\n"
                    f"Closing your open position gracefully.\n"
                    f"Please renew to continue trading."
                )
                
                # Close position at market
                try:
                    side = 'sell' if position_side == 'Buy' else 'buy'
                    client.create_order(symbol=symbol, type='market', side=side, amount=position_size)
                    logger.info(f"✅ Position closed for user {user_id} due to subscription expiry")
                except Exception as e:
                    logger.error(f"Failed to close position: {e}")
                    notifier.send_error(f"Failed to close position: {e}")
            
            # Send final notification and exit
            notifier.send_message(
                f"🛑 *Bot Stopped*\n"
                f"Your subscription has expired.\n"
                f"Please renew to resume trading."
            )
            
            logger.info(f"Bot stopped for user {user_id} - subscription expired")
            break  # Exit loop gracefully
```

### 3. Prevent New Trades if Subscription Inactive
Before opening any new position:

```python
# Before entering new position
if position_size == 0 and signal in ['long', 'short']:
    # Check subscription before opening new position
    if not db.is_subscription_active(user_id):
        logger.warning(f"⚠️ User {user_id} subscription inactive - skipping new trade")
        continue
    
    # ... existing order logic ...
```

## Benefits

1. **Graceful Exit:** Positions closed at market price (best execution)
2. **User Notification:** Clear Telegram messages about what happened
3. **No Orphaned Positions:** Ensures all positions are closed before stopping  
4. **No Free Trading:** Prevents opening new positions after expiration
5. **Respectful:** Doesn't abruptly crash, gives time to renew

## Testing

1. Create test user with subscription expiring soon
2. Start bot with open position
3. Manually update subscription `expires_at` to past date
4. Wait for next check cycle (~5 minutes)
5. Verify position closes and bot stops gracefully
