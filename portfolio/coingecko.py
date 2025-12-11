import requests
from django.core.cache import cache

BASE_URL = 'https://api.coingecko.com/api/v3'

def get_simple_price(asset_ids, vs_currencies, cache_timeout=60):
    ids_str = ','.join(asset_ids)
    vs_str = ','.join(vs_currencies)
    cache_key = f'simple_price:{ids_str}:{vs_str}'
    data = cache.get(cache_key)
    if data is not None:
        return data

    url = f'{BASE_URL}/simple/price'
    params = {
        'ids': ids_str,
        'vs_currencies': vs_str,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    cache.set(cache_key, data, cache_timeout)
    return data


def get_market_chart(asset_id, vs_currency, days, cache_timeout=300):
    cache_key = f'market_chart:{asset_id}:{vs_currency}:{days}'
    data = cache.get(cache_key)
    if data is not None:
        return data

    url = f'{BASE_URL}/coins/{asset_id}/market_chart'
    params = {
        'vs_currency': vs_currency.lower(),
        'days': days,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    cache.set(cache_key, data, cache_timeout)
    return data
