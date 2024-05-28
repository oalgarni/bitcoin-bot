import pandas as pd
import logging

def get_historical_data(client, symbol, interval, start_time, end_time):
    logging.info(f"Fetching historical data from {start_time} to {end_time}")
    klines = client.get_historical_klines(symbol, interval, start_time.strftime('%Y-%m-%dT%H:%M:%S'), end_time.strftime('%Y-%m-%dT%H:%M:%S'))
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    logging.info(f"Fetched {len(data)} rows of data")
    return data

def preprocess_data(data):
    logging.info("Preprocessing data")
    logging.info(f"Data columns: {data.columns}")
    if 'timestamp' not in data.columns:
        logging.error("Timestamp column not found in data")
        raise KeyError("Timestamp column not found in data")
    
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)
    data = data[['open', 'high', 'low', 'close', 'volume']].astype(float)
    # Compute additional technical indicators here
    logging.info("Data preprocessing complete")
    return data

def save_data_to_csv(data, file_path):
    data.to_csv(file_path, index=True)
    logging.info(f"Data saved to {file_path}")

def load_data_from_csv(file_path):
    logging.info(f"Loading data from {file_path}")
    data = pd.read_csv(file_path, parse_dates=['timestamp'], index_col='timestamp')
    # Rename columns if necessary
    if 'Unnamed: 0' in data.columns:
        data = data.rename(columns={'Unnamed: 0': 'timestamp'})
    logging.info("Data loaded from CSV")
    logging.info(f"Loaded data columns: {data.columns}")
    return data