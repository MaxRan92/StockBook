from . import views
from django.urls import path

urlpatterns = [
    path('', views.StockList.as_view(), name='home'),
    path('<slug:slug>/', views.StockDetail.as_view(), name='stock_detail'),
    path('<pk>/update_comment/', views.update_comment, name='update_comment'),
    path('<slug:slug>/<int:pk>/delete_comment/', views.CommentDelete.as_view(), name="delete_comment"),
]