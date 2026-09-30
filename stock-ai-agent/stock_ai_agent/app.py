from __future__ import annotations

import os
import streamlit as st
import plotly.graph_objects as go

from agent import run_analysis
from backtest import backtest_sma_rsi

st.set_page_config(page_title="Local Stock AI", layout="wide")

st.title("Local Stock Research AI")
st.caption("Market data + news + technical analysis + local Ollama model")

with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Ticker", "RELIANCE.NS").strip().upper()
    period = st.selectbox("History", ["1y", "2y", "5y", "10y"], index=1)
    use_newsapi = st.checkbox(
        "Also use NewsAPI",
        value=False,
        help="Requires NEWS_API_KEY in .env and is intended for development/testing."
    )
    run = st.button("Analyze", type="primary")

if run:
    with st.spinner("Downloading data, collecting news and running the local model..."):
        try:
            result = run_analysis(ticker, period, use_newsapi)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    metrics = result["metrics"]
    technical = result["technical"]
    ai = result["ai"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"{metrics['close']:.2f}")
    c2.metric("RSI14", f"{metrics['rsi14']:.1f}")
    c3.metric("Technical signal", technical["label"])
    c4.metric("AI signal", str(ai.get("research_signal", "unknown")).upper())

    st.subheader("Price history")

    h = result["indicators"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h.index, y=h["Close"], name="Close"))
    fig.add_trace(go.Scatter(x=h.index, y=h["SMA50"], name="SMA50"))
    fig.add_trace(go.Scatter(x=h.index, y=h["SMA200"], name="SMA200"))
    fig.update_layout(height=500, xaxis_title="", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Technical analysis")
        st.write("**Signal:**", technical["label"])
        for reason in technical["reasons"]:
            st.write("•", reason)

        st.write({
            "1 month": metrics["return_1m"],
            "6 months": metrics["return_6m"],
            "1 year": metrics["return_1y"],
            "volatility": metrics["volatility20"],
            "drawdown": metrics["drawdown"],
        })

    with right:
        st.subheader("AI research report")
        st.write(ai.get("summary", ""))
        st.write("**News sentiment:**", ai.get("news_sentiment", ""))
        st.write("**Confidence:**", ai.get("confidence", ""))
        st.write("**Technical interpretation:**", ai.get("technical_interpretation", ""))

        st.write("**Catalysts**")
        for x in ai.get("catalysts", []):
            st.write("•", x)

        st.write("**Risks**")
        for x in ai.get("risks", []):
            st.write("•", x)

        st.write("**Reasoning**")
        for x in ai.get("reasoning", []):
            st.write("•", x)

    st.subheader("Recent news")
    for item in result["news"]:
        title = item.get("title", "")
        source = item.get("source", "")
        url = item.get("url", "")
        if url:
            st.markdown(f"- [{title}]({url}) — {source}")
        else:
            st.write(f"- {title} — {source}")

    st.subheader("Backtest: transparent technical strategy")
    bt, stats = backtest_sma_rsi(result["history"])

    bfig = go.Figure()
    bfig.add_trace(go.Scatter(x=bt.index, y=bt["equity"], name="Strategy"))
    bfig.add_trace(go.Scatter(x=bt.index, y=bt["buy_hold_equity"], name="Buy & hold"))
    bfig.update_layout(height=400, yaxis_title="Portfolio value")
    st.plotly_chart(bfig, use_container_width=True)

    cols = st.columns(5)
    cols[0].metric("Strategy return", f"{stats['strategy_return']:.1%}")
    cols[1].metric("Buy & hold", f"{stats['buy_hold_return']:.1%}")
    cols[2].metric("CAGR", f"{stats['cagr']:.1%}")
    cols[3].metric("Sharpe", f"{stats['sharpe']:.2f}")
    cols[4].metric("Max drawdown", f"{stats['max_drawdown']:.1%}")

    st.info(
        "The backtest shown here is a deterministic technical strategy. "
        "It is not a historical backtest of the current LLM/news signal. "
        "Historical news must be stored with publication timestamps to test that without look-ahead bias."
    )

else:
    st.markdown(
        """
        ### What this app does

        **1. Market data** — downloads historical OHLCV data.

        **2. Technical layer** — calculates SMA20/50/200, RSI, volatility and drawdown.

        **3. News layer** — collects recent company-related news.

        **4. Local AI** — sends the structured packet to Ollama/Qwen3 running on your own computer.

        **5. Backtest** — tests a separate transparent technical strategy.

        Enter a ticker in the sidebar and click **Analyze**.
        """
    )
