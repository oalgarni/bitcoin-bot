from tensorflow.keras.models import Sequential, load_model as keras_load_model
from tensorflow.keras.layers import Dense, LSTM, Input
import numpy as np
import logging
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import os

def create_model(input_shape):
    model = Sequential()
    model.add(Input(shape=input_shape))
    model.add(LSTM(50, return_sequences=True))
    model.add(LSTM(50))
    model.add(Dense(1, activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def train_model(data):
    logging.info("Preparing data for training")
    X, y = prepare_data_for_training(data)
    model = create_model((X.shape[1], X.shape[2]))
    logging.info("Starting model training")
    history = model.fit(X, y, epochs=10, batch_size=32, verbose=1)
    logging.info(f"Model training complete with loss: {history.history['loss'][-1]}")
    
    # Evaluate model after training
    evaluate_model(data, model)
    
    # Plot and save training metrics
    plot_training_metrics(history)
    
    return model

def evaluate_model(data, model):
    # Configure logging
    logger = logging.getLogger('btc_trading_bot')
    logger.setLevel(logging.INFO)
    
    X, y = prepare_data_for_training(data)
    
    # Convert continuous target to discrete classes
    y_classes = convert_to_classes(y)
    y_pred = model.predict(X)
    y_pred_classes = convert_to_classes(y_pred)
    
    # Calculate evaluation metrics
    accuracy = accuracy_score(y_classes, y_pred_classes) * 100  # Convert to percentage
    f1 = f1_score(y_classes, y_pred_classes, average='weighted')
    cm = confusion_matrix(y_classes, y_pred_classes, labels=[-1, 0, 1])
    
    logger.info(f"Model Evaluation Metrics:")
    logger.info(f"Accuracy: {accuracy:.2f}%")
    logger.info(f"F1 Score: {f1:.2f}")
    logger.info(f"Confusion Matrix:\n{cm}")

def prepare_data_for_training(data):
    sequence_length = 60  # Number of timesteps to consider for prediction
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i+sequence_length].values)
        # Use percentage change to create more balanced classes
        y_change = (data.iloc[i+sequence_length]['close'] - data.iloc[i+sequence_length-1]['close']) / data.iloc[i+sequence_length-1]['close']
        y.append(y_change)
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], X.shape[2]))
    logging.info(f"Prepared {len(X)} sequences for training")
    return X, y

def predict(model, latest_data):
    X = prepare_latest_data(latest_data)
    prediction = model.predict(X)
    logging.info(f"Prediction: {prediction[0][0]}")
    if prediction > 0.01:
        return 'BUY'
    elif prediction < -0.01:
        return 'SELL'
    else:
        return 'HOLD'

def prepare_latest_data(latest_data):
    sequence_length = 60
    X = [latest_data[-sequence_length:].values]
    X = np.array(X)
    X = X.reshape((X.shape[0], X.shape[1], X.shape[2]))
    return X

def load_model(file_path):
    return keras_load_model(file_path)

def convert_to_classes(values):
    classes = []
    for value in values:
        if value > 0.01:
            classes.append(1)  # BUY
        elif value < -0.01:
            classes.append(-1)  # SELL
        else:
            classes.append(0)  # HOLD
    return np.array(classes)

def plot_training_metrics(history):
    if not os.path.exists('charts'):
        os.makedirs('charts')
    
    plt.figure(figsize=(12, 6))
    
    # Plot training loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.title('Training Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    # Save the plot
    plt.savefig('charts/training_loss.png')
    
    plt.tight_layout()
    plt.show()