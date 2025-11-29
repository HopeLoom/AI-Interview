import abc
import enum
import typing
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar, Union

from interview_details_agent.base import (
    BaseInterviewConfiguration,
    InterviewTopicData,
    SubTopicData,
)
from pydantic import BaseModel, Field

from activity_agent.base import ActivityProgressAnalysisSummaryForPanelistOutputMessage
from core.prompting.base import BaseMasterPromptStrategy
from core.resource.model_providers.gemini import GeminiModelName
from core.resource.model_providers.grok import GrokModelName
from core.resource.model_providers.groq import GroqModelName
from core.resource.model_providers.openai import OPENAI_CHAT_MODELS, ChatPrompt, OpenAIModelName
from core.resource.model_providers.schema import (
    ChatModelInfo,
    ChatModelProvider,
    ChatModelResponse,
    MasterChatMessage,
    SystemSettings,
)
from panelist_agent.base import Background, Profile

S = TypeVar("S", bound=SystemSettings)


class TOPICS_HR_ROUND(str, enum.Enum):
    INTRODUCTION_ROLE_FIT = "Introduction & Role Fit"


class SUBTOPICS_HR_ROUND(str, enum.Enum):
    INTRODUCTIONS_INTERVIEW_FORMAT = "Introductions & Interview Overview"
    JOB_ROLE_FIT = "Job & Role Fit"
    MOTIVATIONS_CAREER_GOALS = "Motivation & Career Goals"


class TOPICS_TECHNICAL_ROUND(str, enum.Enum):
    TEAM_INTRODUCTIONS_AND_INTERVIEW_FORMAT = "Team Introductions and Interview Format"
    PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING = (
        "Problem Introduction, Clarification and Problem Solving Task"
    )
    DEEP_DIVE_QA = "Deep Dive & Q&A"


class SUBTOPICS_TECHNICAL_ROUND(str, enum.Enum):
    PANEL_MEMBER_INTRODUCTIONS = "Panel Member Introductions"
    INTERVIEW_ROUND_OVERVIEW = "Interview Round Overview"
    TECHNCAL_PROBLEM_OVERVIEW = "Technical Problem Overview and Expectation Confirmation"
    TASK_SPECIFIC_DISCUSSION = "Task-Specific Discussion"
    CONCEPTUAL_KNOWLEDGE_CHECK = "Conceptual Knowledge Check"
    BROADER_EXPERTISE_ASSESMENT = "Broader Expertise Assessment"
    PROBLEM_SOLVING = "Problem Solving Task"


class SimulationRole(str, enum.Enum):
    MASTER = "MASTER"
    PANELIST = "PANELIST"
    CANDIDATE = "CANDIDATE"
    ACTIVITY = "ACTIVITY"
    EVALUATION = "EVALUATION"
    ALL = "ALL"


class SystemMessageType(str, enum.Enum):
    USER_LOGIN = "USER_LOGIN"
    START = "START"
    END = "END"
    INTERVIEW_ROUND_CHANGED = "INTERVIEW_ROUND_CHANGED"
    ACTIVITY_DATA = "ACTIVITY_DATA"


class WebSocketMessageTypeFromClient(str, enum.Enum):
    USER_LOGIN = "USER_LOGIN"
    INSTRUCTION = "INSTRUCTION"
    INTERVIEW_START = "INTERVIEW_START"
    INTERVIEW_DATA = "INTERVIEW_DATA"
    DONE_PROBLEM_SOLVING = "DONE_PROBLEM_SOLVING"
    ACTIVITY_INFO = "ACTIVITY_INFO"
    INTERVIEW_END = "INTERVIEW_END"
    AUDIO_PLAYBACK_COMPLETED = "AUDIO_PLAYBACK_COMPLETED"
    USER_LOGOUT = "USER_LOGOUT"
    AUDIO_RAW_DATA = "AUDIO_RAW_DATA"
    START_AUDIO_STREAMING = "START_AUDIO_STREAMING"
    EVALUATION_DATA = "EVALUATION_DATA"
    # Configuration-related messages
    GENERATE_CONFIGURATION = "GENERATE_CONFIGURATION"
    GENERATE_QUESTION = "GENERATE_QUESTION"
    GENERATE_CHARACTERS = "GENERATE_CHARACTERS"
    LOAD_CONFIGURATION = "LOAD_CONFIGURATION"


