import pandas as pd
import yfinance as yf
from stockbook.settings import POLYGON_API_KEY as API_KEY
import plotly.graph_objects as go
from polygon import RESTClient
from typing import cast
from urllib3 import HTTPResponse
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import pdb

        

def get_historical_prices():
    client = RESTClient(API_KEY)
    ticker = "AAPL"
    start_date = "2022-06-01"
    end_date = "2022-06-03"

    trades = client.get_aggs(ticker, 1, "day", start_date, end_date)
    date = trades[0].timestamp
    date = datetime.fromtimestamp(date // 1000)

    for x in enumerate(trades):
        print(x[1].timestamp)


    # for x in range (0, len(trades)):
    #     # pdb.set_trace()
    #     date_unix_msec = trades[x].timestamp
    #     date_converted = datetime.fromtimestamp(date_unix_msec // 1000).date()
    #     trades[x].timestamp = str(date_converted)

    # df = pd.DataFrame(trades)
    # df = df.to_json()
    # # list = df['timestamp'].tolist()
    # print(df)


get_historical_prices()


def get_stock_info(ticker):
    stock_data = yf.Ticker(ticker).stats()
    print(stock_data["financialData"]["freeCashflow"])




def yfinance_error_handler(ticker): 
    stock_data = yf.Ticker(ticker).stats()
    try:
        whatever_data = stock_data[stock_data]["longBusinessSummary"]
    except (KeyError, TypeError):
        whatever_data = "-"

    print(whatever_data)


def yfinance_data_handler(ticker, firstKey, secondKey):

    stock_data = yf.Ticker(ticker).stats()
    try:
        return stock_data[firstKey][secondKey]
    except (KeyError, TypeError):
        return "-"


# dataretrieved = yfinance_data_handler("MBUU", "summaryData", "trailingPE")



