import os

IRIS_HOST         = os.getenv("IRIS_HOST",         "iris")
IRIS_PORT         = int(os.getenv("IRIS_PORT",     "1972"))
IRIS_NAMESPACE    = os.getenv("IRIS_NAMESPACE",    "USER")
IRIS_USERNAME     = os.getenv("IRIS_USERNAME",     "_SYSTEM")
IRIS_PASSWORD     = os.getenv("IRIS_PASSWORD",     "SYS")

EMBED_PROVIDER    = os.getenv("EMBED_PROVIDER",    "ollama")
EMBED_DIM         = int(os.getenv("EMBED_DIM",     "1024"))
SEARCH_TOP_K      = int(os.getenv("SEARCH_TOP_K",  "8"))
MIN_SCORE_THRESHOLD = float(os.getenv("MIN_SCORE_THRESHOLD", "0.01"))

OLLAMA_URL        = os.getenv("OLLAMA_URL",        "http://host.docker.internal:11434")
EMBED_MODEL       = os.getenv("EMBED_MODEL",       "snowflake-arctic-embed2")
EMBED_BATCH_SIZE  = int(os.getenv("EMBED_BATCH_SIZE",  "100"))
EMBED_PARALLELISM = int(os.getenv("EMBED_PARALLELISM", "16"))
OLLAMA_NUM_CTX    = int(os.getenv("OLLAMA_NUM_CTX",    "8192"))

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY",    "")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
