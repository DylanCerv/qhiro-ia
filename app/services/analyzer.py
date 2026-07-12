import json
import os

from openai import OpenAI

from app.models import AnalysisRequest, AnalysisResponse

SYSTEM_PROMPT = """You are an agricultural AI analyst for Qhiro Symbiotic.
Analyze crop health data and respond ONLY with valid JSON matching this schema:
{
  "diagnosis": "string",
  "severity": 0.0-1.0,
  "recommendedNpkFormula": {"nitrogen": number, "phosphorus": number, "potassium": number},
  "recommendedAction": "none|monitor|injection|emergency",
  "explanation": "string",
  "affectedCoordinates": [{"lat": number, "lng": number}] | null
}
Base severity on NDVI, soil nutrients, moisture, crop type, field coordinates, and crop imagery when provided.
If an image is provided, inspect it for visible crop stress, pests, disease, nutrient deficiency, drought stress, or healthy growth.
Do not invent exact field coordinates; only return coordinates that are provided in the request or null.
All text must be in English."""


def analyze_crop(payload: AnalysisRequest) -> AnalysisResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Local rule-based analysis is disabled.")

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    user_content = json.dumps(payload.model_dump(), indent=2)
    content: list[dict] = [{"type": "text", "text": user_content}]

    image_url = payload.imageUrl
    if not image_url and payload.imageBase64:
        image_url = f"data:image/jpeg;base64,{payload.imageBase64}"

    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    completion = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
    )

    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    return AnalysisResponse.model_validate(data)
