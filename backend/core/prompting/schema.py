import enum

from pydantic import BaseModel

from core.resource.model_providers.schema import ChatMessage


class LanguageModelClassification(str, enum.Enum):
    FAST_MODEL = "fast_model"
    SMART_MODEL = "smart_model"


class ChatPrompt(BaseModel):
    messages: list[ChatMessage]

    def raw(self):
        return list(self.messages)
