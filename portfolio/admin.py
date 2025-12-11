from django.contrib import admin
from .models import Asset, Transaction, PriceAlert


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'coingecko_id')
    search_fields = ('name', 'symbol', 'coingecko_id')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'tx_type', 'quantity', 'price_per_unit', 'fee', 'currency', 'timestamp')
    list_filter = ('tx_type', 'currency', 'asset')
    search_fields = ('user__username', 'asset__name')


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'target_price', 'currency', 'is_above', 'active', 'created_at')
    list_filter = ('currency', 'is_above', 'active')
    search_fields = ('user__username', 'asset__name')