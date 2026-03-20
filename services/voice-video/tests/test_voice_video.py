"""
Unit tests for the Voice/Video service with mocked Whisper calls.
"""

import io
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Inject a fake 'whisper' module so src.main can be imported without the
# heavy openai-whisper package actually being installed in the test env.
_fake_whisper = types.ModuleType("whisper")
_fake_whisper.load_model = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
_fake_whisper.Whisper = MagicMock  # type: ignore[attr-defined]
sys.modules.setdefault("whisper", _fake_whisper)

# Similarly mock yt_dlp
_fake_yt_dlp = types.ModuleType("yt_dlp")
_fake_yt_dlp.YoutubeDL = MagicMock  # type: ignore[attr-defined]
sys.modules.setdefault("yt_dlp", _fake_yt_dlp)

from src.main import app, _transcribe_file, get_whisper_model  # noqa: E402

client = TestClient(app)

MOCK_WHISPER_RESULT = {
    "text": "Hello world this is a test transcription.",
    "language": "en",
    "segments": [
        {"start": 0.0, "end": 2.5, "text": "Hello world this is a test transcription."}
    ],
}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "voice-video"


@patch("src.main.get_whisper_model")
def test_transcribe_audio_mp3(mock_get_model):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = MOCK_WHISPER_RESULT
    mock_get_model.return_value = mock_model

    audio_bytes = b"fake audio content"
    with patch("src.main._transcribe_file") as mock_transcribe:
        from src.main import TranscriptResponse
        mock_transcribe.return_value = TranscriptResponse(
            transcript="Hello world this is a test transcription.",
            language="en",
            segments=[{"start": 0.0, "end": 2.5, "text": "Hello world"}],
        )
        response = client.post(
            "/transcribe",
            files={"file": ("test_audio.mp3", io.BytesIO(audio_bytes), "audio/mpeg")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert data["language"] == "en"
    assert "Hello world" in data["transcript"]


@patch("src.main._transcribe_file")
def test_transcribe_audio_wav(mock_transcribe):
    from src.main import TranscriptResponse
    mock_transcribe.return_value = TranscriptResponse(
        transcript="WAV file transcription result.",
        language="en",
        segments=[],
    )
    audio_bytes = b"RIFF fake wav content"
    response = client.post(
        "/transcribe",
        files={"file": ("recording.wav", io.BytesIO(audio_bytes), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["transcript"] == "WAV file transcription result."


def test_transcribe_unsupported_format():
    response = client.post(
        "/transcribe",
        files={"file": ("document.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
    )
    assert response.status_code == 422


@patch("src.main._download_audio_from_url")
@patch("src.main._transcribe_file")
def test_extract_video_transcript(mock_transcribe, mock_download, tmp_path):
    import os
    audio_file = str(tmp_path / "audio.mp3")
    # Create a dummy file so the path-exists check passes
    with open(audio_file, "w") as f:
        f.write("fake")

    mock_download.return_value = audio_file

    from src.main import TranscriptResponse
    mock_transcribe.return_value = TranscriptResponse(
        transcript="Video transcript content here.",
        language="en",
        segments=[],
    )

    response = client.post(
        "/extract-video-transcript",
        json={"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    assert response.status_code == 200
    assert response.json()["transcript"] == "Video transcript content here."
