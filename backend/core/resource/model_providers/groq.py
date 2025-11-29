import abc
import enum
import json
import traceback
import typing
from typing import Callable, Generic, Optional, TypeVar

import httpx
import openai
import tiktoken
from groq import AsyncGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.prompting.schema import ChatPrompt
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelInfo,
    ChatModelProvider,
    ChatModelResponse,
    ModelProviderConfiguration,
    ModelProviderCredentials,
    ModelProviderName,
    ModelProviderService,
    SystemSettings,
)

# You can customize these as needed
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


class GroqModelName(str, enum.Enum):
    LLAMA4MAVERICK: str = "meta-llama/llama-4-maverick-17b-128e-instruct"
    QWEN: str = "qwen-2.5-coder-32b"
    LLAMA4SCOUT: str = "meta-llama/llama-4-scout-17b-16e-instruct"


GROQ_CHAT_MODELS = {
    info.name: info
    for info in [
        ChatModelInfo(
            name=GroqModelName.LLAMA4MAVERICK,
            service=ModelProviderService.CHAT,
            provider_name=ModelProviderName.GROQ,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03 / 1000,
            prompt_token_cost=0.01 / 1000,
        ),
        ChatModelInfo(
            name=GroqModelName.LLAMA4SCOUT,
            service=ModelProviderService.CHAT,
            provider_name=ModelProviderName.GROQ,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03 / 1000,
            prompt_token_cost=0.01 / 1000,
        ),
        ChatModelInfo(
            name=GroqModelName.QWEN,
            service=ModelProviderService.CHAT,
            provider_name=ModelProviderName.GROQ,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03 / 1000,
            prompt_token_cost=0.01 / 1000,
        ),
    ]
}


class GROQConfiguration(ModelProviderConfiguration):
    fix_failed_tries: int = 3


class GroqCredentials(ModelProviderCredentials):
    api_key: str = ""
    api_type: str = ""
    organization: str = ""


class GROQAISettings(SystemSettings):
    configuration: GROQConfiguration
    credentials: Optional[GroqCredentials]
    warning_token_threshold: float = 0.75
    # budget: ModelProviderBudget


S = TypeVar("S", bound=SystemSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]


class GroqProvider(Configurable[GROQAISettings], ChatModelProvider):
    default_settings = GROQAISettings(
        name=GroqModelName.QWEN,
        description="groq model provider",
        configuration=GROQConfiguration(retries_per_request=10, fix_failed_tries=3),
        credentials=None,
    )
    """
        budget = ModelProviderBudget(
            total_budget=10,
            total_cost=0,
            remaining_budget=10,
            usage = ModelProviderUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0
            )

        )
    """
    # _budget: ModelProviderBudget
    _configuration: GROQConfiguration
    _credentials: GroqCredentials

    def __init__(self, settings):
        if not settings:
            settings = self.default_settings

        self.settings = settings

        # self._budget = settings.budget
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        # print ("Credentials: ", self._credentials.api_key)
        self._client = AsyncGroq(api_key=self._credentials.api_key)

    def get_token_limit(self, model_name):
        return GROQ_CHAT_MODELS[model_name].max_tokens

    def get_tokenizer(self, model_name):
        return tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text, model_name):
        encoding_model_name = "gpt-4" if model_name.startswith("gpt-4") else "gpt-3.5-turbo"
        encoder = self.get_tokenizer(encoding_model_name)
        return len(encoder.encode(text))

    def count_message_tokens(self, messages, model_name):
        if isinstance(messages, ChatMessage):
            messages = [messages]
            tokens_per_message = 4
            encoding_model = "gpt-4"

        else:
            raise ValueError(f"Unknown model name {model_name}")

        try:
            encoder = tiktoken.encoding_for_model(encoding_model)
        except KeyError:
            encoder = tiktoken.get_encoding("cl110k_base")

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            content = message.content
            num_tokens += len(encoder.encode(content))
        num_tokens += 3
        return num_tokens

    def _get_embedding_args(self, model_name, **kwargs):
        kwargs["model"] = model_name
        return kwargs

    _T = TypeVar("_T")

    async def create_chat_completion(
        self,
        chat_messages: ChatPrompt,
        model_name: GroqModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        is_json_mode: bool = True,
        **kwargs,
    ):
        response_format = {"type": "json_object"} if is_json_mode else None

        total_cost = 0

        # combine model_name and response_format into keyword arguments

        kwargs = {"response_format": response_format, "model": model_name}
        # print ("model_prompt: ", chatmessages)

        openai_messages = []
        for message in chat_messages.messages:
            role = message.role
            content = message.content

            openai_messages.append({"role": role, "content": content})

        _response, _cost, t_input, t_output = await self._create_chat_completion(
            openai_messages, kwargs
        )

        total_cost += _cost

        if _response is None:
            _assistant_msg = json.dumps({"error": "Failed to get response from model"})

            assistant_msg = AssistantChatMessage(content=_assistant_msg, role="assistant")

        else:
            _assistant_msg = _response.choices[0].message  ## get output from response

            assistant_msg = AssistantChatMessage(
                content=_assistant_msg.content, role=_assistant_msg.role
            )

        if completion_parser is None:
            parsed_result = assistant_msg
        else:
            parsed_result = completion_parser(assistant_msg)

        return ChatModelResponse(
            response=AssistantChatMessage(content=assistant_msg.content),
            parsed_response=parsed_result,
            model_info=GROQ_CHAT_MODELS[model_name],
            prompt_tokens_used=t_input,
            completion_tokens_used=t_output,
        )

    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_fixed(RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type(RETRYABLE_ERRORS),
        reraise=True,
    )
    async def _create_chat_completion_with_retry(self, messages, kwargs):
        return await self._client.chat.completions.create(messages=messages, **kwargs)

    # This function calls the openai chat completion API
    async def _create_chat_completion(self, messages, kwargs):
        if kwargs.get("response_format") is None:
            kwargs.pop("response_format")

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

        # Return fallback on error
        return None, 0, 0, 0
