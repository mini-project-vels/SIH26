# 🛰️ SatQuery AI - Multimodal Remote Sensing Assistant

An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries.

---

## 📖 Project Overview

SatQuery AI is designed around a multi-agent remote-sensing architecture. Complex analyses are broken down into distinct decoupled stages:

1. **Query Understanding (WHAT)**: Normalizes, classifies, and validates the requested details.
2. **Orchestrator / Brain (HOW)**: Compiles steps, checks capabilities, verifies inputs, and delegates control.
3. **Specialist Agents (DO THE WORK)**: Performs calculations, models, and outputs.

---

## 🚀 Development Roadmap

* **Phase 1**: ✅ Query Understanding Agent
* **Phase 2**: ✅ Change Detection Specialist Agent (Classical pixel difference + visual alignment)
* **Phase 3**: ✅ Orchestrator / Brain (Capability Registry + execution planning + end-to-end execution)
* **Phase 4**: ✅ Single Image Vision-Language Specialist Agent (Qwen2.5-VL via Hugging Face Router)
* **Phase 5**: 🔜 Full Multimodal Earth Intelligence Platform

---

## 🖼️ Phase 4 — Single Image Vision-Language Specialist Agent

### What it does

Phase 4 adds a real AI-powered **Vision-Language Analysis** capability to SatQuery AI. Users can:

- Upload **one satellite image**
- Ask any **natural language question** about it
- Receive an **AI-generated expert analysis** from the Qwen2.5-VL vision model

Example queries:
- *"What can you see in this satellite image?"*
- *"Is there a water body visible?"*
- *"Is this area urban or rural?"*
- *"Are buildings visible?"*
- *"Describe the terrain and land cover."*

### Architecture

```
USER + IMAGE + QUERY
        ↓
QUERY UNDERSTANDING AGENT
        ↓
ORCHESTRATOR / BRAIN
        ↓
SINGLE IMAGE ANALYSIS AGENT
        ↓
VISION PROMPT BUILDER
        ↓
HUGGING FACE VISION SERVICE
        ↓
QWEN2.5-VL (via HF Router)
        ↓
AI RESPONSE
```

### Hugging Face Integration

Powered by **Hugging Face OpenAI-compatible Router** using the `openai` Python SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
    timeout=60.0
)
```

**Model**: `Qwen/Qwen2.5-VL-3B-Instruct:featherless-ai`

Images are encoded as **Base64 data URLs** and sent via the `image_url` content type, supporting PNG, JPG, JPEG, and WEBP.

### Remote Sensing Prompt System

All requests include enforced **safety rules** for scientific analysis:
- No invented observations
- Cautious phrasing on uncertainty
- Practical remote sensing categories (water, vegetation, urban, roads, buildings, etc.)

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
HF_TOKEN=your_huggingface_token_here
HF_VISION_MODEL=Qwen/Qwen2.5-VL-3B-Instruct:featherless-ai
HF_BASE_URL=https://router.huggingface.co/v1
```

---

## 🌐 API Endpoints

### `POST /analyze-image`

**Accepts**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | Natural language question about the image |
| `image` | file | ✅ | Satellite image (PNG, JPG, JPEG, WEBP) |

**Response (`SUCCESS`)**:
```json
{
  "request_id": "893c5d6c-...",
  "status": "SUCCESS",
  "query": "What can you see in this satellite image?",
  "analysis_type": "single_image_analysis",
  "model": {
    "provider": "huggingface",
    "model_name": "Qwen/Qwen2.5-VL-3B-Instruct:featherless-ai"
  },
  "result": {
    "answer": "Based on the visible imagery, the area shows..."
  },
  "limitations": [
    "The response is based on visual interpretation of the provided image.",
    "This result should not be treated as a precise scientific remote sensing measurement.",
    "SatQuery AI may not detect fine-grained features at low image resolution."
  ]
}
```

---

### `POST /orchestrate`

End-to-end orchestration endpoint. Now supports three routes:

