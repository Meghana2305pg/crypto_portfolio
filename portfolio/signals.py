from django.db.models.signals import post_migrate
from django.dispatch import receiver
from portfolio.models import Asset

DEFAULT_ASSETS = [
    {"name": "Bitcoin", "symbol": "BTC", "coingecko_id": "bitcoin"},
    {"name": "Ethereum", "symbol": "ETH", "coingecko_id": "ethereum"},
    {"name": "Tether", "symbol": "USDT", "coingecko_id": "tether"},
    {"name": "Solana", "symbol": "SOL", "coingecko_id": "solana"},
    {"name": "BNB", "symbol": "BNB", "coingecko_id": "binancecoin"},
]

@receiver(post_migrate)
def create_default_assets(sender, **kwargs):
    if sender.name != "portfolio":
        return

    if Asset.objects.exists():
        return

    for asset in DEFAULT_ASSETS:
        Asset.objects.create(**asset)