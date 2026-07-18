import json
import os

from openai import OpenAI

from app.models import AnalysisRequest, AnalysisResponse

SYSTEM_PROMPT = """Eres un analista agrícola de Qhiro Symbiotic.
Analiza el estado del cultivo y responde SOLO con JSON válido que siga exactamente este esquema:
{
  "diagnosis": "string",
  "severity": 0.0-1.0,
  "recommendedNpkFormula": {"nitrogen": number, "phosphorus": number, "potassium": number},
  "recommendedAction": "none|monitor|injection|emergency",
  "explanation": "string",
  "affectedCoordinates": [{"lat": number, "lng": number}] | null
}
Base la severidad en NDVI, nutrientes del suelo, humedad, tipo de cultivo, coordenadas del campo e imagen del cultivo cuando esté disponible.
Si se proporciona una imagen, inspecciónala para detectar estrés visible, plagas, enfermedades, deficiencia nutricional, sequía o crecimiento saludable.
No inventes coordenadas exactas del campo; solo devuelve coordenadas que ya vengan en la petición o null.
Todo el texto debe estar en español."""


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
