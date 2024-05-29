import logging
from colorama import Fore

def execute_trade(client, action, usdt_balance, btc_balance, buy_price, stop_loss_threshold):
    logger = logging.getLogger('btc_trading_bot')
    logger.info(f"Executing trade action: {action}")
    price = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])
    profit = None

    if action == 'BUY' and usdt_balance > 0:
        # Execute buy logic
        btc_amount = usdt_balance / price  # Buy as much BTC as possible with USDT
        usdt_balance = 0
        btc_balance += btc_amount
        logger.info(f"Bought BTC at {price} USDT/BTC, BTC amount: {btc_amount}")
        buy_price = price  # Record the buy price

    elif action == 'SELL' and btc_balance > 0:
        # Execute sell logic
        usdt_amount = btc_balance * price  # Sell all BTC for USDT
        profit = usdt_amount - (btc_balance * buy_price) if buy_price else None
        btc_balance = 0
        usdt_balance += usdt_amount
        logger.info(f"Sold BTC at {price} USDT/BTC, USDT amount: {usdt_amount}, PROFIT: {profit}")

    elif action == 'HOLD' and btc_balance > 0:
        # Check if holding is profitable
        if buy_price and (price > buy_price * 1.005):  # 0.5% profit threshold
            usdt_amount = btc_balance * price
            profit = usdt_amount - (btc_balance * buy_price)
            btc_balance = 0
            usdt_balance += usdt_amount
            logger.info(Fore.GREEN + f"Executed HOLD as SELL at {price} USDT/BTC, USDT amount: {usdt_amount}, PROFIT: {profit}")
        else:
            logger.info("Holding position")

    # Check for stop loss
    if btc_balance > 0 and buy_price and price < buy_price * (1 - stop_loss_threshold):
        usdt_amount = btc_balance * price
        profit = usdt_amount - (btc_balance * buy_price)
        btc_balance = 0
        usdt_balance += usdt_amount
        logger.info(Fore.RED + f"Stop Loss Triggered. Sold BTC at {price} USDT/BTC, USDT amount: {usdt_amount}, LOSS: {profit}")

    return usdt_balance, btc_balance, profit, price, buy_price