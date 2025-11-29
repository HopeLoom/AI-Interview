import base64
import os
import tempfile
from typing import Any

from google.cloud import speech

from core.speech.base import SpeechConfig, VoiceBase


class GoogleSpeechToText(VoiceBase):
    def __init__(self, config: SpeechConfig, main_logger):
        super().__init__(config, main_logger)
        self.client = speech.SpeechClient()

    async def _text_to_speech(
        self, websocket_connection_manager, user_id, text, voice_name
    ) -> dict[str, Any]:
        return {"user_id": user_id, "status": False}

    async def _speech_to_text(self, audio_data: str, user_id: str) -> dict[str, Any]:
        audio_bytes = base64.b64decode(audio_data)
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name

        # Process audio with Google Speech-to-Text
        with open(temp_audio_path, "rb") as audio_file:
            audio_content = audio_file.read()

        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # Adjust format
            sample_rate_hertz=48000,
            language_code="en-US",
        )

        response = self.client.recognize(config=config, audio=audio)
        transcript = " ".join(result.alternatives[0].transcript for result in response.results)
        self.main_logger.info(f"Transcription result: {transcript}")
        os.unlink(temp_audio_path)
        return {"result": transcript, "user_id": user_id, "status": True}
