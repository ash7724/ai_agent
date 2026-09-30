# Local Stock Research AI Agent

A free/local stock research agent for Linux/Kubuntu.

It combines:
- Yahoo Finance data through `yfinance`
- Google News RSS (no API key required)
- optional NewsAPI
- technical indicators calculated locally
- Ollama + Qwen3 running locally
- a deterministic scoring layer
- a simple Streamlit dashboard
- a technical-strategy backtester

This is a research/education project. It is not a broker and it does not place trades.

## 1. Requirements

Recommended:
- Kubuntu/Linux
- Python 3.10+
- 8 GB RAM minimum for a small local model; 16 GB+ is more comfortable
- Optional NVIDIA/AMD GPU for faster inference

Streamlit currently supports Python 3.10-3.14.

## 2. Install

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl git

mkdir -p ~/stock-ai-agent
cd ~/stock-ai-agent

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Install Ollama using the official installer:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then start Ollama if your installation does not already run it:

```bash
ollama serve
```

In another terminal:

```bash
ollama pull qwen3:4b
```

If your machine has enough RAM, try:

```bash
ollama pull qwen3:8b
```

Set the model:

```bash
export OLLAMA_MODEL=qwen3:4b
```

## 3. Run

From the project directory:

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the local URL Streamlit prints, normally:
http://localhost:8501

## 4. First test

Try:
- RELIANCE.NS
- TCS.NS
- INFY.NS
- HDFCBANK.NS
- AAPL

The `.NS` suffix is used by Yahoo Finance for many NSE symbols.

## 5. What the agent does

1. Downloads historical OHLCV data.
2. Calculates SMA20, SMA50, SMA200, RSI14, volatility and drawdown.
3. Downloads recent news through Google News RSS.
4. Sends the structured data + news headlines to the local Ollama model.
5. Produces a structured research report.
6. Runs a simple non-ML technical backtest separately.

## 6. Important backtesting limitation

Do NOT assume the AI report is backtested merely because the technical strategy is.

A genuine historical news/LLM backtest requires historical news snapshots available at each historical date and strict timestamp handling. This starter project deliberately separates the deterministic technical backtest from the current-news AI analysis to avoid look-ahead bias.

## 7. Optional NewsAPI

NewsAPI currently has a free Developer plan for development/testing, with 100 requests/day and delayed articles. It is not a free production plan.

Create `.env`:

```text
NEWS_API_KEY=your_key_here
```

Then enable it in the UI.

## 8. Suggested next upgrades

- NSE/BSE-specific data provider
- SEC filings for US stocks
- company financial statements
- earnings calendar
- historical news database
- walk-forward testing
- portfolio simulation
- transaction costs/slippage
- paper trading
- scheduled daily reports
