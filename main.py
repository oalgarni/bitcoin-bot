import os
import time
import logging
from datetime import datetime, timedelta, timezone
from binance_client import get_client
from data_processing import get_historical_data, preprocess_data, save_data_to_csv, load_data_from_csv
from model import train_model, predict
from trading_logic import execute_trade
from utils import save_state, load_state

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting the Bitcoin trading bot")
    client = get_client()
    usdt_balance = 1000  # Starting with 1000 USDT
    btc_balance = 0  # Starting with 0 BTC

    # Ensure the data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
        logging.info("Created 'data' directory")

    # Load previous state if exists
    state = load_state('data/state.json')
    if state:
        usdt_balance = state.get('usdt_balance', usdt_balance)
        btc_balance = state.get('btc_balance', btc_balance)
        logging.info(f"Loaded previous state. USDT Balance: {usdt_balance} USDT, BTC Balance: {btc_balance} BTC")

    # Load historical data from CSV if exists, else fetch from API
    try:
        data = load_data_from_csv('data/historical_data.csv')
        logging.info("Loaded historical data from CSV")
    except FileNotFoundError:
        logging.info("Historical data CSV not found, fetching from Binance API")
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7*365)  # Approx 7 years
        data = get_historical_data(client, 'BTCUSDT', '6h', start_time, end_time)
        save_data_to_csv(data, 'data/historical_data.csv')
        logging.info("Fetched and saved historical data to CSV")

    # Preprocess historical data
    try:
        data = preprocess_data(data)
        logging.info("Preprocessed historical data")
    except Exception as e:
        logging.error(f"Error during data preprocessing: {e}")
        return

    # Train the model
    model = train_model(data)
    logging.info("Model training complete")

    # Main trading loop
    while True:
        try:
            # Fetch latest data dynamically
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=6)
            latest_data = get_historical_data(client, 'BTCUSDT', '6h', start_time, end_time)
            latest_data = preprocess_data(latest_data)
            logging.info("Fetched and preprocessed latest data")

            # Make prediction
            action = predict(model, latest_data)
            logging.info(f"Predicted action: {action}")

            # Execute trade based on prediction
            usdt_balance, btc_balance = execute_trade(client, action, usdt_balance, btc_balance)
            logging.info(f"Executed trade. USDT Balance: {usdt_balance} USDT, BTC Balance: {btc_balance} BTC")

            # Save state
            save_state('data/state.json', {'usdt_balance': usdt_balance, 'btc_balance': btc_balance})
            logging.info("Saved state")

            # Wait for next interval
            logging.info("Waiting for next interval")
            time.sleep(3600)  # Sleep for 1 hour
        except Exception as e:
            logging.error(f"Error: {e}")
            logging.info("Retrying in 1 minute")
            time.sleep(60)  # Sleep for 1 minute before retrying

if __name__ == "__main__":
    main()
