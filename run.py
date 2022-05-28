import pandas as pd
import yfinance as yf
from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
from datetime import datetime, timedelta


API_KEY = "R7PbrIpBoMRsJuAHnAPrD07XGMgpJy89"

def polygon_data():
    client = RESTClient(API_KEY)

    
    last = client.get_last_trade("NOACU", params=None, raw=False)

    date = last.participant_timestamp
    dt = datetime.fromtimestamp(date // 1000000000) - timedelta(1)
    dtprev = dt 
    s = dt.strftime('%Y-%m-%d %H:%M:%S')
    d = dt.strftime('%Y-%m-%d')
    dd = dtprev.strftime('%Y-%m-%d')
    print(d)
    print(dd)
    
    aggs = client.get_aggs("AAPL", 1, "day", d, d)
    daily_aggs= client.get_grouped_daily_aggs(d, adjusted=None, params=None, raw=False, market_type='stocks')
    print(aggs)





def test():

        client = RESTClient(API_KEY)
        ticker = "AAPL"

        last_trade_data = client.get_last_trade(ticker, params=None, raw=False)
        aggs = client.get_aggs(ticker, 1, "day", start_date, end_date)

        # Get last trade price with datetime
        get_last_trade_data(request, stockinfo.ticker)
        last_trade_price = last_trade_data.price
        last_trade_timestamp = last_trade_data.participant_timestamp
        last_trade_datetime = datetime.fromtimestamp(last_trade_timestamp/1e9)

        # Get previous day close price
        previous_day = last_trade_datetime - timedelta(1)
        get_daily_aggs(request, stockinfo.ticker, previous_day, previous_day)
        last_close = aggs.close
        daily_perf = last_trade_price / last_close - 1




test()