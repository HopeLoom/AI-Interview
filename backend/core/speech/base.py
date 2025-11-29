import abc
import asyncio
import base64
import json
from typing import Any, Dict, Optional

from pydantic import BaseModel

from master_agent.base import TextToSpeechDataMessageToClient, WebSocketMessageTypeToClient


class SpeechConfig(BaseModel):
    provider: str = "elevenlabs"
    speak_mode: bool = False
    api_key: str = ""
    voice_id: str = ""
    data_dir: str = ""
    tts_url: str = ""


class SpeechResult(BaseModel):
    user_id: str
    status: bool
    result: Optional[str] = None
    error: Optional[str] = None


class VoiceBase:
    def __init__(self, config: SpeechConfig, main_logger):
        self.config = config
        self.main_logger = main_logger
        self._lock = asyncio.Lock()  # Changed to asyncio.Lock
        self._setup(config)

    async def understand_speech(self, audio_data: str, user_id: str) -> SpeechResult:
        """Convert speech to text"""
        async with self._lock:
            try:
                result = await self._speech_to_text(audio_data, user_id)
                return SpeechResult(
                    user_id=user_id,
                    status=result.get("status", False),
                    result=result.get("result"),
                    error=result.get("error"),
                )
            except Exception as e:
                self.main_logger.error(f"Speech to text error: {e}")
                return SpeechResult(user_id=user_id, status=False, error=str(e))

    async def say_from_text(
        self, websocket_connection_manager, user_id: str, text: str, voice_name: str
    ) -> SpeechResult:
        """Convert text to speech"""
        async with self._lock:
            try:
                result = await self._text_to_speech(
                    websocket_connection_manager, user_id, text, voice_name
                )
                return SpeechResult(
                    user_id=user_id, status=result.get("status", False), error=result.get("error")
                )
            except Exception as e:
                self.main_logger.error(f"Text to speech error: {e}")
                return SpeechResult(user_id=user_id, status=False, error=str(e))

    async def _send_audio_chunk(
        self, websocket_connection_manager, user_id: str, audio_chunk: bytes
    ) -> bool:
        """Send audio chunk via WebSocket"""
        try:
            base64_chunk = base64.b64encode(audio_chunk).decode("utf-8")
            textspeechdata = TextToSpeechDataMessageToClient(audio_data=base64_chunk)

            master_instance = websocket_connection_manager.get_master_instance(user_id)
            if master_instance is None:
                self.main_logger.error(f"Master instance not found for user: {user_id}")
                return False

            await master_instance._send_message_to_frontend(
                textspeechdata.model_dump_json(), WebSocketMessageTypeToClient.AUDIO_CHUNKS.value
            )
            return True
        except Exception as e:
            self.main_logger.error(f"Error sending audio chunk: {e}")
            return False

    async def _send_completion_message(self, websocket_connection_manager, user_id: str) -> bool:
        """Send audio completion message"""
        try:
            master_instance = websocket_connection_manager.get_master_instance(user_id)
            if master_instance is None:
                self.main_logger.error(f"Master instance not found for user: {user_id}")
                return False

            await master_instance._send_message_to_frontend(
                json.dumps({"message": "audio_complete"}),
                WebSocketMessageTypeToClient.AUDIO_STREAMING_COMPLETED.value,
            )
            return True
        except Exception as e:
            self.main_logger.error(f"Error sending completion message: {e}")
            return False

    @abc.abstractmethod
    def _setup(self, config: SpeechConfig) -> None:
        pass

    @abc.abstractmethod
    async def _speech_to_text(self, audio_data: str, user_id: str) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    async def _text_to_speech(
        self, websocket_connection_manager, user_id: str, text: str, voice_name: str
    ) -> Dict[str, Any]:
        pass
