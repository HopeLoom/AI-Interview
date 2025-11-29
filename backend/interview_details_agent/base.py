from pydantic import BaseModel, Field
from typing import List, DefaultDict, Any
import enum
from abc import ABC, abstractmethod
from core.resource.model_providers.schema import ChatModelProvider, ChatModelInfo, SystemSettings, ChatMessage
from core.resource.model_providers.openai import OpenAIModelName, OPENAI_CHAT_MODELS
from core.prompting.base import BaseInterviewPromptStrategy
import abc
import typing
from typing import Generic, TypeVar
from panelist_agent.base import Profile

S = TypeVar("S", bound=SystemSettings)

class InterviewSettings(BaseModel):
    fast_llm: str = OpenAIModelName.GPT4O_MINI
    slow_llm: str = OpenAIModelName.GPT4O
    big_brain: bool = True

class SubTopicData(BaseModel):
    name:str = ""
    time_limit:float = 0
    description:str = ""
    sections:List[str] = Field(default_factory=list)

class InterviewTopicData(BaseModel):
    name:str = ""
    description:str = ""
    time_limit:float = 0
    evaluation_criteria:List[str] = Field(default_factory=list)
    subtopics:List[SubTopicData] = Field(default_factory=list)

class InterviewRoundData(BaseModel):
    description:str = ""
    objective:str = ""
    metrics_covered:List[str] = Field(default_factory=list)
    topic_info:List[InterviewTopicData] = []

class CharacterData(BaseModel):
    character_id:str = ""
    character_name:str = ""
    role:str = ""
    objective:str = ""
    job_description:str = ""
    interview_round_part_of:str = ""    

class EvaluationCriteriaData(BaseModel):
    criteria:str = ""
    description:str = ""

# we will load this from a database
class InterviewRoundDetails(BaseModel):
    rounds: dict[str, InterviewRoundData] = Field(default_factory=dict)

# this wil be the input coming from the frontend
class JobDetails(BaseModel):
    job_description:str = ""
    job_title:str = ""
    job_requirements:List[str] = Field(default_factory=list)
    job_qualifications:List[str] = Field(default_factory=list)
    company_name:str = ""
    company_description:str = ""

class CharacterDataInput(BaseModel):
    interview_round_details: InterviewRoundDetails = InterviewRoundDetails()
    job_details: JobDetails = JobDetails()
    user_profile: Profile = Profile()

# use model to generate this
class CharacterDataOutput(BaseModel):
    data:List[CharacterData] = Field(default_factory=list)
    reason:str = ""

class StarterCodeData(BaseModel):
    code:str = ""
    description:str = ""

class InterviewDetailsInput(BaseModel):
    interview_round_details: InterviewRoundDetails = InterviewRoundDetails()
    job_details: JobDetails = JobDetails()
    user_profile: Profile = Profile()
    character_data: CharacterDataOutput = CharacterDataOutput()

class ActivityDetailsOutputMessage(BaseModel):
    scenario:str = ""
    data_available:str = ""
    task_for_the_candidate:str = ""

class BaseInterviewConfiguration(BaseModel):
    interview_id: str = ""
    settings: InterviewSettings = Field(default_factory=InterviewSettings)
    job_details: JobDetails = JobDetails()
    interview_round_details:InterviewRoundDetails = InterviewRoundDetails()
    character_data: CharacterDataOutput = CharacterDataOutput()
    activity_details: ActivityDetailsOutputMessage = ActivityDetailsOutputMessage()
    activity_code_path:str = ""
    activity_raw_data_path: str = ""

