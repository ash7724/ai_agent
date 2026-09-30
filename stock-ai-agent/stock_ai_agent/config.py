import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()

DEFAULT_PERIOD = "2y"
