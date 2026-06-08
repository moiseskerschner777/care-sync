import json
import logging
import time
from typing import Any, Dict

from litellm import completion

from config import settings
from database import SessionLocal
from memory.knowledge_base_indexer import index_knowledge_base
from models.knowledge_base import KnowledgeBase
from tools.knowledge_base import _normalize_target, search_knowledge_base

logger = logging.getLogger(__name__)


def run_doc_reader(state: Dict[str, Any]) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        operation = state.get("operation", "")
        system_target = state.get("system_target", "")
        payload = state.get("payload", {})

        query = f"{operation} {system_target}"

        normalized_target = _normalize_target(system_target)
        all_docs = db.query(KnowledgeBase).all()
        count = sum(
            1 for d in all_docs
            if _normalize_target(d.system_target) == normalized_target
        )

        if count == 0:
            logger.info("→ indexing %s on first use", system_target)
            index_knowledge_base(db, system_target=system_target)

        chunks = search_knowledge_base(db, system_target, query, top_k=5)
        logger.info("→ %d chunks retrieved from knowledge base", len(chunks))

        docs_size = sum(len(c) for c in chunks)
        logger.info("→ LLM building payload | model=%s docs=%d chars", settings.llm_provider, docs_size)

        prompt = _build_prompt(operation, system_target, payload, chunks)
        built_payload = _call_llm(prompt)

        if isinstance(built_payload, dict):
            logger.info("built_payload:\n%s", json.dumps(built_payload, indent=2))
        state["built_payload"] = built_payload
    finally:
        db.close()

    return state


def _build_prompt(operation: str, system_target: str, payload: Dict[str, Any], chunks: list[str]) -> str:
    docs_text = "\n\n---\n\n".join(chunks) if chunks else "(no documentation available)"

    return f"""You are an AI integration agent. Your job is to build the correct HTTP request body
for a target system based on its integration documentation.

OPERATION: {operation}
TARGET SYSTEM: {system_target}
USER PAYLOAD: {json.dumps(payload, indent=2)}

INTEGRATION DOCUMENTATION:
{docs_text}

TASK:
Read the documentation above carefully. Build the exact JSON request body required to
perform the operation "{operation}" on the target system "{system_target}".

Use the values from USER PAYLOAD (exam_code, patient_id, practitioner_id, etc.)
to fill in the fields described in the documentation.

IMPORTANT RULES:
- For "reflab": ALWAYS use FHIR R4 format. Wrap in a Bundle. Use resourceType fields.
- For "vitacare": NEVER use FHIR. Never include resourceType. Never wrap in a Bundle.
- Return ONLY the JSON request body — no explanation, no markdown, no code fences.
- The output must be valid JSON that can be sent directly to the target system."""


def _call_llm(prompt: str) -> Dict[str, Any]:
    model = settings.llm_provider
    start = time.time()
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=settings.llm_api_key or None,
            api_base=settings.llm_api_base or None,
        )
        text = response["choices"][0]["message"]["content"]
        elapsed = time.time() - start
        total_tokens = response.get("usage", {}).get("total_tokens", 0)
        logger.info("✓ payload built in %.1fs | tokens=%d", elapsed, total_tokens)
        return _parse_llm_response(text)
    except Exception as e:
        elapsed = time.time() - start
        logger.error("LLM call failed time_taken=%.2fs error=%s", elapsed, e)
        return {"error": str(e)}


def _parse_llm_response(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        pass

    try:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        pass

    return {"raw_response": text}
