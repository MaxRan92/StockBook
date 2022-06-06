import math
import json
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from stockbook.settings import POLYGON_API_KEY as API_KEY
from flask import url_for, render_template
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.views.generic import DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import StockInfo, Comment
from .forms import CommentForm, EditForm
from polygon import RESTClient



MILLNAMES = ['',' k',' M',' Bn',' Tn']


class StockList(generic.ListView):
    model = StockInfo
    queryset = StockInfo.objects.filter(status=1).order_by("-created_on")
    template_name = 'index.html'
    paginate_by = 6


class StockDetail(View):

    comment_edited = False
    comment_deleted = False


    def get(self, request, slug, *args, **kwargs):
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        all_comments = Comment.objects.filter(approved=True)
        comments = stockinfo.comments.filter(approved=True).order_by('-created_on')
        
        self.sentiment_analysis(stockinfo)
        self.get_polygon_last_trade(stockinfo.ticker)
        self.get_yfinance_figures(stockinfo.ticker)
        self.get_chart_data(stockinfo.ticker, "day", "2021-12-31", self.previous_day)

        self.comment_edited_var = False
        self.comment_deleted_var = False

        if self.comment_edited == True:
            self.comment_edited_var = True
            StockDetail.comment_edited = False
        else:
            self.comment_edited_var = False
        
        if self.comment_deleted == True:
            self.comment_deleted_var = True
            StockDetail.comment_deleted = False
        else:
            self.comment_deleted_var = False


        return render(
            request,
            "stock_detail.html",
            {
                "stockinfo": stockinfo,
                "comments": comments,
                "commented": False,
                "comment_form": CommentForm,
                "comment_edited": self.comment_edited_var,
                "comment_deleted": self.comment_deleted_var,
                "bulls_num": self.bulls_num,
                "bears_num": self.bears_num,
                "hold_num": self.hold_num,
                "bulls_bears_ratio": self.bulls_bears_ratio,
                "last_trade_price": self.last_trade_price,
                "last_trade_datetime": self.last_trade_datetime,
                "daily_perf": self.daily_perf,
                "price_earnings": self.price_earnings,
                "price_to_fcf": self.price_to_fcf,
                "profit_margin": self.profit_margin,
                "debt_to_equity": self.debt_to_equity,
                "sector": self.sector,
                "market_cap": self.market_cap_formatted,
                "high_52w": self.high_52w,
                "low_52w": self.low_52w,
                "avg_vol": self.avg_vol,
                "revenue": self.revenue,
                "income": self.income,
                "dividend_rate": self.dividend_rate,
                "dividend_yield": self.dividend_yield,
                "payout_ratio": self.payout_ratio,
                "currency": self.currency,
                "context": self.context,
            },
        )

        

    def sentiment_analysis(self, stockinfo):
        '''
        Function that counts the number of bull and bear sentiment
        expressed by the users and calculates a bull to bear ratio
        '''
        self.bulls_num = len(stockinfo.comments.filter(sentiment='BULL', approved=True).order_by('-created_on'))
        self.bears_num = len(stockinfo.comments.filter(sentiment='BEAR', approved=True).order_by('-created_on'))
        self.hold_num = len(stockinfo.comments.filter(sentiment='HOLD', approved=True).order_by('-created_on'))
        if self.bulls_num == 0 or self.bears_num == 0:
            self.bulls_bears_ratio = "N/A"
        else:
            self.bulls_bears_ratio = self.bulls_num/self.bears_num
        

    def get_polygon_last_trade(self, ticker):
        '''
        Function that takes ticker, retrieves stock trade data from polygon API, 
        in order to get the last trade price, the linked timestamp and the daily
        performance relative to previous close
        '''
         # Get last trade price with datetime
        self.get_last_trade_data(ticker)
        self.last_trade_price = self.last_trade_data.price
        self.last_trade_timestamp = self.last_trade_data.participant_timestamp
        self.last_trade_datetime = datetime.fromtimestamp(self.last_trade_timestamp/1e9)

        # Get previous day close price
        nyse = mcal.get_calendar('NYSE')
        market_open_days = nyse.valid_days(start_date='2010-12-31', end_date='2030-12-31')

        market_open = False
        while market_open is False:
            for i in range(10):
                self.previous_day = self.last_trade_datetime - timedelta(i+1)
                if self.previous_day.strftime('%Y-%m-%d') in market_open_days:
                    market_open = True
                    break

        self.previous_day = self.previous_day.strftime("%Y-%m-%d")
        self.get_daily_aggs(ticker, "day", self.previous_day, self.previous_day)
        last_close = self.aggs[0].close
        self.daily_perf = Percent(self.last_trade_price / last_close - 1)
        

    def get_yfinance_figures(self, ticker):
        '''
        Function that takes ticker, retrieves stock data from yfinance library, 
        and populates a list of variables used for Overview, Financials and Fundamental 
        data
        '''
        # Get stock info from YFinance
        self.get_stock_info(ticker)

        # Overview
        self.currency = self.stock_data["summaryDetail"]["currency"]
        self.sector = self.stock_data["summaryProfile"]["sector"]
        self.market_cap = self.stock_data["price"]["marketCap"]
        self.market_cap_formatted = millify(self.market_cap)
        self.high_52w = self.stock_data["summaryDetail"]["fiftyTwoWeekHigh"]
        self.low_52w = self.stock_data["summaryDetail"]["fiftyTwoWeekLow"]
        self.avg_vol = '{:,}'.format(self.stock_data["summaryDetail"]["averageVolume"])

        # Financials
        self.revenue = millify(self.stock_data["financialData"]["totalRevenue"])
        self.income = millify(self.stock_data["defaultKeyStatistics"]["netIncomeToCommon"])
        self.dividend_rate = self.stock_data["summaryDetail"]["dividendRate"]
        self.dividend_yield = self.stock_data["summaryDetail"]["dividendYield"]
        if self.dividend_rate is None:
            self.dividend_rate = 0
        if self.dividend_yield is None:
            self.dividend_yield = 0
        self.dividend_rate = round(self.dividend_rate, 2)
        self.dividend_yield = Percent(self.dividend_yield)
        self.payout_ratio = Percent(self.stock_data["summaryDetail"]["payoutRatio"])

        # Multiples
        self.price_earnings = round(self.stock_data["summaryDetail"]['trailingPE'], 2)
        free_cash_flow = self.stock_data["financialData"]['freeCashflow']
        if free_cash_flow is None or free_cash_flow <= 0:
            self.price_to_fcf = "-"
        else:
            self.price_to_fcf = round(self.market_cap / free_cash_flow,2)
        self.profit_margin = Percent(self.stock_data["defaultKeyStatistics"]['profitMargins'])
        self.debt_to_equity = round(self.stock_data["financialData"]['debtToEquity']/100,2)

        

    def get_chart_data(self, ticker, interval, start_date, end_date):
        '''
        Function that get ticker, data interval, start date and end date,
        retrieves stock data from Polygon API, creates a list of 
        timestamps and prices, and converts the list to JSON array in order
        to be rendered in the chart.js
        '''
        self.get_daily_aggs(ticker, interval, start_date, end_date)
        trades = self.aggs

        for x in range (0, len(trades)):
            date_unix_msec = trades[x].timestamp
            date_converted = datetime.fromtimestamp(date_unix_msec // 1000).date()
            trades[x].timestamp = str(date_converted)
        
        df = pd.DataFrame(trades)
        dates = df["timestamp"].tolist()
        prices = df["close"].tolist()
        self.context = {"dates": mark_safe(json.dumps(dates)), "prices": mark_safe(json.dumps(prices))}


    def get_last_trade_data(self, ticker):
        client = RESTClient(API_KEY)

        self.last_trade_data = client.get_last_trade(ticker, params=None, raw=False)
    

    def get_daily_aggs(self, ticker, timespan, start_date, end_date):
        client = RESTClient(API_KEY)

        self.aggs = client.get_aggs(ticker, 1, timespan, start_date, end_date)


    def get_stock_info(self, ticker):
        self.stock_data = yf.Ticker(ticker).stats()
        
    def post(self, request, slug, *args, **kwargs):
        """
        Post method to post the comment.
        """
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        comments = stockinfo.comments.filter(approved=True).order_by('-created_on')
        
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            comment_form.instance.email = request.user.email
            comment_form.instance.name = request.user.username
            comment = comment_form.save(commit=False)
            comment.stock = stockinfo
            comment.approved = True
            comment.save()
        else:
            comment_form = CommentForm()

        self.sentiment_analysis(stockinfo)
        self.get_polygon_last_trade(stockinfo.ticker)
        self.get_yfinance_figures(stockinfo.ticker)
        self.get_chart_data(stockinfo.ticker, "day", "2021-12-31", self.previous_day)

        return render(
            request,
            "stock_detail.html",
            {
                "stockinfo": stockinfo,
                "comments": comments,
                "commented": True,
                "comment_form": CommentForm,
                "bulls_num": self.bulls_num,
                "bears_num": self.bears_num,
                "hold_num": self.hold_num,
                "bulls_bears_ratio": self.bulls_bears_ratio,
                "last_trade_price": self.last_trade_price,
                "last_trade_datetime": self.last_trade_datetime,
                "daily_perf": self.daily_perf,
                "price_earnings": self.price_earnings,
                "price_to_fcf": self.price_to_fcf,
                "profit_margin": self.profit_margin,
                "debt_to_equity": self.debt_to_equity,
                "sector": self.sector,
                "market_cap": self.market_cap_formatted,
                "high_52w": self.high_52w,
                "low_52w": self.low_52w,
                "avg_vol": self.avg_vol,
                "revenue": self.revenue,
                "income": self.income,
                "dividend_rate": self.dividend_rate,
                "dividend_yield": self.dividend_yield,
                "payout_ratio": self.payout_ratio,
                "currency": self.currency,
                "context": self.context,
            },
        )


@method_decorator(login_required, name="dispatch")
class CommentDelete(DeleteView):
    """
    If user is logged in:
    Direct user to delete_comment.html template
    User will be prompted with a message to confirm.
    """
    model = Comment
    template_name = "delete_comment.html"
    success_message = "Your Review was successfully deleted."
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(CommentDelete, self).delete(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        StockDetail.comment_deleted = True
        return reverse("stock_detail", kwargs={"slug": self.object.stock.slug})


@method_decorator(login_required, name="dispatch")
class CommentEdit(UpdateView):
    """
    If user is logged in:
    Direct user to update_comment.html template,
    displaying ReviewForm for that specific review.
    Post edited info back to the DB
    return user to post.
    display success message.
    """
    model = Comment
    form_class = EditForm
    template_name = "edit_comment.html"

    def form_valid(self, form):
        """
        Upon success prompt the user with a success message.
        """
        super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        """
        Upon success returns user to the stock detail page.
        """
        StockDetail.comment_edited = True
        return reverse("stock_detail", kwargs={"slug": self.object.stock.slug})


class Percent(float):
    def __str__(self):
        return '{:.2%}'.format(self)



# adapted version of code form Janus on StackOverflow https://stackoverflow.com/questions/3154460/python-human-readable-large-numbers
def millify(n):
    n = float(n)
    millidx = max(0,min(len(MILLNAMES)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), MILLNAMES[millidx])