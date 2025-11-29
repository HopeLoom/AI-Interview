import base64
import json
from typing import Any, Dict

import httpx

from core.speech.base import SpeechConfig, VoiceBase
from master_agent.base import TextToSpeechDataMessageToClient, WebSocketMessageTypeToClient


class OPENAI(VoiceBase):
    def __init__(self, config: SpeechConfig, main_logger):
        super().__init__(config, main_logger)

    async def _text_to_speech(
        self, websocket_connection_manager, user_id, text, voice_name
    ) -> Dict[str, Any]:
        if not self.config.api_key:
            self.main_logger.error("Missing OpenAI API key")
            return {"user_id": user_id, "status": False}

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-4o-mini-tts",
            "voice": voice_name,
            "input": text,
            "instructions": "Speak in a professional tone since you are taking an interview of a candidate",
            "response_format": "mp3",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client, client.stream(
                "POST", self.config.tts_url, json=payload, headers=headers
            ) as response:
                if response.status_code != 200:
                    error_msg = (
                        f"TTS API error: {response.status_code} - {await response.aread()}"
                    )
                    self.main_logger.error("error: %s", error_msg)
                    return {"user_id": user_id, "status": False}
                async for chunk in response.aiter_bytes():
                    if chunk:
                        try:
                            base64_chunk = base64.b64encode(chunk).decode("utf-8")
                            textspeechdata = TextToSpeechDataMessageToClient(
                                audio_data=base64_chunk
                            )
                            if (
                                websocket_connection_manager is not None
                                and websocket_connection_manager.get_master_instance(user_id)
                            ):
                                master_instance = (
                                    websocket_connection_manager.get_master_instance(user_id)
                                )
                                if master_instance is None:
                                    self.main_logger.error(
                                        f"Master instance not found for user: {user_id}"
                                    )
                                    return {"user_id": user_id, "status": False}
                                await master_instance._send_message_to_frontend(
                                    textspeechdata.model_dump_json(),
                                    WebSocketMessageTypeToClient.AUDIO_CHUNKS.value,
                                )
                        except Exception as e:
                            self.main_logger.error(f"Error processing audio chunk: {e}")
                            return {"user_id": user_id, "status": False}

        except httpx.RequestError as e:
            self.main_logger.error(f"Request error in text to speech: {e}")
            return {"user_id": user_id, "status": False}

        except Exception as e:
            self.main_logger.error(f"Unexpected error in text to speech: {e}")
            return {"user_id": user_id, "status": False}

        # Send completion message
        if (
            websocket_connection_manager is not None
            and websocket_connection_manager.get_master_instance(user_id)
        ):
            master_instance = websocket_connection_manager.get_master_instance(user_id)
            if master_instance is None:
                self.main_logger.error(f"Master instance not found for user: {user_id}")
                return {"user_id": user_id, "status": False}
            await master_instance._send_message_to_frontend(
                json.dumps({"message": "audio_complete"}),
                WebSocketMessageTypeToClient.AUDIO_STREAMING_COMPLETED.value,
            )
            return {"user_id": user_id, "status": True}

        return {"user_id": user_id, "status": False}

    async def _speech_to_text(self, audio_data: str, user_id: str) -> Dict[str, Any]:
        return {"user_id": user_id, "status": False}
