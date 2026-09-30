from __future__ import annotations

from indicators import add_indicators, latest_metrics, deterministic_signal
from market_data import download_history, company_snapshot
from news import collect_news
from ollama_client import analyze_with_ollama


def run_analysis(
    ticker: str,
    period: str = "2y",
    use_newsapi: bool = False,
) -> dict:
    ticker = ticker.strip().upper()

    history = download_history(ticker, period)
    enriched = add_indicators(history)
    metrics = latest_metrics(history)
    technical = deterministic_signal(metrics)

    snapshot = company_snapshot(ticker)
    company_name = snapshot.get("longName")

    news = collect_news(ticker, company_name, use_newsapi=use_newsapi)

    packet = {
        "ticker": ticker,
        "company": company_name or ticker,
        "market_data": metrics,
        "technical_signal": technical,
        "company_snapshot": snapshot,
        "recent_news": news,
    }

    ai = analyze_with_ollama(packet)

    return {
        "ticker": ticker,
        "history": history,
        "indicators": enriched,
        "metrics": metrics,
        "technical": technical,
        "company": snapshot,
        "news": news,
        "ai": ai,
    }
