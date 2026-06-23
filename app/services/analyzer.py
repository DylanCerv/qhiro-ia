import json
import os

from openai import OpenAI

from app.models import AnalysisRequest, AnalysisResponse, SoilNutrients

SYSTEM_PROMPT = """You are an agricultural AI analyst for Qhiro Symbiotic.
Analyze crop health data and respond ONLY with valid JSON matching this schema:
{
  "diagnosis": "string",
  "severity": 0.0-1.0,
  "recommendedNpkFormula": {"nitrogen": number, "phosphorus": number, "potassium": number},
  "recommendedAction": "none|monitor|injection|emergency",
  "explanation": "string"
}
Base severity on NDVI, soil nutrients, and moisture. All text must be in English."""


def analyze_crop(payload: AnalysisRequest) -> AnalysisResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_analysis(payload)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    user_content = json.dumps(payload.model_dump(), indent=2)

    completion = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )

    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    return AnalysisResponse.model_validate(data)


def _fallback_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    severity = _estimate_severity(payload)
    action = _action_from_severity(severity)
    npk = _suggest_npk(payload, severity)

    diagnosis = (
        f"{payload.cropType.capitalize()} in zone {payload.zoneId} shows "
        f"NDVI {payload.ndvi:.2f} with moisture at {payload.soilMoisture:.0f}%."
    )

    return AnalysisResponse(
        diagnosis=diagnosis,
        severity=severity,
        recommendedNpkFormula=npk,
        recommendedAction=action,
        explanation="Rule-based analysis (OpenAI API key not configured).",
    )


def _estimate_severity(payload: AnalysisRequest) -> float:
    ndvi_risk = max(0.0, 0.7 - payload.ndvi) / 0.7
    moisture_risk = abs(payload.soilMoisture - 45) / 45
    nutrient_avg = (
        payload.soilNutrients.nitrogen
        + payload.soilNutrients.phosphorus
        + payload.soilNutrients.potassium
    ) / 3
    nutrient_risk = max(0.0, (40 - nutrient_avg) / 40)
    score = ndvi_risk * 0.5 + moisture_risk * 0.25 + nutrient_risk * 0.25
    return round(min(1.0, max(0.0, score)), 2)


def _action_from_severity(severity: float) -> str:
    if severity >= 0.8:
        return "emergency"
    if severity >= 0.6:
        return "injection"
    if severity >= 0.3:
        return "monitor"
    return "none"


def _suggest_npk(payload: AnalysisRequest, severity: float) -> SoilNutrients:
    base_n = payload.soilNutrients.nitrogen
    base_p = payload.soilNutrients.phosphorus
    base_k = payload.soilNutrients.potassium
    boost = 10 + severity * 30

    return SoilNutrients(
        nitrogen=round(base_n + boost * 0.4, 1),
        phosphorus=round(base_p + boost * 0.3, 1),
        potassium=round(base_k + boost * 0.3, 1),
    )
