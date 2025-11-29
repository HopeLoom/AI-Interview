
from pydantic import BaseModel

from core.resource.model_providers.schema import (
    ChatMessage,
    ReasoningChatMessage,
    ReflectionChatMessage,
)


class SimpleMemory(BaseModel):
    conversation_memory: list[ChatMessage] = []
    reflection_memory: list[ReflectionChatMessage] = []
    reasoning_memory: list[ReasoningChatMessage] = []

    def add_to_memory(self, item: ChatMessage):
        self.conversation_memory.append(item)

    def add_reasoning_to_memory(self, item: ReasoningChatMessage):
        self.reasoning_memory.append(item)

    def add_reflection_to_memory(self, item: ReflectionChatMessage):
        self.reflection_memory.append(item)

    def recall_last_message(self):
        if self.conversation_memory:
            return self.conversation_memory[-1]
        else:
            return None

    def recall_last_reasoning(self):
        if self.reasoning_memory:
            return self.reasoning_memory[-1]
        else:
            return None

    def recall_reflection(self):
        if self.reflection_memory:
            return self.reflection_memory[-1]
        else:
            return None

    def clear(self):
        self.conversation_memory.clear()
        self.reflection_memory.clear()
        self.reasoning_memory.clear()

    def get_all_from_memory(self):
        return self.conversation_memory

    def get_all_reflection_from_memory(self):
        return self.reflection_memory

    def get_all_reasoning_from_memory(self):
        return self.reasoning_memory
