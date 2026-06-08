import asyncio
import json
import logging
import time
from typing import Any, Dict

from litellm import completion

from config import settings
from database import SessionLocal
from tools.codebase import search_labcore_code
from tools.iris_db import (
    check_exam_exists,
    check_patient_exists,
    get_covenant_id,
    get_exam_can_perform,
    get_service_request_status,
)
from tools.knowledge_base import search_knowledge_base

logger = logging.getLogger(__name__)


def run_error_checker(state: Dict[str, Any]) -> Dict[str, Any]:
    operation = state.get("operation", "")
    system_target = state.get("system_target", "")
    payload_sent = state.get("payload_sent", {})
    error_raw = state.get("error_raw", {})

    http_code = error_raw.get("http_code", 0)
    error_body = error_raw.get("body", {})

    error_fields = []
    if isinstance(payload_sent, dict):
        error_fields = list(payload_sent.keys())
    query_parts = [operation, system_target] + error_fields
    query = " ".join(str(p) for p in query_parts if p)

    logger.info("error_checker query: %s", query)
    logger.info("✗ payload sent:\n%s", json.dumps(payload_sent, indent=2))
    logger.info("✗ error received: HTTP %s\n%s", http_code, json.dumps(error_body, indent=2))

    code_chunks = search_labcore_code(query, top_k=8)

    doc_chunks = []
    db = SessionLocal()
    try:
        doc_chunks = search_knowledge_base(db, system_target, query, top_k=8)
    finally:
        db.close()

    state["_debug_code_chunks"] = code_chunks
    state["_debug_doc_chunks"] = doc_chunks

    if isinstance(payload_sent, dict):
        patient_id = payload_sent.get("patient_id")
        exam_code = payload_sent.get("exam_code")
        service_request_id = payload_sent.get("service_request_id")
    else:
        patient_id = exam_code = service_request_id = None

    db_findings = _collect_db_findings(patient_id, exam_code, service_request_id)
    print(db_findings)
    state["_db_findings"] = db_findings

    prompt = _build_prompt(operation, system_target, payload_sent, http_code, error_body, code_chunks, doc_chunks)
    result = _call_llm(prompt)
    diag = _parse_llm_response(result)

    sources = []
    if code_chunks:
        sources.append("codebase")
    if doc_chunks:
        sources.append("knowledge_base")
    diag["sources_used"] = sources

    confidence = diag.get("confidence", 0)
    if confidence < 0.70:
        diag["origin"] = "AMBIGUOUS"

    state["error_diagnosis"] = diag

    return state


def _collect_db_findings(patient_id, exam_code, service_request_id):
    async def _gather():
        return await asyncio.gather(
            check_patient_exists(patient_id),
            check_exam_exists(exam_code),
            get_exam_can_perform(exam_code),
            get_service_request_status(service_request_id),
            get_covenant_id(service_request_id),
            return_exceptions=True,
        )

    try:
        results = asyncio.run(_gather())
        return {
            "patient_exists": None if isinstance(results[0], BaseException) else results[0],
            "exam_exists": None if isinstance(results[1], BaseException) else results[1],
            "exam_can_perform": None if isinstance(results[2], BaseException) else results[2],
            "service_request_status": None if isinstance(results[3], BaseException) else results[3],
            "covenant_id": None if isinstance(results[4], BaseException) else results[4],
        }
    except Exception:
        return {
            "patient_exists": None,
            "exam_exists": None,
            "exam_can_perform": None,
            "service_request_status": None,
            "covenant_id": None,
        }


def _build_prompt(operation: str, system_target: str, payload_sent: Dict[str, Any],
                  http_code: int, error_body: Dict[str, Any],
                  code_chunks: list[str], doc_chunks: list[str]) -> str:
    code_text = "\n\n---\n\n".join(code_chunks) if code_chunks else "(no LabCore source code available)"
    doc_text = "\n\n---\n\n".join(doc_chunks) if doc_chunks else "(no integration documentation available)"

    return f"""You are a healthcare integration error analyst.

FAILED OPERATION: {operation}
TARGET SYSTEM: {system_target}

PAYLOAD THAT WAS SENT:
{json.dumps(payload_sent, indent=2)}

ERROR RECEIVED:
HTTP {http_code}
{json.dumps(error_body, indent=2)}

LABCORE SOURCE CODE (how the payload is built):
{code_text}

INTEGRATION DOCUMENTATION (what the target system expects):
{doc_text}

TASK:
Analyze the error using the following priority order:

1. ERROR MESSAGE FIRST — read the error response carefully.
   If the external system explicitly says "unknown", "not found", "invalid",
   "unrecognized", or "rejected" for a specific value (code, id, field),
   that is a direct signal. Do not ignore it.

2. PAYLOAD vs DOCUMENTATION — check if the payload structure matches
   what the integration documentation requires. Format mismatches are ORIGIN_A.

3. CODEBASE — use source code only to confirm or investigate, never to
   override a clear signal from steps 1 or 2. The codebase may be stale.

4. DATABASE LIMITATION — you do not have access to LabCore's database.
   This means you cannot verify whether a code, id, or value was registered
   correctly in LabCore. When the error is about an unknown or unrecognized
   value and the root cause could be:
     - a typo at data entry in LabCore (ORIGIN_A)
     - the external system not having that value in its catalog (ORIGIN_B)
     - a wrong mapping between systems (CONTRATO)
   ...and you cannot distinguish between them without database access,
   set confidence below 0.70 and origin to AMBIGUOUS.
   In suggestion, explicitly state: "check LabCore catalog for this value".

Return ONLY valid JSON with no markdown, no backticks, no preamble:
{{
  "origin": "ORIGIN_A | ORIGIN_B | CONTRATO | INFRA | AMBIGUOUS",
  "confidence": 0.0-1.0,
  "evidence": "specific explanation with file/field references if available",
  "suggestion": "what should be fixed"
}}

Origin meanings:
- ORIGIN_A: bug or mapping issue in LabCore code, or wrong data registered in LabCore
- ORIGIN_B: problem on the external system side — it rejected a value that should be valid
- CONTRATO: business rule or contract violation between systems
- INFRA: timeout, network failure, system down
- AMBIGUOUS: not enough evidence to conclude — use when database access would be
  required to determine the true root cause"""


def _call_llm(prompt: str) -> str:
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
        logger.info("✓ error diagnosis in %.1fs | tokens=%d", elapsed, total_tokens)
        logger.info("diagnosis:\n%s", text[:1000])
        return text
    except Exception as e:
        elapsed = time.time() - start
        logger.error("LLM call failed time_taken=%.2fs error=%s", elapsed, e)
        return json.dumps({"origin": "AMBIGUOUS", "confidence": 0.0, "evidence": f"LLM call failed: {e}", "suggestion": "retry or escalate to human"})


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

    return {"origin": "AMBIGUOUS", "confidence": 0.0, "evidence": text[:500], "suggestion": "manual review required"}