**Accepts**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | Natural language query |
| `image` | file | ⬜ | Single image (for VQA / single image analysis) |
| `before_image` | file | ⬜ | Baseline image (for change detection) |
| `after_image` | file | ⬜ | Post-event image (for change detection) |

#### Route 1 — Single Image Analysis
```
query:  "What can you see in this satellite image?"
image:  [satellite.png]
→ SingleImageAnalysisAgent → Qwen2.5-VL
```

#### Route 2 — Visual Question Answering
```
query:  "Is there a water body visible?"
image:  [satellite.png]
→ SingleImageAnalysisAgent → Qwen2.5-VL
```

#### Route 3 — Change Detection
```
query:        "What changed between these two images?"
before_image: [before.png]
after_image:  [after.png]
→ ChangeDetectionAgent → Pixel analysis
```

---

## 🧠 Phase 3 — Orchestrator / Brain Architecture

```
                    👤 USER
                       │
                       ▼
             Natural Language Query + Files
                       │
                       ▼
        🧠 QUERY UNDERSTANDING AGENT (WHAT)
                       │
                       ▼
           STRUCTURED TASK DESCRIPTION
                       │
                       ▼
             🧠 ORCHESTRATOR / BRAIN (HOW)
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
      Capability Registry    Execution Planner
             │                   │
             └─────────┬─────────┘
                       │
                       ▼
             🛰️ SPECIALIST AGENT (DO THE WORK)
                       │
                       ▼
                  📊 RESULT
```

---

## 📁 Full Project Structure

```
satquery-ai/
│
├── main.py                             # FastAPI app + router registration
├── requirements.txt                    # Dependencies
├── .env                                # Secrets (never commit!)
├── .env.example                        # Template for required env vars
├── .gitignore                          # Git exclusions
├── README.md                           # Project documentation
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── routes.py                   # /health, /analyze-query
│   │   ├── orchestration_routes.py     # /orchestrate
│   │   └── vision_routes.py            # /analyze-image  [NEW Phase 4]
│   │
│   ├── agents/
│   │   ├── query_understanding_agent.py
│   │   ├── change_detection_agent.py
│   │   ├── orchestrator.py             # Updated: routes vision capabilities
│   │   └── single_image_analysis_agent.py  [NEW Phase 4]
│   │
│   ├── services/
│   │   ├── capability_registry.py      # Updated: SIA/VQA now available=True
│   │   ├── execution_planner.py
│   │   ├── orchestration_service.py    # Updated: passes image parameter
│   │   ├── classifier_interface.py
│   │   ├── rule_based_classifier.py
│   │   ├── input_validator.py
│   │   ├── task_builder.py
│   │   ├── huggingface_vision_service.py   [NEW Phase 4]
│   │   └── vision_prompt_builder.py        [NEW Phase 4]
│   │
│   ├── models/
│   │   ├── schemas.py
│   │   ├── orchestration_schemas.py
│   │   └── vision_schemas.py               [NEW Phase 4]
│   │
│   └── config/
│       ├── intents.py
│       └── vision_config.py                [NEW Phase 4]
│
└── tests/
    ├── test_classifier.py
    ├── test_input_validator.py
    ├── test_query_agent.py
    ├── test_orchestrator.py
    ├── test_orchestration_api.py
    ├── test_single_image_agent.py          [NEW Phase 4]
    └── test_vision_api.py                  [NEW Phase 4]
```

---

## ⚙️ Installation & Running

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
# Edit .env and add your HF_TOKEN
```

### 4. Run FastAPI application
```bash
uvicorn main:app --reload
```

Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for Swagger UI.

### 5. Run Pytest Suite
```bash
pytest -v
```

---

## 🔌 Extensibility: Adding New Agents

To add a new capability (e.g. `region_grounding`):

1. Create `app/agents/your_agent.py`
2. Set `available: True` in `app/services/capability_registry.py`
3. Add the execution hook in `app/agents/orchestrator.py`

The planner and routing handle validation automatically.
