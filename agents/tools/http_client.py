import json
import logging
import time

import httpx

logger = logging.getLogger(__name__)


def send_request(system_target: str, method: str, path: str, body: dict = None):
    hosts = {"reflab": "http://reflab:8001", "vitacare": "http://vitacare:8002"}
    base = hosts.get(system_target)
    if not base:
        return 400, {"error": f"unknown system_target: {system_target}"}
    url = f"{base}{path}"

    logger.info("→ %s %s\n%s", method.upper(), url, json.dumps(body or {}, indent=2))

    with httpx.Client(timeout=30) as client:
        try:
            start = time.time()
            if method.upper() == "GET":
                resp = client.get(url)
            else:
                resp = client.post(url, json=body or {})
            elapsed_ms = int((time.time() - start) * 1000)
            resp_body = resp.json()
            logger.info("← %s %s | %dms\n%s", resp.status_code, url, elapsed_ms, json.dumps(resp_body, indent=2))
            return resp.status_code, resp_body
        except httpx.RequestError as e:
            logger.error("request failed method=%s url=%s error=%s", method.upper(), url, e)
            return 502, {"error": str(e)}
