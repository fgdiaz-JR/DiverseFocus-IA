"""
Voice/Video processing service for DiverseFocus-IA.

Provides audio transcription using OpenAI Whisper and video transcript extraction.
"""

import logging
import os
import tempfile

import whisper
import yt_dlp
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    whisper_model: str = "base"

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI(
    title="DiverseFocus-IA Voice/Video Service",
    description="Audio transcription and video processing using OpenAI Whisper",
    version="1.0.0",
)

# Load the Whisper model once at startup to avoid repeated loading overhead.
_whisper_model: whisper.Whisper | None = None


def get_whisper_model() -> whisper.Whisper:
    global _whisper_model  # noqa: PLW0603
    if _whisper_model is None:
        logger.info("Loading Whisper model: %s", settings.whisper_model)
        _whisper_model = whisper.load_model(settings.whisper_model)
    return _whisper_model


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TranscriptResponse(BaseModel):
    transcript: str
    language: str
    segments: list[dict]


class VideoTranscriptRequest(BaseModel):
    video_url: str = Field(..., description="Public URL of the video to transcribe")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _transcribe_file(file_path: str) -> TranscriptResponse:
    """Run Whisper transcription on a local file path."""
    model = get_whisper_model()
    result = model.transcribe(file_path, verbose=False)
    return TranscriptResponse(
        transcript=result.get("text", "").strip(),
        language=result.get("language", "unknown"),
        segments=[
            {
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", "").strip(),
            }
            for seg in result.get("segments", [])
        ],
    )


def _download_audio_from_url(url: str, output_path: str) -> str:
    """Download audio from a video URL using yt-dlp. Returns the output file path."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    # yt-dlp appends .mp3 to the outtmpl
    return output_path + ".mp3"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "voice-video"}


@app.post("/transcribe", response_model=TranscriptResponse, tags=["Audio"])
async def transcribe_audio(file: UploadFile = File(...)) -> TranscriptResponse:
    """
    Accept an uploaded audio file (mp3, wav, m4a, ogg, flac) and return a
    Whisper transcription.
    """
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    _, ext = os.path.splitext(file.filename or "audio.wav")
    if ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_extensions}",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        return _transcribe_file(tmp_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Transcription failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {exc}",
        ) from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/extract-video-transcript", response_model=TranscriptResponse, tags=["Video"])
async def extract_video_transcript(body: VideoTranscriptRequest) -> TranscriptResponse:
    """
    Download audio from a public video URL and return a Whisper transcription.
    Supports YouTube, Vimeo, and other yt-dlp-compatible sources.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = os.path.join(tmp_dir, "audio")
        try:
            audio_path = _download_audio_from_url(body.video_url, base_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Video download failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not download video: {exc}",
            ) from exc

        if not os.path.exists(audio_path):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio extraction produced no output file",
            )

        try:
            return _transcribe_file(audio_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Transcription failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {exc}",
            ) from exc
