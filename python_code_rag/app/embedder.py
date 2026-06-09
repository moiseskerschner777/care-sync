import asyncio, httpx, logging
from app import config

logger = logging.getLogger(__name__)

def embed(texts: list[str]) -> list[list[float]]:
    logger.info("embedding %d texts using provider=%r model=%r", len(texts), config.EMBED_PROVIDER, config.EMBED_MODEL)
    if config.EMBED_PROVIDER == "ollama":
        result = _ollama_embed(texts)
    elif config.EMBED_PROVIDER == "openai":
        result = _openai_embed(texts)
    else:
        raise ValueError(f"Unknown EMBED_PROVIDER: {config.EMBED_PROVIDER!r}. Use 'ollama' or 'openai'.")
    logger.info("embedding complete — %d vectors of dimension %d obtained", len(result), len(result[0]) if result else 0)
    return result

# ── Ollama ────────────────────────────────────────────────────────────────────

async def _embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    logger.debug("sending embed batch of %d texts to %s/api/embed", len(texts), config.OLLAMA_URL)
    resp = await client.post(
        f"{config.OLLAMA_URL}/api/embed",
        json={"model": config.EMBED_MODEL, "input": texts, "options": {"num_ctx": config.OLLAMA_NUM_CTX}},
        timeout=httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=10.0),
    )
    resp.raise_for_status()
    result = resp.json()["embeddings"]
    logger.debug("embed batch returned %d vectors", len(result))
    return result

def _ollama_embed(texts: list[str]) -> list[list[float]]:
    batches = [texts[i:i+config.EMBED_BATCH_SIZE] for i in range(0, len(texts), config.EMBED_BATCH_SIZE)]
    logger.info("ollama embedding %d batches (batch_size=%d, parallelism=%d, url=%s)",
                len(batches), config.EMBED_BATCH_SIZE, config.EMBED_PARALLELISM, config.OLLAMA_URL)

    async def run():
        async with httpx.AsyncClient() as client:
            sem = asyncio.Semaphore(config.EMBED_PARALLELISM)
            async def limited(batch):
                async with sem:
                    return await _embed_batch(client, batch)
            results = await asyncio.gather(*[limited(b) for b in batches])
        return [vec for batch_vecs in results for vec in batch_vecs]

    return asyncio.run(run())

# ── OpenAI ────────────────────────────────────────────────────────────────────

async def _openai_embed_batch(client: httpx.AsyncClient, texts: list[str], api_key: str, base_url: str, model: str) -> list[list[float]]:
    logger.debug("sending openai embed batch of %d texts to %s/embeddings", len(texts), base_url)
    resp = await client.post(
        f"{base_url}/embeddings",
        json={"model": model, "input": texts},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=10.0),
    )
    if resp.is_error:
        logger.error("OpenAI embeddings error: %s — %s", resp.status_code, resp.text)
    resp.raise_for_status()
    data = resp.json()
    result = [item["embedding"] for item in data["data"]]
    logger.debug("openai embed batch returned %d vectors", len(result))
    return result

def _openai_embed(texts: list[str]) -> list[list[float]]:
    api_key = config.EMBEDDING_API_KEY
    if not api_key:
        raise ValueError("EMBEDDING_API_KEY is required for OpenAI embeddings")
    base_url = config.EMBEDDING_API_BASE or "https://api.openai.com/v1"
    model = config.EMBED_MODEL

    batches = [texts[i:i+config.EMBED_BATCH_SIZE] for i in range(0, len(texts), config.EMBED_BATCH_SIZE)]
    logger.info("openai embedding %d batches (batch_size=%d, parallelism=%d, base_url=%s, model=%s)",
                len(batches), config.EMBED_BATCH_SIZE, config.EMBED_PARALLELISM, base_url, model)

    async def run():
        async with httpx.AsyncClient() as client:
            sem = asyncio.Semaphore(config.EMBED_PARALLELISM)
            async def limited(batch):
                async with sem:
                    return await _openai_embed_batch(client, batch, api_key, base_url, model)
            results = await asyncio.gather(*[limited(b) for b in batches])
        return [vec for batch_vecs in results for vec in batch_vecs]

    return asyncio.run(run())
