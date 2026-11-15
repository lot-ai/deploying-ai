"""
Service 1: API Calls
- CoinGecko keyless simple price + 24h change (crypto)
- Frankfurter free FX rates
Responses are transformed into natural language summaries, never returned verbatim.
"""

import json
import requests
from typing import Optional
from utils.logger import get_logger

_logs = get_logger(__name__)


def get_crypto_price(ids: str = "bitcoin,ethereum", vs_currencies: str = "usd") -> str:
    """
    Fetch current prices and 24h percentage change for one or more cryptocurrencies
    from the CoinGecko keyless public API, then rephrase into a concise analyst note.
    ids: comma-separated CoinGecko ids (e.g. 'bitcoin,ethereum,solana')
    vs_currencies: target fiat (default 'usd')
    """
    _logs.info(f"Crypto price request: ids={ids}, vs={vs_currencies}")
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ids.lower().replace(" ", ""),
        "vs_currencies": vs_currencies.lower(),
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }
    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        _logs.error(f"CoinGecko error: {e}")
        return f"Unable to retrieve live crypto prices at this time ({type(e).__name__}). Please try again shortly."

    if not data:
        return "No price data returned for the requested assets."

    lines = []
    for coin_id, info in data.items():
        price = info.get(vs_currencies)
        change = info.get(f"{vs_currencies}_24h_change")
        mcap = info.get(f"{vs_currencies}_market_cap")
        name = coin_id.replace("-", " ").title()
        if price is None:
            continue
        change_str = f"{change:+.2f}%" if change is not None else "n/a"
        mcap_str = f", market cap approx. {mcap:,.0f} {vs_currencies.upper()}" if mcap else ""
        lines.append(
            f"{name} is trading near {price:,.4g} {vs_currencies.upper()} "
            f"(24-hour change {change_str}{mcap_str})."
        )

    if not lines:
        return "Could not parse usable price data from the response."

    summary = "Live crypto desk note — " + " ".join(lines)
    summary += " Figures are indicative only; always cross-check against primary venues."
    return summary


def get_fx_rate(base: str = "USD", symbols: Optional[str] = None) -> str:
    """
    Fetch latest reference exchange rates from the Frankfurter free API (no key required)
    and rewrite them as a short market comment.
    base: base currency (default USD)
    symbols: optional comma-separated quote currencies (e.g. 'EUR,GBP,JPY,HKD'). 
             If omitted, a standard set is returned.
    """
    _logs.info(f"FX rate request: base={base}, symbols={symbols}")
    url = "https://api.frankfurter.dev/v1/latest"
    params = {"base": base.upper()}
    if symbols:
        params["symbols"] = symbols.upper().replace(" ", "")

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        _logs.error(f"Frankfurter error: {e}")
        return f"Unable to retrieve FX reference rates ({type(e).__name__}). Try again later."

    rates = data.get("rates", {})
    date = data.get("date", "unknown date")
    if not rates:
        return "No exchange-rate data available for the requested pair(s)."

    # Prefer a focused set if many were returned
    preferred = ["EUR", "GBP", "JPY", "HKD", "CNY", "AUD", "CAD", "CHF"]
    ordered = [c for c in preferred if c in rates] or list(rates.keys())[:8]

    pieces = [f"1 {base.upper()} = {rates[c]:.4g} {c}" for c in ordered]
    body = "; ".join(pieces)
    summary = (
        f"FX reference rates as of {date} (central-bank blended sources via Frankfurter). "
        f"{body}. These are end-of-day style reference prints, not live tradable quotes."
    )
    return summary


def get_crypto_global() -> str:
    """
    Fetch high-level global crypto market statistics from CoinGecko and rephrase
    into a short desk summary.
    """
    _logs.info("Global crypto stats request")
    url = "https://api.coingecko.com/api/v3/global"
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except Exception as e:
        _logs.error(f"CoinGecko global error: {e}")
        return f"Global market snapshot unavailable ({type(e).__name__})."

    total_mcap = data.get("total_market_cap", {}).get("usd")
    total_vol = data.get("total_volume", {}).get("usd")
    btc_dom = data.get("market_cap_percentage", {}).get("btc")
    eth_dom = data.get("market_cap_percentage", {}).get("eth")
    change_24h = data.get("market_cap_change_percentage_24h_usd")

    parts = []
    if total_mcap:
        parts.append(f"total crypto market capitalisation stands near ${total_mcap/1e12:.2f} trillion")
    if change_24h is not None:
        parts.append(f"24-hour market-cap change {change_24h:+.2f}%")
    if total_vol:
        parts.append(f"24-hour volume approximately ${total_vol/1e9:.1f} billion")
    if btc_dom is not None:
        parts.append(f"Bitcoin dominance {btc_dom:.1f}%")
    if eth_dom is not None:
        parts.append(f"Ethereum dominance {eth_dom:.1f}%")

    if not parts:
        return "Global crypto metrics could not be parsed."

    return "Global crypto market snapshot: " + "; ".join(parts) + ". Data via CoinGecko public endpoint."
