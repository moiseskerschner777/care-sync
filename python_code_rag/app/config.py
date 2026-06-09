import logging
import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

IRIS_HOST         = os.getenv("IRIS_HOST",         "iris")
IRIS_PORT         = int(os.getenv("IRIS_PORT",     "1972"))
IRIS_NAMESPACE    = os.getenv("IRIS_NAMESPACE",    "USER")
IRIS_USERNAME     = os.getenv("IRIS_USERNAME",     "_SYSTEM")
IRIS_PASSWORD     = os.getenv("IRIS_PASSWORD",     "SYS")

_emb_provider_raw = os.getenv("EMBEDDING_PROVIDER", "")
if _emb_provider_raw and "/" in _emb_provider_raw:
    _parts = _emb_provider_raw.split("/", 1)
    EMBED_PROVIDER = _parts[0]
    EMBED_MODEL    = _parts[1]
else:
    EMBED_PROVIDER = _emb_provider_raw or os.getenv("EMBED_PROVIDER", "ollama")
    EMBED_MODEL    = os.getenv("EMBED_MODEL", "snowflake-arctic-embed2")

EMBED_DIM         = int(os.getenv("EMBED_DIM",     "1024"))
SEARCH_TOP_K      = int(os.getenv("SEARCH_TOP_K",  "8"))
MIN_SCORE_THRESHOLD = float(os.getenv("MIN_SCORE_THRESHOLD", "0.01"))

OLLAMA_URL        = os.getenv("OLLAMA_URL",        "http://host.docker.internal:11434")
EMBED_BATCH_SIZE  = int(os.getenv("EMBED_BATCH_SIZE",  "100"))
EMBED_PARALLELISM = int(os.getenv("EMBED_PARALLELISM", "16"))
OLLAMA_NUM_CTX    = int(os.getenv("OLLAMA_NUM_CTX",    "8192"))

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE", "")
