from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timezone as dt_timezone
from .utils import get_chart_data_for_asset
import csv
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from django.core.mail import send_mail
from .models import PortfolioSnapshot
from .forms import RegisterForm, TransactionForm, CurrencySelectorForm, PriceAlertForm
from .models import Transaction, Asset, PriceAlert
from .utils import compute_fifo_for_user, save_daily_snapshot
from .coingecko import get_simple_price, get_market_chart
from .utils import compute_fifo_for_user, get_simple_price, save_daily_snapshot, check_price_alerts,get_chart_data_for_asset



def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'portfolio/register.html', {'form': form})


@login_required
def dashboard(request):
    # ✅ Currency selector
    if request.method == 'POST' and 'currency' in request.POST:
        curr_form = CurrencySelectorForm(request.POST)
        if curr_form.is_valid():
            currency = curr_form.cleaned_data['currency']
            request.session['currency'] = currency
    else:
        curr_form = CurrencySelectorForm()

    currency = request.session.get('currency', 'INR')

    # ✅ FIFO holdings
    holdings, realized_pl = compute_fifo_for_user(request.user, currency)

    # ✅ Fetch live prices
    if holdings:
        asset_ids = [h['asset'].coingecko_id for h in holdings.values()]
        prices = get_simple_price(asset_ids, [currency.lower()])
    else:
        prices = {}

    # ✅ Calculate totals and enrich holdings dict
    total_current_value = Decimal('0')
    for asset_id, h in holdings.items():
        cg_id = h['asset'].coingecko_id
        price = Decimal(str(prices.get(cg_id, {}).get(currency.lower(), 0)))
        current_value = h['quantity'] * price

        h['current_price'] = price
        h['current_value'] = current_value
        h['unrealized_pl'] = current_value - h['total_cost']

        total_current_value += current_value

    # ✅ Save snapshot ONLY if user has holdings
    if holdings:
        save_daily_snapshot(request.user, total_current_value)

    # ✅ Snapshot history (for line chart)
    snapshots = PortfolioSnapshot.objects.filter(user=request.user).order_by('date')
    history_labels = []
    history_values = []

    if snapshots.exists():
        history_labels = [s.date.strftime('%Y-%m-%d') for s in snapshots]
        history_values = [float(s.total_value) for s in snapshots]

    # ✅ Check alerts
    check_price_alerts(request.user, currency, prices)

    # ✅ Pie chart data (portfolio distribution)
    labels = [h['asset'].symbol for h in holdings.values()]
    values = [float(h['current_value']) for h in holdings.values()]

    # ✅ Triggered alerts
    alerts = PriceAlert.objects.filter(user=request.user)
    triggered_alerts = []

    for alert in alerts:
        cg_id = alert.asset.coingecko_id
        current_price = prices.get(cg_id, {}).get(currency.lower(), 0)

        if alert.is_above and current_price > alert.target_price:
            triggered_alerts.append(alert)

        if not alert.is_above and current_price < alert.target_price:
            triggered_alerts.append(alert)

    # ✅ Final context sent to dashboard.html
    context = {
        'holdings': holdings,            # used in holdings table
        'realized_pl': realized_pl,
        'total_current_value': total_current_value,
        'currency': currency,
        'currency_form': curr_form,

        # 🔹 Pie chart
        'labels': labels,
        'values': values,

        # 🔹 Alerts
        'triggered_alerts': triggered_alerts,

        # 🔹 Line chart
        'history_labels': history_labels,
        'history_values': history_values,
    }

    return render(request, 'portfolio/dashboard.html', context)
@login_required
def transactions_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.save()
            messages.success(request, 'Transaction saved.')
            return redirect('transactions')
    else:
        form = TransactionForm()

    # ✅ Fetch all transactions
    qs = Transaction.objects.filter(user=request.user).select_related('asset').order_by('-timestamp')

    # ✅ Apply pagination (10 per page)
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    # ✅ Compute total for each transaction (THIS WAS MISSING)
    for tx in transactions:
        if tx.quantity and tx.price_per_unit:
            tx.total = tx.quantity * tx.price_per_unit
        else:
            tx.total = None

    return render(request, 'portfolio/transactions.html', {
        'form': form,
        'transactions': transactions
    })


