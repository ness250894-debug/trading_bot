import ccxt
import pandas as pd
import logging

class ExchangeClient:
    def __init__(self, api_key, api_secret, demo=True):
        self.logger = logging.getLogger(__name__)
        self.demo = demo
        
        self.exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'adjustForTimeDifference': False,
                'recvWindow': 10000,
            }
        })
        
        if demo:
            self.exchange.set_sandbox_mode(True)
            # Force Bybit UTA Demo URLs (ccxt uses testnet by default)
            self.exchange.urls['api']['public'] = 'https://api-demo.bybit.com'
            self.exchange.urls['api']['private'] = 'https://api-demo.bybit.com'
        
        # Explicitly sync time
        try:
            server_time = self.exchange.fetch_time()
            import time
            local_time = int(time.time() * 1000)
            
            # Calculate diff
            diff = (local_time - server_time) + 1000
            
            self.exchange.options['timeDifference'] = diff
            self.logger.info(f"Time synced. Server: {server_time}, Local: {local_time}, Diff: {diff}ms")
        except Exception as e:
            self.logger.error(f"Failed to sync time: {e}")

        # Load markets
        self.precisions = {}
        try:
            self.exchange.load_markets()
        except Exception as e:
             self.logger.error(f"Failed to load markets: {e}")

    def _load_demo_precisions(self):
        """Manually load precisions for Demo if load_markets fails."""
        try:
            # Fetch all linear instruments
            response = self.exchange.public_get_v5_market_instruments_info({'category': 'linear'})
            if str(response.get('retCode')) == '0':
                for item in response['result']['list']:
                    symbol = item['symbol'] # e.g. BTCUSDT
                    # Map to CCXT symbol if needed, but we mostly use raw symbol for demo calls
                    # Lot size filter
                    lot_size = item.get('lotSizeFilter', {})
                    qty_step = lot_size.get('qtyStep', '0.001')
                    self.precisions[symbol] = float(qty_step)
                    
                    # Also map 'BTC/USDT' format
                    base = item.get('baseCoin')
                    quote = item.get('quoteCoin')
                    if base and quote:
                        ccxt_symbol = f"{base}/{quote}"
                        self.precisions[ccxt_symbol] = float(qty_step)
                self.logger.info(f"Loaded {len(self.precisions)} precisions manually for Demo.")
        except Exception as e:
            self.logger.error(f"Failed to load demo precisions: {e}")

    def format_amount(self, symbol, amount):
        """Formats amount to precision, handling Demo fallback."""
        try:
            return self.exchange.amount_to_precision(symbol, amount)
        except Exception:
            # Fallback to manual precision
            # Try CCXT symbol or raw symbol
            prec = self.precisions.get(symbol)
            if not prec:
                market_symbol = symbol.replace('/', '')
                prec = self.precisions.get(market_symbol)
            
            if prec:
                # Calculate decimals from step
                # e.g. 0.001 -> 3, 0.1 -> 1, 1 -> 0
                import math
                if prec < 1:
                    decimals = int(-math.log10(prec))
                    return f"{amount:.{decimals}f}"
                else:
                    return str(int(amount))
            
            # If all else fails, default to 3 decimals (safe for BTC)
            return f"{amount:.3f}"

    def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        """Fetches OHLCV data and returns a DataFrame."""
        last_error = None
        for attempt in range(3):
            try:
                if self.demo:
                    # Workaround for ByBit Demo error 10032
                    # Use raw endpoint for kline
                    interval_map = {
                        '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
                        '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
                        '1d': 'D', '1w': 'W', '1M': 'M'
                    }
                    interval = interval_map.get(timeframe, '60')
                    
                    params = {
                        'category': 'linear',
                        'symbol': symbol.replace('/', ''),
                        'interval': interval,
                        'limit': limit
                    }
                    if since:
                        params['start'] = since

                    response = self.exchange.public_get_v5_market_kline(params)
                    
                    # Check for success (retCode can be 0 or '0')
                    if str(response.get('retCode')) == '0':
                        # Parse list: [startTime, open, high, low, close, volume, turnover]
                        data = response['result']['list']
                        # ByBit returns newest first, reverse it
                        data.reverse()
                        
                        ohlcv = []
                        for candle in data:
                            ohlcv.append([
                                int(candle[0]),
                                float(candle[1]),
                                float(candle[2]),
                                float(candle[3]),
                                float(candle[4]),
                                float(candle[5])
                            ])
                        
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        return df
                    else:
                        # Log error but truncate result if it's too long
                        log_response = response.copy()
                        if 'result' in log_response:
                            log_response['result'] = '...truncated...'
                        error_msg = f"ByBit API Error: {log_response}"
                        self.logger.error(error_msg)
                        last_error = Exception(error_msg)
                        # Don't retry on API logic errors (like invalid symbol), unless it's rate limit (which is usually handled by ccxt but here we are manual)
                        # But retCode != 0 could be anything. Let's assume it's fatal for now unless we know otherwise.
                        raise last_error
                else:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    return df
                    
            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                self.logger.warning(f"Network error fetching OHLCV (Attempt {attempt+1}/3): {e}")
                last_error = e
                import time
                time.sleep(2 * (attempt + 1)) # Exponential backoff
            except ccxt.RateLimitExceeded as e:
                self.logger.warning(f"Rate limit exceeded fetching OHLCV: {e}")
                last_error = e
                import time
                time.sleep(10) # Wait longer for rate limit
            except Exception as e:
                self.logger.error(f"Error fetching OHLCV: {e}")
                last_error = e
                # If it's the API error we raised above, we might want to stop retrying if we decide so.
                # For now, let's just continue to next attempt if any (though usually logic errors shouldn't be retried)
                if "ByBit API Error" in str(e):
                     break # Don't retry logic errors
        
        # If we get here, we failed
        if last_error:
            raise last_error
        raise Exception("Failed to fetch OHLCV: Unknown error")

    def fetch_balance(self):
        """Fetches account balance."""
        try:
            if self.demo:
                # Workaround for ByBit Demo error 10032 (Demo trading not supported on fetchBalance)
                # We call the raw endpoint directly to avoid ccxt's extra calls
                response = self.exchange.private_get_v5_account_wallet_balance({'accountType': 'UNIFIED'})
                
                # Parse response to match ccxt structure
                # Structure: {'retCode': 0, 'result': {'list': [{'coin': [{'coin': 'USDT', 'walletBalance': '...', ...}]}]}}
                result = {'total': {}, 'free': {}, 'used': {}, 'info': response}
                
                # Check for success (retCode can be 0 or '0')
                if str(response.get('retCode')) == '0' and 'list' in response.get('result', {}):
                    account = response['result']['list'][0]
                    for coin_data in account.get('coin', []):
                        currency = coin_data['coin']
                        wallet_balance = coin_data.get('walletBalance', '0')
                        available_balance = coin_data.get('availableToWithdraw', '0')
                        
                        total = float(wallet_balance) if wallet_balance else 0.0
                        free = float(available_balance) if available_balance else 0.0
                        used = total - free
                        
                        result['total'][currency] = total
                        result['free'][currency] = free
                        result['used'][currency] = used
                        result[currency] = {'total': total, 'free': free, 'used': used}
                
                return result
            else:
                return self.exchange.fetch_balance()
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return None

    def create_order(self, symbol, type, side, amount, price=None, take_profit=None, stop_loss=None, trailing_stop=None):
        """Creates an order with optional TP/SL/Trailing."""
        try:
            # Ensure amount is precise enough (ByBit usually needs specific precision)
            # For now, we rely on ccxt's handling or user input, but we could add precision handling here.
            
            if self.demo:
                # Workaround for ByBit Demo error 10032
                # Use raw v5 endpoint
                market_symbol = symbol.replace('/', '')
                
                # Format amount to correct precision
                formatted_amount = self.format_amount(symbol, amount)
                
                params = {
                    'category': 'linear',
                    'symbol': market_symbol,
                    'side': side.capitalize(),
                    'orderType': type.capitalize(),
                    'qty': formatted_amount,
                }
                if price:
                    params['price'] = str(price)
                
                if take_profit:
                    params['takeProfit'] = str(take_profit)
                if stop_loss:
                    params['stopLoss'] = str(stop_loss)
                if trailing_stop:
                    params['trailingStop'] = str(trailing_stop)
                
                response = self.exchange.private_post_v5_order_create(params)
                
                if str(response.get('retCode')) == '0':
                    return {'id': response['result']['orderId'], 'info': response}
                else:
                    self.logger.error(f"ByBit Demo Order Failed: {response}")
                    return None
            else:
                params = {}
                if take_profit:
                    params['takeProfit'] = str(take_profit)
                if stop_loss:
                    params['stopLoss'] = str(stop_loss)
                if trailing_stop:
                    params['trailingStop'] = str(trailing_stop)

                if price:
                    return self.exchange.create_order(symbol, type, side, amount, price, params)
                else:
                    return self.exchange.create_order(symbol, type, side, amount, None, params)
        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Insufficient Funds: {e}")
            return None
        except ccxt.InvalidOrder as e:
            self.logger.error(f"Invalid Order (Size too small/large?): {e}")
            return None
        except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
            self.logger.error(f"Network error creating order: {e}")
            # We might NOT want to retry orders automatically to avoid duplicates if the first one actually went through.
            # Safer to return None and let the next cycle handle it.
            return None
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetches current ticker data (last, bid, ask)."""
        try:
            if self.demo:
                # Workaround for ByBit Demo error 10032
                market_symbol = symbol.replace('/', '')
                response = self.exchange.public_get_v5_market_tickers({
                    'category': 'linear',
                    'symbol': market_symbol
                })
                if str(response.get('retCode')) == '0':
                    result = response.get('result', {})
                    list_data = result.get('list', [])
                    if list_data:
                        ticker = list_data[0]
                        return {
                            'last': float(ticker.get('lastPrice', 0)),
                            'bid': float(ticker.get('bid1Price', 0)),
                            'ask': float(ticker.get('ask1Price', 0)),
                            'info': ticker
                        }
                return None
            else:
                return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {e}")
            return None

    def get_market_price(self, symbol):
        """Fetches current market price."""
        ticker = self.fetch_ticker(symbol)
        if ticker:
            return ticker['last']
        return None

    def fetch_position(self, symbol):
        """Fetches current position for a symbol."""
        for attempt in range(3):
            try:
                if self.demo:
                    # Use private_get_v5_position_list for Unified Account (Demo Workaround)
                    # symbol needs to be formatted, e.g., BTCUSDT
                    market_symbol = symbol.replace('/', '')
                    response = self.exchange.private_get_v5_position_list({
                        'category': 'linear',
                        'symbol': market_symbol
                    })
                    
                    if str(response.get('retCode')) == '0':
                        result = response.get('result', {})
                        list_data = result.get('list', [])
                        if list_data:
                            pos = list_data[0]
                            return {
                                'size': float(pos.get('size', 0)),
                                'side': pos.get('side', 'None'), # Buy, Sell, None
                                'entry_price': float(pos.get('avgPrice', 0))
                            }
                    return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
                else:
                    # Standard CCXT for Live Trading
                    positions = self.exchange.fetch_positions([symbol])
                    if positions:
                        pos = positions[0]
                        return {
                            'size': float(pos.get('contracts', 0) if pos.get('contracts') is not None else pos.get('info', {}).get('size', 0)),
                            'side': pos.get('side', 'None'),
                            'entry_price': float(pos.get('entryPrice', 0))
                        }
                    return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}

            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                self.logger.warning(f"Network error fetching position (Attempt {attempt+1}/3): {e}")
                import time
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                self.logger.error(f"Error fetching position: {e}")
                return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}
        return {'size': 0.0, 'side': 'None', 'entry_price': 0.0}

    def set_trailing_stop(self, symbol, trailing_stop_dist):
        """Sets trailing stop for the current position."""
        try:
            if self.demo:
                market_symbol = symbol.replace('/', '')
                response = self.exchange.private_post_v5_position_trading_stop({
                    'category': 'linear',
                    'symbol': market_symbol,
                    'trailingStop': str(trailing_stop_dist),
                    'positionIdx': 0 # 0 for one-way mode
                })
                if str(response.get('retCode')) == '0':
                    return True
                else:
                    self.logger.error(f"Failed to set trailing stop: {response}")
                    return False
            else:
                # CCXT might have a method, but for V5 specific, we can use the raw call or set_trading_stop if available
                # CCXT's set_trading_stop usually maps to the correct endpoint
                # But to be safe and consistent with Demo workaround:
                market_symbol = symbol.replace('/', '')
                params = {
                    'category': 'linear',
                    'symbol': market_symbol,
                    'trailingStop': str(trailing_stop_dist),
                    'positionIdx': 0
                }
                return self.exchange.set_trading_stop(symbol, trailing_stop_dist, params=params)
        except Exception as e:
            self.logger.error(f"Error setting trailing stop: {e}")
            return False
    def set_leverage(self, symbol, leverage):
        """Sets leverage for the symbol."""
        try:
            if self.demo:
                market_symbol = symbol.replace('/', '')
                response = self.exchange.private_post_v5_position_set_leverage({
                    'category': 'linear',
                    'symbol': market_symbol,
                    'buyLeverage': str(leverage),
                    'sellLeverage': str(leverage)
                })
                
                # Check for success or "leverage not modified" (retCode 110043)
                ret_code = str(response.get('retCode'))
                if ret_code == '0':
                    self.logger.info(f"Leverage set to {leverage}x for {symbol}")
                    return True
                elif ret_code == '110043': # Leverage not modified
                    self.logger.info(f"Leverage already {leverage}x for {symbol}")
                    return True
                else:
                    self.logger.error(f"Failed to set leverage: {response}")
                    return False
            else:
                # CCXT
                try:
                    self.exchange.set_leverage(leverage, symbol)
                    self.logger.info(f"Leverage set to {leverage}x for {symbol}")
                    return True
                except Exception as e:
                    if "not modified" in str(e).lower():
                         self.logger.info(f"Leverage already {leverage}x for {symbol}")
                         return True
                    raise e
                    
        except Exception as e:
            # Check for "leverage not modified" error (retCode 110043)
            if "110043" in str(e) or "leverage not modified" in str(e):
                self.logger.info(f"Leverage already {leverage}x for {symbol} (caught exception)")
                return True
            
    def close_position(self, symbol):
        """Closes the current position for the symbol."""
        try:
            position = self.fetch_position(symbol)
            size = position.get('size', 0.0)
            side = position.get('side', 'None')
            
            if size > 0 and side != 'None':
                # Determine opposing side
                close_side = 'Sell' if side == 'Buy' else 'Buy'
                
                self.logger.info(f"Closing {side} position of {size} {symbol}...")
                
                # Execute Market Order to close
                return self.create_order(
                    symbol=symbol,
                    type='market',
                    side=close_side,
                    amount=size
                )
            else:
                self.logger.info(f"No position to close for {symbol}")
                return True
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
