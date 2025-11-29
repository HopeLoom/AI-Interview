import abc
import enum
import json
import traceback
from typing import Callable, ClassVar, Generic, Optional, TypeVar

import httpx
import openai
import tiktoken
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.prompting.schema import ChatPrompt
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelInfo,
    ChatModelProvider,
    ChatModelResponse,
    EmbeddingModelProvider,
    EmbeddingModelResponse,
    ModelProviderConfiguration,
    ModelProviderCredentials,
    ModelProviderName,
    ModelProviderService,
    SystemSettings,
)

# Constants
RETRY_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 2

# Define which exceptions are retryable
RETRYABLE_ERRORS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    openai.RateLimitError,
    openai.APIError,
    openai.APIConnectionError,
)

# Token counting constants
TOKEN_COUNTING_CONFIG = {
    "gpt-3": {"tokens_per_message": 4, "tokens_per_names": -1, "encoding_model": "gpt-3.5-turbo"},
    "gpt-4": {"tokens_per_message": 3, "tokens_per_names": 1, "encoding_model": "gpt-4"},
}


class OpenAIModelName(str, enum.Enum):
    GPT4O_MINI = "gpt-4o-mini"
    GPT_5 = "gpt-5"
    GPT4O = "gpt-4o"
    O4_MINI = "o4-mini"


# Pre-compute model info to avoid repeated object creation
OPENAI_CHAT_MODELS = {
    OpenAIModelName.GPT4O_MINI: ChatModelInfo(
        name=OpenAIModelName.GPT4O_MINI,
        service=ModelProviderService.CHAT,
        provider_name=ModelProviderName.OPENAI,
        max_tokens=50000,
        has_function_call_api=True,
        completion_token_cost=0.03 / 1000,
        prompt_token_cost=0.01 / 1000,
    ),
    OpenAIModelName.GPT4O: ChatModelInfo(
        name=OpenAIModelName.GPT4O,
        service=ModelProviderService.CHAT,
        provider_name=ModelProviderName.OPENAI,
        max_tokens=50000,
        has_function_call_api=True,
        completion_token_cost=0.03 / 1000,
        prompt_token_cost=0.01 / 1000,
    ),
    OpenAIModelName.GPT_5: ChatModelInfo(
        name=OpenAIModelName.GPT_5,
        service=ModelProviderService.CHAT,
        provider_name=ModelProviderName.OPENAI,
        max_tokens=50000,
        has_function_call_api=True,
        completion_token_cost=0.03 / 1000,
        prompt_token_cost=0.01 / 1000,
    ),
    OpenAIModelName.O4_MINI: ChatModelInfo(
        name=OpenAIModelName.O4_MINI,
        service=ModelProviderService.CHAT,
        provider_name=ModelProviderName.OPENAI,
        max_tokens=50000,
        has_function_call_api=True,
        completion_token_cost=0.03 / 1000,
        prompt_token_cost=0.01 / 1000,
    ),
}


class OpenAIConfiguration(ModelProviderConfiguration):
    fix_failed_tries: int = 3


class OpenAICredentials(ModelProviderCredentials):
    api_key: str = ""
    api_type: str = ""
    organization: str = ""


class OpenAISettings(SystemSettings):
    configuration: OpenAIConfiguration
    credentials: Optional[OpenAICredentials]
    warning_token_threshold: float = 0.75


