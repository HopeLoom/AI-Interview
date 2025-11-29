import base64
import binascii
import os
import tempfile
from typing import Any

from groq import Groq
from pydantic import BaseModel

from core.speech.base import VoiceBase


class SpeechToTextConfig(BaseModel):
    provider: str = "groq"
    api_key: str = ""
    voice_id: str = ""
    data_dir: str = ""


class GroqSpeechToText(VoiceBase):
    def __init__(self, config: SpeechToTextConfig, main_logger):
        super().__init__(config, main_logger)

        api_key = self.config.api_key
        if not api_key:
            self.main_logger.error("Missing GROQ API key")

        self.client = Groq(api_key=api_key)

    async def _speech_to_text(self, audio_data: str, user_id: str) -> dict[str, Any]:
        """Process base64-encoded audio data using Groq's transcription API.

        Returns:
            dict: {
                "result": str (transcription or error message),
                "status": bool (True if successful, False if error)
            }
        """
        if not audio_data:
            return {"result": "No audio data provided", "user_id": user_id, "status": False}

        try:
            audio_bytes = base64.b64decode(audio_data)
        except (binascii.Error, ValueError):
            return {"result": "Invalid base64 audio data", "user_id": user_id, "status": False}

        temp_audio_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name

            with open(temp_audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(temp_audio_path), file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="text",
                    language="en",
                )

            return {"result": transcription, "user_id": user_id, "status": True}

        except Exception as e:
            return {
                "result": f"Error during transcription: {e!s}",
                "user_id": user_id,
                "status": False,
            }

        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except Exception as cleanup_error:
                    self.main_logger.exception(f"Error cleaning up temp file: {cleanup_error}")

    async def _text_to_speech(
        self, websocket_connection_manager, settings, user_id, text, voice_name
    ) -> dict[str, Any]:
        return {"result": "Not implemented", "user_id": user_id, "status": False}
