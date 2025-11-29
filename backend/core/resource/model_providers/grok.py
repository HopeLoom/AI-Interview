import enum
from typing import Callable, Optional

import tiktoken
from openai import AsyncOpenAI

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


class GrokModelName(str, enum.Enum):
    GROK2_LATEST: str = "grok-2-latest"
    GROK2: str = "grok-2"


GROK_CHAT_MODELS = {
    info.name: info
    for info in [
        ChatModelInfo(
            name=GrokModelName.GROK2_LATEST,
            service=ModelProviderService.CHAT,
            provider_name=ModelProviderName.GROK,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03 / 1000,
            prompt_token_cost=0.01 / 1000,
        ),
        ChatModelInfo(
            name=GrokModelName.GROK2,
            service=ModelProviderService.CHAT,
            provider_name=ModelProviderName.GROK,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03 / 1000,
            prompt_token_cost=0.01 / 1000,
        ),
    ]
}


class GrokConfiguration(ModelProviderConfiguration):
    fix_failed_tries: int = 3


class GrokCredentials(ModelProviderCredentials):
    api_key: str = ""
    api_type: str = ""
    organization: str = ""


class GrokSettings(SystemSettings):
    configuration: GrokConfiguration
    credentials: Optional[GrokCredentials]
    warning_token_threshold: float = 0.75
    # budget: ModelProviderBudget


import abc
import typing
from typing import Generic, TypeVar

S = TypeVar("S", bound=SystemSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]


class GrokProvider(Configurable[GrokSettings], ChatModelProvider):
    default_settings = GrokSettings(
        name=GrokModelName.GROK2_LATEST,
        description="Grok model provider",
        configuration=GrokConfiguration(retries_per_request=10, fix_failed_tries=3),
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
    _configuration: GrokConfiguration
    _credentials: GrokCredentials

    def __init__(self, settings):
        if not settings:
            settings = self.default_settings

        self.settings = settings

        # self._budget = settings.budget
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        # print ("Credentials: ", self._credentials.api_key)
        self._client = AsyncOpenAI(
            api_key=self._credentials.api_key, base_url="https://api.x.ai/v1"
        )

    def get_token_limit(self, model_name):
        return GROK_CHAT_MODELS[model_name].max_tokens

    def get_tokenizer(self, model_name):
        return tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text, model_name):
        encoding_model_name = "gpt-4" if model_name.startswith("grok") else "gpt-3.5-turbo"
        encoder = self.get_tokenizer(encoding_model_name)
        return len(encoder.encode(text))

    def count_message_tokens(self, messages, model_name):
        if isinstance(messages, ChatMessage):
            messages = [messages]

        if model_name.startswith("grok"):
            tokens_per_message = 4
            encoding_model = "gpt-3.5-turbo"
        elif model_name.startswith("grok2"):
            tokens_per_message = 3
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
        model_name: GrokModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        is_json_mode: bool = True,
        **kwargs,
    ):
        print("model_name: ", model_name)
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
            model_info=GROK_CHAT_MODELS[model_name],
            prompt_tokens_used=t_input,
            completion_tokens_used=t_output,
        )

    # This function calls the openai chat completion API
    async def _create_chat_completion(self, messages, kwargs):
        # if response format is not, then remove the keyword
        if kwargs.get("response_format") is None:
            kwargs.pop("response_format")

        async def _create_chat_completion_with_retry(messages, kwargs):
            print("create_chat_completion_with_retry")
            return await self._client.chat.completions.create(messages=messages, **kwargs)

        completion = await _create_chat_completion_with_retry(messages, kwargs)

        # print ("Completion: ", completion)

        if completion.usage:
            prompt_tokens_used = completion.usage.prompt_tokens
            completion_tokens_used = completion.usage.completion_tokens
        else:
            prompt_tokens_used = 0
            completion_tokens_used = 0

        # update cost
        cost = 0

        return completion, cost, prompt_tokens_used, completion_tokens_used
