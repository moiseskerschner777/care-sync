import asyncio, httpx
from app import config

def embed(texts: list[str]) -> list[list[float]]:
    if config.EMBED_PROVIDER == "ollama":
        return _ollama_embed(texts)
    elif config.EMBED_PROVIDER == "openai":
        return _openai_embed(texts)
    else:
        raise ValueError(f"Unknown EMBED_PROVIDER: {config.EMBED_PROVIDER!r}. Use 'ollama' or 'openai'.")

# ── Ollama ────────────────────────────────────────────────────────────────────

async def _embed_batch(client: httpx.AsyncClient, texts: list[str]) -> list[list[float]]:
    resp = await client.post(
        f"{config.OLLAMA_URL}/api/embed",
        json={"model": config.EMBED_MODEL, "input": texts, "options": {"num_ctx": config.OLLAMA_NUM_CTX}},
        timeout=httpx.Timeout(connect=5.0, read=180.0, write=10.0, pool=5.0),
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]

def _ollama_embed(texts: list[str]) -> list[list[float]]:
    batches = [texts[i:i+config.EMBED_BATCH_SIZE] for i in range(0, len(texts), config.EMBED_BATCH_SIZE)]

    async def run():
        async with httpx.AsyncClient() as client:
            sem = asyncio.Semaphore(config.EMBED_PARALLELISM)
            async def limited(batch):
                async with sem:
                    return await _embed_batch(client, batch)
            results = await asyncio.gather(*[limited(b) for b in batches])
        return [vec for batch_vecs in results for vec in batch_vecs]

    return asyncio.run(run())

# ── OpenAI (placeholder) ─────────────────────────────────────────────────────

def _openai_embed(texts: list[str]) -> list[list[float]]:
    # NOT IMPLEMENTED — placeholder for future work
    # Switch by setting EMBED_PROVIDER=openai + OPENAI_API_KEY=sk-...
    # Remember to also set EMBED_DIM to match the chosen model:
    #   text-embedding-3-small → 1536
    #   text-embedding-3-large → 3072
    raise NotImplementedError("OpenAI provider not yet implemented")
