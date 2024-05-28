from binance.client import Client
from config import API_KEY, API_SECRET

def get_client():
    return Client(API_KEY, API_SECRET)
