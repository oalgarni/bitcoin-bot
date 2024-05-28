import os
import time
import logging
import csv
from datetime import datetime, timedelta, timezone
from binance_client import get_client
from data_processing import get_historical_data, preprocess_data, save_data_to_csv, load_data_from_csv
from model import train_model, load_model, predict, evaluate_model
from trading_logic import execute_trade
from utils import save_state, load_state
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Custom logging formatter with colors
class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_colors = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.WHITE,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.RED + Style.BRIGHT
        }
        color = log_colors.get(record.levelname, Fore.WHITE)
        message = logging.Formatter.format(self, record)
        return color + message

# Configure colored logging for btc_trading_bot logger
logger = logging.getLogger('btc_trading_bot')
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Ensure the root logger does not propagate to avoid duplication
logger.propagate = False

def log_current_price(client):
    try:
        ticker = client.get_ticker(symbol='BTCUSDT')
        current_price = ticker['lastPrice']
        logger.info(f"Current BTC price: {current_price} USDT")
    except Exception as e:
        logger.error(f"Error fetching current BTC price: {e}")

def load_trade_history(file_path):
    trade_history = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trade_history.append({
                    'timestamp': row['timestamp'],
                    'action': row['action'],
                    'price': float(row['price']),
                    'usdt_balance': float(row['usdt_balance']),
                    'btc_balance': float(row['btc_balance']),
                    'profit': float(row['profit']) if row['profit'] and row['profit'] != 'None' else None
                })
    return trade_history

def main():
    logger.info("Starting the Bitcoin trading bot")
    client = get_client()
    usdt_balance = 1000  # Starting with 1000 USDT
    btc_balance = 0  # Starting with 0 BTC
    stop_loss_threshold = 0.05  # 5% stop loss

    # Ensure the data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
        logger.info("Created 'data' directory")

    # Load previous state if exists
    state = load_state('data/state.json')
    if state:
        usdt_balance = state.get('usdt_balance', usdt_balance)
        btc_balance = state.get('btc_balance', btc_balance)
        logger.info(f"Loaded previous state. USDT Balance: {usdt_balance} USDT, BTC Balance: {btc_balance} BTC")

    # Load trade history if exists
    trade_history = load_trade_history('data/trade_history.csv')

    # Fetch historical data from Binance API
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7*365)  # Approx 7 years
    data = get_historical_data(client, 'BTCUSDT', '6h', start_time, end_time)
    save_data_to_csv(data, 'data/historical_data.csv')
    logger.info("Fetched and saved historical data to CSV")

    # Preprocess historical data
    try:
        data = preprocess_data(data)
        logger.info("Preprocessed historical data")
    except Exception as e:
        logger.error(f"Error during data preprocessing: {e}")
        return

    # Load or train the model
    model_file = 'data/model.keras'
    if (os.path.exists(model_file)):
        model = load_model(model_file)
        logger.info("Model loaded from file")

        # Evaluate model and log metrics
        evaluate_model(data, model)
    else:
        model = train_model(data)
        model.save(model_file)
        logger.info("Model trained and saved")

        # Evaluate model and log metrics
        evaluate_model(data, model)

    # Main trading loop
    previous_price = None
    if trade_history:
        previous_price = trade_history[-1]['price']
    
    while True:
        try:
            # Fetch latest data dynamically
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=6)
            latest_data = get_historical_data(client, 'BTCUSDT', '6h', start_time, end_time)
            latest_data = preprocess_data(latest_data)
            logger.info("Fetched and preprocessed latest data")

            # Make prediction
            action = predict(model, latest_data)
            if action == 'BUY' and usdt_balance == 0:
                action = 'HOLD'
            logger.info(f"Predicted action: {action}")

            # Execute trade based on prediction
            usdt_balance, btc_balance, profit, trade_price = execute_trade(client, action, usdt_balance, btc_balance, previous_price, stop_loss_threshold)
            trade_history.append({
                'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                'action': action,
                'price': trade_price,
                'usdt_balance': usdt_balance,
                'btc_balance': btc_balance,
                'profit': profit
            })
            if profit is not None:
                if profit > 0:
                    logger.info(Fore.GREEN + f"Trade Result: PROFIT of {profit:.2f} USDT")
                else:
                    logger.info(Fore.RED + f"Trade Result: LOSS of {abs(profit):.2f} USDT")
            logger.info(f"Executed trade. USDT Balance: {usdt_balance} USDT, BTC Balance: {btc_balance} BTC")
            previous_price = trade_price

            # Save state
            save_state('data/state.json', {'usdt_balance': usdt_balance, 'btc_balance': btc_balance})
            logger.info("Saved state")

            # Save trade history
            with open('data/trade_history.csv', 'w', newline='') as f:
                fieldnames = ['timestamp', 'action', 'price', 'usdt_balance', 'btc_balance', 'profit']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for trade in trade_history:
                    writer.writerow(trade)

            # Wait for next interval, logging every hour
            interval = 3600  # Total wait time of 1 hour
            check_interval = 600  # Check every 10 minutes
            for remaining in range(interval, 0, -check_interval):
                logger.info(f"Waiting for next interval. Time left: {remaining // 60} minutes")
                log_current_price(client)
                time.sleep(check_interval)

        except Exception as e:
            logger.error(f"Error: {e}")
            logger.info("Retrying in 1 minute")
            time.sleep(60)  # Sleep for 1 minute before retrying

if __name__ == "__main__":
    main()