class PromptInput(BaseModel):
    job_details:JobDetails = JobDetails()
    interview_round_details:InterviewRoundDetails = InterviewRoundDetails()
    example_character_data_output:List[CharacterDataOutput] = Field(default_factory=list)
    example_activity_details_output:List[ActivityDetailsOutputMessage] = Field(default_factory=list)
    example_starter_code_output:List[StarterCodeData] = Field(default_factory=list)
    example_job_details:List[JobDetails] = Field(default_factory=list)
    generated_activity_details_output:ActivityDetailsOutputMessage = ActivityDetailsOutputMessage()
    message:Any = None
    response_type:BaseInterviewPromptStrategy.RESPONSE_TYPE = BaseInterviewPromptStrategy.RESPONSE_TYPE.CHARACTER_INFO


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""
    prefix: str = ""
    default_settings: typing.ClassVar[S]

class BaseInterview(Configurable[BaseInterviewConfiguration], ABC):
    # base agent consists of the following:
    # settings: This would consist of name, id, profile, what task to do, budget etc 
    # provider: This would consist of two methods: counting tokens and chat completion api
    # Prompt strategy: This would consist of building prompt and parsing response content
    # Base Agent consists of common methods that are used by all agents
    llm_provider:Any = None
    prompt_strategy: Any = None
    interview_id:str = ""
    
    def __init__(
        self, 
        interview_id: str,
        interview_config: BaseInterviewConfiguration,
        llm_provider: ChatModelProvider,
        prompt_strategy: BaseInterviewPromptStrategy
    ):
        super(BaseInterview, self).__init__()

        self.config:InterviewSettings = interview_config.settings
        self.llm_provider = llm_provider
        self.prompt_strategy = prompt_strategy
        self.interview_id = interview_id
        
    def get_llm_info(self) -> ChatModelInfo:
        llm_name = self.config.fast_llm if self.config.big_brain else self.config.slow_llm
        return OPENAI_CHAT_MODELS[llm_name]
    
    def build_prompt(self, **kwargs):
        # this returns a chat prompt which is a list of messages
        prompt = self.prompt_strategy.build_prompt(**kwargs)
        return prompt

    async def run_model(self, prompt, response_type):
        if response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.CHARACTER_INFO.value:
            response = await self.llm_provider.create_chat_completion(
                chat_messages = prompt,
                model_name = "gpt-4o",
                completion_parser = lambda r: self.parse_and_process_response_character_info(r, prompt),
                is_json_mode = True
            )

        elif response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.ACTIVITY_DETAILS.value:
            print ("Running activity details model")
            response = await self.llm_provider.create_chat_completion(
                chat_messages = prompt,
                model_name = "gpt-4o",
                completion_parser = lambda r: self.parse_and_process_response_activity_details_scenario(r, prompt),
                is_json_mode = True
            )

        elif response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.STARTER_CODE_GENERATION.value:
            response = await self.llm_provider.create_chat_completion(
                chat_messages = prompt,
                model_name = "gpt-4o",
                completion_parser = lambda r: self.parse_and_process_response_starter_code(r, prompt),
                is_json_mode = True
            )
        
        return response.parsed_response    
    
    
    async def get_character_information(self, prompt:ChatMessage) -> CharacterDataOutput:
        response = await self.run_model(prompt, BaseInterviewPromptStrategy.RESPONSE_TYPE.CHARACTER_INFO)
        return response
    
    async def get_activity_details(self, prompt:ChatMessage) -> ActivityDetailsOutputMessage:
        response = await self.run_model(prompt, BaseInterviewPromptStrategy.RESPONSE_TYPE.ACTIVITY_DETAILS)
        return response

    async def get_starter_code(self, prompt:ChatMessage) -> StarterCodeData:
        response = await self.run_model(prompt, BaseInterviewPromptStrategy.RESPONSE_TYPE.STARTER_CODE_GENERATION)
        return response
    
    @abstractmethod
    def parse_and_process_response_character_info(self,response, prompt):
        pass     

    @abstractmethod
    def parse_and_process_response_activity_details_scenario(self,response, prompt):
        pass

    @abstractmethod
    def parse_and_process_response_starter_code(self,response, prompt):
        pass