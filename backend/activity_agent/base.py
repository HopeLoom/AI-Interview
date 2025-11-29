from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import enum
from abc import ABC, abstractmethod
from core.resource.model_providers.schema import ChatModelProvider, ChatModelInfo, SystemSettings, ChatMessage, ChatModelResponse
from core.prompting.schema import ChatPrompt
from core.resource.model_providers.openai import OpenAIModelName, OPENAI_CHAT_MODELS
from core.resource.model_providers.gemini import GeminiModelName
from core.resource.model_providers.groq import GroqModelName
from core.prompting.base import BaseActivityPromptStrategy
import abc
import typing
from interview_details_agent.base import BaseInterviewConfiguration, ActivityDetailsOutputMessage
from typing import Generic, TypeVar

# Constants
DEFAULT_SCORE = 0.0
DEFAULT_PERCENTAGE = 0.0

S = TypeVar("S", bound=SystemSettings)

class ActivitySettings(BaseModel):
    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "frozen": False
    }
    
    fast_llm: str = OpenAIModelName.GPT4O_MINI
    slow_llm: str = OpenAIModelName.GPT4O
    gemini_fast_llm: str = GeminiModelName.GEMINI_2_FLASH
    gemini_slow_llm: str = GeminiModelName.GEMINI_1_5_PRO
    groq_llama_llm: str = GroqModelName.LLAMA4MAVERICK
    groq_mistral_llm: str = GroqModelName.LLAMA4SCOUT
    groq_qwen_llm: str = GroqModelName.QWEN
    big_brain: bool = True

class ActivityProgressAnalysisOutputMessage(BaseModel):
    code_intrepretation: str = Field(default="", description="Code interpretation analysis")
    complexity_analysis: str = Field(default="", description="Complexity analysis")
    logic_analysis: str = Field(default="", description="Logic analysis")

class ActivityProgressWithRespectToQuestionOutputMessage(BaseModel):
    code_intrepretation_with_respect_to_question: str = Field(default="", description="Code interpretation with respect to question")
    logic_analysis_with_respect_to_question: str = Field(default="", description="Logic analysis with respect to question")
    complexity_analysis_with_respect_to_question: str = Field(default="", description="Complexity analysis with respect to question")
    remaining_things_to_do_with_respect_to_question: str = Field(default="", description="Remaining tasks with respect to question")

class ActivityProgressAnalysisSummaryForPanelistOutputMessage(BaseModel):
    candidate_performance_summary: str = Field(default="", description="Summary of candidate performance")
    percentage_of_question_solved: float = Field(default=DEFAULT_PERCENTAGE, ge=0, le=100, description="Percentage of question solved")
    things_left_to_do_with_respect_to_question: str = Field(default="", description="Remaining tasks for the question")

class BaseActivityConfiguration(SystemSettings):
    activity_name: str = Field(default="", description="Activity name")
    settings: ActivitySettings = Field(default_factory=ActivitySettings, description="Activity settings")
    activity_details: ActivityDetailsOutputMessage = Field(default_factory=ActivityDetailsOutputMessage, description="Activity details")
    activity_code_file_path: str = Field(default="", description="Path to activity code file")
    activity_info_file_path: str = Field(default="", description="Path to activity info file")

class PromptInput(BaseModel):
    response_type: BaseActivityPromptStrategy.RESPONSE_TYPE = Field(
        default=BaseActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_HIGH_LEVEL_ANALYSIS, 
        description="Response type"
    )
    activity_code_from_candidate: str = Field(default="", description="Activity code from candidate")
    starter_code: str = Field(default="", description="Starter code")
    activity_progress_history: List[str] = Field(default_factory=list, description="Activity progress history")
    activity_progress_analysis: ActivityProgressAnalysisOutputMessage = Field(
        default_factory=ActivityProgressAnalysisOutputMessage, 
        description="Activity progress analysis"
    )
    activity_progress_with_respect_to_question: ActivityProgressWithRespectToQuestionOutputMessage = Field(
        default_factory=ActivityProgressWithRespectToQuestionOutputMessage, 
        description="Activity progress with respect to question"
    )

class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""
    prefix: str = ""
    default_settings: typing.ClassVar[BaseActivityConfiguration]

