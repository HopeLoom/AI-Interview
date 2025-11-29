import abc
import enum
import typing
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from core.prompting.base import BasePanelistPromptStrategy
from core.prompting.schema import ChatPrompt
from core.resource.model_providers.deepseek import DeepSeekModelNames
from core.resource.model_providers.gemini import GeminiModelName
from core.resource.model_providers.grok import GrokModelName
from core.resource.model_providers.groq import GroqModelName
from core.resource.model_providers.openai import OPENAI_CHAT_MODELS, OpenAIModelName
from core.resource.model_providers.schema import (
    ChatModelInfo,
    ChatModelProvider,
    ChatModelResponse,
    ReflectionChatMessage,
    SystemSettings,
)
from panelist_agent.background import (
    Background,
    CurrentOccupation,
    Education,
    Experience,
    Projects,
    Skills,
)
from panelist_agent.personality import Personality

# Constants
DEFAULT_SCORE = 0.0
DEFAULT_BUDGET = 0
DEFAULT_AGE = 0
DEFAULT_BIO = "John is a software engineer with 5 years of experience"

S = TypeVar("S", bound=SystemSettings)


class INTENSITY_LEVELS(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def get_intensity_value(cls, level: str) -> str:
        """Get intensity value with validation"""
        try:
            return cls(level.lower()).value
        except ValueError:
            return cls.LOW.value


class PanelistSettings(BaseModel):
    model_config = {"validate_assignment": True, "extra": "forbid", "frozen": False}

    gpt_4o_mini: str = OpenAIModelName.GPT4O_MINI
    gpt_4o: str = OpenAIModelName.GPT4O
    gemini_fast_llm: str = GeminiModelName.GEMINI_2_FLASH
    gemini_slow_llm: str = GeminiModelName.GEMINI_1_5_PRO
    groq_llama_llm: str = GroqModelName.LLAMA4MAVERICK
    groq_mistral_llm: str = GroqModelName.LLAMA4SCOUT
    groq_qwen_llm: str = GroqModelName.QWEN
    grok_llm: str = GrokModelName.GROK2
    deepseek_llm: str = DeepSeekModelNames.DEEPSEEKCHAT
    big_brain: bool = True
    budget: int = DEFAULT_BUDGET


class Profile(BaseModel):
    model_config = {"validate_assignment": True, "extra": "forbid", "frozen": False}

    background: Background = Field(
        default_factory=lambda: Background(
            name="John",
            gender="",
            age=DEFAULT_AGE,
            bio=DEFAULT_BIO,
            current_occupation=CurrentOccupation(),
            education=[Education()],
            experience=[Experience()],
            skills=[Skills()],
            projects=[Projects()],
        )
    )

    personality: Personality = Field(
        default_factory=lambda: Personality(
            openness={INTENSITY_LEVELS.LOW: "Is introvert and doesn't interact much with people"},
            conscientiousness={INTENSITY_LEVELS.HIGH: "Lot of self reflection"},
            extraversion={INTENSITY_LEVELS.LOW: ""},
            agreeableness={INTENSITY_LEVELS.MEDIUM: "somewhat agrees with people"},
            neuroticism={INTENSITY_LEVELS.LOW: ""},
        )
    )

    interview_round_part_of: str = Field(
        default="", description="Interview round this panelist belongs to"
    )
    character_id: str = Field(default="", description="Unique character identifier")


class BasePanelistConfiguration(SystemSettings):
    id: str = Field(default="", description="Configuration identifier")
    profile: Profile = Field(default_factory=Profile, description="Panelist profile")
    settings: PanelistSettings = Field(
        default_factory=PanelistSettings, description="Panelist settings"
    )


class ResponseOutputMessage(BaseModel):
    response: str = Field(default="", description="Generated response")


class ResponseWithReasoningOutputMessage(BaseModel):
    interview_thoughts_for_myself: str = Field(default="", description="Internal thoughts")
    should_i_ask_a_new_question: bool = Field(
        default=False, description="Whether to ask new question"
    )
    are_my_questions_too_repetitive: bool = Field(
        default=False, description="Repetitive questions flag"
    )
    areas_to_cover_in_next_response: list[str] = Field(
        default_factory=list, description="Areas to cover"
    )
    facts_corresponding_to_areas_to_cover_in_next_response: list[str] = Field(
        default_factory=list, description="Facts for areas"
    )
    areas_already_covered: list[str] = Field(
        default_factory=list, description="Already covered areas"
    )
    response: str = Field(default="", description="Generated response")


class DomainKnowledgeOutputMessage(BaseModel):
    topic: str = Field(default="", description="Domain topic")
    explanation: str = Field(default="", description="Topic explanation")
    relevance_to_conversation: str = Field(
        default="", description="Relevance to current conversation"
    )


class ReasoningOutputMessage(BaseModel):
    interview_thoughts_for_myself: str = Field(default="", description="Internal thoughts")
    should_i_ask_a_new_question: bool = Field(
        default=False, description="Whether to ask new question"
    )
    are_my_questions_too_repetitive: bool = Field(
        default=False, description="Repetitive questions flag"
    )
    areas_to_cover_in_next_response: list[str] = Field(
        default_factory=list, description="Areas to cover"
    )
    facts_corresponding_to_areas_to_cover_in_next_response: list[str] = Field(
        default_factory=list, description="Facts for areas"
    )
    areas_already_covered: list[str] = Field(
        default_factory=list, description="Already covered areas"
    )
    is_domain_knowledge_access_needed: bool = Field(
        default=False, description="Domain knowledge needed"
    )


class ReflectionOutputMessage(BaseModel):
    character_name: str = Field(default="", description="Character name")
    reflection: str = Field(default="", description="Reflection content")


class CriteriaSpecificScoring(BaseModel):
    criteria: str = Field(default="", description="Evaluation criteria")
    score: float = Field(default=DEFAULT_SCORE, ge=0, le=100, description="Criteria score")
    reason: str = Field(default="", description="Scoring reason")
    key_phrases_from_conversation: list[str] = Field(
        default_factory=list, description="Key phrases from conversation"
    )


class EvaluationOutputMessage(BaseModel):
    feedback_to_the_hiring_manager_about_candidate: str = Field(
        default="", description="Feedback for hiring manager"
    )
    score: float = Field(
        default=DEFAULT_SCORE, ge=0, le=100, description="Overall evaluation score"
    )


class PromptInput(BaseModel):
    response_type: BasePanelistPromptStrategy.RESPONSE_TYPE = Field(
        default=BasePanelistPromptStrategy.RESPONSE_TYPE.REASON, description="Response type"
    )
    candidate_profile: Profile = Field(default_factory=Profile, description="Candidate profile")
    message: Any = Field(default=None, description="Input message")
    activity_progress: Any = Field(default=None, description="Activity progress")
    subqueries_data: Any = Field(default=None, description="Subqueries data")
    activity_code_from_candidate: str = Field(
        default="", description="Activity code from candidate"
    )
    reason: ReasoningOutputMessage = Field(
        default_factory=ReasoningOutputMessage, description="Reasoning output"
    )
    domain_knowledge: DomainKnowledgeOutputMessage = Field(
        default_factory=DomainKnowledgeOutputMessage, description="Domain knowledge"
    )
    reflection_history: list[ReflectionChatMessage] = Field(
        default_factory=list, description="Reflection history"
    )


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[BasePanelistConfiguration]


class BasePanelist(Configurable[BasePanelistConfiguration], ABC):
    """Base class for all panelist agents."""

    def __init__(
        self,
        config: BasePanelistConfiguration,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        grok_provider: ChatModelProvider,
        deepseek_provider: ChatModelProvider,
        prompt_strategy: BasePanelistPromptStrategy,
    ):
        super().__init__()

        self.settings = config.settings
        self.llm_provider = llm_provider
        self.gemini_provider = gemini_provider
        self.groq_provider = groq_provider
        self.grok_provider = grok_provider
        self.deepseek_provider = deepseek_provider
        self.prompt_strategy = prompt_strategy

    def get_llm_info(self) -> ChatModelInfo:
        """Get LLM information with caching"""
        llm_name = self.settings.gpt_4o_mini
        return OPENAI_CHAT_MODELS[llm_name]

    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        """Build prompt using the prompt strategy"""
        return self.prompt_strategy.build_prompt(prompt_input)

    async def run_model_with_schema(
        self, prompt: ChatPrompt, model_name: str, parser_method, json_schema: dict, provider=None
    ) -> Any:
        """Generic method to run any model with JSON schema and error handling"""
        try:
            if provider is None:
                provider = self.llm_provider

            response = await provider.create_chat_completion(
                chat_messages=prompt,
                model_name=model_name,
                completion_parser=lambda r: parser_method(r, prompt),
                is_json_mode=True,
            )
            return response.parsed_response
        except Exception as e:
            # Log error or handle gracefully
            raise RuntimeError(f"Failed to run model {model_name}: {e}")

    async def run_response_model(self, prompt: ChatPrompt) -> ResponseOutputMessage:
        """Run response model with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.gpt_4o_mini,
            parser_method=self.parse_process_response_model,
            json_schema=ResponseOutputMessage.model_json_schema(),
        )

    async def run_reasoning_model(self, prompt: ChatPrompt) -> ReasoningOutputMessage:
        """Run reasoning model with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.gpt_4o,
            parser_method=self.parse_process_reason_model,
            json_schema=ReasoningOutputMessage.model_json_schema(),
        )

    async def run_reflection_model(self, prompt: ChatPrompt) -> ReflectionOutputMessage:
        """Run reflection model with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.deepseek_llm,
            parser_method=self.parse_process_reflect_model,
            json_schema=ReflectionOutputMessage.model_json_schema(),
            provider=self.deepseek_provider,
        )

    async def run_evaluation_model(self, prompt: ChatPrompt) -> EvaluationOutputMessage:
        """Run evaluation model with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.gpt_4o,
            parser_method=self.parse_process_evaluate_model,
            json_schema=EvaluationOutputMessage.model_json_schema(),
        )

    async def run_domain_knowledge_model(self, prompt: ChatPrompt) -> DomainKnowledgeOutputMessage:
        """Run domain knowledge model with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.gpt_4o,
            parser_method=self.parse_process_domain_knowledge_model,
            json_schema=DomainKnowledgeOutputMessage.model_json_schema(),
        )

    async def respond(self, prompt: ChatPrompt) -> ResponseOutputMessage:
        """Generate response"""
        return await self.run_response_model(prompt)

    async def respond_with_reasoning(
        self, prompt: ChatPrompt
    ) -> ResponseWithReasoningOutputMessage:
        """Generate response with reasoning"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.settings.gpt_4o,
            parser_method=self.parse_process_respond_with_reasoning_model,
            json_schema=ResponseWithReasoningOutputMessage.model_json_schema(),
        )

    async def reason(self, prompt: ChatPrompt) -> ReasoningOutputMessage:
        """Generate reasoning"""
        return await self.run_reasoning_model(prompt)

    async def reflect(self, prompt: ChatPrompt) -> ReflectionOutputMessage:
        """Generate reflection"""
        return await self.run_reflection_model(prompt)

    async def evaluate(self, prompt: ChatPrompt) -> EvaluationOutputMessage:
        """Generate evaluation"""
        return await self.run_evaluation_model(prompt)

    async def get_domain_knowledge(self, prompt: ChatPrompt) -> DomainKnowledgeOutputMessage:
        """Get domain knowledge"""
        return await self.run_domain_knowledge_model(prompt)

    def validate_configuration(self) -> bool:
        """Validate the panelist configuration"""
        try:
            if not self.settings:
                return False
            if not hasattr(self, "llm_provider"):
                return False
            return hasattr(self, "prompt_strategy")
        except Exception:
            return False

    @abstractmethod
    def parse_process_reason_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> ReasoningOutputMessage:
        """Parse reasoning model response"""
        pass

    @abstractmethod
    def parse_process_evaluate_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> EvaluationOutputMessage:
        """Parse evaluation model response"""
        pass

    @abstractmethod
    def parse_process_response_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> ResponseOutputMessage:
        """Parse response model response"""
        pass

    @abstractmethod
    def parse_process_reflect_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> ReflectionOutputMessage:
        """Parse reflection model response"""
        pass

    @abstractmethod
    def parse_process_domain_knowledge_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> DomainKnowledgeOutputMessage:
        """Parse domain knowledge model response"""
        pass

    @abstractmethod
    def parse_process_respond_with_reasoning_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> ResponseWithReasoningOutputMessage:
        """Parse respond with reasoning model response"""
        pass
