import requests
import logging
from . import config

logger = logging.getLogger("Notifier")

class TelegramNotifier:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.token and self.chat_id)
        
        if self.enabled:
            logger.info("Telegram Notifier Enabled")
        else:
            logger.warning("Telegram Notifier Disabled (Missing Token or Chat ID)")

    def send_message(self, text):
        """Sends a simple text message."""
        if not self.enabled:
            return

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")

    def send_trade_alert(self, trade):
        """Sends a formatted trade alert."""
        if not self.enabled:
            return

        try:
            # Determine emoji based on side/pnl
            emoji = "🟢" if trade['side'].lower() == 'buy' else "🔴"
            if trade['type'] == 'CLOSE':
                pnl = trade.get('pnl', 0)
                emoji = "💰" if pnl >= 0 else "💸"
            
            message = (
                f"{emoji} *Trade Executed*\n"
                f"Symbol: `{trade['symbol']}`\n"
                f"Side: *{trade['side'].upper()}*\n"
                f"Price: `${trade['price']}`\n"
                f"Amount: `{trade['amount']}`\n"
                f"Value: `${(trade['price'] * trade['amount']):.2f}`\n"
            )
            
            # Add Margin info if leverage available
            leverage = trade.get('leverage', 1)
            if leverage > 1:
                margin = (trade['price'] * trade['amount']) / leverage
                message += f"Margin: `${margin:.2f}` ({leverage}x)\n"
            
            if trade['type'] == 'CLOSE':
                pnl = trade.get('pnl', 0)
                message += f"PnL: `${pnl:.2f}`\n"
            
            if 'strategy' in trade:
                message += f"Strategy: `{trade['strategy']}`"

            self.send_message(message)
        except Exception as e:
            logger.error(f"Error sending trade alert: {e}")

    def send_error(self, error_msg):
        """Sends an error alert."""
        if not self.enabled:
            return
        self.send_message(f"🚨 *CRITICAL ERROR*\n`{error_msg}`")
