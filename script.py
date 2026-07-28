import os
import sys
import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

SYMBOL = "^NSEI"
MIN_MOMENTUM_POINTS = 15
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


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


def build_email(momentum: dict, sender: str, receiver: str) -> EmailMessage:
    subject = "🚨 F&O AI ALERT: Nifty Momentum Detected"
    body = (
        f"Nifty 50 Live Price: ₹{momentum['current_price']:.2f}\n"
        f"Point Change: {momentum['point_change']:+.2f}\n"
        f"Signal: {momentum['ai_signal']}\n"
        f"Trend: {momentum['trend']}\n"
        f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.set_content(body)
    return msg


def send_email(sender: str, password: str, receiver: str, message: EmailMessage) -> None:
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(sender, password)
            smtp.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"Failed to send email: {exc}") from exc


def main() -> int:
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    receiver = os.getenv("RECEIVER_EMAIL")

    missing = [name for name, value in (
        ("SENDER_EMAIL", sender),
        ("SENDER_PASSWORD", password),
        ("RECEIVER_EMAIL", receiver),
    ) if not value]

    if missing:
        logging.error("Missing environment variables: %s", ", ".join(missing))
        return 1

    try:
        momentum = get_recent_momentum(SYMBOL)
    except Exception as exc:
        logging.error("Failed to calculate momentum: %s", exc)
        return 1

    if momentum["ai_signal"] == "HOLD":
        logging.info("No momentum alert triggered: %s", momentum)
        return 0

    email_msg = build_email(momentum, sender, receiver)
    try:
        send_email(sender, password, receiver, email_msg)
        logging.info("Email alert sent to %s", receiver)
    except Exception as exc:
        logging.error("Email sending failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
