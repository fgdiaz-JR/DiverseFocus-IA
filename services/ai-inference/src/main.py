"""
AI Inference service for DiverseFocus-IA.

Provides text simplification, video summarisation, and visual-aid generation
powered by Google Gemini Pro.
"""

import json
import logging

import google.generativeai as genai
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from .prompt_templates import (
    SIMPLIFY_TEMPLATE,
    SUMMARIZE_VIDEO_TEMPLATE,
    VISUAL_AID_TEMPLATE,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"

    class Config:
        env_file = ".env"


settings = Settings()

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

app = FastAPI(
    title="DiverseFocus-IA AI Inference",
    description="AI-powered text simplification and learning support using Gemini Pro",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(settings.gemini_model)


async def _generate(prompt: str) -> str:
    """Call Gemini and return the text response."""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY is not configured",
        )
    try:
        model = _get_model()
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini generation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model error: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SimplifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000, description="Text to simplify")
    level: str = Field(
        default="medium",
        pattern="^(easy|medium|advanced)$",
        description="Simplification level: easy, medium, or advanced",
    )


class SimplifyResponse(BaseModel):
    simplified_text: str
    level: str
    original_length: int
    simplified_length: int


class SummarizeVideoRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=50_000)


class SummarizeVideoResponse(BaseModel):
    big_idea: str
    key_points: list[str]
    glossary: dict[str, str]
    quiz: list[dict]


class VisualAidRequest(BaseModel):
    concept: str = Field(..., min_length=1, max_length=500)


class VisualAidResponse(BaseModel):
    concept: str
    emoji: str
    one_line_definition: str
    colour: str
    branches: list[dict]
    memory_tip: str
    real_world_connection: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "ai-inference"}


@app.post("/simplify", response_model=SimplifyResponse, tags=["AI"])
async def simplify_text(body: SimplifyRequest) -> SimplifyResponse:
    """Simplify complex text for neurodivergent learners."""
    prompt = SIMPLIFY_TEMPLATE.format(text=body.text, level=body.level)
    simplified = await _generate(prompt)
    return SimplifyResponse(
        simplified_text=simplified.strip(),
        level=body.level,
        original_length=len(body.text),
        simplified_length=len(simplified.strip()),
    )


@app.post("/summarize-video", response_model=SummarizeVideoResponse, tags=["AI"])
async def summarize_video(body: SummarizeVideoRequest) -> SummarizeVideoResponse:
    """Summarise a video transcript into accessible structured notes."""
    prompt = SUMMARIZE_VIDEO_TEMPLATE.format(transcript=body.transcript)
    raw = await _generate(prompt)

    # Strip markdown fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned malformed JSON",
        ) from exc

    return SummarizeVideoResponse(
        big_idea=data.get("big_idea", ""),
        key_points=data.get("key_points", []),
        glossary=data.get("glossary", {}),
        quiz=data.get("quiz", []),
    )


@app.post("/generate-visual-aid", response_model=VisualAidResponse, tags=["AI"])
async def generate_visual_aid(body: VisualAidRequest) -> VisualAidResponse:
    """Generate structured data for an interactive visual mind-map."""
    prompt = VISUAL_AID_TEMPLATE.format(concept=body.concept)
    raw = await _generate(prompt)

    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned malformed JSON",
        ) from exc

    return VisualAidResponse(
        concept=data.get("concept", body.concept),
        emoji=data.get("emoji", "🧠"),
        one_line_definition=data.get("one_line_definition", ""),
        colour=data.get("colour", "#b0c4de"),
        branches=data.get("branches", []),
        memory_tip=data.get("memory_tip", ""),
        real_world_connection=data.get("real_world_connection", ""),
    )
