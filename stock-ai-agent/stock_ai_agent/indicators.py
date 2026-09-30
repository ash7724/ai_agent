from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    close = x["Close"]

    x["SMA20"] = close.rolling(20).mean()
    x["SMA50"] = close.rolling(50).mean()
    x["SMA200"] = close.rolling(200).mean()
    x["RSI14"] = rsi(close, 14)

    x["DailyReturn"] = close.pct_change()
    x["Volatility20"] = x["DailyReturn"].rolling(20).std() * np.sqrt(252)

    running_max = close.cummax()
    x["Drawdown"] = close / running_max - 1

    return x.dropna().copy()


def latest_metrics(df: pd.DataFrame) -> dict:
    x = add_indicators(df)
    r = x.iloc[-1]

    return {
        "date": str(x.index[-1].date()),
        "close": float(r["Close"]),
        "sma20": float(r["SMA20"]),
        "sma50": float(r["SMA50"]),
        "sma200": float(r["SMA200"]),
        "rsi14": float(r["RSI14"]),
        "volatility20": float(r["Volatility20"]),
        "drawdown": float(r["Drawdown"]),
        "return_1m": float(r["Close"] / x["Close"].iloc[-21] - 1) if len(x) > 21 else None,
        "return_6m": float(r["Close"] / x["Close"].iloc[-126] - 1) if len(x) > 126 else None,
        "return_1y": float(r["Close"] / x["Close"].iloc[-252] - 1) if len(x) > 252 else None,
    }


def deterministic_signal(metrics: dict) -> dict:
    """Transparent score. This is intentionally separate from the LLM."""
    score = 0
    reasons = []

    if metrics["close"] > metrics["sma50"]:
        score += 1
        reasons.append("Price is above SMA50")
    else:
        score -= 1
        reasons.append("Price is below SMA50")

    if metrics["sma50"] > metrics["sma200"]:
        score += 1
        reasons.append("SMA50 is above SMA200")
    else:
        score -= 1
        reasons.append("SMA50 is below SMA200")

    if metrics["rsi14"] < 30:
        score += 1
        reasons.append("RSI14 is below 30 (oversold condition)")
    elif metrics["rsi14"] > 70:
        score -= 1
        reasons.append("RSI14 is above 70 (overbought condition)")
    else:
        reasons.append("RSI14 is between 30 and 70")

    if score >= 2:
        label = "BULLISH"
    elif score <= -2:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    return {"score": score, "label": label, "reasons": reasons}