S = TypeVar("S", bound=SystemSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: ClassVar[S]


class OpenAIProvider(Configurable[OpenAISettings], ChatModelProvider, EmbeddingModelProvider):
    default_settings = OpenAISettings(
        name=OpenAIModelName.GPT4O_MINI,
        description="OpenAI model provider",
        configuration=OpenAIConfiguration(retries_per_request=10, fix_failed_tries=3),
        credentials=None,
    )

    def __init__(self, settings: Optional[OpenAISettings] = None):
        self.settings = settings or self.default_settings
        self._configuration = self.settings.configuration
        self._credentials = self.settings.credentials
        self._client = AsyncOpenAI(api_key=self._credentials.api_key)

        # Cache tokenizers for better performance
        self._tokenizer_cache = {}

    def get_token_limit(self, model_name: str) -> int:
        return OPENAI_CHAT_MODELS[model_name].max_tokens

    def get_tokenizer(self, model_name: str):
        if model_name not in self._tokenizer_cache:
            self._tokenizer_cache[model_name] = tiktoken.encoding_for_model(model_name)
        return self._tokenizer_cache[model_name]

    def count_tokens(self, text: str, model_name: str) -> int:
        encoding_model_name = "gpt-4" if model_name.startswith("gpt-4") else "gpt-3.5-turbo"
        encoder = self.get_tokenizer(encoding_model_name)
        return len(encoder.encode(text))

    def count_message_tokens(self, messages, model_name: str) -> int:
        if isinstance(messages, ChatMessage):
            messages = [messages]

        # Determine model type for token counting
        if model_name.startswith("gpt-3"):
            config = TOKEN_COUNTING_CONFIG["gpt-3"]
        elif model_name.startswith("gpt-4"):
            config = TOKEN_COUNTING_CONFIG["gpt-4"]
        else:
            raise ValueError(f"Unknown model name {model_name}")

        try:
            encoder = tiktoken.encoding_for_model(config["encoding_model"])
        except KeyError:
            encoder = tiktoken.get_encoding("cl110k_base")

        num_tokens = sum(
            config["tokens_per_message"] + len(encoder.encode(message.content))
            for message in messages
        )
        return num_tokens + 3

    def _get_embedding_args(self, model_name: str, **kwargs) -> dict:
        kwargs["model"] = model_name
        return kwargs

    _T = TypeVar("_T")

    async def create_chat_completion(
        self,
        chat_messages: ChatPrompt,
        model_name: OpenAIModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        is_json_mode: bool = True,
        **kwargs,
    ) -> ChatModelResponse:
        # Prepare response format
        if is_json_mode:
            response_format = {"type": "json_object"}
        else:
            response_format = None
        # Prepare API arguments
        api_kwargs = {"model": model_name, **kwargs}
        if response_format is not None:
            api_kwargs["response_format"] = response_format

        # Convert messages to OpenAI format
        openai_messages = [
            {"role": message.role, "content": message.content} for message in chat_messages.messages
        ]

        if model_name.startswith("gpt-5"):
            response = await self._create_response_completion_with_retry(
                openai_messages, api_kwargs
            )
        else:
            response = await self._create_chat_completion_with_retry(openai_messages, api_kwargs)

        # Make API call
        response, cost, t_input, t_output = await self._create_chat_completion(
            openai_messages, api_kwargs
        )

        # Handle response
        if response is None:
            assistant_msg = AssistantChatMessage(
                content=json.dumps({"error": "Failed to get response from model"}), role="assistant"
            )
        else:
            _assistant_msg = response.choices[0].message
            assistant_msg = AssistantChatMessage(
                content=_assistant_msg.content, role=_assistant_msg.role
            )

        parsed_result = (
            assistant_msg if completion_parser is None else completion_parser(assistant_msg)
        )

        return ChatModelResponse(
            response=AssistantChatMessage(content=assistant_msg.content),
            parsed_response=parsed_result,
            model_info=OPENAI_CHAT_MODELS[model_name],
            prompt_tokens_used=t_input,
            completion_tokens_used=t_output,
        )

    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_fixed(RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type(RETRYABLE_ERRORS),
        reraise=True,
    )
    async def _create_chat_completion_with_retry(self, messages: list, kwargs: dict):
        return await self._client.chat.completions.create(messages=messages, **kwargs)

    async def _create_response_completion_with_retry(self, messages: list, kwargs: dict):
        return await self._client.responses.create(input=messages, **kwargs)

    async def _create_chat_completion(self, messages: list, kwargs: dict):
        # Remove None response_format to avoid API errors
        if kwargs.get("response_format") is None:
            kwargs.pop("response_format", None)

        try:
            completion = await self._create_chat_completion_with_retry(messages, kwargs)

            prompt_tokens_used = getattr(completion.usage, "prompt_tokens", 0)
            completion_tokens_used = getattr(completion.usage, "completion_tokens", 0)
            cost = 0  # Optional: add your cost calculation logic

            return completion, cost, prompt_tokens_used, completion_tokens_used

        except openai.AuthenticationError as e:
            print(f"[Auth Error] Invalid API key: {e}")
        except openai.InternalServerError as e:
            print(f"[Bad Request] Payload error: {e}")
        except Exception as e:
            print(f"[Unhandled Error] {e}")
            traceback.print_exc()

        return None, 0, 0, 0

    async def _create_embedding_with_retry(self, text: str, **kwargs):
        return await self._client.embeddings.create(input=text, **kwargs)

    async def create_embedding(
        self, text: str, model_name: str, embedding_parser: Callable, **kwargs
    ) -> EmbeddingModelResponse:
        embedding_kwargs = self._get_embedding_args(model_name, **kwargs)
        response = await self._create_embedding_with_retry(text, **embedding_kwargs)

        return EmbeddingModelResponse(
            embedding=embedding_parser(response.data[0].embedding),
            model_info=model_name,
            prompt_tokens_used=response.usage.prompt_tokens,
            completion_tokens_used=0,
        )
