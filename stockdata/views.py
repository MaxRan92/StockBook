from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from .models import StockInfo
from .forms import CommentForm


class StockList(generic.ListView):
    model = StockInfo
    queryset = StockInfo.objects.filter(status=1).order_by("-created_on")
    template_name = 'index.html'
    paginate_by = 6


class StockDetail(View):

    def get(self, request, slug, *args, **kwargs):
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        comments = stockinfo.comments.filter(approved=True).order_by('-created_on')
        
        return render(
            request,
            "stock_detail.html",
            {
                "stockinfo": stockinfo,
                "comments": comments,
                "commented": False,
                "comment_form": CommentForm,
            },
        )

    def post(self, request, slug, *args, **kwargs):
        queryset = StockInfo.objects.filter(status=1)
        stockinfo = get_object_or_404(queryset, slug=slug)
        comments = stockinfo.comments.filter(approved=True).order_by('-created_on')
        
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            comment_form.instance.email = request.user.email
            comment_form.instance.name = request.user.username
            comment = comment_form.save(commit=False)
            comment.stockinfo = stockinfo
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