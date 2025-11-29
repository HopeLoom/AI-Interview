import json

from candidate_agent.base import INTENSITY_LEVELS
from pydantic import BaseModel

from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import ChatMessage
from panelist_agent.personality import Personality


class PersonalityGeneratorConfiguration(BaseModel):
    modeltype: str = LanguageModelClassification.SMART_MODEL


class PersonalityGenerator:
    def __init__(self, modeltype):
        self.modeltype = modeltype
        self.system_prompt = self.build_system_prompt()

    def build_system_prompt(self):
        self.system_message = self._generate_personality_prompt()
        return self.system_message

    def _generate_personality_prompt(self):
        intensity_level_json = {level.name: level.value for level in INTENSITY_LEVELS}
        personality = Personality()
        return (
            "You are responsible for generating personality information for the user. In terms of peronality, you specifically look at 5 personality traits along with their intensity levels.\n"
            "The personality traits are: openness, conscientiousness, extraversion, agreeableness, and neuroticism. For each of personality traits, while you determine the intensity levels between LOW, MEDIUM and HIGH, you must also give a one line reason\n"
            "You will be provided by the user with the professional background information that was extracted from their resume.\n"
            "Apart from the background information, you will also be provided with the raw resume data to better understand the user professional background.\n"
            "The main aim is to make sure we are able to accurately determine how user is as a person especially in their work environment.\n"
            f"You must respond with JSON with the following structure {personality.model_dump_json()}. The intensity levels for each of the personalities can be one of the following: {intensity_level_json}\n"
        )

    def build_user_prompt(self, background, resume_data):
        user_prompt = f"Background: {background}" + "\n" + f"Resume data: {resume_data}"
        return user_prompt

    def build_prompt(self, background, resume_data):
        system_message = ChatMessage.system(self.system_prompt)
        user_prompt = self.build_user_prompt(background, resume_data)
        user_message = ChatMessage.user(user_prompt)
        chat_prompt = ChatPrompt(messages=[system_message, user_message])
        return chat_prompt

    @staticmethod
    def parse_response_content(response):
        print("personality callback is triggered")
        json_data = json.loads(response.content)
        personality = Personality.model_validate(json_data)
        return personality


async def generate_personality_info(llm_provider, background, resume_data):
    print("Cadndidate Personality Generator")
    default_configuration = PersonalityGeneratorConfiguration()
    default_configuration.modeltype = LanguageModelClassification.SMART_MODEL
    # default_configuration.system_prompt = system_prompt
    agent_profile_generator = PersonalityGenerator(**default_configuration.dict())
    prompts = agent_profile_generator.build_prompt(background, resume_data)
    output = await llm_provider.create_chat_completion(
        chat_messages=prompts,
        model_name=llm_provider.default_settings.name,
        completion_parser=PersonalityGenerator.parse_response_content,
        is_json_mode=True,
    )

    # output is a ChatModelResponse object. The callback that gets triggered is saved in parsed_response
    return output.parsed_response
