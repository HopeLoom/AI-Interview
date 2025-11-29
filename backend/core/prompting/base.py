import abc
import enum
from typing import Any

from core.resource.model_providers.schema import AssistantChatMessage

from .schema import ChatPrompt


class BaseActivityPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        ACTIVITY_HIGH_LEVEL_ANALYSIS = "ACTIVITY_HIGH_LEVEL_ANALYSIS"
        ACTIVITY_ANALYSIS_WITH_RESPECT_TO_QUESTION = "ACTIVITY_ANALYSIS_WITH_RESPECT_TO_QUESTION"
        ACTIVITY_ANALYSIS_SUMMARY_FOR_PANELIST = "ACTIVITY_ANALYSIS_SUMMARY_FOR_PANELIST"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...


class BaseInterviewPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        ACTIVITY_DETAILS = "ACTIVITY_DETAILS"
        CHARACTER_INFO = "CHARACTER_INFO"
        STARTER_CODE_GENERATION = "STARTER_CODE_GENERATION"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...


class BaseDiscussionPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        FEEDBACK_INFO = "FEEDBACK_INFO"
        ACTIVITY_INFO = "ACTIVITY_INFO"
        ACTIVITY_CODE_INFO = "ACTIVITY_CODE_INFO"
        CONSENSUS_INFO = "CONSENSUS_INFO"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...


class BaseMasterPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        INTRO = "INTRO"
        SPEAKER_DETERMINATION = "SPEAKER_DETERMINATION"
        TOPIC_SECTION_COMPLETION = "TOPIC_SECTION_COMPLETION"
        CONVERSATIONAL_ADVICE = "CONVERSATIONAL_ADVICE"
        RULES_AND_REGULATIONS = "RULES_AND_REGULATIONS"
        SUBTOPIC_SUMMARY = "SUBTOPIC_SUMMARY"
        TOPIC_SUMMARY = "TOPIC_SUMMARY"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...


class BaseEvaluationPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        EVALUATION = "EVALUATION"
        EVALUATION_SUMMARY = "EVALUATION_SUMMARY"
        SUBQUERY_GENERATION = "SUBQUERY_GENERATION"
        SUBQUERY_DATA_EXTRACTION = "SUBQUERY_DATA_EXTRACTION"
        CODE_ANALYSIS_VISUAL_SUMMARY = "CODE_ANALYSIS_VISUAL_SUMMARY"
        OVERALL_VISUAL_SUMMARY = "OVERALL_VISUAL_SUMMARY"
        PANELIST_FEEDBACK_VISUAL_SUMMARY = "PANELIST_FEEDBACK_VISUAL_SUMMARY"
        CRITERIA_VISUAL_SUMMARY = "CRITERIA_VISUAL_SUMMARY"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_subquery_generation_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_subquery_data_extraction_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_evaluation_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_evaluation_summary_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_code_analysis_visual_summary_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_overall_visual_summary_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_panelist_feedback_visual_summary_content(self, response): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_criteria_visual_summary_content(self, response): ...


class BaseCandidatePromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        REASON = "REASON"
        DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE"
        RESPOND = "RESPOND"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_content(self, response): ...


class BasePanelistPromptStrategy(abc.ABC):
    class RESPONSE_TYPE(str, enum.Enum):
        REASON = "REASON"
        DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE"
        RESPOND = "RESPOND"
        REFLECT = "REFLECT"
        EVALUATE = "EVALUATE"
        RESPOND_WITH_REASONING = "RESPOND_WITH_REASONING"

    @abc.abstractmethod
    # this method should return ChatPrompt Instance after building the prompt
    def build_prompt(self, prompt_input: Any) -> ChatPrompt: ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_process_response_model(self, response: AssistantChatMessage): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_domain_knowledge_content(self, response: AssistantChatMessage): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_evaluate_content(self, response: AssistantChatMessage): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_reflect_content(self, response: AssistantChatMessage): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_response_reason_content(self, response: AssistantChatMessage): ...

    @abc.abstractmethod
    # the callback that will be used to parse the response from the model provider
    def parse_process_respond_with_reasoning_model(self, response: AssistantChatMessage): ...
