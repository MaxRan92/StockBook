from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

# Status of a new stock can be draft or publised
STATUS = ((0, "Draft"), (1, "Published"))

# Declare fixed sentiment choices
SENTIMENT_CHOICES = (
    ('BULL', 'Bullish'),
    ('HOLD', 'Hold'),
    ('BEAR', 'Bearish'),
)


class StockInfo(models.Model):
    '''
    Django model for the information stored
    for each stock
    '''

    title = models.CharField(max_length=200, unique=True)
    ticker = models.CharField(max_length=6, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="stockdata_stockinfo")
    updated_on = models.DateTimeField(auto_now=True)
    description = models.TextField()
    logo_image = CloudinaryField('image', default='placeholder')
    excerpt = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return str(self.title)


class Comment(models.Model):
    '''
    Django model for the information stored
    for each comment. Each comment is linked to one
    stock via one-to-many relationship. The on_delete
    CASCADE specification allows to delete all the comment
    of a stock when the latter is deleted.
    '''

    stock = models.ForeignKey(
        StockInfo, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    sentiment = models.CharField(
        max_length=9, choices=SENTIMENT_CHOICES, default="HOLD")

    class Meta:
        ordering = ["created_on"]

    def __str__(self):
        return f"Comment {self.body} by {self.name}"