class WebSocketMessageTypeToClient(str, enum.Enum):
    INTERVIEW_DETAILS = ("INTERVIEW_DETAILS",)
    USER_PROFILE = ("USER_PROFILE",)
    INSTRUCTION = ("INSTRUCTION",)
    INTERVIEW_START = ("INTERVIEW_START",)
    NEXT_SPEAKER_INFO = ("NEXT_SPEAKER_INFO",)
    INTERVIEW_DATA = ("INTERVIEW_DATA",)
    ACTIVITY_INFO = ("ACTIVITY_INFO",)
    INTERVIEW_END = ("INTERVIEW_END",)
    AUDIO_SPEECH_TO_TEXT = ("AUDIO_SPEECH_TO_TEXT",)
    AUDIO_CHUNKS = ("AUDIO_CHUNKS",)
    AUDIO_STREAMING_COMPLETED = ("AUDIO_STREAMING_COMPLETED",)
    EVALUATION_DATA = ("EVALUATION_DATA",)
    ERROR = ("ERROR_DATA",)
    # Configuration-related messages
    CONFIGURATION_GENERATED = ("CONFIGURATION_GENERATED",)
    QUESTION_GENERATED = ("QUESTION_GENERATED",)
    CHARACTERS_GENERATED = ("CHARACTERS_GENERATED",)
    CONFIGURATION_LOADED = ("CONFIGURATION_LOADED",)


class WebSocketMessageToClient(BaseModel):
    message_type: str = WebSocketMessageTypeToClient.INSTRUCTION
    message: Any = None
    id: str = ""


class InterviewRound(str, enum.Enum):
    ROUND_ONE = "HR_ROUND"
    ROUND_TWO = "TECHNICAL_ROUND"
    ROUND_THREE = "BEHAVIORAL_ROUND"

    @classmethod
    def get_round_name(cls, round_value: str) -> str:
        return round_value.replace("_", " ").title()


class PanelData(BaseModel):
    id: str = ""
    interview_round_part_of: InterviewRound = InterviewRound.ROUND_ONE
    name: str = ""
    intro: str = ""
    avatar: str = ""
    isAI: bool = True
    isActive: bool = False
    connectionStatus: str = "connected"


class SimulationIntroductionOutputMessage(BaseModel):
    introduction: str = ""
    panelists: list[PanelData] = Field(default_factory=list)


class SimulationIntroductionInputMessage(BaseModel):
    panelists: list[Profile] = Field(default_factory=list)


class ActivityDataToClient(BaseModel):
    scenario: str = ""
    data_available: str = ""
    task_for_the_candidate: str = ""
    raw_data: str = ""
    starter_code: str = ""


class ConvertedSpeechToClient(BaseModel):
    text: str = ""
    speaker_name: str = ""


class InterviewStartDataToClient(BaseModel):
    round: InterviewRound = InterviewRound.ROUND_ONE
    participants: list[PanelData] = Field(default_factory=list)
    message: str = ""
    voice_name: str = ""


class InstructionDataToClient(BaseModel):
    introduction: str = ""
    panelists: list[PanelData] = Field(default_factory=list)
    role: str = ""
    company: str = ""
    interview_type: str = ""


class InterviewMessageDataToClient(BaseModel):
    speaker: str = ""
    text_message: str = ""
    voice_name: str = ""
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    current_topic: str = ""
    current_subtopic: str = ""
    is_user_input_required: bool = False


class NextSpeakerInfoToClient(BaseModel):
    speaker: str = ""
    is_user_input_required: bool = False


class InterviewEndDataToClient(BaseModel):
    message: str = ""
    voice_name: str = ""


class WebSocketMessageFromClient(BaseModel):
    message_type: WebSocketMessageTypeFromClient = WebSocketMessageTypeFromClient.USER_LOGIN
    message: Any = None
    id: str = ""


class TextToSpeechDataMessageFromClient(BaseModel):
    text: str = ""
    voice_name: str = ""


class TextToSpeechDataMessageToClient(BaseModel):
    audio_data: str = ""


class SpeechDataMessageFromClient(BaseModel):
    raw_audio_data: str = ""


class UserLoginDataMessageFromClient(BaseModel):
    name: str = ""
    email: str = ""
    id: str = ""


class UserLogoutDataMessageFromClient(BaseModel):
    id: str = ""


class InstructionDataMessageFromClient(BaseModel):
    message: str = ""


class InterviewStartDataMessageFromClient(BaseModel):
    message: str = ""