@login_required
def export_transactions_csv(request):
    txs = Transaction.objects.filter(user=request.user).select_related('asset').order_by('timestamp')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=""transactions.csv""'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Asset', 'Type', 'Quantity', 'Price per unit', 'Fee', 'Currency'])
    for tx in txs:
        writer.writerow([
            tx.timestamp.astimezone(timezone.get_current_timezone()).isoformat(),
            tx.asset.name,
            tx.tx_type,
            tx.quantity,
            tx.price_per_unit,
            tx.fee,
            tx.currency,
        ])
    return response


@login_required
def price_alerts_view(request):
    if request.method == 'POST':
        form = PriceAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            messages.success(request, 'Price alert saved.')
            return redirect('price_alerts')
    else:
        form = PriceAlertForm()

    alerts = PriceAlert.objects.filter(user=request.user).select_related('asset')
    return render(request, 'portfolio/price_alerts.html', {'form': form, 'alerts': alerts})


def check_price_alerts(user, currency, prices_dict):
    alerts = PriceAlert.objects.filter(user=user, currency=currency, active=True).select_related('asset')
    for alert in alerts:
        cg_id = alert.asset.coingecko_id
        current_price = prices_dict.get(cg_id, {}).get(currency.lower())
        if current_price is None:
            continue
        current_price = Decimal(str(current_price))
        triggered = False
        if alert.is_above and current_price >= alert.target_price:
            triggered = True
        if not alert.is_above and current_price <= alert.target_price:
            triggered = True

        if triggered:
            subject = f'Price alert: {alert.asset.name} reached {current_price} {currency}'
            message = (
                f'Hello {user.username},\n\n'
                f'Your alert for {alert.asset.name} was triggered.\n'
                f'Current price: {current_price} {currency}\n'
                f'Target price: {alert.target_price} {currency}\n'
            )
            send_mail(subject, message, None, [user.email or 'test@example.com'])
            alert.active = False
            alert.save()


@login_required
def asset_chart_view(request, asset_id):
    currency = request.session.get('currency', 'INR')
    days = request.GET.get('days', '30')
    if days not in ['30', '90', '365']:
        days = '30'

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return render(request, 'portfolio/asset_chart.html', {
            'error': f'Asset with ID {asset_id} not found.',
            'labels': [],
            'values': [],
        })

    if not asset.coingecko_id:
        return render(request, 'portfolio/asset_chart.html', {
            'asset': asset,
            'currency': currency,
            'days': days,
            'labels': [],
            'values': [],
            'error': 'Coingecko ID is missing for this asset.',
        })

    try:
        data = get_market_chart(asset.coingecko_id, currency, days)
        prices = data.get('prices', [])
        labels = [
            timezone.datetime.fromtimestamp(p[0] / 1000, tz=dt_timezone.utc)
            .astimezone(timezone.get_current_timezone())
            .strftime('%Y-%m-%d')
            for p in prices
        ]
        values = [p[1] for p in prices]
    except Exception as e:
        return render(request, 'portfolio/asset_chart.html', {
            'asset': asset,
            'currency': currency,
            'days': days,
            'labels': [],
            'values': [],
            'error': f'Chart generation failed: {str(e)}',
        })

    return render(request, 'portfolio/asset_chart.html', {
        'asset': asset,
        'currency': currency,
        'days': days,
        'labels': labels,
        'values': values,
    })
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'portfolio/profile.html')

@login_required
def create_price_alert(request):
    if request.method == 'POST':
        form = PriceAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            return redirect('dashboard')
    else:
        form = PriceAlertForm()

    return render(request, 'portfolio/create_price_alert.html', {'form': form})

def home(request):
    return render(request, 'home.html')
def transactions(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.save()
    else:
        form = TransactionForm()

    user_transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'portfolio/transactions.html', {
        'form': form,
        'transactions': user_transactions
    })
from .utils import get_chart_data_for_asset

@login_required
def asset_chart(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)

    # ✅ Accept the correct GET parameter from your template
    days = request.GET.get('days', '30')

    # ✅ Convert to int safely
    try:
        days_int = int(days)
    except:
        days_int = 30

    print("VIEW CALLED — fetching chart for", asset.symbol, "days:", days_int)

    # ✅ Call your function
    chart_data = get_chart_data_for_asset(asset, days=days_int)

    print("VIEW RECEIVED:", chart_data)
    print("Asset:", asset.name, "CoinGecko ID:", asset.coingecko_id)
    print("Days:", days)
    print("Chart data:", chart_data)

    context = {
        'asset': asset,
        'chart_data': chart_data,
        'days': days
    }
    

    return render(request, 'portfolio/asset_chart.html', context)