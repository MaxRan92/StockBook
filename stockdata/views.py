from datetime import datetime, timedelta
import math
import json
from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import DeleteView, UpdateView
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from polygon import RESTClient, exceptions
from requests.exceptions import Timeout, TooManyRedirects, RequestException, HTTPError  # noqa
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from stockbook.settings import POLYGON_API_KEY as API_KEY
from .models import StockInfo, Comment
from .forms import CommentForm, EditForm


MILLNAMES = ['', ' k', ' M', ' Bn', ' Tn']


class StockList(generic.ListView):
    model = StockInfo
    queryset = StockInfo.objects.filter(status=1).order_by("-created_on")
    template_name = 'index.html'
    paginate_by = 8


class AboutTemplateView(TemplateView):
    template_name = 'about.html'


class Page403(TemplateView):
    template_name = '403.html'


class Page404(TemplateView):
    template_name = '404.html'


class Page500(TemplateView):
    template_name = '500.html'


class StockDetail(View):

    comment_edited = comment_deleted = comment_edited_var = \
        comment_deleted_var = False
    api_error = yfinance_error = False
    context = {}
    bulls_num = bears_num = hold_num = bulls_bears_ratio = ""
    last_trade_price = daily_perf = last_trade_data = aggs = \
        stock_data = ""
    last_trade_timestamp = last_trade_datetime = \
        last_trade_datetime_converted = ""
    previous_day = ""
    currency = sector = market_cap = market_cap_formatted = ""
    high_52w = low_52w = avg_vol = ""
    revenue = income = dividend_rate = dividend_yield = ""
    payout_ratio = price_earnings = price_to_fcf = ""
    profit_margin = debt_to_equity = ""

    def get(self, request, slug):
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        comments = stockinfo.comments.filter(
            approved=True).order_by('-created_on')

        self.sentiment_analysis(stockinfo)
        self.get_polygon_last_trade(stockinfo.ticker)
        self.get_yfinance_figures(stockinfo.ticker)

        # If data from Polygon API is received, run get_chart_data to
        # retrieve YTD stock and price data in context
        # otherwhise set the context to None
        if not self.api_error:
            self.get_chart_data(stockinfo.ticker, "day",
                                "2021-12-31", self.previous_day)
        else:
            self.context = None

        if self.comment_edited:
            self.comment_edited_var = True
            StockDetail.comment_edited = False
        else:
            self.comment_edited_var = False

        if self.comment_deleted:
            self.comment_deleted_var = True
            StockDetail.comment_deleted = False
        else:
            self.comment_deleted_var = False

        self.set_error_variables()

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
                "api_error": self.api_error,
                "yfinance_error": self.yfinance_error,
            },
        )

    def sentiment_analysis(self, stockinfo):
        '''
        Function that counts the number of bull and bear sentiment
        expressed by the users and calculates a bull to bear ratio
        '''
        self.bulls_num = len(stockinfo.comments.filter(
            sentiment='BULL', approved=True).order_by('-created_on'))
        self.bears_num = len(stockinfo.comments.filter(
            sentiment='BEAR', approved=True).order_by('-created_on'))
        self.hold_num = len(stockinfo.comments.filter(
            sentiment='HOLD', approved=True).order_by('-created_on'))
        if self.bulls_num == 0 or self.bears_num == 0:
            self.bulls_bears_ratio = "N/A"
        else:
            self.bulls_bears_ratio = self.bulls_num/self.bears_num

    def get_polygon_last_trade(self, ticker):
        '''
        Function that takes ticker, retrieves stock trade data from
        polygon API, in order to get the last trade price, the linked
        timestamp and the daily performance relative to previous close
        '''

        # Get last trade price with datetime
        self.get_last_trade_data(ticker)
        # If trade data from Polygon API is received, return last
        # trade price, datetime and daily perf
        # Otherwise set them to None
        if not self.api_error:
            self.last_trade_price = self.last_trade_data.price
            self.last_trade_timestamp = \
                self.last_trade_data.participant_timestamp
            self.last_trade_datetime = datetime.fromtimestamp(
                self.last_trade_timestamp/1e9)

            # Get previous day close price
            nyse = mcal.get_calendar('NYSE')
            market_open_days = nyse.valid_days(
                start_date='2010-12-31', end_date='2030-12-31')

            market_open = False
            while market_open is False:
                for i in range(10):
                    self.previous_day = self.last_trade_datetime - \
                        timedelta(i+1)
                    if self.previous_day.strftime('%Y-%m-%d') in\
                            market_open_days:
                        market_open = True
                        break

            self.previous_day = self.previous_day.strftime("%Y-%m-%d")
            self.get_daily_aggs(
                ticker, "day", self.previous_day, self.previous_day)
            # if aggregates data from Polygon API is received, return last
            # close and calculate performance, otherwise return API error
            last_close = self.aggs[0].close
            self.daily_perf = Percent(self.last_trade_price / last_close - 1)

    def get_yfinance_figures(self, ticker):
        '''
        Function that takes ticker, retrieves stock data from yfinance library,
        and populates a list of variables used for Overview,
        Financials and Fundamental data
        '''
        # Get stock info from YFinance

        self.get_stock_info(ticker)

        if not self.yfinance_error:

            # Overview
            # Currency
            self.currency = self.yfinance_data_handler(
                "summaryDetail", "currency")
            # Sector
            self.sector = self.yfinance_data_handler(
                "summaryProfile", "sector")
            # Market Cap
            self.market_cap = self.yfinance_data_handler("price", "marketCap")
            try:
                self.market_cap_formatted = millify(self.market_cap)
            except (ValueError, TypeError):
                self.market_cap_formatted = "-"
            # High-Low 52 Weeks
            self.high_52w = self.yfinance_data_handler(
                "summaryDetail", "fiftyTwoWeekHigh")
            self.low_52w = self.yfinance_data_handler(
                "summaryDetail", "fiftyTwoWeekLow")
            # Average Volume
            self.avg_vol = self.yfinance_data_handler(
                "summaryDetail", "averageVolume")
            try:
                self.avg_vol = '{:,}'.format(self.avg_vol)
            except (ValueError, TypeError):
                pass

            # Financials
            # Revenue
            self.revenue = self.yfinance_data_handler(
                "financialData", "totalRevenue")
            try:
                self.revenue = millify(self.revenue)
            except (ValueError, TypeError):
                pass
            # Income
            self.income = self.yfinance_data_handler(
                "defaultKeyStatistics", "netIncomeToCommon")
            try:
                self.income = millify(self.income)
            except (ValueError, TypeError):
                pass
            # Dividend Yield and Dividend Rate
            self.dividend_rate = self.yfinance_data_handler(
                "summaryDetail", "dividendRate")
            self.dividend_yield = self.yfinance_data_handler(
                "summaryDetail", "dividendYield")
            if self.dividend_rate is None:
                self.dividend_rate = "-"
            if self.dividend_yield is None:
                self.dividend_yield = "-"
            try:
                self.dividend_rate = round(self.dividend_rate, 2)
            except (ValueError, TypeError):
                pass
            try:
                self.dividend_yield = Percent(self.dividend_yield)
            except (ValueError, TypeError):
                pass
            # Payout Ratio
            self.payout_ratio = self.yfinance_data_handler(
                "summaryDetail", "payoutRatio")
            try:
                self.payout_ratio = Percent(self.payout_ratio)
            except (ValueError, TypeError):
                pass

            # Multiples
            # Price/Earnings
            self.price_earnings = self.yfinance_data_handler(
                "summaryDetail", "trailingPE")
            if isinstance(self.price_earnings, float) or \
                    isinstance(self.price_earnings, int):
                self.price_earnings = round(self.price_earnings, 2)
            # Price/FCF
            free_cash_flow = self.yfinance_data_handler(
                "financialData", "freeCashflow")
            if (isinstance(free_cash_flow, int) or
                    isinstance(free_cash_flow, float)) and free_cash_flow > 0:
                if isinstance(self.market_cap, int) or \
                        isinstance(self.market_cap, float):
                    self.price_to_fcf = round(
                        self.market_cap / free_cash_flow, 2)
                else:
                    self.price_to_fcf = "-"
            else:
                self.price_to_fcf = "-"
            # Profit Margin
            self.profit_margin = self.yfinance_data_handler(
                "defaultKeyStatistics", "profitMargins")
            if isinstance(self.profit_margin, float) or \
                    isinstance(self.profit_margin, int):
                self.profit_margin = Percent(self.profit_margin)
            # Debt to Equity
            self.debt_to_equity = self.yfinance_data_handler(
                "financialData", "debtToEquity")
            if isinstance(self.debt_to_equity, float) or \
                    isinstance(self.debt_to_equity, int):
                self.debt_to_equity = round(self.debt_to_equity/100, 2)

    def yfinance_data_handler(self, key1, key2):
        '''
        To override yfinance objects so UX handles error condition gracefully
        '''
        try:
            return self.stock_data[key1][key2]
        except (KeyError, TypeError):
            return "-"

    def get_chart_data(self, ticker, interval, start_date, end_date):
        '''
        Function that get ticker, data interval, start date and end date,
        retrieves stock data from Polygon API, creates a list of
        timestamps and prices, and converts the list to JSON array in order
        to be rendered in the chart.js
        '''
        self.get_daily_aggs(ticker, interval, start_date, end_date)
        trades = self.aggs

        for x in range(0, len(trades)):
            date_unix_msec = trades[x].timestamp
            date_converted = datetime.fromtimestamp(
                date_unix_msec // 1000).date()
            trades[x].timestamp = str(date_converted)

        df = pd.DataFrame(trades)
        dates = df["timestamp"].tolist()
        self.last_trade_datetime_converted = str(
            self.last_trade_datetime.date())
        dates.append(self.last_trade_datetime_converted)
        prices = df["close"].tolist()
        prices.append(self.last_trade_price)
        self.context = {"dates": mark_safe(json.dumps(
            dates)), "prices": mark_safe(json.dumps(prices))}

    def get_last_trade_data(self, ticker):
        '''
        Function that connects with Polygon API to retrieve
        last trade data.
        If error occurs, returns none variable.
        '''
        try:
            client = RESTClient(API_KEY)
            self.last_trade_data = client.get_last_trade(
                ticker, params=None, raw=False)
        except (ConnectionError, Timeout, TooManyRedirects, RequestException,
                HTTPError, exceptions.BadResponse):
            self.api_error = True

    def get_daily_aggs(self, ticker, timespan, start_date, end_date):
        '''
        Function that connects with Polygon API to retrieve
        data aggregates from start_date to end_date.
        If error occurs, returns none variable.
        '''
        try:
            client = RESTClient(API_KEY)
            self.aggs = client.get_aggs(
                ticker, 1, timespan, start_date, end_date)
        except (ConnectionError, Timeout, TooManyRedirects, RequestException,
                HTTPError, exceptions.BadResponse):
            self.api_error = True

    def get_stock_info(self, ticker):
        self.stock_data = yf.Ticker(ticker).stats()

        if len(self.stock_data) == 0:
            self.yfinance_error = True

    def set_error_variables(self):
        # if there is a Polygon API error, set trade data and perf
        # to None
        if self.api_error:
            self.last_trade_price = None
            self.last_trade_datetime = None
            self.daily_perf = None

        # if there is a yfinance error, set all the related
        # variables to None
        if self.yfinance_error:
            self.price_earnings = None
            self.price_to_fcf = None
            self.profit_margin = None
            self.debt_to_equity = None
            self.sector = None
            self.market_cap_formatted = None
            self.high_52w = None
            self.low_52w = None
            self.avg_vol = None
            self.revenue = None
            self.income = None
            self.dividend_rate = None
            self.dividend_yield = None
            self.payout_ratio = None
            self.currency = None

    def post(self, request, slug):
        """
        Post method to post the comment.
        """
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        comments = stockinfo.comments.filter(
            approved=True).order_by('-created_on')

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

        self.api_error = False
        self.yfinance_error = False

        self.sentiment_analysis(stockinfo)
        self.get_polygon_last_trade(stockinfo.ticker)
        self.get_yfinance_figures(stockinfo.ticker)

        # If data from Polygon API is received, run get_chart_data to retrieve
        # YTD stock and price data in context otherwhise set the context
        # to None
        if not self.api_error:
            self.get_chart_data(stockinfo.ticker, "day",
                                "2021-12-31", self.previous_day)
        else:
            self.context = None

        self.set_error_variables()

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
                "api_error": self.api_error,
                "yfinance_error": self.yfinance_error,
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

    def delete(self, request, *args, **kwargs):
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


# adapted version of code form Janus on StackOverflow
# https://stackoverflow.com/questions/3154460/python-human-readable-large-numbers
def millify(n):
    n = float(n)
    millidx = max(0, min(len(MILLNAMES)-1,
                         int(math.floor(0 if n == 0 else
                             math.log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), MILLNAMES[millidx])