class InterviewDataMessageFromClient(BaseModel):
    speaker: str = ""
    message: str = ""
    activity_data: str = ""


class InterviewEndDataMessageFromClient(BaseModel):
    message: str = ""


class AudioPlaybackCompletedDataMessageFromClient(BaseModel):
    isAudioPlaybackCompleted: bool = False


# Configuration-related message models
class ConfigurationGenerationRequestFromClient(BaseModel):
    config_input: dict = Field(default_factory=dict)
    user_id: str = ""


class QuestionGenerationRequestFromClient(BaseModel):
    question_request: dict = Field(default_factory=dict)
    user_id: str = ""


class CharacterGenerationRequestFromClient(BaseModel):
    character_request: dict = Field(default_factory=dict)
    user_id: str = ""


class ConfigurationLoadRequestFromClient(BaseModel):
    configuration_id: str = ""
    user_id: str = ""


class ConfigurationGeneratedToClient(BaseModel):
    success: bool = True
    configuration_id: str = ""
    simulation_config: Optional[dict] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# this is used in the interview round check prompt
class INTERVIEW_COMPLETION_TYPE(str, enum.Enum):
    CONTINUE = "CONTINUE"
    END = "END"


# topic completion
class TopicSectionCompletionInputMessage(BaseModel):
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    topic_data: InterviewTopicData = InterviewTopicData()
    subtopic_data: SubTopicData = SubTopicData()
    section: str = ""
    panelists: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    topic_just_got_completed: bool = False


class TopicSectionCompletionOutputMessage(BaseModel):
    decision: str = ""
    reason: str = ""


class SpeakerDeterminationOutputMessage(BaseModel):
    model_config = {"validate_assignment": True, "extra": "forbid", "frozen": False}
    last_speaker: str = ""
    next_speaker: str = ""
    should_next_speaker_address_last_speaker: bool = False
    reason_for_selecting_next_speaker: str = ""


# conversation advice
class ConversationalAdviceInputMessage(BaseModel):
    next_speaker: Profile = Profile()
    topic_data: InterviewTopicData = InterviewTopicData()
    subtopic_data: SubTopicData = SubTopicData()
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    topic_just_got_completed: bool = False
    section: str = ""
    speaker_determination_output: SpeakerDeterminationOutputMessage = (
        SpeakerDeterminationOutputMessage()
    )
    topic_completion_output: TopicSectionCompletionOutputMessage = (
        TopicSectionCompletionOutputMessage()
    )


class ConversationalAdviceOutputMessage(BaseModel):
    advice_for_speaker: str = ""
    should_ask_completely_new_question: bool = False
    should_wrap_up_current_topic: bool = False
    should_end_the_interview: bool = False


# this is the system message structure that is sent from main instance to all slave agents
class SystemMessageStructure(BaseModel):
    system_message_type: SystemMessageType = SystemMessageType.START
    system_message: str = ""
    system_message_sender: SimulationRole = SimulationRole.MASTER
    system_message_receiver: SimulationRole = SimulationRole.ALL


# this is the message which is communicated from main instance to all slave agents
class MasterMessageStructure(BaseModel):
    model_config = {"validate_assignment": True, "extra": "forbid", "frozen": False}
    speaker: Optional[Profile] = Field(default_factory=Profile)
    current_interview_round: InterviewRound = InterviewRound.ROUND_ONE
    activity_code_from_candidate: str = ""
    conversation_history_for_current_subtopic: list[MasterChatMessage] = Field(default_factory=list)
    conversation_summary_for_current_topic: list[str] = Field(default_factory=list)
    conversation_summary_for_completed_topics: list[str] = Field(default_factory=list)
    last_completed_conversation_history: list[MasterChatMessage] = Field(default_factory=list)
    panelist_thoughts: dict = Field(default_factory=dict)
    panelist_profiles: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    topic: InterviewTopicData = InterviewTopicData()
    sub_topic: SubTopicData = SubTopicData()
    current_section: str = ""
    evaluation_criteria: list[str] = Field(default_factory=list)
    remaining_topics: list[str] = Field(default_factory=list)
    remaining_time: float = 0
    topic_completion_message: TopicSectionCompletionOutputMessage = (
        TopicSectionCompletionOutputMessage()
    )
    speaker_determination_message: SpeakerDeterminationOutputMessage = (
        SpeakerDeterminationOutputMessage()
    )
    advice: ConversationalAdviceOutputMessage = ConversationalAdviceOutputMessage()


