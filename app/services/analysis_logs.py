import json
import time
from pathlib import Path
from uuid import uuid4

from app.models import AnalysisRequest, AnalysisResponse

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "analysis.jsonl"


def _sanitize_payload(payload: AnalysisRequest) -> dict:
    data = payload.model_dump()
    image_base64 = data.get("imageBase64")
    if image_base64:
        data["imageBase64"] = f"<base64 omitted; length={len(image_base64)}>"
    return data


def write_analysis_log(
    payload: AnalysisRequest,
    started_at: float,
    response: AnalysisResponse | None = None,
    error: str | None = None,
) -> dict:
    LOG_DIR.mkdir(exist_ok=True)
    entry = {
        "logId": str(uuid4()),
        "status": "success" if response else "failed",
        "request": _sanitize_payload(payload),
        "response": response.model_dump() if response else None,
        "error": error,
        "durationMs": round((time.perf_counter() - started_at) * 1000),
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_analysis_logs(limit: int = 50) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    entries = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(entries[-limit:]))
