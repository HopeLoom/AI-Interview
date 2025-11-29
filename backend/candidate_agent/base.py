import abc
import enum
import typing
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from core.prompting.base import BaseCandidatePromptStrategy
from core.prompting.schema import ChatPrompt
from core.resource.model_providers.openai import OPENAI_CHAT_MODELS, OpenAIModelName
from core.resource.model_providers.schema import ChatModelInfo, ChatModelProvider, SystemSettings
from panelist_agent.base import Profile

S = TypeVar("S", bound=SystemSettings)


class INTELLIGENCE_LEVELS(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class INTENSITY_LEVELS(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CandidateSettings(BaseModel):
    fast_llm: OpenAIModelName = OpenAIModelName.GPT4O_MINI
    slow_llm: OpenAIModelName = OpenAIModelName.GPT4O
    default_cycle_instruction: str = ""
    big_brain: bool = False
    cycle_budget: int = 0
    cycles_remaining: float = 0


class ActionTypes(str, enum.Enum):
    RESPOND = "respond"
    IGNORE = "ignore"
    SILENT = "silent"


class BaseCandidateConfiguration(BaseModel):
    candidate_id: str = ""
    profile: Profile = Profile()
    settings: CandidateSettings = Field(default_factory=CandidateSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]


class BaseCandidate(Configurable[BaseCandidateConfiguration], ABC):
    # base agent consists of the following:
    # settings: This would consist of name, id, profile, what task to do, budget etc
    # provider: This would consist of two methods: counting tokens and chat completion api
    # Prompt strategy: This would consist of building prompt and parsing response content
    # Base Agent consists of common methods that are used by all agents

    def __init__(
        self,
        user_config: BaseCandidateConfiguration,
        llm_provider: ChatModelProvider,
        prompt_strategy: BaseCandidatePromptStrategy,
    ):
        super().__init__()

        self.config = user_config.settings
        self.llm_provider = llm_provider
        self.prompt_strategy = prompt_strategy

    def get_llm_info(self) -> ChatModelInfo:
        llm_name = self.config.slow_llm
        return OPENAI_CHAT_MODELS[llm_name]

    def build_prompt(self, **kwargs):
        prompt = self.prompt_strategy.build_prompt(**kwargs)
        return prompt

    async def run_decision_model(self, prompt):
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.get_llm_info().name,
            completion_parser=lambda r: self.parse_process_decision_model(r, prompt),
            is_json_mode=True,
        )
        return response.parsed_response

    async def think(self, prompt: ChatPrompt):
        response = await self.run_decision_model(prompt)
        return response

    @abstractmethod
    def parse_process_decision_model(self, response, prompt):
        pass
