""""
App configuration with Django
"""

from django.apps import AppConfig


class StockdataConfig(AppConfig):
    """
    Config stockdata app
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stockdata'