# this is the message which is communicated from slave agents to main instance
class SlaveMessageStructure(BaseModel):
    message: list[str] = Field(default_factory=list)
    speaker: str = ""
    voice_name: str = ""
    activity_analysis: str = ""


class CommunicationMessage(BaseModel):
    sender: SimulationRole
    receiver: SimulationRole
    content: Union[MasterMessageStructure, SlaveMessageStructure, SystemMessageStructure]

    @staticmethod
    def message_to_slave(
        sender: SimulationRole,
        receiver: SimulationRole,
        content: Union[MasterMessageStructure, SlaveMessageStructure, SystemMessageStructure],
    ) -> "CommunicationMessage":
        return CommunicationMessage(sender=sender, receiver=receiver, content=content)

    @staticmethod
    def message_to_master(
        sender: SimulationRole,
        receiver: SimulationRole,
        content: Union[SlaveMessageStructure, SystemMessageStructure],
    ) -> "CommunicationMessage":
        return CommunicationMessage(sender=sender, receiver=receiver, content=content)


class MasterSettings(BaseModel):
    fast_llm: str = OpenAIModelName.GPT4O_MINI
    slow_llm: str = OpenAIModelName.GPT4O
    gemini_fast_llm: str = GeminiModelName.GEMINI_2_FLASH
    gemini_slow_llm: str = GeminiModelName.GEMINI_1_5_PRO
    groq_llama_llm: str = GroqModelName.LLAMA4MAVERICK
    groq_mistral_llm: str = GroqModelName.LLAMA4SCOUT
    groq_qwen_llm: str = GroqModelName.QWEN
    grok_llm: str = GrokModelName.GROK2
    big_brain: bool = True


class BaseMasterConfiguration(SystemSettings):
    id: str = ""
    name: str = ""
    port: int = 8000
    address: str = "0.0.0.0"
    settings: MasterSettings = Field(default_factory=MasterSettings)
    interview_data: BaseInterviewConfiguration = Field(default_factory=BaseInterviewConfiguration)


# speaker determination
class SpeakerDeterminationInputMessage(BaseModel):
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    panelists: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    current_topic: InterviewTopicData = InterviewTopicData()
    current_subtopic: SubTopicData = SubTopicData()
    current_section: str = ""
    topic_completion_message: TopicSectionCompletionOutputMessage = (
        TopicSectionCompletionOutputMessage()
    )
    topic_just_got_completed: bool = False
    last_speaker: str = ""


# rules and regulations
class RulesAndRegulationsInputMessage(BaseModel):
    panelists_profile: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    topic: InterviewTopicData = InterviewTopicData()
    subtopic: SubTopicData = SubTopicData()


class RulesAndRegulationsMessage(BaseModel):
    character_name: str = ""
    reason: str = ""


class RulesAndRegulationsOutputMessage(BaseModel):
    data: list[RulesAndRegulationsMessage] = Field(default_factory=list)


# evaluation message
class EvaluationInputMessage(BaseModel):
    panelists: list[Profile] = Field(default_factory=list)
    candidate_profile: Profile = Profile()
    topic_data: InterviewTopicData = InterviewTopicData()
    subtopic_data: SubTopicData = SubTopicData()
    interview_round: InterviewRound = InterviewRound.ROUND_ONE
    evaluation_criteria: list[str] = Field(default_factory=list)
    subqueries_data: Any = None


class CriteriaSpecificScoring(BaseModel):
    criteria: str = ""
    score: float = 0
    reason: str = ""
    key_phrases_from_conversation: list[str] = Field(default_factory=list)


class QuestionSpecificScoring(BaseModel):
    question_number: int = 0
    decision: str = ""
    reason: str = ""


class QuestionCriteriaSpecificScoring(BaseModel):
    criteria: str = ""
    question_specific_scoring: list[QuestionSpecificScoring] = Field(default_factory=list)
    key_phrases_from_conversation: list[str] = Field(default_factory=list)


class QuestionSpecificEvaluationOutputMessage(BaseModel):
    question_criteria_specific_scoring: list[QuestionCriteriaSpecificScoring] = Field(
        default_factory=list
    )


class OldEvaluationMessage(BaseModel):
    criteria_specific_scoring: list[CriteriaSpecificScoring] = Field(default_factory=list)


