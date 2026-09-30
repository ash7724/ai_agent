from __future__ import annotations

import json
import requests

from config import OLLAMA_HOST, OLLAMA_MODEL


SYSTEM_PROMPT = """
You are a cautious stock research assistant.

You do NOT have guaranteed predictive ability.
You must not invent facts, prices, financial figures, or news.
Use only the structured market data and news supplied by the user/system.
Separate observed facts from interpretation.
Mention important uncertainty and risks.
Do not claim that a signal guarantees a future return.

Return JSON with these fields:
{
  "summary": "short plain-language summary",
  "news_sentiment": "positive|mixed|negative|unclear",
  "key_news": ["...", "..."],
  "catalysts": ["...", "..."],
  "risks": ["...", "..."],
  "technical_interpretation": "...",
  "research_signal": "bullish|neutral|bearish",
  "confidence": 0,
  "reasoning": ["...", "...", "..."]
}

The confidence must be an integer from 0 to 100 and should reflect uncertainty,
not probability of making money.
"""


def analyze_with_ollama(payload: dict) -> dict:
    prompt = (
        "Analyze this stock research packet. Do not use outside knowledge.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )

    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.1},
        },
        timeout=180,
    )
    r.raise_for_status()

    content = r.json()["message"]["content"]
    return json.loads(content)
