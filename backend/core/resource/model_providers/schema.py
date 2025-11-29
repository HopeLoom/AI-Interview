import abc
import enum
from typing import Any, ClassVar, Literal, Optional, TypeVar

from pydantic import BaseModel


class ModelProviderService(str, enum.Enum):
    EMBEDDING = "embedding"
    CHAT = "chat_completion"
    TEXT = "text_completion"


class ModelProviderName(str, enum.Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    GROK = "grok"
    DEEPSEEK = "deepseek"
    Perplexity = "perplexity"


class ChatMessage(BaseModel):
    class Role(str, enum.Enum):
        USER = "user"
        SYSTEM = "system"
        ASSISTANT = "assistant"

    role: Role
    content: str

    @staticmethod
    def user(content: str) -> "ChatMessage":
        return ChatMessage(role=ChatMessage.Role.USER, content=content)

    @staticmethod
    def system(content: str) -> "ChatMessage":
        return ChatMessage(role=ChatMessage.Role.SYSTEM, content=content)

    @staticmethod
    def assistant(content: str) -> "ChatMessage":
        return ChatMessage(role=ChatMessage.Role.ASSISTANT, content=content)


class MasterChatMessage(BaseModel):
    speaker: str = ""
    content: str = ""


class ReflectionChatMessage(BaseModel):
    reflection: str
    character_name: str


class ReasoningChatMessage(BaseModel):
    interview_thoughts_for_myself: str


class AssistantChatMessage(ChatMessage):
    role: Literal["assistant"] = "assistant"
    content: Optional[str]


class ModelInfo(BaseModel):
    name: str
    service: ModelProviderService
    provider_name: ModelProviderName
    prompt_token_cost: float
    completion_token_cost: float


class ModelProviderUsage:
    completion_tokens = 0
    prompt_tokens = 0
    total_tokens = 0


class ModelProviderBudget:
    total_budget = 0
    total_cost = 0
    remaining_budget = 0
    usage: ModelProviderUsage


class ModelProviderConfiguration(BaseModel):
    retries_per_request: int = 3


class SystemSettings(BaseModel):
    name: str
    description: str


class ModelProviderCredentials(BaseModel):
    api_key: str
    api_type: str
    organization: str


class ModelProviderSettings(SystemSettings):
    # resource_type = None
    configuration: ModelProviderConfiguration
    # credentials: ModelProviderCredentials
    # budget = None


class ModelResponse(BaseModel):
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    model_info: ModelInfo


class ChatModelInfo(ModelInfo):
    llm_service: str = ModelProviderService.CHAT
    max_tokens: float = 0
    has_function_call_api: bool = False


_T = TypeVar("_T")


class ChatModelResponse(ModelResponse):
    response: AssistantChatMessage
    parsed_response: Any = None


class EmbeddingModelInfo(ModelInfo):
    llm_service: str = ModelProviderService.EMBEDDING
    max_tokens: float = 0
    embedding_dimension: int = 0


class EmbeddingModelResponse(ModelResponse):
    embedding: list[float]
    model_info: str
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0


class ModelProvider(abc.ABC):
    @abc.abstractmethod
    def count_tokens(self, text, model_name): ...

    @abc.abstractmethod
    def get_tokenizer(self, model_name): ...

    @abc.abstractmethod
    def get_token_limit(self, model_name): ...

    default_settings: ClassVar[ModelProviderSettings]

    # budget: ModelProviderBudget
    _configuration: ModelProviderConfiguration


class ChatModelProvider(ModelProvider):
    @abc.abstractmethod
    def count_message_tokens(self, messages, model_name) -> int: ...
    @abc.abstractmethod
    async def create_chat_completion(
        self, chat_messages, model_name, completion_parser, is_json_mode, **kwargs
    ) -> ChatModelResponse: ...


class EmbeddingModelProvider(ModelProvider):
    @abc.abstractmethod
    async def create_embedding(self, text, model_name, embedding_parser, **kwargs): ...
