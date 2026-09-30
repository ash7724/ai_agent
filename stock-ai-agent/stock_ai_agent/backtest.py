from __future__ import annotations

import numpy as np
import pandas as pd

from indicators import add_indicators


def backtest_sma_rsi(
    df: pd.DataFrame,
    initial_cash: float = 100_000,
    fee_bps: float = 10,
) -> tuple[pd.DataFrame, dict]:
    """
    Simple long/flat strategy:
      - enter when Close > SMA50 > SMA200 and RSI < 70
      - exit when Close < SMA50 or RSI > 75

    Signals are shifted by one trading day before returns are applied,
    avoiding same-bar look-ahead.
    """
    x = add_indicators(df)

    x["entry"] = (
        (x["Close"] > x["SMA50"])
        & (x["SMA50"] > x["SMA200"])
        & (x["RSI14"] < 70)
    )
    x["exit"] = (x["Close"] < x["SMA50"]) | (x["RSI14"] > 75)

    position = []
    in_position = False

    for _, row in x.iterrows():
        if not in_position and row["entry"]:
            in_position = True
        elif in_position and row["exit"]:
            in_position = False
        position.append(1 if in_position else 0)

    x["position"] = pd.Series(position, index=x.index).shift(1).fillna(0)
    x["asset_return"] = x["Close"].pct_change().fillna(0)

    turnover = x["position"].diff().abs().fillna(x["position"].abs())
    fee = fee_bps / 10_000

    x["strategy_return"] = x["position"] * x["asset_return"] - turnover * fee
    x["equity"] = initial_cash * (1 + x["strategy_return"]).cumprod()

    buy_hold = initial_cash * (1 + x["asset_return"]).cumprod()

    total_return = x["equity"].iloc[-1] / initial_cash - 1
    bh_return = buy_hold.iloc[-1] / initial_cash - 1

    years = max((x.index[-1] - x.index[0]).days / 365.25, 1 / 365.25)
    cagr = (x["equity"].iloc[-1] / initial_cash) ** (1 / years) - 1

    daily = x["strategy_return"]
    sharpe = np.sqrt(252) * daily.mean() / daily.std() if daily.std() else 0

    max_dd = (x["equity"] / x["equity"].cummax() - 1).min()

    stats = {
        "initial_cash": initial_cash,
        "final_equity": float(x["equity"].iloc[-1]),
        "strategy_return": float(total_return),
        "buy_hold_return": float(bh_return),
        "cagr": float(cagr),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "days": int((x.index[-1] - x.index[0]).days),
    }

    x["buy_hold_equity"] = buy_hold
    return x, stats
