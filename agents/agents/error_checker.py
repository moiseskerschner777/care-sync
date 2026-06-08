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
    state["_db_findings"] = db_findings

    prompt = _build_prompt(operation, system_target, payload_sent, http_code, error_body, code_chunks, doc_chunks, db_findings)
    result = _call_llm(prompt)
    diag = _parse_llm_response(result)

    sources = []
    if code_chunks:
        sources.append("codebase")
    if doc_chunks:
        sources.append("knowledge_base")
    if db_findings and any(v is not None for v in db_findings.values()):
        sources.append("iris_db")
    diag["sources_used"] = sources

    confidence = diag.get("confidence", 0)
    if confidence < 0.70:
        diag["origin"] = "AMBIGUOUS"

    state["error_diagnosis"] = diag

    return state


def _collect_db_findings(patient_id, exam_code, service_request_id):
    async def _gather():
        coros = []
        coros.append(check_patient_exists(patient_id) if patient_id else _none())
        coros.append(check_exam_exists(exam_code) if exam_code else _none())
        coros.append(get_exam_can_perform(exam_code) if exam_code else _none())
        coros.append(get_service_request_status(service_request_id) if service_request_id else _none())
        coros.append(get_covenant_id(service_request_id) if service_request_id else _none())
        return await asyncio.gather(*coros, return_exceptions=True)

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


async def _none():
    return None


def _build_prompt(operation: str, system_target: str, payload_sent: Dict[str, Any],
                  http_code: int, error_body: Dict[str, Any],
                  code_chunks: list[str], doc_chunks: list[str],
                  db_findings: Dict[str, Any]) -> str:
    code_text = "\n\n---\n\n".join(code_chunks) if code_chunks else "(no LabCore source code available)"
    doc_text = "\n\n---\n\n".join(doc_chunks) if doc_chunks else "(no integration documentation available)"
    db_text = json.dumps(db_findings, indent=2) if db_findings else "(no database findings available)"

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

=== DATABASE FINDINGS ===
patient_exists: {db_findings.get("patient_exists")}
exam_exists: {db_findings.get("exam_exists")}
exam_can_perform: {db_findings.get("exam_can_perform")}
service_request_status: {db_findings.get("service_request_status")}
covenant_id: {db_findings.get("covenant_id")}

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

4. DATABASE FINDINGS — use the live LabCore database findings above to
   resolve questions that previously required AMBIGUOUS classification.
   - patient_exists = False → ORIGIN_A (non-existent patient sent)
   - exam_exists = False → ORIGIN_A (non-existent exam code sent)
   - exam_can_perform = True → exam should not have been routed externally (ORIGIN_A)
   - exam_can_perform = False → routing was correct (ORIGIN_B if RefLab rejected)
   - service_request_status = CANCELLED → ORIGIN_A (cancelled order sent)
   - covenant_id = None + VitaCare auth error → ORIGIN_A (null covenant sent)
   If a finding is None, the database check failed — do not treat None
   as a signal, but note it in evidence.

Return ONLY valid JSON with no markdown, no backticks, no preamble:
{{
  "origin": "ORIGIN_A | ORIGIN_B | CONTRACT | INFRA | AMBIGUOUS",
  "confidence": 0.0-1.0,
  "evidence": "specific explanation with file/field references if available.
               Base your reasoning strictly on: schema structure, field existence,
               routing logic, and system contract violations.
               Do NOT comment on whether a value appears synthetic, test-like,
               or invalid by naming convention — reason only from observable facts.",
  "suggestion": "what should be fixed"
}}

Origin meanings:
- ORIGIN_A: bug or mapping issue in LabCore code, or wrong data registered in LabCore
- ORIGIN_B: problem on the external system side — it rejected a value that should be valid
- CONTRACT: business rule or contract violation between systems
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
