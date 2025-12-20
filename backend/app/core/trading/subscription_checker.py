"""
Subscription Checker Module

Periodic subscription validation and graceful shutdown handling.
Extracted from bot.py for better modularity and testability.
"""
import logging

logger = logging.getLogger("TradingBot")


class SubscriptionChecker:
    """Manages periodic subscription checks and expiry handling"""
    
    def __init__(self, db, notifier, user_id, loop_delay):
        """
        Initialize subscription checker.
        
        Args:
            db: Database handler instance
            notifier: Telegram notifier instance
            user_id: User ID
            loop_delay: Trading loop delay in seconds
        """
        self.db = db
        self.notifier = notifier
        self.user_id = user_id
        self.check_counter = 0
        # Check every 5 minutes
        self.interval = max(1, int(300 / loop_delay))
        self.logger = logger
        
        self.logger.info(f"Subscription check interval: {self.interval} loops (~{self.interval * loop_delay}s)")
    
    def should_check_now(self):
        """
        Determine if it's time to check subscription.
        
        Returns:
            bool: True if should check now
        """
        self.check_counter += 1
        if self.check_counter >= self.interval:
            self.check_counter = 0
            return True
        return False
    
    def handle_expired_subscription(self, client, symbol, position):
        """
        Handle subscription expiry.
        - Close open position if exists
        - Send notifications
        - Return should_exit flag
        
        Args:
            client: Exchange client instance
            symbol: Trading symbol
            position: Current position dict
            
        Returns:
            bool: True if bot should exit
        """
        self.logger.warning(f"⚠️ User {self.user_id} subscription expired!")
        
        position_size = position.get('size', 0.0)
        
        # Check if position is open
        if position_size > 0:
            self.logger.info(f"📤 Closing position gracefully for user {self.user_id} (subscription expired)")
            self.notifier.send_message(
                f"⚠️ *Subscription Expired*\\n"
                f"Closing your open position gracefully.\\n"
                f"Please renew to continue trading."
            )
            
            # Close position at market
            try:
                side = 'sell' if position.get('side') == 'Buy' else 'buy'
                close_order = client.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=side,
                    amount=position_size
                )
                self.logger.info(f"✅ Position closed for user {self.user_id} due to subscription expiry")
                
                # Clear state
                self.db.update_bot_state(self.user_id, position_start_time=None, active_order_id='NO_CHANGE')
                
            except Exception as e:
                self.logger.error(f"❌ Failed to close position on subscription expiry: {e}")
                self.notifier.send_error(f"Failed to close position: {e}")
        
        # Send final notification and exit
        self.notifier.send_message(
            f"🛑 *Bot Stopped*\\n"
            f"Your subscription has expired.\\n"
            f"Please renew to resume trading."
        )
        
        self.logger.info(f"Bot stopped for user {self.user_id} - subscription expired")
        return True  # Signal to exit loop
