import os 
import requests 
import vlc
from core.speech.base import VoiceBase, SpeechConfig
import time 
from pydantic import BaseModel
from elevenlabs.client import ElevenLabs
from elevenlabs import stream, Voice 
import base64
import json
import httpx
import traceback
from master_agent.base import TextToSpeechDataMessageToClient, WebSocketMessageTypeToClient
from elevenlabs import HttpValidationError
from typing import Dict, Any

class ElevenLabsTTS(VoiceBase):

    def __init__(self, config:SpeechConfig, main_logger):
        super().__init__(config, main_logger)

    async def _speech_to_text(self, audio_data: str, user_id: str) -> Dict[str, Any]:
        return {"user_id":user_id, "status":False}


    async def _text_to_speech(self, websocket_connection_manager, user_id: str, text: str, voice_name: str) -> Dict[str, Any]:
        self.main_logger.info(f"Running text to speech for user: {user_id}, text: {text}, voice: {voice_name}")
        # Initialize Eleven Labs TTS Client
        client = ElevenLabs(api_key=self.config.api_key)

        voices = client.voices.get_all().voices
        
        for voice in voices:
            if isinstance(voice, Voice): 
                name = voice.name
                voice_id = voice.voice_id
                if name.lower() == voice_name.lower():
                    self.main_logger.info(f"Voice found: {name}, ID: {voice_id}")
                    break
        try:
            # Generate audio stream
            audio_stream = client.text_to_speech.convert_as_stream(
                text = text,
                voice_id = voice_id,
                model_id = "eleven_turbo_v2_5"
            )
            
            # Stream audio in JSON format
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    base64_chunk = base64.b64encode(chunk).decode("utf-8")
                    textspeechdata = TextToSpeechDataMessageToClient(audio_data=base64_chunk)
                    
                    if (websocket_connection_manager.get_master_instance(user_id)):
                        master_instance = websocket_connection_manager.get_master_instance(user_id)
                        if master_instance is None:
                            self.main_logger.error(f"Master instance not found for user: {user_id}")
                            return {"user_id":user_id, "status":False}
                        await master_instance._send_message_to_frontend(textspeechdata.model_dump_json(), WebSocketMessageTypeToClient.AUDIO_CHUNKS.value)

            # Send completion message
            if (websocket_connection_manager.get_master_instance(user_id)):
                master_instance = websocket_connection_manager.get_master_instance(user_id)
                if master_instance is None:
                    self.main_logger.error(f"Master instance not found for user: {user_id}")
                    return {"user_id":user_id, "status":False}
                await master_instance._send_message_to_frontend(json.dumps({"message": "audio_complete"}), WebSocketMessageTypeToClient.AUDIO_STREAMING_COMPLETED.value)
                return {"user_id":user_id, "status":True}
            
        except (HttpValidationError) as api_err:
            self.main_logger.error(f"Eleven labs [API Error] {api_err}")
            return {"user_id":user_id, "status":False}

        except httpx.TimeoutException as net_timeout:
            self.main_logger.error(f"[Timeout Error] {net_timeout}")
            return {"user_id":user_id, "status":False}

        except httpx.RequestError as net_error:
            self.main_logger.error(f"[Network Error] {net_error}")
            return {"user_id":user_id, "status":False}

        except Exception as e:
            self.main_logger.error(f"Unexpected error in Eleven Labs TTS: {e}")
            traceback.print_exc()
            return {"user_id":user_id, "status":False}

        return {"user_id":user_id, "status":False}