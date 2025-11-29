import abc
import typing
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from activity_agent.base import ActivityProgressAnalysisSummaryForPanelistOutputMessage
from core.prompting.base import BaseEvaluationPromptStrategy
from core.resource.model_providers.gemini import GeminiModelName
from core.resource.model_providers.groq import GroqModelName
from core.resource.model_providers.openai import OPENAI_CHAT_MODELS, OpenAIModelName
from core.resource.model_providers.perplexity import PerplexityModelName
from core.resource.model_providers.schema import (
    ChatMessage,
    ChatModelInfo,
    ChatModelProvider,
    MasterChatMessage,
    SystemSettings,
)
from master_agent.base import (
    CriteriaSpecificScoring,
    Profile,
    QuestionSpecificEvaluationOutputMessage,
)

S = TypeVar("S", bound=SystemSettings)


class EvaluationSettings(BaseModel):
    fast_llm: str = OpenAIModelName.GPT4O_MINI
    slow_llm: str = OpenAIModelName.GPT4O
    gemini_fast_llm: str = GeminiModelName.GEMINI_2_FLASH
    gemini_slow_llm: str = GeminiModelName.GEMINI_1_5_PRO
    groq_llama_llm: str = GroqModelName.LLAMA4MAVERICK
    groq_mistral_llm: str = GroqModelName.LLAMA4SCOUT
    groq_qwen_llm: str = GroqModelName.QWEN
    perplexity_llm: str = PerplexityModelName.SONAR_PRO
    big_brain: bool = True


class BaseEvaluationConfiguration(SystemSettings):
    evaluation_name: str = ""
    settings: EvaluationSettings = EvaluationSettings()


class PromptInput(BaseModel):
    topic_time_remaining: float = 0
    remaining_subtopics: list[str] = Field(default_factory=list)
    response_type: BaseEvaluationPromptStrategy.RESPONSE_TYPE = (
        BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION
    )
    conversation_history_for_current_subtopic: list[MasterChatMessage] = Field(default_factory=list)
    last_completed_conversation_history: list[MasterChatMessage] = Field(default_factory=list)
    conversation_summary_for_current_topic: list[str] = Field(default_factory=list)
    conversation_summary_for_completed_topics: list[str] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    message: Any = None
    activity_analysis: Any = None
    activity_code_from_candidate: str = ""
    evaluation_output: QuestionSpecificEvaluationOutputMessage = (
        QuestionSpecificEvaluationOutputMessage()
    )


class SubqueryGeneratorInputMessage(BaseModel):
    panelists: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()


class SubqueryGeneratorOutputMessage(BaseModel):
    subqueries: list[str] = Field(default_factory=list)


class SubqueryDataExtractionInputMessage(BaseModel):
    subqueries: list[str] = Field(default_factory=list)


class SubqueryDataExtractionOutputMessage(BaseModel):
    subquery_names: list[str] = Field(default_factory=list)
    subquery_result: list[str] = Field(default_factory=list)


class CodeSummaryVisualizationInputMessage(BaseModel):
    code: str = ""
    activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
        ActivityProgressAnalysisSummaryForPanelistOutputMessage()
    )


class CriteriaVisualizationInputMessage(BaseModel):
    criteria_score_list: list[CriteriaSpecificScoring] = Field(default_factory=list)


class PanelistFeedbackVisualizationInputMessage(BaseModel):
    panelist_feedback: list[str] = Field(default_factory=list)
    panelist_names: list[str] = Field(default_factory=list)
    panelist_occupations: list[str] = Field(default_factory=list)


class SummaryEvaluationOutput(BaseModel):
    summary: str = ""


class OverallVisualizationInputMessage(BaseModel):
    overall_analysis: str = ""
    overall_score: float = 0.0


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[BaseEvaluationConfiguration]


