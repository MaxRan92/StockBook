import pandas as pd
import yfinance as yf
from polygon import RESTClient


API_KEY = "R7PbrIpBoMRsJuAHnAPrD07XGMgpJy89"

def polygon_data():
    client = RESTClient(API_KEY)

    aggs = client.get_aggs("PLTR", 1, "day", "2022-04-04", "2022-04-04")
    last = client.get_last_trade("PLTR", params=None, raw=False)
    print(last)


polygon_data()