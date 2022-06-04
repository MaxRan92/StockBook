import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from flask import url_for, render_template
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic, View
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.views.generic import DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import StockInfo, Comment
from .forms import CommentForm, EditForm
from polygon import RESTClient


API_KEY = "R7PbrIpBoMRsJuAHnAPrD07XGMgpJy89"


class StockList(generic.ListView):
    model = StockInfo
    queryset = StockInfo.objects.filter(status=1).order_by("-created_on")
    template_name = 'index.html'
    paginate_by = 6


class StockDetail(View):

    def get(self, request, slug, *args, **kwargs):
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        all_comments = Comment.objects.filter(approved=True)
        comments = stockinfo.comments.filter(approved=True).order_by('-created_on')
        
        #CAN WE REFACTOR THIS?
        bulls_num = len(stockinfo.comments.filter(sentiment='BULL', approved=True).order_by('-created_on'))
        bears_num = len(stockinfo.comments.filter(sentiment='BEAR', approved=True).order_by('-created_on'))
        if bulls_num == 0 or bears_num == 0:
            bulls_bears_ratio = "N/A"
        else:
            bulls_bears_ratio = bulls_num/bears_num
        
        # Get last trade price with datetime
        self.get_last_trade_data(stockinfo.ticker)
        last_trade_price = self.last_trade_data.price
        last_trade_timestamp = self.last_trade_data.participant_timestamp
        last_trade_datetime = datetime.fromtimestamp(last_trade_timestamp/1e9)

        # Get previous day close price
        nyse = mcal.get_calendar('NYSE')
        market_open_days = nyse.valid_days(start_date='2010-12-31', end_date='2030-12-31')

        market_open = False
        while market_open is False:
            for i in range(10):
                previous_day = last_trade_datetime - timedelta(i+1)
                if previous_day.strftime('%Y-%m-%d') in market_open_days:
                    market_open = True
                    break

        previous_day = previous_day.strftime("%Y-%m-%d")
        self.get_daily_aggs(stockinfo.ticker, previous_day, previous_day)
        last_close = self.aggs[0].close
        daily_perf = Percent(last_trade_price / last_close - 1)

        # Get stock info
        self.get_stock_info(stockinfo.ticker)
        price_earnings = round(self.stock_data['trailingPE'], 2)
        market_cap = self.stock_data['marketCap']
        free_cash_flow = self.stock_data['freeCashflow']
        if free_cash_flow is None or free_cash_flow <= 0:
            price_to_fcf = "-"
        else:
            price_to_fcf = round(market_cap / free_cash_flow,2)
        profit_margin = Percent(self.stock_data['profitMargins'])
        debt_to_equity = round(self.stock_data['debtToEquity']/100,2)

        return render(
            request,
            "stock_detail.html",
            {
                "stockinfo": stockinfo,
                "comments": comments,
                "commented": False,
                "comment_form": CommentForm,
                "bulls_num": bulls_num,
                "bears_num": bears_num,
                "bulls_bears_ratio": bulls_bears_ratio,
                "last_trade_price": last_trade_price,
                "last_trade_datetime": last_trade_datetime,
                "daily_perf": daily_perf,
                "price_earnings": price_earnings,
                "price_to_fcf": price_to_fcf,
                "profit_margin": profit_margin,
                "debt_to_equity": debt_to_equity,
            },
        )


    def get_last_trade_data(self, ticker):
        client = RESTClient(API_KEY)

        self.last_trade_data = client.get_last_trade(ticker, params=None, raw=False)
    

    def get_daily_aggs(self, ticker, start_date, end_date):
        client = RESTClient(API_KEY)

        self.aggs = client.get_aggs(ticker, 1, "day", start_date, end_date)

    def get_stock_info(self, ticker):
        self.stock_data = yf.Ticker(ticker).info
        
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
            comment.save()
        else:
            comment_form = CommentForm()

        return render(
            request,
            "stock_detail.html",
            {
                "stockinfo": stockinfo,
                "comments": comments,
                "commented": True,
                "comment_form": CommentForm,
            },
        )

def update_comment(UpdateView):
    model = Comment
    template_name = 'update_comment.html'
    success_url = reverse_lazy("")

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
        return reverse("stock_detail", kwargs={"slug": self.object.stock.slug})

class Percent(float):
    def __str__(self):
        return '{:.2%}'.format(self)


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
        messages.success(self.request, "Edit made!")
        super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        """
        Upon success returns user to the stock detail page.
        """
        return reverse("stock_detail", kwargs={"slug": self.object.stock.slug})

