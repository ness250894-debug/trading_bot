"""
Risk Management Module

Centralizes all risk management checks and limits.
Extracted from bot.py for better modularity and testability.
"""
import logging

logger = logging.getLogger("TradingBot")


class RiskManager:
    """Manages risk checks and trading limits"""
    
    def __init__(self, db, notifier, user_id):
        """
        Initialize risk manager.
        
        Args:
            db: Database handler instance
            notifier: Telegram notifier instance
            user_id: User ID
        """
        self.db = db
        self.notifier = notifier
        self.user_id = user_id
        self.logger = logger
    
    def check_subscription_active(self):
        """
        Check if user subscription is valid.
        
        Returns:
            bool: True if subscription is active
        """
        return self.db.is_subscription_active(self.user_id)
    
    def check_can_open_position(self, amount_usdt, client=None):
        """
        Run all pre-trade risk checks.
        
        Checks:
        - Daily loss limit
        - Max position size
        - Max open positions
        - Balance check (if client provided)
        
        Args:
            amount_usdt: Trade amount in USDT
            client: Optional exchange client for balance check
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        self.logger.info(f"3. 🛡️ [User {self.user_id}] Running Risk Checks...")
        
        # Log balance if client provided
        if client:
            self.log_balance_info(client, amount_usdt)
        
        risk_profile = self.db.get_risk_profile(self.user_id)
        if not risk_profile:
            return True, "No risk profile configured"
        
        # 1. Check Max Daily Loss
        if risk_profile.get('max_daily_loss'):
            daily_pnl = self.db.get_daily_pnl(self.user_id)
            limit = abs(float(risk_profile['max_daily_loss']))
            if daily_pnl <= -limit:
                reason = f"Max Daily Loss breached. PnL: {daily_pnl:.2f}, Limit: {limit:.2f}"
                self.logger.warning(f"⛔ {reason}")
                self.notifier.send_message(f"⛔ *Risk Warning*: Daily Loss Limit Hit ({daily_pnl:.2f}). Trading paused.")
                return False, reason
        
        # 2. Check Max Position Size
        if risk_profile.get('max_position_size'):
            max_size = float(risk_profile['max_position_size'])
            if amount_usdt > max_size:
                reason = f"Max Position Size exceeded. Amount: {amount_usdt}, Max: {max_size}"
                self.logger.warning(f"⛔ {reason}")
                self.notifier.send_message(f"⚠️ Trade blocked: Amount ({amount_usdt}) exceeds limit ({max_size})")
                return False, reason
        
        # 3. Check Max Open Positions
        if risk_profile.get('max_open_positions'):
            max_pos = int(risk_profile['max_open_positions'])
            try:
                from ..bot_manager import bot_manager
                bot_stats = bot_manager.get_status(self.user_id)
                
                open_positions = 0
                if bot_stats:
                    if isinstance(bot_stats, dict) and 'is_running' not in bot_stats:
                        # Multi-instance dict
                        for s in bot_stats.values():
                            if s.get('active_trades', 0) > 0:
                                open_positions += 1
                    elif bot_stats.get('active_trades', 0) > 0:
                        open_positions = 1
                
                if open_positions >= max_pos:
                    reason = f"Max Open Positions reached. Current: {open_positions}, Max: {max_pos}"
                    self.logger.warning(f"⛔ {reason}")
                    self.notifier.send_message(f"⚠️ Trade blocked: Max open positions reached ({max_pos})")
                    return False, reason
            except Exception as e:
                self.logger.error(f"Failed to check open positions: {e}")
        
        return True, "All risk checks passed"
    
    def log_balance_info(self, client, amount_usdt):
        """
        Log balance and trade size for monitoring.
        
        Args:
            client: Exchange client instance
            amount_usdt: Trade amount in USDT
        """
        try:
            balance_data = client.fetch_balance()
            total_balance = balance_data['total']['USDT'] if balance_data else 0.0
            pct_of_balance = (amount_usdt / total_balance * 100) if total_balance > 0 else 0
            self.logger.info(f"💰 Balance: ${total_balance:.2f} | Trade Amount: ${amount_usdt:.2f} ({pct_of_balance:.1f}% of total)")
        except Exception as e:
            self.logger.warning(f"Failed to log balance: {e}")
