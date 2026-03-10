import os
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Look for .env in project root (parent of scripts/)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv not installed, try manual parsing
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load API key from environment variable or .env file
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

if not UPSTAGE_API_KEY:
    # Import lang_config lazily to avoid circular imports
    try:
        from scripts.lang_config import L
        _msg = L.config.api_key_error
    except Exception:
        _msg = "❌ UPSTAGE_API_KEY not found!\nSet it in .env or via environment variable."
    raise ValueError(_msg)

UPSTAGE_BASE_URL = "https://api.upstage.ai/v1"

EMBEDDING_MODEL = "embedding-passage"
LLM_MODEL = "solar-mini"

TEXT_STRATEGY_MIN_SUMMARY_LENGTH = 50
TEXT_STRATEGY_MIN_FIRST_MSG_LENGTH = 20
TEXT_STRATEGY_TURNS_COUNT = 6

DEFAULT_K_RANGE = [8, 10, 12, 15, 20, 25]
DEFAULT_CACHE_DIR = "cache"
DEFAULT_OUTPUT_DIR = "results"
DEFAULT_OUTPUT_PREFIX = "output"

LLM_TEMPERATURE = 0.3
LLM_SAMPLES_PER_CLUSTER = 20
EMBEDDING_BATCH_SIZE = 100
