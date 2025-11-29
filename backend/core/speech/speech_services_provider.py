import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from core.speech.eleven_labs import ElevenLabsTTS
from core.speech.openai import OPENAI
from core.speech.google import GoogleSpeechToText
from core.speech.groq import GroqSpeechToText
from core.speech.base import SpeechConfig, SpeechResult

VOICE_CATEGORIES = {
    "female_us": ["Hope - The podcaster", "Sarah", "Clara - Casual Conversational", "Bella - Bubbly Best Friend", "Jessica Anne Bogart - Conversations", "Cassidy", "Alice"],
    "male_us": ["Jerry B. - Hyper-Real & Conversational", "Mark - Natural Conversations", "Matthew Schmitz  - Relaxed Conversational Exploration", "Jarnathan - warm, confident, versatile", "Kevin - Career & Life Coach", "Leo – Call Center Concierge", "Brian", "Daniel"],
    "male_indian": ["Nikhil - Young Conversational Voice", "Raju - Human-like Customer Care Voice", "Ranbir M - Customer Support (Neutral Accent)"],
    "female_indian": ["Ziina - Confident & Clear", "Monika Sogam - Interactive E-Learning Bot Voice (Neutral Accent)", "Anika - Warm & Intimate Voice", "Riya Rao - Famous Customer Care Voice"],
    "male_openai": ["alloy", "ash", "echo", "fable", "onyx"],
    "female_openai": ["coral", "nova", "sage", "shimmer"]
}

class SpeechServiceProvider:
    def __init__(self, config: SpeechConfig, main_logger):
        self._config = config
        self.main_logger = main_logger
        self.voice_engine = self._get_voice_engine(config, main_logger)
        
        # Semaphores for limiting concurrent requests
        self.tts_semaphore = asyncio.Semaphore(10)
        self.stt_semaphore = asyncio.Semaphore(10)

    async def say(self, websocket_connection_manager, user_id: str, text: str, voice_name: str) -> SpeechResult:
        """Convert text to speech with concurrency control"""
        async with self.tts_semaphore:
            return await self.voice_engine.say_from_text(
                websocket_connection_manager, user_id, text, voice_name
            )

    async def understand(self, user_id: str, audio_data: str) -> SpeechResult:
        """Convert speech to text with concurrency control"""
        async with self.stt_semaphore:
            return await self.voice_engine.understand_speech(audio_data, user_id)

    @staticmethod
    def _get_voice_engine(config: SpeechConfig, main_logger):
        """Factory method to create appropriate voice engine"""
        providers = {
            "eleven_labs": ElevenLabsTTS,
            "openai": OPENAI,
            "google": GoogleSpeechToText,
            "groq": GroqSpeechToText,
        }
        
        provider_class = providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Invalid TTS provider: {config.provider}")
            
        return provider_class(config, main_logger)

    def get_available_voices(self, provider: str, gender:str, region:str) -> List[str]:
        """Get available voices for a provider based on gender and country"""
        if provider == "eleven_labs":
            if gender == "male":
                return VOICE_CATEGORIES["male_us"] if region == "us" else VOICE_CATEGORIES["male_indian"]
            elif gender == "female":
                return VOICE_CATEGORIES["female_us"] if region == "us" else VOICE_CATEGORIES["female_indian"]
            else:
                return []
        elif provider == "openai":
            if gender == "male":
                return VOICE_CATEGORIES["male_openai"]
            elif gender == "female":
                return VOICE_CATEGORIES["female_openai"]
            else:
                return []
        else:
            return []