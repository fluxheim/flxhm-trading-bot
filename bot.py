"""
FLXHM Trading Bot — Moving Average Crossover Strategy
Runs daily via GitHub Actions. Trades on Alpaca's PAPER account only.

Strategy:
  - Short MA (20-day) crosses ABOVE Long MA (50-day) -> BUY
  - Short MA (20-day) crosses BELOW Long MA (50-day) -> SELL (close position)

Logs every run's state to data/history.json so the dashboard can read it.
"""

import os
import json
import datetime
from pathlib import Path

import requests
import pandas as pd

# ---------- Config ----------
TICKERS = ["AAPL", "TSLA", "SPY"]
SHORT_WINDOW = 20
LONG_WINDOW = 50
QTY = 1  # shares per trade, keep it simple to start

ALPACA_KEY = os.environ["ALPACA_API_KEY"]
ALPACA_SECRET = os.environ["ALPACA_SECRET_KEY"]
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET,
}

HISTORY_FILE = Path(__file__).parent / "data" / "history.json"


# ---------- Helpers ----------
def get_bars(symbol, limit=100):
    """Pull daily price bars for a symbol from Alpaca's data API."""
    url = f"{ALPACA_DATA_URL}/v2/stocks/{symbol}/bars"
    params = {
        "timeframe": "1Day",
        "limit": limit,
        "adjustment": "raw",
        "feed": "iex",
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    bars = resp.json()["bars"]
    df = pd.DataFrame(bars)
    df["t"] = pd.to_datetime(df["t"])
    df.rename(columns={"c": "close"}, inplace=True)
    return df


def get_position(symbol):
    """Check if we currently hold a position in this symbol."""
    url = f"{ALPACA_BASE_URL}/v2/positions/{symbol}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def place_order(symbol, side, qty):
    """Submit a simple market order to the paper account."""
    url = f"{ALPACA_BASE_URL}/v2/orders"
    order = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "day",
    }
    resp = requests.post(url, headers=HEADERS, json=order)
    resp.raise_for_status()
    return resp.json()


def get_account():
    url = f"{ALPACA_BASE_URL}/v2/account"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {"runs": []}


def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))


# ---------- Core strategy ----------
def evaluate_symbol(symbol):
    df = get_bars(symbol, limit=LONG_WINDOW + 10)
    df["short_ma"] = df["close"].rolling(SHORT_WINDOW).mean()
    df["long_ma"] = df["close"].rolling(LONG_WINDOW).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    signal = "hold"
    action_taken = None

    crossed_up = prev["short_ma"] <= prev["long_ma"] and latest["short_ma"] > latest["long_ma"]
    crossed_down = prev["short_ma"] >= prev["long_ma"] and latest["short_ma"] < latest["long_ma"]

    position = get_position(symbol)
    holding = position is not None

    if crossed_up and not holding:
        signal = "buy"
        order = place_order(symbol, "buy", QTY)
        action_taken = f"BUY {QTY} share(s) of {symbol}"
    elif crossed_down and holding:
        signal = "sell"
        order = place_order(symbol, "sell", QTY)
        action_taken = f"SELL {QTY} share(s) of {symbol}"

    return {
        "symbol": symbol,
        "date": latest["t"].isoformat(),
        "close": round(float(latest["close"]), 2),
        "short_ma": round(float(latest["short_ma"]), 2),
        "long_ma": round(float(latest["long_ma"]), 2),
        "signal": signal,
        "holding": holding,
        "action_taken": action_taken,
    }


def main():
    history = load_history()

    run_result = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "symbols": [],
    }

    for symbol in TICKERS:
        try:
            result = evaluate_symbol(symbol)
        except Exception as e:
            result = {"symbol": symbol, "error": str(e)}
        run_result["symbols"].append(result)

    account = get_account()
    run_result["portfolio_value"] = float(account["portfolio_value"])
    run_result["cash"] = float(account["cash"])

    history["runs"].append(run_result)
    # keep last 180 runs so the file doesn't grow forever
    history["runs"] = history["runs"][-180:]

    save_history(history)
    print(json.dumps(run_result, indent=2, default=str))


if __name__ == "__main__":
    main()
