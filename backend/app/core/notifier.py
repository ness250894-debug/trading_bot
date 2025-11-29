"""
Enhanced Telegram Notifier with Rich Notifications and Interactive Features.
Provides daily reports, detailed trade alerts, and interactive buttons.
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from . import config

logger = logging.getLogger("Notifier")


class TelegramNotifier:
    """Enhanced Telegram notifier with rich formatting and interactive features."""
    
    def __init__(self, token=None, chat_id=None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.token and self.chat_id)
        
        if self.enabled:
            logger.info(f"Telegram Notifier Enabled (Chat ID: {self.chat_id})")
        else:
            logger.warning("Telegram Notifier Disabled (Missing Token or Chat ID)")
    
    def send_message(self, text: str, parse_mode: str = "Markdown", reply_markup: Optional[Dict] = None):
        """
        Sends a text message with optional interactive buttons.
        
        Args:
            text: Message text
            parse_mode: Parsing mode (Markdown or HTML)
            reply_markup: Inline keyboard markup for interactive buttons
        """
        if not self.enabled:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
    
    def send_trade_alert(self, trade: Dict[str, Any]):
        """
        Sends an enhanced, richly formatted trade alert.
        
        Args:
            trade: Trade dictionary with details
        """
        if not self.enabled:
            return
        
        try:
            # Determine emoji and header based on trade type
            if trade['type'] == 'OPEN':
                emoji = "🟢 BUY" if trade['side'].lower() == 'buy' else "🔴 SELL"
                header = "📊 *POSITION OPENED*"
            else:  # CLOSE
                pnl = trade.get('pnl', 0)
                emoji = "💰 PROFIT" if pnl >= 0 else "💸 LOSS"
                header = "✅ *POSITION CLOSED*"
            
            # Build message with rich formatting
            message = f"{header}\n\n"
            message += f"{emoji}\n\n"
            message += f"*Symbol:* `{trade['symbol']}`\n"
            message += f"*Side:* {trade['side'].upper()}\n"
            message += f"*Price:* ${trade['price']:.2f}\n"
            message += f"*Amount:* {trade['amount']:.4f}\n"
            
            # Calculate position value
            value = trade['price'] * trade['amount']
            message += f"*Position Value:* ${value:,.2f}\n"
            
            # Add leverage and margin info
            leverage = trade.get('leverage', 1)
            if leverage > 1:
                margin = value / leverage
                message += f"*Leverage:* {leverage}x\n"
                message += f"*Margin Used:* ${margin:,.2f}\n"
            
            # Add PnL for closing trades
            if trade['type'] == 'CLOSE':
                pnl = trade.get('pnl', 0)
                pnl_pct = trade.get('pnl_pct', 0)
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                message += f"\n{pnl_emoji} *PnL:* ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
            
            # Add strategy info
            if 'strategy' in trade:
                message += f"\n*Strategy:* `{trade['strategy']}`\n"
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message += f"\n🕒 {timestamp}"
            
            # Add interactive buttons for open positions
            buttons = None
            if trade['type'] == 'OPEN':
                buttons = {
                    "inline_keyboard": [[
                        {"text": "📊 View Position", "callback_data": "view_position"},
                        {"text": "🛑 Close Position", "callback_data": "close_position"}
                    ]]
                }
            
            self.send_message(message, reply_markup=buttons)
            
        except Exception as e:
            logger.error(f"Error sending trade alert: {e}")
    
    def send_daily_summary(self, stats: Dict[str, Any]):
        """
        Sends a daily PnL and performance summary.
        
        Args:
            stats: Dictionary with daily statistics
        """
        if not self.enabled:
            return
        
        try:
            total_pnl = stats.get('total_pnl', 0)
            trades_count = stats.get('trades_count', 0)
            win_rate = stats.get('win_rate', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            
            # Header with emoji based on performance
            if total_pnl > 0:
                header = "🎉 *DAILY SUMMARY - PROFITABLE DAY!*"
                emoji = "💰"
            elif total_pnl < 0:
                header = "📊 *DAILY SUMMARY*"
                emoji = "💸"
            else:
                header = "📊 *DAILY SUMMARY*"
                emoji = "➖"
            
            message = f"{header}\n\n"
            message += f"{emoji} *Total PnL:* ${total_pnl:,.2f}\n\n"
            
            # Trading activity
            message += f"📈 *Trading Activity*\n"
            message += f"• Total Trades: {trades_count}\n"
            message += f"• Wins: {wins} 🟢\n"
            message += f"• Losses: {losses} 🔴\n"
            message += f"• Win Rate: {win_rate:.1f}%\n\n"
            
            # Portfolio stats
            if 'balance' in stats:
                message += f"💼 *Portfolio*\n"
                message += f"• Balance: ${stats['balance']:,.2f}\n"
                
                if 'balance_change' in stats:
                    change = stats['balance_change']
                    change_emoji = "📈" if change >= 0 else "📉"
                    message += f"• Daily Change: {change_emoji} ${change:,.2f}\n"
            
            # Add date
            date = datetime.now().strftime("%B %d, %Y")
            message += f"\n📅 {date}"
            
            # Add interactive buttons
            buttons = {
                "inline_keyboard": [
                    [{"text": "📊 View Detailed Report", "callback_data": "detailed_report"}],
                    [{"text": "📈 View Trades", "callback_data": "view_trades"}]
                ]
            }
            
            self.send_message(message, reply_markup=buttons)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def send_weekly_digest(self, stats: Dict[str, Any]):
        """
        Sends a weekly performance digest.
        
        Args:
            stats: Dictionary with weekly statistics
        """
        if not self.enabled:
            return
        
        try:
            weekly_pnl = stats.get('weekly_pnl', 0)
            total_trades = stats.get('total_trades', 0)
            win_rate = stats.get('win_rate', 0)
            best_day = stats.get('best_day', {})
            worst_day = stats.get('worst_day', {})
            
            message = "📊 *WEEKLY PERFORMANCE DIGEST*\n\n"
            
            # Overall performance
            pnl_emoji = "💰" if weekly_pnl >= 0 else "💸"
            message += f"{pnl_emoji} *Weekly PnL:* ${weekly_pnl:,.2f}\n\n"
            
            # Trading stats
            message += f"📈 *Statistics*\n"
            message += f"• Total Trades: {total_trades}\n"
            message += f"• Win Rate: {win_rate:.1f}%\n\n"
            
            # Best and worst days
            if best_day:
                message += f"🌟 *Best Day:* ${best_day.get('pnl', 0):,.2f} ({best_day.get('date', 'N/A')})\n"
            if worst_day:
                message += f"💔 *Worst Day:* ${worst_day.get('pnl', 0):,.2f} ({worst_day.get('date', 'N/A')})\n\n"
            
            # Week range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            message += f"\n📅 {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            
            self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {e}")
    
    def send_stop_loss_alert(self, trade: Dict[str, Any]):
        """
        Sends alert when stop loss is hit.
        
        Args:
            trade: Trade information
        """
        if not self.enabled:
            return
        
        message = "🚨 *STOP LOSS HIT*\n\n"
        message += f"*Symbol:* `{trade['symbol']}`\n"
        message += f"*Entry Price:* ${trade.get('entry_price', 0):.2f}\n"
        message += f"*Stop Price:* ${trade.get('stop_price', 0):.2f}\n"
        message += f"*Loss:* ${trade.get('loss', 0):,.2f}\n"
        
        self.send_message(message)
    
    def send_take_profit_alert(self, trade: Dict[str, Any]):
        """
        Sends alert when take profit is hit.
        
        Args:
            trade: Trade information
        """
        if not self.enabled:
            return
        
        message = "🎯 *TAKE PROFIT HIT*\n\n"
        message += f"*Symbol:* `{trade['symbol']}`\n"
        message += f"*Entry Price:* ${trade.get('entry_price', 0):.2f}\n"
        message += f"*Target Price:* ${trade.get('target_price', 0):.2f}\n"
        message += f"*Profit:* ${trade.get('profit', 0):,.2f}\n"
        
        self.send_message(message)
    
    def send_portfolio_update(self, portfolio: Dict[str, Any]):
        """
        Sends current portfolio overview.
        
        Args:
            portfolio: Portfolio information
        """
        if not self.enabled:
            return
        
        try:
            message = "💼 *PORTFOLIO OVERVIEW*\n\n"
            
            balance = portfolio.get('balance', 0)
            equity = portfolio.get('equity', 0)
            pnl_today = portfolio.get('pnl_today', 0)
            
            message += f"*Balance:* ${balance:,.2f}\n"
            message += f"*Equity:* ${equity:,.2f}\n"
            
            pnl_emoji = "📈" if pnl_today >= 0 else "📉"
            message += f"{pnl_emoji} *Today's PnL:* ${pnl_today:,.2f}\n\n"
            
            # Open positions
            open_positions = portfolio.get('open_positions', [])
            if open_positions:
                message += f"📊 *Open Positions:* {len(open_positions)}\n"
                for pos in open_positions[:3]:  # Show max 3
                    message += f"• {pos['symbol']}: ${pos.get('pnl', 0):,.2f}\n"
            else:
                message += "📊 *No Open Positions*\n"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message += f"\n🕒 {timestamp}"
            
            self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending portfolio update: {e}")
    
    def send_error(self, error_msg: str):
        """
        Sends an error alert with enhanced formatting.
        
        Args:
            error_msg: Error message
        """
        if not self.enabled:
            return
        
        message = "🚨 *CRITICAL ERROR*\n\n"
        message += f"```\n{error_msg}\n```\n\n"
        message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_message(message)
    
    def send_bot_status(self, status: str, details: str = ""):
        """
        Sends bot status update (started/stopped).
        
        Args:
            status: Status (started/stopped)
            details: Additional details
        """
        if not self.enabled:
            return
        
        if status.lower() == "started":
            emoji = "🚀"
            message = f"{emoji} *BOT STARTED*\n\n"
        else:
            emoji = "🛑"
            message = f"{emoji} *BOT STOPPED*\n\n"
        
        if details:
            message += f"{details}\n\n"
        
        message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_message(message)
