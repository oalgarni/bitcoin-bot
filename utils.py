import json
import logging

def save_state(file_path, state):
    with open(file_path, 'w') as f:
        json.dump(state, f)
    logging.info(f"State saved to {file_path}")

def load_state(file_path):
    try:
        with open(file_path, 'r') as f:
            state = json.load(f)
        logging.info(f"State loaded from {file_path}")
        return state
    except FileNotFoundError:
        logging.warning(f"State file {file_path} not found")
        return None
