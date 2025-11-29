import abc 
from threading import Lock 

class ImageBase:
    _lock = Lock()
    def __init__(self, *args):
        
        self._url = None
        self._headers = None 
        self._api_key = None
        self._setup(*args)

    async def generate_image(self, text:str, filename):
        # preprocessing the text
        with self._lock:
            return await self._text_to_image(text, filename)
    
    @abc.abstractmethod
    def _setup(self, *args):
        pass

    @abc.abstractmethod
    async def _text_to_image(self, text, filename):
        pass