import config
import logging
import time
from exchange.client import ExchangeClient
from strategies.mean_reversion import MeanReversion
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("test_tpsl_output.log"), logging.StreamHandler()])
logger = logging.getLogger("TestTPSL")

def test_tpsl_order():
    try:
        logger.info("Starting TP/SL/Trailing Order Test on ByBit Demo...")
        
        client = ExchangeClient(config.API_KEY, config.API_SECRET, demo=config.DEMO)
        symbol = config.SYMBOL
        amount = 0.001  # Small amount for testing
        
        # Check Balance
        logger.info("Checking Balance...")
        balance = client.fetch_balance()
        logger.info(f"Balance: {balance}")

        # Get Current Price
        current_price = client.get_market_price(symbol)
        logger.info(f"Current Price: {current_price}")

        # Calculate TP/SL/Trailing with Fees (Simulating bot logic)
        gross_tp_pct = 0.01 + (2 * 0.0006) # 1% + 0.12% = 1.12%
        gross_sl_pct = 0.005 - (2 * 0.0006) # 0.5% - 0.12% = 0.38%
        
        tp_price = current_price * (1 + gross_tp_pct)
        sl_price = current_price * (1 - gross_sl_pct)
        trailing_dist = current_price * 0.005 # 0.5%
        
        # Round to precision (simple rounding for test)
        tp_price = round(tp_price, 2)
        sl_price = round(sl_price, 2)
        trailing_dist = round(trailing_dist, 2)

        logger.info(f"Test Params (Fee Adjusted) - TP: {tp_price}, SL: {sl_price}, Trailing: {trailing_dist}")

        # 1. Place BUY Order with TP/SL/Trailing
        logger.info(f"1. Placing MARKET BUY order for {amount} {symbol} with TP/SL/Trailing...")
        order = client.create_order(
            symbol, 
            'market', 
            'buy', 
            amount, 
            take_profit=tp_price, 
            stop_loss=sl_price, 
            trailing_stop=trailing_dist
        )
        
        if order:
            logger.info(f"Order placed successfully: {order.get('id')}")
            logger.info(f"Order Info: {order.get('info')}")
        else:
            logger.error("Failed to place order. Aborting.")
            return

        # Wait for order to fill/propagate
        time.sleep(5)
        
        # 2. Check Position to confirm TP/SL attached
        logger.info("2. Checking position to confirm TP/SL...")
        
        # Fetch raw position to see TP/SL details
        market_symbol = symbol.replace('/', '')
        raw_position = client.exchange.private_get_v5_position_list({
            'category': 'linear',
            'symbol': market_symbol
        })
        logger.info(f"Raw Position Data: {raw_position}")
        
        # If trailing stop is 0, try setting it manually using the new method
        pos_data = raw_position['result']['list'][0]
        if float(pos_data.get('trailingStop', 0)) == 0:
            logger.info("Trailing Stop not set. Attempting to set via client.set_trailing_stop...")
            res = client.set_trailing_stop(symbol, trailing_dist)
            logger.info(f"Set Trading Stop Result: {res}")
            
            # Check again
            time.sleep(2)
            raw_position_2 = client.exchange.private_get_v5_position_list({
                'category': 'linear',
                'symbol': market_symbol
            })
            logger.info(f"Raw Position Data 2: {raw_position_2}")

        position = client.fetch_position(symbol)
        logger.info(f"Simplified Position: {position}")
        
        # 3. Close Position
        logger.info(f"3. Closing position...")
        client.create_order(symbol, 'market', 'sell', amount)
        logger.info("Position closed.")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tpsl_order()
