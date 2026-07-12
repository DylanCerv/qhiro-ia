from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time

from app.models import AnalysisRequest, AnalysisResponse
from app.services.analyzer import analyze_crop
from app.services.analysis_logs import read_analysis_logs, write_analysis_log

load_dotenv()

app = FastAPI(
    title="Qhiro Symbiotic AI Engine",
    description="Crop health analysis — no hardware control",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "qhiro-backend-ia"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalysisRequest) -> AnalysisResponse:
    started_at = time.perf_counter()
    try:
        response = analyze_crop(payload)
        write_analysis_log(payload, started_at, response=response)
        return response
    except RuntimeError as exc:
        write_analysis_log(payload, started_at, error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        write_analysis_log(payload, started_at, error=str(exc))
        raise


@app.get("/analysis-logs")
def analysis_logs(limit: int = 50):
    return {"logs": read_analysis_logs(limit)}
