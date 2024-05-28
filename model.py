from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
import numpy as np
import logging

def create_model(input_shape):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_model(data):
    logging.info("Preparing data for training")
    X, y = prepare_data_for_training(data)
    model = create_model((X.shape[1], X.shape[2]))
    logging.info("Starting model training")
    history = model.fit(X, y, epochs=10, batch_size=32, verbose=1)
    logging.info(f"Model training complete with loss: {history.history['loss'][-1]}")
    return model

def prepare_data_for_training(data):
    sequence_length = 60  # Number of timesteps to consider for prediction
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i+sequence_length].values)
        y.append(data.iloc[i+sequence_length]['close'])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], X.shape[2]))
    logging.info(f"Prepared {len(X)} sequences for training")
    return X, y

def predict(model, latest_data):
    X = prepare_latest_data(latest_data)
    prediction = model.predict(X)
    logging.info(f"Prediction: {prediction[0][0]}")
    if prediction > 0.5:
        return 'BUY'
    elif prediction < -0.5:
        return 'SELL'
    else:
        return 'HOLD'

def prepare_latest_data(latest_data):
    sequence_length = 60
    X = [latest_data[-sequence_length:].values]
    X = np.array(X)
    X = X.reshape((X.shape[0], X.shape[1], X.shape[2]))
    return X
