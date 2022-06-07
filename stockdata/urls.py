from . import views
from django.urls import path

urlpatterns = [
    path('', views.StockList.as_view(), name='home'),
    path('about/', views.AboutTemplateView.as_view(), name='about'),
    path('<slug:slug>/', views.StockDetail.as_view(), name='stock_detail'),
    path('<slug:slug>/<int:pk>/delete_comment/', views.CommentDelete.as_view(), name="delete_comment"),
    path('<slug:slug>/<int:pk>/edit_comment/', views.CommentEdit.as_view(), name="edit_comment"),
]