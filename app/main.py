from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalysisRequest, AnalysisResponse
from app.services.analyzer import analyze_crop

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
    return analyze_crop(payload)