class BaseEvaluation(Configurable[BaseEvaluationConfiguration], ABC):
    # base agent consists of the following:
    # settings: This would consist of name, id, profile, what task to do, budget etc
    # provider: This would consist of two methods: counting tokens and chat completion api
    # Prompt strategy: This would consist of building prompt and parsing response content

    # Base Agent consists of common methods that are used by all agents
    prompt_strategy: Any = None

    def __init__(
        self,
        evaluation_config: BaseEvaluationConfiguration,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        perplexity_provider: ChatModelProvider,
        prompt_strategy: BaseEvaluationPromptStrategy,
    ):
        super().__init__()

        self.config: EvaluationSettings = evaluation_config.settings
        self.llm_provider = llm_provider
        self.gemini_provider = gemini_provider
        self.perplexity_provider = perplexity_provider
        self.groq_provider = groq_provider
        self.prompt_strategy = prompt_strategy

    def get_llm_info(self) -> ChatModelInfo:
        llm_name = self.config.slow_llm
        return OPENAI_CHAT_MODELS[llm_name]

    def build_prompt(self, prompt_input: PromptInput):
        # this returns a chat prompt which is a list of messages
        prompt = self.prompt_strategy.build_prompt(prompt_input)
        return prompt

    async def run_model(self, prompt, response_type):
        if response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_DATA_EXTRACTION:
            response = await self.perplexity_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.perplexity_llm,
                completion_parser=lambda r: self.parse_response_subquery_data_extraction_content(
                    r, prompt
                ),
                is_json_mode=True,
                json_type="json_schema",
                json_schema={
                    "schema": SubqueryDataExtractionOutputMessage.model_json_schema()
                },  # perplexity format
            )

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_GENERATION:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_subquery_generation_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_evaluation_content(r, prompt),
                is_json_mode=True,
            )

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION_SUMMARY:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_evaluation_summary_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif (
            response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.CODE_ANALYSIS_VISUAL_SUMMARY
        ):
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_code_analysis_visual_summary_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.CRITERIA_VISUAL_SUMMARY:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_criteria_visual_summary_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif (
            response_type
            == BaseEvaluationPromptStrategy.RESPONSE_TYPE.PANELIST_FEEDBACK_VISUAL_SUMMARY
        ):
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_panelist_feedback_visual_summary_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.OVERALL_VISUAL_SUMMARY:
            response = await self.llm_provider.create_chat_completion(
                chat_messages=prompt,
                model_name=self.config.slow_llm,
                completion_parser=lambda r: self.parse_response_overall_visual_summary_content(
                    r, prompt
                ),
                is_json_mode=True,
            )

        return response.parsed_response

    async def run_subquery_generation(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_GENERATION
        )
        return response

    async def run_evaluation(self, prompt: ChatMessage) -> QuestionSpecificEvaluationOutputMessage:
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION
        )
        return response

    async def run_subquery_data_extraction(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_DATA_EXTRACTION
        )
        return response

    async def generate_summary(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION_SUMMARY
        )
        return response

    async def generate_code_analysis_visual_summary(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.CODE_ANALYSIS_VISUAL_SUMMARY
        )
        return response

    async def generate_criteria_visual_summary(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.CRITERIA_VISUAL_SUMMARY
        )
        return response

    async def generate_panelist_feedback_visual_summary(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.PANELIST_FEEDBACK_VISUAL_SUMMARY
        )
        return response

    async def generate_overall_visual_summary(self, prompt: ChatMessage):
        response = await self.run_model(
            prompt, BaseEvaluationPromptStrategy.RESPONSE_TYPE.OVERALL_VISUAL_SUMMARY
        )
        return response

    @abstractmethod
    def parse_response_subquery_generation_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_subquery_data_extraction_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_evaluation_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_evaluation_summary_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_criteria_visual_summary_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_code_analysis_visual_summary_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_overall_visual_summary_content(self, response, prompt):
        pass

    @abstractmethod
    def parse_response_panelist_feedback_visual_summary_content(self, response, prompt):
        pass
