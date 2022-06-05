import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
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

    trades = []
    for t in client.list_trades(ticker, "2022-04-04", limit=5):
        trades.append(t)
    print(trades)

get_last_trade_data()


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
    stock_data = ticker.stats()
    
    stock_price = stock_data["summaryProfile"]["sector"]
    stock_price = stock_data["price"]["marketCap"]
    stock_price = stock_data["summaryDetail"]["fiftyTwoWeekHigh"]
    stock_price = stock_data["summaryDetail"]["fiftyTwoWeekLow"]
    stock_price = stock_data["summaryDetail"]["averageVolume"]
    stock_price = stock_data["financialData"]["totalRevenue"]
    stock_price = stock_data["defaultKeyStatistics"]["netIncomeToCommon"]
    stock_price = stock_data["summaryDetail"]["dividendRate"]
    stock_price = stock_data["summaryDetail"]["dividendYield"]
    stock_price = stock_data["summaryDetail"]["payoutRatio"]
    stock_price = stock_data["summaryDetail"]["trailingPE"]
    stock_price = stock_data["financialData"]["freeCashflow"]
    stock_price = stock_data["defaultKeyStatistics"]["profitMargins"]
    stock_price = stock_data["financialData"]["debtToEquity"]

    
    print(stock_price)


def test5():
    timeseries = yf.download(tickers = "PANL",
        # use "period" instead of start/end
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # (optional, default is '1mo')
        period = "ytd",

        # fetch data by interval (including intraday if period < 60 days)
        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval = "1d",

        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust = True,

        # download pre/post regular market hours data
        # (optional, default is False)
        prepost = True,
    )

    timeseries = timeseries.reset_index()
    timeseries.rename(columns={timeseries.columns[0]:"Date"}, inplace = True)
    print(timeseries)

    fig = px.line(timeseries, x="Date", y="Open")

    fig.layout = dict(xaxis=dict(type="category"))

    fig.show()

