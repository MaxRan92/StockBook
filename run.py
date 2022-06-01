import pandas as pd
import yfinance as yf
from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
from datetime import datetime, timedelta
import pandas_market_calendars as mcal




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



API_KEY = "R7PbrIpBoMRsJuAHnAPrD07XGMgpJy89"

def test():

        client = RESTClient(API_KEY)
        ticker = "AAPL"

        last_trade_data = client.get_last_trade(ticker, params=None, raw=False)

        # Get last trade price with datetime
        last_trade_price = last_trade_data.price
        print(last_trade_price)
        





def get_last_trade_data():
    client = RESTClient(API_KEY)
    ticker = "AAPL"

    aggs = client.get_aggs(ticker, 1, "day", "2022-05-29", "2022-05-29")

    print(aggs)




def get_daily_aggs(self, request, ticker, start_date, end_date):
    client = RESTClient(API_KEY)

    self.aggs = client.get_aggs(ticker, 1, "day", start_date, end_date)



def test3():
    nyse = mcal.get_calendar('NYSE')
    market_open_days = nyse.valid_days(start_date='2010-12-31', end_date='2030-12-31')
    
    last_trade_datetime = datetime.today()
    print(last_trade_datetime)
    
    market_open = False
    while market_open is False:
        for i in range(4):
            previous_day = last_trade_datetime - timedelta(i+1)
            if previous_day.strftime('%Y-%m-%d') in market_open_days:
                market_open = True
                print(i)
                print(previous_day)
                break
                

    
def test4():
    ticker = yf.Ticker("GS")
    stock_data = ticker.info
    price_earnings = stock_data['trailingPE']
    market_cap = stock_data['marketCap']
    profit_margin = stock_data['profitMargins']
    free_cash_flow = stock_data['freeCashflow']
    debt_to_equity = stock_data['debtToEquity']
    
    print(price_earnings, market_cap, free_cash_flow, debt_to_equity, profit_margin)


test4()