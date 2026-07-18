# qhiro-backend-ia

Servicio de IA agrícola de Qhiro Symbiotic. Recibe datos del cultivo desde el backend operativo y devuelve una decisión estructurada en español para que el backend pueda generar alertas, reportes y acciones. Los títulos del PDF y el texto visible al usuario también salen en español.

## Qué Hace

- Expone una API FastAPI.
- Recibe datos de parcela, zona, cultivo, NDVI, humedad, nutrientes NPK, coordenadas e imagen.
- Envía el análisis a OpenAI.
- Devuelve diagnóstico, severidad, fórmula NPK recomendada, acción recomendada, explicación y coordenadas afectadas si aplica.
- Registra cada análisis en `logs/analysis.jsonl` con request recibido, response enviada, error si ocurre y duración.
- No controla hardware.
- No publica MQTT.
- No escribe en Firebase.

## Por Qué Existe

La IA está separada del backend operativo para mantener responsabilidades claras:

- `qhiro-backend` orquesta usuarios, Firebase, MQTT, vuelos y decisiones.
- `qhiro-backend-ia` solo interpreta datos agrícolas y responde con JSON validado.

Esto permite cambiar modelos, prompts o proveedores de IA sin romper la API principal ni el flujo MQTT.

## Requisito Importante

`OPENAI_API_KEY` es obligatoria. No hay reglas locales ni fallback determinístico para decisiones agronómicas.

Si falta la clave, `/analyze` responde `503` para evitar que el sistema actúe con datos inventados o reglas no validadas.

La IA debe responder en español: diagnóstico, explicación y cualquier texto visible para el usuario deben salir en español, aunque el JSON siga siendo el mismo.

## Variables de Entorno

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
PORT=8000
```

## Ejecución Local

Windows CMD:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verificación:

```bash
curl http://localhost:8000/health
```

Consultar logs recientes:

```bash
curl "http://localhost:8000/analysis-logs?limit=20"
```

## Endpoint Principal

```text
POST /analyze
```

Payload:

```json
{
  "parcelId": "parcel_001",
  "zoneId": "zone_a",
  "ndvi": 0.55,
  "soilNutrients": {
    "nitrogen": 35,
    "phosphorus": 28,
    "potassium": 36
  },
  "soilMoisture": 40,
  "cropType": "cacao",
  "timestamp": "2026-07-12T20:00:00.000Z",
  "imageUrl": "https://example.com/crop-image.jpg",
  "coordinates": [{ "lat": -0.1807, "lng": -78.4678 }]
}
```

También se acepta:

```json
{
  "imageBase64": "<jpeg-base64-without-data-prefix>"
}
```

Respuesta:

```json
{
  "diagnosis": "Se detectó estrés en el cultivo a partir de la imagen y la telemetría.",
  "severity": 0.72,
  "recommendedNpkFormula": {
    "nitrogen": 42,
    "phosphorus": 31,
    "potassium": 40
  },
  "recommendedAction": "injection",
  "explanation": "El NDVI y el estrés visible sugieren una intervención nutricional.",
  "affectedCoordinates": [{ "lat": -0.1807, "lng": -78.4678 }]
}
```

## Contrato con el Backend Operativo

El backend operativo llama este servicio cuando recibe telemetría válida de un dron, especialmente cuando:

- El dispositivo pertenece al usuario.
- El vuelo corresponde a la parcela.
- El estado del dron indica finalización o hay datos suficientes para análisis.
- Hay NDVI, nutrientes, humedad y/o imagen.

La respuesta no debe ejecutarse directamente sobre hardware sin validación operacional. El backend usa la severidad y acción recomendada para alertas, reportes y comandos, pero la conexión física requiere interlocks, límites de dosis y confirmaciones.

## Logs de IA

El log lo genera este servicio, no el frontend. Cada entrada incluye:

- `request`: datos recibidos por `/analyze`.
- `response`: JSON enviado al backend operativo.
- `durationMs`: tiempo que tomó el análisis.
- `status`: `success` o `failed`.
- `error`: detalle del error si OpenAI o la validación fallan.

Para evitar archivos enormes, `imageBase64` se guarda como referencia omitida con su longitud, no como la imagen completa.

## Qué Falta

- Validación agronómica por cultivo, etapa fenológica y tipo de suelo.
- Definir dosis reales según área, concentración, caudal y límites máximos.
- Versionado de prompts/modelos.
- Evaluación con datos etiquetados de campo.
- Manejo de almacenamiento privado de imágenes.
- Persistir los logs de IA en una base de datos o sistema centralizado para producción.
- Trazabilidad completa de versión de modelo, entrada, salida y decisión.
