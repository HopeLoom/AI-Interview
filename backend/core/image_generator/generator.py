import os 
import threading 
from pydantic import BaseModel
from core.image_generator.openai import OPENAI, Text2ImageConfig


class TextToImageProvider:
    thread = None
    lock = threading.Lock()  # Class-level lock for thread-safe access

    def __init__(self, config:Text2ImageConfig):
        self._config = config
        self.image_engine = self._get_image_engine(config)
        
    async def generate_image(self, text:str, filename):
           
        with TextToImageProvider.lock:  # Acquire lock for thread-safe check
            print ("Thread is started inside generate_image")
            #self.thread = threading.Thread(target=_speak)
            #self.thread.start()
            success = await self.image_engine.generate_image(text, filename)
            return success

    @staticmethod
    def _get_image_engine(config:Text2ImageConfig):
        image_engine = OPENAI(config)
        return image_engine