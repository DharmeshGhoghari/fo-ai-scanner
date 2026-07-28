import os
import sys
import logging
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

SYMBOLS = {
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
}

MIN_MOMENTUM_POINTS = 15


def get_recent_momentum(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    try:
        data = ticker.history(period="1d", interval="5m")
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch data for {symbol}: {exc}") from exc

    if data is None or len(data) < 2:
        raise ValueError(f"Not enough 5-minute data for {symbol}")

    latest = data.iloc[-1]
    previous = data.iloc[-2]
    current_price = float(latest["Close"])
    point_change = float(current_price - float(previous["Close"]))

    if point_change >= MIN_MOMENTUM_POINTS:
        ai_signal = "BUY CE"
        trend = "Bullish"
    elif point_change <= -MIN_MOMENTUM_POINTS:
        ai_signal = "BUY PE"
        trend = "Bearish"
    else:
        ai_signal = "HOLD"
        trend = "Neutral"

    return {
        "symbol": symbol,
        "current_price": current_price,
        "point_change": round(point_change, 2),
        "ai_signal": ai_signal,
        "trend": trend,
    }


def build_discord_message(momentum: dict) -> str:
    return (
        f"**{momentum['symbol']}**\n"
        f"Live Price: ₹{momentum['current_price']:.2f}\n"
        f"Point Change: {momentum['point_change']:+.2f}\n"
        f"AI Signal: {momentum['ai_signal']}\n"
        f"Trend: {momentum['trend']}\n"
        f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


def send_discord_alert(webhook_url: str, message: str) -> None:
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Discord webhook post failed: {exc}") from exc


def main() -> int:
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not webhook_url:
        logging.error("Missing DISCORD_WEBHOOK environment variable.")
        return 1

    for name, symbol in SYMBOLS.items():
        try:
            momentum = get_recent_momentum(symbol)
            message = build_discord_message(momentum)
            send_discord_alert(webhook_url, message)
            logging.info("Sent alert for %s: %s", name, momentum)
        except Exception as exc:
            logging.error("Skipping %s due to error: %s", name, exc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
