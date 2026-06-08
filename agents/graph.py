import json
import logging
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agents.doc_reader import run_doc_reader
from agents.error_checker import run_error_checker
from database import SessionLocal
from memory.error_dedup import find_duplicate_diagnosis
from memory.mapping_cache import get_mapping, save_mapping, update_usage
from tools.fhir_writer import write_audit_event, write_task
from tools.http_client import send_request

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    operation: str
    system_target: str
    payload: Dict[str, Any]
    cached_mapping: Optional[Dict[str, Any]]
    built_payload: Optional[Dict[str, Any]]
    response: Optional[Dict[str, Any]]
    cache_hit: bool
    error: Optional[Dict[str, Any]]
    error_diagnosis: Optional[Dict[str, Any]]
    dedup_hit: bool


def check_cache(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        mapping = get_mapping(db, state["operation"], state["system_target"])
        if mapping is not None:
            state["cached_mapping"] = {
                "id": mapping.id,
                "operation": mapping.operation,
                "system_target": mapping.system_target,
                "payload_schema": mapping.payload_schema,
                "example_request": mapping.example_request,
                "example_response": mapping.example_response,
                "use_count": mapping.use_count,
            }
            state["cache_hit"] = True
        else:
            state["cached_mapping"] = None
            state["cache_hit"] = False
    finally:
        db.close()
    logger.info("▶ %s → %s | cache_hit=%s", state["operation"], state["system_target"], state["cache_hit"])
    return state


TARGET_PATHS = {
    "reflab": "/fhir/r4/ServiceRequest",
    "vitacare": "/authorizations",
}


def _inject_request_values(body: dict, payload: dict) -> dict:
    exam_code = payload.get("exam_code", "")
    patient_id = payload.get("patient_id", "")
    practitioner_id = payload.get("practitioner_id", "")
    service_request_id = payload.get("service_request_id", "")

    if body.get("entry") and isinstance(body["entry"], list) and body["entry"]:
        resource = body["entry"][0].get("resource", {})
        if resource:
            try:
                resource["code"]["coding"][0]["code"] = exam_code or resource["code"]["coding"][0]["code"]
            except (KeyError, IndexError, TypeError):
                pass
            if patient_id and "subject" in resource:
                resource["subject"]["reference"] = f"Patient/{patient_id}"
            if practitioner_id and "requester" in resource:
                resource["requester"]["reference"] = f"Practitioner/{practitioner_id}"
            if service_request_id:
                resource["id"] = service_request_id
    return body


def send_direct(state: AgentState) -> AgentState:
    mapping = state.get("cached_mapping")
    if not mapping:
        state["cache_hit"] = False
        state["error"] = {"http_code": 400, "body": "no cached mapping available"}
        return state

    schema = json.loads(mapping["payload_schema"]) if isinstance(mapping["payload_schema"], str) else mapping["payload_schema"]
    body = {**schema, **state.get("payload", {})}
    body = _inject_request_values(body, state.get("payload", {}))

    target = state["system_target"]
    path = TARGET_PATHS.get(target, "/")
    code, resp_body = send_request(target, "POST", path, body)

    state["cache_hit"] = True
    state["built_payload"] = body
    logger.info("✓ sent → %s", code)
    if 200 <= code < 300:
        state["response"] = resp_body
        state["error"] = None
    else:
        state["response"] = None
        state["error"] = {"http_code": code, "body": resp_body}
    return state


def update_cache(state: AgentState) -> AgentState:
    if state.get("error") is not None:
        return state
    mapping = state.get("cached_mapping")
    if mapping and state.get("response") is not None:
        db = SessionLocal()
        try:
            new_count = update_usage(db, mapping["id"])
            logger.info("✓ cache updated use_count=%s", new_count)
        finally:
            db.close()
    return state


def doc_reader(state: AgentState) -> AgentState:
    return run_doc_reader(state)


def send_built(state: AgentState) -> AgentState:
    built = state.get("built_payload")
    if not built:
        state["error"] = {"http_code": 400, "body": "no built payload available"}
        return state

    target = state["system_target"]
    path = TARGET_PATHS.get(target, "/")
    code, resp_body = send_request(target, "POST", path, built)

    logger.info("✓ sent → %s", code)
    if 200 <= code < 300:
        state["response"] = resp_body
        state["error"] = None
    else:
        state["response"] = None
        state["error"] = {"http_code": code, "body": resp_body}
    return state


def save_cache(state: AgentState) -> AgentState:
    if state.get("error") is not None:
        return state
    built = state.get("built_payload")
    if built and state.get("response") is not None:
        db = SessionLocal()
        try:
            save_mapping(
                db,
                operation=state["operation"],
                system_target=state["system_target"],
                payload_schema=json.dumps(built),
                example_request=json.dumps(state.get("payload", {})),
                example_response=json.dumps(state["response"]),
            )
            logger.info("✓ cache saved")
        finally:
            db.close()
    return state


def route_after_check(state: AgentState) -> str:
    hit = state.get("cache_hit")
    if hit:
        logger.info("✓ cache hit → send_direct")
        return "send_direct"
    else:
        logger.info("✗ cache miss → doc_reader")
        return "doc_reader"


def route_after_send_direct(state: AgentState) -> str:
    if state.get("error"):
        logger.info("✗ error detected → dedup_check")
        return "dedup_check"
    else:
        logger.info("✓ success → update_cache")
        return "update_cache"


def route_after_send_built(state: AgentState) -> str:
    if state.get("error"):
        logger.info("✗ error detected → dedup_check")
        return "dedup_check"
    else:
        logger.info("✓ success → save_cache")
        return "save_cache"


def dedup_check(state: AgentState) -> AgentState:
    payload_sent = state.get("built_payload") or {}
    raw_error = state.get("error") or {}
    if isinstance(raw_error, str):
        try:
            raw_error = json.loads(raw_error)
        except Exception:
            raw_error = {"raw": raw_error}

    db = SessionLocal()
    try:
        result = find_duplicate_diagnosis(
            db,
            state["operation"],
            state["system_target"],
            payload_sent,
            raw_error,
        )
    finally:
        db.close()

    if result:
        state["dedup_hit"] = True
        state["error_diagnosis"] = result
        logger.info(
            "✓ dedup hit → error already diagnosed (origin=%s, confidence=%.0f%%) | "
            "LLM not used — reusing error_report id=%s",
            result["origin"],
            result["confidence"] * 100,
            result["id"],
        )
    else:
        logger.info("✗ dedup miss → error_checker")
        state["dedup_hit"] = False
    return state


def route_after_dedup(state: AgentState) -> str:
    if state.get("dedup_hit"):
        return END
    return "error_checker"


def error_checker_node(state: AgentState) -> AgentState:
    state["error_raw"] = state.get("error") or {}
    state["payload_sent"] = state.get("built_payload") or {}
    return run_error_checker(state)


def write_task_node(state: AgentState) -> AgentState:
    if state.get("error") is None and state.get("response") is not None:
        write_task(
            operation=state["operation"],
            system_target=state["system_target"],
            response=state["response"],
        )
    return state


def write_audit_event_node(state: AgentState) -> AgentState:
    diag = state.get("error_diagnosis") or {}
    payload_sent = state.get("payload_sent") or state.get("built_payload") or {}
    raw_error = state.get("error_raw") or state.get("error") or {}
    write_audit_event(
        operation=state["operation"],
        system_target=state["system_target"],
        diagnosis=diag,
        payload_sent=payload_sent,
        raw_error=raw_error,
    )
    return state


builder = StateGraph(AgentState)
builder.add_node("check_cache", check_cache)
builder.add_node("send_direct", send_direct)
builder.add_node("update_cache", update_cache)
builder.add_node("doc_reader", doc_reader)
builder.add_node("send_built", send_built)
builder.add_node("save_cache", save_cache)
builder.add_node("dedup_check", dedup_check)
builder.add_node("error_checker", error_checker_node)
builder.add_node("write_task", write_task_node)
builder.add_node("write_audit_event", write_audit_event_node)
builder.set_entry_point("check_cache")
builder.add_conditional_edges("check_cache", route_after_check)
builder.add_conditional_edges("send_direct", route_after_send_direct)
builder.add_edge("update_cache", END)
builder.add_edge("doc_reader", "send_built")
builder.add_conditional_edges("send_built", route_after_send_built)
builder.add_edge("save_cache", "write_task")
builder.add_edge("write_task", END)
builder.add_conditional_edges("dedup_check", route_after_dedup)
builder.add_edge("error_checker", "write_audit_event")
builder.add_edge("write_audit_event", END)

graph = builder.compile()
