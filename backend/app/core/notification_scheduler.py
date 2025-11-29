"""
Scheduled notification manager for daily/weekly reports.
Handles automated summary generation and delivery via Telegram.
"""
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
from .database import DuckDBHandler
from .notifier import TelegramNotifier

logger = logging.getLogger("NotificationScheduler")


class NotificationScheduler:
    """Manages scheduled notifications (daily/weekly reports)."""
    
    def __init__(self, user_id: int):
        """
        Initialize notification scheduler for a user.
        
        Args:
            user_id: User ID for personalized reports
        """
        self.user_id = user_id
        self.db = DuckDBHandler()
        self.running = False
        self.thread = None
        
        # Get user's Telegram settings
        user_settings = self.db.get_user_by_id(user_id)
        chat_id = user_settings.get('telegram_chat_id') if user_settings else None
        self.notifier = TelegramNotifier(chat_id=chat_id)
    
    def calculate_daily_stats(self) -> Dict[str, Any]:
        """
        Calculate daily trading statistics.
        
        Returns:
            Dictionary with daily stats
        """
        try:
            # Get today's trades
            today = datetime.now().date()
            
            result = self.db.conn.execute("""
                SELECT 
                    COUNT(*) as trades_count,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(pnl) as total_pnl
                FROM trades
                WHERE user_id = ?
                  AND DATE(timestamp) = ?
                  AND type = 'CLOSE'
            """, [self.user_id, today]).fetchone()
            
            trades_count = result[0] or 0
            wins = result[1] or 0
            losses = result[2] or 0
            total_pnl = result[3] or 0
            
            win_rate = (wins / trades_count * 100) if trades_count > 0 else 0
            
            # Get current balance (from latest balance record or calculate)
            balance_result = self.db.conn.execute("""
                SELECT balance FROM trades
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, [self.user_id]).fetchone()
            
            balance = balance_result[0] if balance_result else 0
            
            return {
                'trades_count': trades_count,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'balance': balance
            }
            
        except Exception as e:
            logger.error(f"Error calculating daily stats: {e}")
            return {}
    
    def calculate_weekly_stats(self) -> Dict[str, Any]:
        """
        Calculate weekly trading statistics.
        
        Returns:
            Dictionary with weekly stats
        """
        try:
            # Get last 7 days of trades
            week_ago = datetime.now() - timedelta(days=7)
            
            result = self.db.conn.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(pnl) as weekly_pnl
                FROM trades
                WHERE user_id = ?
                  AND timestamp >= ?
                  AND type = 'CLOSE'
            """, [self.user_id, week_ago]).fetchone()
            
            total_trades = result[0] or 0
            wins = result[1] or 0
            weekly_pnl = result[2] or 0
            
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            # Get best and worst days
            daily_pnl = self.db.conn.execute("""
                SELECT 
                    DATE(timestamp) as trade_date,
                    SUM(pnl) as daily_pnl
                FROM trades
                WHERE user_id = ?
                  AND timestamp >= ?
                  AND type = 'CLOSE'
                GROUP BY DATE(timestamp)
                ORDER BY daily_pnl DESC
            """, [self.user_id, week_ago]).fetchall()
            
            best_day = {}
            worst_day = {}
            
            if daily_pnl:
                best = daily_pnl[0]
                worst = daily_pnl[-1]
                best_day = {'date': best[0], 'pnl': best[1]}
                worst_day = {'date': worst[0], 'pnl': worst[1]}
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'weekly_pnl': weekly_pnl,
                'best_day': best_day,
                'worst_day': worst_day
            }
            
        except Exception as e:
            logger.error(f"Error calculating weekly stats: {e}")
            return {}
    
    def send_daily_report(self):
        """Send daily summary report."""
        logger.info(f"Sending daily report for user {self.user_id}")
        try:
            stats = self.calculate_daily_stats()
            if stats:
                self.notifier.send_daily_summary(stats)
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    def send_weekly_report(self):
        """Send weekly digest report."""
        logger.info(f"Sending weekly report for user {self.user_id}")
        try:
            stats = self.calculate_weekly_stats()
            if stats:
                self.notifier.send_weekly_digest(stats)
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        
        # Schedule daily report at 8 PM
        schedule.every().day.at("20:00").do(self.send_daily_report)
        
        # Schedule weekly report on Sunday at 9 PM
        schedule.every().sunday.at("21:00").do(self.send_weekly_report)
        
        # Run scheduler in background thread
        def run_scheduler():
            logger.info(f"Notification scheduler started for user {self.user_id}")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info(f"Scheduler thread started for user {self.user_id}")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        logger.info(f"Notification scheduler stopped for user {self.user_id}")


# Global scheduler instances (one per user)
_schedulers: Dict[int, NotificationScheduler] = {}


def get_scheduler(user_id: int) -> NotificationScheduler:
    """
    Get or create scheduler for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        NotificationScheduler instance
    """
    if user_id not in _schedulers:
        _schedulers[user_id] = NotificationScheduler(user_id)
    return _schedulers[user_id]


def start_scheduler(user_id: int):
    """
    Start notification scheduler for a user.
    
    Args:
        user_id: User ID
    """
    scheduler = get_scheduler(user_id)
    scheduler.start()


def stop_scheduler(user_id: int):
    """
    Stop notification scheduler for a user.
    
    Args:
        user_id: User ID
    """
    if user_id in _schedulers:
        _schedulers[user_id].stop()
