import logging

def execute_trade(client, action, usdt_balance, btc_balance, previous_price):
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
    
    elif action == 'SELL' and btc_balance > 0:
        # Execute sell logic
        usdt_amount = btc_balance * price  # Sell all BTC for USDT
        profit = usdt_amount - (btc_balance * previous_price) if previous_price else None
        btc_balance = 0
        usdt_balance += usdt_amount
        logger.info(f"Sold BTC at {price} USDT/BTC, USDT amount: {usdt_amount}")
    
    return usdt_balance, btc_balance, profit, price