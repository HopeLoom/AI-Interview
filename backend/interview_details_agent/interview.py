import json
from typing import Any

from interview_details_agent.base import (
    ActivityDetailsOutputMessage,
    BaseInterview,
    BaseInterviewConfiguration,
    BaseInterviewPromptStrategy,
    CharacterDataOutput,
    PromptInput,
    StarterCodeData,
)

from core.prompting.prompt_strategies.interview_one_shot import InterviewGenerationPromptStrategy
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelProvider,
)


class Interview(BaseInterview):
    config: BaseInterviewConfiguration = BaseInterviewConfiguration()
    prompt_strategy: Any = None

    def __init__(
        self,
        interview_id,
        interview_config: BaseInterviewConfiguration,
        llm_provider: ChatModelProvider,
    ):
        prompt_strategy = InterviewGenerationPromptStrategy(interview_config)
        super().__init__(
            interview_id=interview_id,
            interview_config=interview_config,
            llm_provider=llm_provider,
            prompt_strategy=prompt_strategy,
        )
        print(f"Interview id: {interview_id}")
        # this calls the __init__ method of the base agent
        self.prompt_strategy = prompt_strategy
        self.job_details = interview_config.job_details
        self.interview_round_details = interview_config.interview_round_details
        self.character_data = interview_config.character_data
        self.activity_details = interview_config.activity_details

    def build_prompt(self, **kwargs):
        return super().build_prompt(**kwargs)

    def parse_and_process_response_character_info(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> CharacterDataOutput:
        data = self.prompt_strategy.parse_response_content(response)
        try:
            if response.content is None:
                raise Exception("Response content is None")
            json_data = json.loads(response.content)
            data = CharacterDataOutput.model_validate(json_data)
        except Exception as e:
            print(f"Error parsing character info: {e}")
            data = CharacterDataOutput()
            data.reason = f"Error parsing character info: {e}"
        return data

    def parse_and_process_response_activity_details_scenario(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> ActivityDetailsOutputMessage:
        data = self.prompt_strategy.parse_response_content(response)
        try:
            if response.content is None:
                raise Exception("Response content is None")
            json_data = json.loads(response.content)
            data = ActivityDetailsOutputMessage.model_validate(json_data)
        except Exception as e:
            print(f"Error parsing activity details: {e}")
            data = ActivityDetailsOutputMessage()
        return data

    def parse_and_process_response_starter_code(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> StarterCodeData:
        data = self.prompt_strategy.parse_response_content(response)
        try:
            if response.content is None:
                raise Exception("Response content is None")
            json_data = json.loads(response.content)
            data = StarterCodeData.model_validate(json_data)
        except Exception as e:
            print(f"Error parsing starter code: {e}")
            data = StarterCodeData()
        return data

    async def generate_character_information(self, example_character_data) -> CharacterDataOutput:
        prompt_input = PromptInput()
        prompt_input.response_type = BaseInterviewPromptStrategy.RESPONSE_TYPE.CHARACTER_INFO
        prompt_input.job_details = self.job_details
        prompt_input.interview_round_details = self.interview_round_details
        prompt_input.example_character_data_output = example_character_data
        prompt = super().build_prompt(prompt_input=prompt_input)
        data = await super().get_character_information(prompt)
        return data

    async def generate_activity_details(
        self, example_job_details, example_activity_details
    ) -> ActivityDetailsOutputMessage:
        prompt_input = PromptInput()
        prompt_input.response_type = BaseInterviewPromptStrategy.RESPONSE_TYPE.ACTIVITY_DETAILS
        prompt_input.job_details = self.job_details
        prompt_input.interview_round_details = self.interview_round_details
        prompt_input.example_job_details = example_job_details
        prompt_input.example_activity_details_output = example_activity_details
        prompt = super().build_prompt(prompt_input=prompt_input)
        data = await super().get_activity_details(prompt)
        return data

    async def generate_starter_code(
        self,
        example_activity_details,
        example_starter_code_output,
        generated_activity_details_output,
    ) -> StarterCodeData:
        prompt_input = PromptInput()
        prompt_input.response_type = (
            BaseInterviewPromptStrategy.RESPONSE_TYPE.STARTER_CODE_GENERATION
        )
        prompt_input.job_details = self.job_details
        prompt_input.interview_round_details = self.interview_round_details
        prompt_input.example_activity_details_output = example_activity_details
        prompt_input.example_starter_code_output = example_starter_code_output
        prompt_input.generated_activity_details_output = generated_activity_details_output
        prompt = super().build_prompt(prompt_input=prompt_input)
        data = await super().get_starter_code(prompt)
        return data
