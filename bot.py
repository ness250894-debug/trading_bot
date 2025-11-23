import time
import logging
import sys
from exchange.client import ExchangeClient
from strategies.sma_crossover import SMACrossover
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TradingBot")

def main():
    logger.info("Starting Trading Bot...")
    
    # Initialize Exchange Client
    if getattr(config, 'DRY_RUN', False):
        from exchange.paper import PaperExchange
        logger.info("⚠️ DRY RUN MODE ENABLED: Using Paper Exchange")
        client = PaperExchange(config.API_KEY, config.API_SECRET)
    else:
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
    
    # Initialize Strategy
    strategy_name = getattr(config, 'STRATEGY', 'mean_reversion')
    logger.info(f"Selected Strategy: {strategy_name}")

    if strategy_name == 'mean_reversion':
        from strategies.mean_reversion import MeanReversion
        strategy = MeanReversion()
    elif strategy_name == 'sma_crossover':
        from strategies.sma_crossover import SMACrossover
        strategy = SMACrossover()
    elif strategy_name == 'combined':
        from strategies.combined import CombinedStrategy
        strategy = CombinedStrategy()
    elif strategy_name == 'macd':
        from strategies.macd import MACDStrategy
        strategy = MACDStrategy()
    elif strategy_name == 'rsi':
        from strategies.rsi import RSIStrategy
        strategy = RSIStrategy()
    else:
        logger.warning(f"Unknown strategy '{strategy_name}'. Defaulting to Mean Reversion.")
        from strategies.mean_reversion import MeanReversion
        strategy = MeanReversion()

    # Initialize Trend Filter
    from strategies.filters import TrendFilter
    trend_filter = TrendFilter(client, config.SYMBOL, config.HIGHER_TIMEFRAME)

    while True:
        try:
            logger.info("Fetching market data...")
            # Fetch OHLCV data
            df = client.fetch_ohlcv(config.SYMBOL, config.TIMEFRAME)
            
            if df is not None:
                # Generate Signal
                result = strategy.generate_signal(df)
                signal = result['signal']
                score = result['score']
                details = result['details']
                
                current_price = df.iloc[-1]['close']
                
                # --- Multi-Timeframe Analysis (Trend Filter) ---
                trend, price_high, ema_200 = trend_filter.check_trend()
                logger.info(f"Trend ({config.HIGHER_TIMEFRAME}): {trend} | Price: {price_high} | EMA 200: {ema_200:.2f}")
                # -----------------------------------------------

                # Apply Filter
                if signal == 'BUY' and trend == 'DOWNTREND':
                    logger.info("Signal is BUY but Trend is DOWNTREND. Filtering signal.")
                    signal = 'HOLD'
                elif signal == 'SELL' and trend == 'UPTREND':
                    logger.info("Signal is SELL but Trend is UPTREND. Filtering signal.")
                    signal = 'HOLD'
                # -----------------------------------------------
                
                # Log Indicators
                # sma_short = df.iloc[-1].get('sma_short', 0)
                # sma_long = df.iloc[-1].get('sma_long', 0)
                # rsi = df.iloc[-1].get('rsi', 0)
                # macd = df.iloc[-1].get('macd', 0)
                
                # logger.info(f"Price: {current_price} | SMA: {details.get('sma', 'N/A')} | RSI: {details.get('rsi', 'N/A')} | MACD: {details.get('macd', 'N/A')}")
                logger.info(f"Price: {current_price} | Signal: {signal} | Score: {score}/3")
                logger.info(f"Details: {details}")
                
                # Fetch current position
                position = client.fetch_position(config.SYMBOL)
                current_pos_size = position.get('size', 0.0)
                current_pos_side = position.get('side', 'None') # 'Buy', 'Sell', 'None'
                
                logger.info(f"Current Position: {current_pos_side} {current_pos_size} {config.SYMBOL}")

                # --- Scalping Risk Management (TP/SL) ---
                # Manual monitoring removed in favor of exchange-level TP/SL/Trailing
                # ----------------------------------------

                if signal == 'BUY':
                    # Reversal: If Short, Close Short first
                    if current_pos_side == 'Sell' and current_pos_size > 0:
                        logger.info(f"Closing SHORT position of {current_pos_size} {config.SYMBOL}...")
                        order = client.create_order(config.SYMBOL, 'market', 'buy', current_pos_size)
                        if order:
                            current_pos_size = 0 # Reset after close
                        else:
                            logger.error("Failed to close SHORT position. Skipping Long entry.")
                            continue # Skip the rest of this loop
                    
                    # Open Long if no position (or just closed short)
                    if current_pos_size == 0:
                        # Calculate amount based on balance
                        balance = client.fetch_balance()
                        if balance:
                            usdt_balance = balance['total']['USDT']
                            # Dynamic Risk based on Score
                            risk_pct = config.POSITION_SIZES.get(score, 0.01)
                            
                            amount = (usdt_balance * risk_pct) / current_price
                            
                            # Calculate TP/SL/Trailing with Fees
                            # TP: We want Net Profit = TP_PCT. Gross Profit = TP_PCT + 2 * Fee
                            # SL: We want Net Loss = SL_PCT. Gross Loss = SL_PCT - 2 * Fee (Tighter SL)
                            
                            gross_tp_pct = config.TAKE_PROFIT_PCT + (2 * config.TAKER_FEE_PCT)
                            gross_sl_pct = config.STOP_LOSS_PCT - (2 * config.TAKER_FEE_PCT)
                            
                            # Ensure SL is not negative (impossible unless fees > SL)
                            if gross_sl_pct <= 0:
                                logger.warning(f"Warning: Fees ({2*config.TAKER_FEE_PCT}) are larger than SL ({config.STOP_LOSS_PCT}). Setting SL to break-even (0).")
                                gross_sl_pct = 0

                            tp_price = current_price * (1 + gross_tp_pct)
                            sl_price = current_price * (1 - gross_sl_pct)
                            trailing_dist = current_price * config.TRAILING_STOP_PCT
                            
                            logger.info(f"Opening LONG position: {amount} {config.SYMBOL} (Score: {score}, Size: {risk_pct*100}%)")
                            logger.info(f"Fees: {2*config.TAKER_FEE_PCT*100:.3f}% | Gross TP: {gross_tp_pct*100:.3f}% | Gross SL: {gross_sl_pct*100:.3f}%")
                            logger.info(f"TP: {tp_price}, SL: {sl_price}, Trailing: {trailing_dist}")
                            
                            order = client.create_order(
                                config.SYMBOL, 
                                'market', 
                                'buy', 
                                amount, 
                                take_profit=tp_price, 
                                stop_loss=sl_price, 
                                trailing_stop=trailing_dist
                            )
                            
                            if order and trailing_dist > 0:
                                client.set_trailing_stop(config.SYMBOL, trailing_dist)
                        
                elif signal == 'SELL':
                    # Reversal: If Long, Close Long first
                    if current_pos_side == 'Buy' and current_pos_size > 0:
                        logger.info(f"Closing LONG position of {current_pos_size} {config.SYMBOL}...")
                        order = client.create_order(config.SYMBOL, 'market', 'sell', current_pos_size)
                        if order:
                            current_pos_size = 0 # Reset after close
                        else:
                            logger.error("Failed to close LONG position. Skipping Short entry.")
                            continue
                    
                    # Open Short if no position (or just closed long)
                    if current_pos_size == 0:
                        # Calculate amount based on balance
                        balance = client.fetch_balance()
                        if balance:
                            usdt_balance = balance['total']['USDT']
                            # Dynamic Risk based on Score
                            risk_pct = config.POSITION_SIZES.get(score, 0.01)
                            
                            amount = (usdt_balance * risk_pct) / current_price
                            
                            # Calculate TP/SL/Trailing with Fees
                            gross_tp_pct = config.TAKE_PROFIT_PCT + (2 * config.TAKER_FEE_PCT)
                            gross_sl_pct = config.STOP_LOSS_PCT - (2 * config.TAKER_FEE_PCT)
                            
                            if gross_sl_pct <= 0:
                                logger.warning(f"Warning: Fees ({2*config.TAKER_FEE_PCT}) are larger than SL ({config.STOP_LOSS_PCT}). Setting SL to break-even (0).")
                                gross_sl_pct = 0

                            tp_price = current_price * (1 - gross_tp_pct)
                            sl_price = current_price * (1 + gross_sl_pct)
                            trailing_dist = current_price * config.TRAILING_STOP_PCT
                            
                            logger.info(f"Opening SHORT position: {amount} {config.SYMBOL} (Score: {score}, Size: {risk_pct*100}%)")
                            logger.info(f"Fees: {2*config.TAKER_FEE_PCT*100:.3f}% | Gross TP: {gross_tp_pct*100:.3f}% | Gross SL: {gross_sl_pct*100:.3f}%")
                            logger.info(f"TP: {tp_price}, SL: {sl_price}, Trailing: {trailing_dist}")
                            
                            order = client.create_order(
                                config.SYMBOL, 
                                'market', 
                                'sell', 
                                amount,
                                take_profit=tp_price, 
                                stop_loss=sl_price, 
                                trailing_stop=trailing_dist
                            )
                            
                            if order and trailing_dist > 0:
                                client.set_trailing_stop(config.SYMBOL, trailing_dist)
            
            # Sleep for a bit (e.g., 10 seconds for scalping)
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            # Add a small delay to avoid rapid error loops
            time.sleep(10)

if __name__ == "__main__":
    main()
