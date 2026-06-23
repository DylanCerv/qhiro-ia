from typing import Literal

from pydantic import BaseModel, Field


class SoilNutrients(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float


class AnalysisRequest(BaseModel):
    parcelId: str
    zoneId: str
    ndvi: float = Field(ge=0.0, le=1.0)
    soilNutrients: SoilNutrients
    soilMoisture: float
    cropType: str
    timestamp: str


class AnalysisResponse(BaseModel):
    diagnosis: str
    severity: float = Field(ge=0.0, le=1.0)
    recommendedNpkFormula: SoilNutrients
    recommendedAction: Literal["none", "monitor", "injection", "emergency"]
    explanation: str