class EvaluationMessageToFrontEnd(BaseModel):
    candidate_id: str = Field(default="", description="Candidate identifier")
    candidate_profile_image: str = Field(default="", description="Profile image URL")
    candidate_name: str = Field(default="", description="Candidate name")
    candidate_profile: Background = Background()
    overall_analysis: str = Field(default="", description="Overall evaluation analysis")
    overall_score: float = Field(default=0.0, ge=0, le=5, description="Overall score")
    evaluation_output: OldEvaluationMessage = OldEvaluationMessage()
    code_from_candidate: str = ""
    activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
        ActivityProgressAnalysisSummaryForPanelistOutputMessage()
    )
    transcript: list[MasterChatMessage] = Field(default_factory=list)
    panelist_feedback: list[str] = Field(default_factory=list)
    panelist_names: list[str] = Field(default_factory=list)
    panelist_occupations: list[str] = Field(default_factory=list)


class CriteriaScoreVisualSummary(BaseModel):
    criteria: str = ""
    score: float = 0
    reason_bullets: list[str] = Field(default_factory=list)
    topics_covered: list[str] = Field(default_factory=list)


class CriteriaScoreVisualSummaryList(BaseModel):
    criteria_score_list: list[CriteriaScoreVisualSummary] = Field(default_factory=list)


class CodeDimensions(str, enum.Enum):
    TIME_COMPLEXITY = "Time Complexity"
    CODE_LOGIC = "Logic"
    CODE_INTERPRETATION = "Code Interpretation"
    CODE_STYLE = "Code Style"
    CODE_CORRECTNESS = "Code Correctness"
    CODE_EFFICIENCY = "Code Efficiency"
    CODE_READABILITY = "Code Readability"
    CODE_REUSABILITY = "Code Reusability"


class CodeSubmissionVisualSummary(BaseModel):
    language: str = ""
    content: str = ""


class CodeDimensionSummary(BaseModel):
    name: str = ""
    comment: str = ""
    rating: str = ""


class CodeAnalysisVisualSummary(BaseModel):
    code_overall_summary: list[str] = Field(default_factory=list)
    code_dimension_summary: list[CodeDimensionSummary] = Field(default_factory=list)
    completion_percentage: float = 0


class PanelistFeedbackVisualSummary(BaseModel):
    name: str = ""
    role: str = ""
    summary_bullets: list[str] = Field(default_factory=list)


class PanelistFeedbackVisualSummaryList(BaseModel):
    panelist_feedback: list[PanelistFeedbackVisualSummary] = Field(default_factory=list)


class OverallVisualSummary(BaseModel):
    score_label: str = ""
    key_insights: list[str] = Field(default_factory=list)


class CandidateEvaluationVisualisationReport(BaseModel):
    candidate_id: str = ""
    candidate_name: str = ""
    candidate_profile_image: str = ""
    overall_score: float = 0
    overall_visual_summary: OverallVisualSummary = OverallVisualSummary()
    criteria_scores: list[CriteriaScoreVisualSummary] = Field(default_factory=list)
    code_submission: CodeSubmissionVisualSummary = CodeSubmissionVisualSummary()
    code_analysis: CodeAnalysisVisualSummary = CodeAnalysisVisualSummary()
    panelist_feedback: list[PanelistFeedbackVisualSummary] = Field(default_factory=list)
    transcript: list[MasterChatMessage] = Field(default_factory=list)
    candidate_profile: Background = Background()


