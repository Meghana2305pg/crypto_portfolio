from decimal import Decimal
from django.utils import timezone
from .models import Transaction, Asset, PortfolioSnapshot
import requests
from django.core.mail import send_mail
from django.conf import settings
from .models import PriceAlert
from datetime import datetime


def compute_fifo_for_user(user, currency):
    holdings = {}
    realized_pl = Decimal('0')

    qs = Transaction.objects.filter(user=user, currency=currency).select_related('asset').order_by('timestamp')

    fifo_queues = {}

    for tx in qs:
        asset_id = tx.asset_id
        if asset_id not in fifo_queues:
            fifo_queues[asset_id] = []

        if tx.tx_type == 'BUY':
            total_cost = (tx.quantity * tx.price_per_unit) + tx.fee
            cost_per_unit = total_cost / tx.quantity
            fifo_queues[asset_id].append([tx.quantity, cost_per_unit])

        elif tx.tx_type == 'SELL':
            qty_to_sell = tx.quantity
            sell_revenue = (tx.quantity * tx.price_per_unit) - tx.fee
            cost_basis_total = Decimal('0')

            queue = fifo_queues[asset_id]
            while qty_to_sell > 0 and queue:
                lot_qty, lot_cost = queue[0]
                if lot_qty <= qty_to_sell:
                    cost_basis_total += lot_qty * lot_cost
                    qty_to_sell -= lot_qty
                    queue.pop(0)
                else:
                    cost_basis_total += qty_to_sell * lot_cost
                    queue[0][0] = lot_qty - qty_to_sell
                    qty_to_sell = Decimal('0')

            pl = sell_revenue - cost_basis_total
            realized_pl += pl

    for asset_id, queue in fifo_queues.items():
        total_qty = sum(q[0] for q in queue)
        if total_qty > 0:
            total_cost = sum(q[0] * q[1] for q in queue)
            holdings[asset_id] = {
                'asset': Asset.objects.get(id=asset_id),
                'quantity': total_qty,
                'total_cost': total_cost,
                'avg_cost': total_cost / total_qty,
            }

    return holdings, realized_pl


def save_daily_snapshot(user, total_value):
    today = timezone.now().date()

    PortfolioSnapshot.objects.update_or_create(
        user=user,
        date=today,
        defaults={'total_value': total_value}
    )

def get_simple_price(asset_ids, vs_currencies):
    """
    Fetches live prices from CoinGecko for a list of asset IDs.
    Example:
        asset_ids = ['bitcoin', 'ethereum']
        vs_currencies = ['inr']
    Returns:
        {
            'bitcoin': {'inr': 1234567},
            'ethereum': {'inr': 98765}
        }
    """
    if not asset_ids:
        return {}

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(asset_ids),
        "vs_currencies": ",".join(vs_currencies)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}  # fail silently to avoid dashboard crash
    
def check_price_alerts(user, currency, prices):
    """
    Checks all alerts for the user and returns triggered ones.
    Does NOT send email unless you enable it.
    """
    alerts = PriceAlert.objects.filter(user=user)

    for alert in alerts:
        cg_id = alert.asset.coingecko_id
        current_price = prices.get(cg_id, {}).get(currency.lower(), None)

        if current_price is None:
            continue

        triggered = False

        # Above alert
        if alert.is_above and Decimal(str(current_price)) > alert.target_price:
            triggered = True

        # Below alert
        if not alert.is_above and Decimal(str(current_price)) < alert.target_price:
            triggered = True

        if triggered:
            alert.last_triggered = timezone.now()
            alert.save()

            # OPTIONAL: send email (enable if you want)
            # send_mail(
            #     subject=f"Price Alert Triggered for {alert.asset.symbol}",
            #     message=f"{alert.asset.symbol} has reached {current_price} {currency}",
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[user.email],
            #     fail_silently=True,
            # )
import requests

import requests
from datetime import datetime   # ✅ REQUIRED IMPORT

def get_chart_data_for_asset(asset, days=30, currency='inr'):
    cg_id = asset.coingecko_id
    print("Fetching chart for:", cg_id)

    url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
    params = {
        'vs_currency': currency.lower(),
        'days': days,
        'interval': 'daily' if days > 1 else 'hourly'   # ✅ better for 1-day range
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print("Status code:", response.status_code)
        print("Raw response:", response.text[:300])

        response.raise_for_status()
        data = response.json()

        prices = data.get('prices', [])
        print("Prices returned:", len(prices))

        labels = [
            datetime.utcfromtimestamp(p[0] / 1000).strftime('%Y-%m-%d')
            for p in prices
        ]
        values = [round(p[1], 2) for p in prices]

        print("Sample labels:", labels[:3])
        print("Sample values:", values[:3])
        print("API URL:", response.url)
        print("API URL:", response.url)
        print("Raw response:", response.text[:300])

        return {'labels': labels, 'values': values}

    except Exception as e:
        print("Chart fetch error:", e)
        return {'labels': [], 'values': []}