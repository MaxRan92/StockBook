from . import views
from django.urls import path

urlpatterns = [
    path('', views.StockList.as_view(), name='home'),
    path('<slug:slug>/', views.StockDetail.as_view(), name='stock_detail'),
    path('<pk>/update_comment/', views.update_comment, name='update_comment'),
    path('delete/<id>/', views.delete_comment, name='delete_comment'),
]