class PromptInput(BaseModel):
    topic_time_remaining: float = 0
    remaining_subtopics: list[str] = Field(default_factory=list)
    response_type: BaseMasterPromptStrategy.RESPONSE_TYPE = (
        BaseMasterPromptStrategy.RESPONSE_TYPE.INTRO
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


class InterviewDetails(BaseModel):
    candidate_name: str = ""
    role: str = ""
    company: str = ""
    duration: int = 0
    interviewType: str = ""
    expectations: list[str] = Field(default_factory=list)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[BaseMasterConfiguration]


class BaseMaster(Configurable[BaseMasterConfiguration], ABC):
    # base agent consists of the following:
    # settings: This would consist of name, id, profile, what task to do, budget etc
    # provider: This would consist of two methods: counting tokens and chat completion api
    # Prompt strategy: This would consist of building prompt and parsing response content

    # Base Agent consists of common methods

    def __init__(
        self,
        master_config: BaseMasterConfiguration,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        grok_provider: ChatModelProvider,
        deepseek_provider: ChatModelProvider,
        prompt_strategy: BaseMasterPromptStrategy,
    ):
        super().__init__()

        self.settings = master_config.settings
        self.interview_config = master_config.interview_data
        self.llm_provider = llm_provider
        self.gemini_provider = gemini_provider
        self.groq_provider = groq_provider
        self.grok_provider = grok_provider
        self.deepseek_provider = deepseek_provider
        self.prompt_strategy = prompt_strategy
        self.master_config = master_config

    def get_name(self) -> str:
        return self.master_config.name

    def get_llm_info(self) -> ChatModelInfo:
        llm_name = self.settings.fast_llm
        return OPENAI_CHAT_MODELS[llm_name]

    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        # this returns a chat prompt which is a list of messages
        prompt = self.prompt_strategy.build_prompt(prompt_input)
        return prompt

    async def run_summary_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.slow_llm,
            completion_parser=lambda r: self.parse_and_process_summary_model(r, prompt),
            is_json_mode=True,
        )
        return response

    async def run_intro_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.get_llm_info().name,
            completion_parser=lambda r: self.parse_and_process_response_introduction(r, prompt),
            is_json_mode=True,
        )
        return response

    async def run_speaker_determination_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.slow_llm,
            completion_parser=lambda r: self.parse_and_process_response_speaker_determination(
                r, prompt
            ),
            is_json_mode=True,
        )
        return response

    async def run_rules_regulation_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.groq_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.groq_qwen_llm,
            completion_parser=lambda r: self.parse_and_process_response_rules_regulation(r, prompt),
            is_json_mode=True,
        )
        return response

    async def run_conversational_advice_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.slow_llm,
            completion_parser=lambda r: self.parse_and_process_response_conversational_advice(
                r, prompt
            ),
            is_json_mode=True,
        )
        return response

    async def run_topic_completion_model(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.slow_llm,
            completion_parser=lambda r: self.parse_and_process_response_topic_completion(r, prompt),
            is_json_mode=True,
        )
        return response

    async def run_topic_summarizer(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.grok_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.grok_llm,
            completion_parser=lambda r: self.parse_and_process_response_summarized_conversation(
                r, prompt
            ),
            is_json_mode=True,
        )
        return response

    async def run_subtopic_summarizer(self, prompt: ChatPrompt) -> ChatModelResponse:
        response = await self.llm_provider.create_chat_completion(
            chat_messages=prompt,
            model_name=self.settings.slow_llm,
            completion_parser=lambda r: self.parse_and_process_response_summarized_conversation(
                r, prompt
            ),
            is_json_mode=True,
        )
        return response

    async def generate_introduction(self, prompt: ChatPrompt):
        response = await self.run_intro_model(prompt)
        return response

    async def generate_summary(self, prompt: ChatPrompt):
        response = await self.run_summary_model(prompt)
        return response

    async def generate_speaker_determination_information(self, prompt: ChatPrompt):
        response = await self.run_speaker_determination_model(prompt)
        return response

    async def generate_rules_and_regulations_check(self, prompt: ChatPrompt):
        response = await self.run_rules_regulation_model(prompt)
        return response

    async def generate_conversational_advice(self, prompt: ChatPrompt):
        response = await self.run_conversational_advice_model(prompt)
        return response

    async def generate_topic_completion(self, prompt: ChatPrompt):
        response = await self.run_topic_completion_model(prompt)
        return response

    @abstractmethod
    def parse_and_process_response_topic_completion(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> TopicSectionCompletionOutputMessage:
        """Parse topic completion response"""
        pass

    @abstractmethod
    def parse_and_process_response_summarized_conversation(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> list[str]:
        """Parse summarized conversation response"""
        pass

    @abstractmethod
    def parse_and_process_response_introduction(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> SimulationIntroductionOutputMessage:
        """Parse introduction response"""
        pass

    @abstractmethod
    def parse_and_process_response_speaker_determination(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> SpeakerDeterminationOutputMessage:
        """Parse speaker determination response"""
        pass

    @abstractmethod
    def parse_and_process_response_rules_regulation(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> list[RulesAndRegulationsMessage]:
        """Parse rules and regulations response"""
        pass

    @abstractmethod
    def parse_and_process_response_conversational_advice(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> ConversationalAdviceOutputMessage:
        """Parse conversational advice response"""
        pass

    @abstractmethod
    def parse_and_process_summary_model(
        self, response: ChatModelResponse, prompt: ChatPrompt
    ) -> str:
        """Parse summary model response"""
        pass