class BaseActivity(Configurable[BaseActivityConfiguration], ABC):
    """Base class for all activity agents."""

    def __init__(
        self, 
        activity_config: BaseActivityConfiguration,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        prompt_strategy: BaseActivityPromptStrategy
    ):
        super(BaseActivity, self).__init__()

        self.config: ActivitySettings = activity_config.settings
        self.llm_provider = llm_provider
        self.gemini_provider = gemini_provider
        self.groq_provider = groq_provider
        self.prompt_strategy = prompt_strategy

    def get_llm_info(self) -> ChatModelInfo:
        """Get LLM information with caching"""
        llm_name = self.config.slow_llm
        return OPENAI_CHAT_MODELS[llm_name]
    
    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        """Build prompt using the prompt strategy"""
        return self.prompt_strategy.build_prompt(prompt_input)

    async def run_model_with_schema(self, prompt: ChatPrompt, model_name: str, 
                                   parser_method, json_schema: dict, provider=None) -> Any:
        """Generic method to run any model with JSON schema and error handling"""
        try:
            if provider is None:
                provider = self.groq_provider
            
            response = await provider.create_chat_completion(
                chat_messages=prompt,
                model_name=model_name,
                completion_parser=lambda r: parser_method(r, prompt),
                is_json_mode=True
            )
            return response.parsed_response
        except Exception as e:
            # Log error or handle gracefully
            raise RuntimeError(f"Failed to run model {model_name}: {e}")

    async def run_activity_progress_analysis(self, prompt: ChatPrompt) -> ActivityProgressAnalysisOutputMessage:
        """Run activity progress analysis with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.config.groq_llama_llm,
            parser_method=self.parse_and_process_response_activity_progress,
            json_schema=ActivityProgressAnalysisOutputMessage.model_json_schema()
        )
    
    async def run_activity_progress_analysis_with_respect_question(self, prompt: ChatPrompt) -> ActivityProgressWithRespectToQuestionOutputMessage:
        """Run activity progress analysis with respect to question with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.config.groq_llama_llm,
            parser_method=self.parse_and_process_response_activity_progress_with_respect_to_question,
            json_schema=ActivityProgressWithRespectToQuestionOutputMessage.model_json_schema()
        )
    
    async def run_activity_progress_analysis_summary_for_panelist(self, prompt: ChatPrompt) -> ActivityProgressAnalysisSummaryForPanelistOutputMessage:
        """Run activity progress analysis summary for panelist with direct schema access"""
        return await self.run_model_with_schema(
            prompt=prompt,
            model_name=self.config.groq_llama_llm,
            parser_method=self.parse_and_process_response_activity_progress_summary_for_panelist,
            json_schema=ActivityProgressAnalysisSummaryForPanelistOutputMessage.model_json_schema()
        )

    def validate_configuration(self) -> bool:
        """Validate the activity configuration"""
        try:
            if not self.config:
                return False
            if not hasattr(self, 'groq_provider'):
                return False
            if not hasattr(self, 'prompt_strategy'):
                return False
            return True
        except Exception:
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration"""
        return {
            "activity_name": self.config.activity_name if hasattr(self.config, 'activity_name') else "Unknown",
            "has_groq_provider": bool(self.groq_provider),
            "has_prompt_strategy": bool(self.prompt_strategy),
            "settings_valid": self.validate_configuration()
        }

    @abstractmethod
    def parse_and_process_response_activity_progress(self, response: ChatModelResponse, prompt: ChatPrompt) -> ActivityProgressAnalysisOutputMessage:
        """Parse activity progress response"""
        pass
    
    @abstractmethod
    def parse_and_process_response_activity_progress_with_respect_to_question(self, response: ChatModelResponse, prompt: ChatPrompt) -> ActivityProgressWithRespectToQuestionOutputMessage:
        """Parse activity progress with respect to question response"""
        pass

    @abstractmethod
    def parse_and_process_response_activity_progress_summary_for_panelist(self, response: ChatModelResponse, prompt: ChatPrompt) -> ActivityProgressAnalysisSummaryForPanelistOutputMessage:
        """Parse activity progress summary for panelist response"""
        pass