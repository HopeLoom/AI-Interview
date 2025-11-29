import os

import requests
from openai import OpenAI
from pydantic import BaseModel

from core.image_generator.base import ImageBase


class Text2ImageConfig(BaseModel):
    provider: str = "openai"
    api_key: str = ("",)
    data_dir: str = ""


class OPENAI(ImageBase):
    def __init__(self, config: Text2ImageConfig):
        super().__init__(config)

    def _setup(self, config: Text2ImageConfig):
        self._api_key = config.api_key
        self._client = OpenAI(api_key=self._api_key)
        self.data_dir = config.data_dir

    async def _text_to_image(self, text: str, filename):
        # response = self._client.images.generate(
        #     model="dall-e-2",
        #     prompt=text,
        #     size="256x256",                     # smallest size
        #     quality="standard",
        #     n=1,
        # )

        response = self._client.images.generate(
            model="dall-e-3",
            prompt=text,
            size="1024x1024",  # smallest size
            quality="hd",
            n=1,
        )

        url = response.data[0].url
        response = requests.get(url)
        data_dir = os.path.join(self.data_dir, filename)

        with open(data_dir, "wb") as f:
            f.write(response.content)

        return data_dir
