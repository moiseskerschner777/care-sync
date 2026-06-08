import ast
import logging

from config import settings

logger = logging.getLogger(__name__)


async def _execute_query(query: str, params: list[str] | None = None):
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(settings.iris_mcp_url + "/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("execute_sql", {
                "query": query,
                "params": params or [],
            })
            raw = result.content[0].text if result.content else "[]"
            return ast.literal_eval(raw)


async def check_patient_exists(patient_id: str) -> bool | None:
    try:
        rows = await _execute_query(
            "SELECT COUNT(*) FROM labcore.patient WHERE id = ?",
            [patient_id],
        )
        return bool(rows and rows[0][0])
    except Exception:
        logger.warning("check_patient_exists failed for %s", patient_id, exc_info=True)
        return None


async def check_exam_exists(exam_code: str) -> bool | None:
    try:
        rows = await _execute_query(
            "SELECT COUNT(*) FROM labcore.exam_catalog WHERE exam_code = ?",
            [exam_code],
        )
        return bool(rows and rows[0][0])
    except Exception:
        logger.warning("check_exam_exists failed for %s", exam_code, exc_info=True)
        return None


async def get_exam_can_perform(exam_code: str) -> bool | None:
    try:
        rows = await _execute_query(
            "SELECT can_perform FROM labcore.exam_catalog WHERE exam_code = ?",
            [exam_code],
        )
        return rows[0][0] if rows else None
    except Exception:
        logger.warning("get_exam_can_perform failed for %s", exam_code, exc_info=True)
        return None


async def get_service_request_status(service_request_id: str) -> str | None:
    try:
        rows = await _execute_query(
            "SELECT status FROM labcore.service_request WHERE id = ?",
            [service_request_id],
        )
        return rows[0][0] if rows else None
    except Exception:
        logger.warning("get_service_request_status failed for %s", service_request_id, exc_info=True)
        return None


async def get_covenant_id(service_request_id: str) -> str | None:
    return None
