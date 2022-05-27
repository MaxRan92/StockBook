from . import views
from django.urls import path

urlpatterns = [
    path('', views.StockList.as_view(), name='home'),
]