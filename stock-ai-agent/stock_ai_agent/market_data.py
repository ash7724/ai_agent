from __future__ import annotations

import pandas as pd
import yfinance as yf


def download_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Download daily OHLCV data from Yahoo Finance via yfinance."""
    ticker = ticker.strip().upper()
    df = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if df.empty:
        raise ValueError(f"No market data returned for {ticker}")

    # yfinance can return a MultiIndex even for one ticker.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[required].dropna().copy()
    df.index = pd.to_datetime(df.index)
    return df


def company_snapshot(ticker: str) -> dict:
    """Best-effort fundamental/company metadata. Yahoo fields can be incomplete."""
    t = yf.Ticker(ticker)
    try:
        info = t.info
    except Exception:
        info = {}

    keys = [
        "longName", "sector", "industry", "marketCap", "trailingPE",
        "forwardPE", "priceToBook", "returnOnEquity", "profitMargins",
        "revenueGrowth", "earningsGrowth", "dividendYield",
    ]
    return {k: info.get(k) for k in keys if info.get(k) is not None}
