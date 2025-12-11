from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

CURRENCY_CHOICES = [
    ('INR', 'Indian Rupee'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
]

class Asset(models.Model):
    coingecko_id = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    tx_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=8)
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user} {self.tx_type} {self.quantity} {self.asset}"


class PriceAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    is_above = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        direction = "above" if self.is_above else "below"
        return f"{self.user} alert {direction} {self.target_price} {self.currency} for {self.asset}"


# ✅ FIXED: PortfolioSnapshot is now a top-level model
class PortfolioSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    total_value = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.total_value}"