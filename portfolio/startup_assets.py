from portfolio.models import Asset

DEFAULT_ASSETS = [
    {"name": "Bitcoin", "symbol": "BTC", "coingecko_id": "bitcoin"},
    {"name": "Ethereum", "symbol": "ETH", "coingecko_id": "ethereum"},
    {"name": "Tether", "symbol": "USDT", "coingecko_id": "tether"},
    {"name": "Solana", "symbol": "SOL", "coingecko_id": "solana"},
    {"name": "BNB", "symbol": "BNB", "coingecko_id": "binancecoin"},
    {"name": "XRP", "symbol": "XRP", "coingecko_id": "ripple"},
    {"name": "Cardano", "symbol": "ADA", "coingecko_id": "cardano"},
    {"name": "Dogecoin", "symbol": "DOGE", "coingecko_id": "dogecoin"},
    {"name": "Polkadot", "symbol": "DOT", "coingecko_id": "polkadot"},
    {"name": "Avalanche", "symbol": "AVAX", "coingecko_id": "avalanche-2"},
    {"name": "Chainlink", "symbol": "LINK", "coingecko_id": "chainlink"},
    {"name": "Tron", "symbol": "TRX", "coingecko_id": "tron"},
    {"name": "Litecoin", "symbol": "LTC", "coingecko_id": "litecoin"},
    {"name": "Stellar", "symbol": "XLM", "coingecko_id": "stellar"},
    {"name": "Uniswap", "symbol": "UNI", "coingecko_id": "uniswap"},
    {"name": "Cosmos", "symbol": "ATOM", "coingecko_id": "cosmos"},
    {"name": "Monero", "symbol": "XMR", "coingecko_id": "monero"},
    {"name": "NEAR", "symbol": "NEAR", "coingecko_id": "near"},
    {"name": "Aptos", "symbol": "APT", "coingecko_id": "aptos"},
    {"name": "VeChain", "symbol": "VET", "coingecko_id": "vechain"},
]

def create_default_assets():
    if Asset.objects.exists():
        return
    for asset in DEFAULT_ASSETS:
        Asset.objects.create(**asset)