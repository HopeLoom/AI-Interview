import abc
import typing
from abc import ABC, abstractmethod
from resource.model_providers.openai import OPENAI_CHAT_MODELS, OpenAIModelName
from resource.model_providers.schema import (
    ChatMessage,
    ChatModelInfo,
    ChatModelProvider,
    SystemSettings,
)
from typing import Any, Generic, List, TypeVar

from activity.base import (
    ActivityCodeGenerationOutputMessage,
    ActivityDetailsOutputMessage,
    BaseActivityConfiguration,
)
from interview.base import CharacterData
from pydantic import BaseModel, Field

from core.prompting.base import DiscussionPromptStrategy

S = TypeVar("S", bound=SystemSettings)


class DiscussionSettings(BaseModel):
    fast_llm: OpenAIModelName = OpenAIModelName.GPT4O
    slow_llm: OpenAIModelName = OpenAIModelName.GPT4O
    big_brain: bool = True


class FeedbackOutput(BaseModel):
    feedback_info: str = ""
    feedback_type: str = ""


class FeedbackInput(BaseModel):
    activity_data: BaseActivityConfiguration = BaseActivityConfiguration()
    character_data: CharacterData = CharacterData()
    previous_feedback: List[FeedbackOutput] = Field(default_factory=list)
    isCode: bool = False


class ConsensusInput(BaseModel):
    activity_data: BaseActivityConfiguration = BaseActivityConfiguration()
    feedbackData: List[str] = Field(default_factory=list)


class ConsensusOutput(BaseModel):
    consensus_info: str = ""
    consensus_type: str = ""
    consensus_reason: str = ""


class ActivityDetailsInputMessage(BaseModel):
    activity_data: BaseActivityConfiguration = BaseActivityConfiguration()
    consensus_output: ConsensusOutput = ConsensusOutput()


class ActivityCodeInputMessage(BaseModel):
    activity_data: BaseActivityConfiguration = BaseActivityConfiguration()
    consensus_output: ConsensusOutput = ConsensusOutput()


class BaseDiscussionConfiguration(BaseModel):
    discussion_id: str = ""
    settings: DiscussionSettings = Field(default_factory=DiscussionSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]


class BaseDiscussion(Configurable[BaseDiscussionConfiguration], ABC):
    # base agent consists of the following:
    # settings: This would consist of name, id, profile, what task to do, budget etc
    # provider: This would consist of two methods: counting tokens and chat completion api
    # Prompt strategy: This would consist of building prompt and parsing response content
    # Base Agent consists of common methods that are used by all agents

    llm_provider: Any = None
    prompt_strategy: Any = None
    discussion_id: str = ""
    config: Any = None

    def __init__(
        self,
        discussion_id: str,
        discussion_config: BaseDiscussionConfiguration,
        llm_provider: ChatModelProvider,
        prompt_strategy: DiscussionPromptStrategy,
    ):
        super(BaseDiscussion, self).__init__()

        self.config: DiscussionSettings = discussion_config.settings
        self.llm_provider = llm_provider
        self.prompt_strategy = prompt_strategy
        self.discussion_id = discussion_id

    def get_llm_info(self) -> ChatModelInfo:
        llm_name = self.config.fast_llm if self.config.big_brain else self.config.slow_llm
        return OPENAI_CHAT_MODELS[llm_name]

    def build_prompt(self, **kwargs):
        # this returns a chat prompt which is a list of messages
        prompt = self.prompt_strategy.build_prompt(**kwargs)
        return prompt

    async def run_model(self, prompt, response_type):
        if response_type == DiscussionPromptStrategy.RESPONSE_TYPE.FEEDBACK_INFO:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.get_llm_info().name,
                completion_parser=lambda r: self.parse_and_process_response_feedback_info(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_INFO:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.get_llm_info().name,
                completion_parser=lambda r: self.parse_and_process_response_activity_info(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_CODE_INFO:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.get_llm_info().name,
                completion_parser=lambda r: self.parse_and_process_response_activity_code_info(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.CONSENSUS_INFO:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.get_llm_info().name,
                completion_parser=lambda r: self.parse_and_process_response_consensus_info(
                    r, prompt
                ),
                is_json_mode=True,
            )

        return response.parsed_response

    async def get_feedback_information(self, prompt: ChatMessage) -> FeedbackOutput:
        response = await self.run_model(
            prompt, DiscussionPromptStrategy.RESPONSE_TYPE.FEEDBACK_INFO
        )
        return response

    async def get_activity_details(self, prompt: ChatMessage) -> ActivityDetailsOutputMessage:
        response = await self.run_model(
            prompt, DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_INFO
        )
        return response

    async def get_activity_code_details(
        self, prompt: ChatMessage
    ) -> ActivityCodeGenerationOutputMessage:
        response = await self.run_model(
            prompt, DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_CODE_INFO
        )
        return response

    async def get_consensus_details(self, prompt: ChatMessage) -> ConsensusOutput:
        response = await self.run_model(
            prompt, DiscussionPromptStrategy.RESPONSE_TYPE.CONSENSUS_INFO
        )
        return response

    @abstractmethod
    def parse_and_process_response_feedback_info(self, response, prompt):
        pass

    @abstractmethod
    def parse_and_process_response_activity_info(self, response, prompt):
        pass

    @abstractmethod
    def parse_and_process_response_activity_code_info(self, response, prompt):
        pass

    @abstractmethod
    def parse_and_process_response_consensus_info(self, response, prompt):
        pass
