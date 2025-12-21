"""
Order Execution Module

Handles order creation and execution for entry and exit trades.
Extracted from bot.py for better modularity and testability.
"""
import time
import logging

logger = logging.getLogger("TradingBot")


class OrderExecutor:
    """Executes trading orders and logs trades"""
    
    def __init__(self, client, db, notifier, user_id, is_mock=True):
        """
        Initialize order executor.
        
        Args:
            client: Exchange client instance
            db: Database handler instance
            notifier: Telegram notifier instance
            user_id: User ID
            is_mock: Whether running in mock/paper mode
        """
        self.client = client
        self.db = db
        self.notifier = notifier
        self.user_id = user_id
        self.is_mock = is_mock
        self.logger = logger
    
    def execute_entry_order(self, symbol, signal, amount_usdt, current_price,
                           strategy_name, take_profit_pct, stop_loss_pct, leverage=1.0):
        """
        Execute market entry order with TP/SL.
        
        Args:
            symbol: Trading symbol
            signal: 'long' or 'short'
            amount_usdt: Trade amount in USDT
            current_price: Current market price
            strategy_name: Name of the strategy
            take_profit_pct: Take profit percentage
            stop_loss_pct: Stop loss percentage
            leverage: Leverage multiplier
            
        Returns:
            Tuple of (success: bool, entry_price: float or None)
        """
        try:
            # Calculate order parameters
            ticker = self.client.fetch_ticker(symbol)
            current_price = ticker['last']
            amount = (amount_usdt * leverage) / current_price
            side = 'buy' if signal == 'long' else 'sell'
            
            # Log TP/SL parameters
            tp_price = current_price * (1 + take_profit_pct) if take_profit_pct and side == 'buy' else current_price * (1 - take_profit_pct) if take_profit_pct else None
            sl_price = current_price * (1 - stop_loss_pct) if stop_loss_pct and side == 'buy' else current_price * (1 + stop_loss_pct) if stop_loss_pct else None
            
            tp_str = f"{tp_price:.2f}" if tp_price else "N/A"
            sl_str = f"{sl_price:.2f}" if sl_price else "N/A"
            self.logger.info(f"📝 Order Params | TP: {tp_str} ({take_profit_pct*100 if take_profit_pct else 0}%) | SL: {sl_str} ({stop_loss_pct*100 if stop_loss_pct else 0}%)")
            
            # Execute order
            self.logger.info(f"4. 🚀 [User {self.user_id}] Executing Order: {side.upper()} {amount:.6f} {symbol}")
            order = self.client.create_order(
                symbol=symbol,
                order_type='market',
                side=side,
                amount=amount,
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct
            )
            
            # Verify fill
            time.sleep(1)
            exec_price = current_price
            if order and 'id' in order:
                fetched = self.client.fetch_order(order['id'], symbol)
                if fetched and fetched.get('average'):
                    exec_price = fetched.get('average')
                    self.logger.info(f"Verified Fill Price: {exec_price}")
            
            # Log trade to database
            trade_data = {
                'symbol': symbol,
                'side': side,
                'price': exec_price,
                'amount': amount,
                'type': 'OPEN',
                'pnl': 0.0,
                'leverage': leverage,
                'strategy': strategy_name,
                'user_id': self.user_id,
                'is_mock': self.is_mock
            }
            self.db.log_trade(trade_data)
            
            # Send notification
            self.notifier.send_trade_alert(trade_data)
            
            self.logger.info(f"✓ User {self.user_id}: {signal} entry at {exec_price}")
            
            return True, exec_price
            
        except Exception as e:
            self.logger.error(f"❌ User {self.user_id} order creation failed:")
            self.logger.error(f"   Symbol: {symbol}, Side: {side}, Amount: {amount:.6f}")
            self.logger.error(f"   Error: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(f"   Stack: {traceback.format_exc()}")
            return False, None
    
    def execute_exit_order(self, symbol, position, current_price, strategy_name, leverage=1.0):
        """
        Execute market exit order and log trade.
        
        Args:
            symbol: Trading symbol
            position: Current position dict
            current_price: Current market price
            strategy_name: Name of the strategy
            leverage: Leverage used
            
        Returns:
            Tuple of (success: bool, pnl: float or None)
        """
        try:
            position_side = position.get('side')
            position_size = position.get('size', 0.0)
            side = 'sell' if position_side == 'long' else 'buy'
            entry_price = float(position.get('entry_price', 0) or 0)
            
            self.logger.info(f"6. 📤 [User {self.user_id}] Closing Position: {side.upper()} {position_size} {symbol}")
            self.client.create_order(symbol=symbol, order_type='market', side=side, amount=position_size)
            self.logger.info(f"✓ User {self.user_id}: Closed position")
            
            # Fetch realized PnL
            time.sleep(2)
            trades = self.client.fetch_my_trades(symbol, limit=1)
            pnl = 0.0
            if trades:
                last_trade = trades[0]
                if last_trade.get('pnl'):
                    pnl = last_trade.get('pnl')
                self.logger.info(f"Trade Info: {last_trade}")
            
            # Calculate PnL % (ROE)
            # ROE = (PnL / Initial Margin) * 100
            # Initial Margin = (Entry Price * Size) / Leverage
            pnl_pct = 0.0
            if entry_price > 0 and position_size > 0:
                initial_margin = (entry_price * position_size) / leverage
                if initial_margin > 0:
                    pnl_pct = (pnl / initial_margin) * 100
            
            # Log trade to database
            trade_data = {
                'symbol': symbol,
                'side': side,
                'price': current_price,
                'amount': position_size,
                'type': 'CLOSE',
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'leverage': leverage,
                'strategy': strategy_name,
                'user_id': self.user_id,
                'is_mock': self.is_mock,
                'entry_price': entry_price
            }
            self.db.log_trade(trade_data)
            self.notifier.send_trade_alert(trade_data)
            
            return True, pnl
            
        except Exception as e:
            self.logger.error(f"❌ User {self.user_id} position close failed:")
            self.logger.error(f"   Symbol: {symbol}, Side: {side}, Size: {position_size}")
            self.logger.error(f"   Error: {type(e).__name__}: {str(e)}")
            return False, None
