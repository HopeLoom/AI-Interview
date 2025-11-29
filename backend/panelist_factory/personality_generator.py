import json

from interview_details_agent.base import CharacterData
from pydantic import BaseModel

from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import ChatMessage
from panelist_agent.base import INTENSITY_LEVELS, Background
from panelist_agent.personality import Personality


class PersonalityGeneratorConfiguration(BaseModel):
    modeltype: str = LanguageModelClassification.SMART_MODEL


class PersonalityGenerator:
    def __init__(self, modeltype):
        self.modeltype = modeltype
        self.system_prompt = self.build_system_prompt()

    def build_system_prompt(self):
        system_prompt_parts = self._generate_intro_prompt()
        system_message = "\n".join(system_prompt_parts)
        return system_message

    def _generate_intro_prompt(self):
        personality = Personality()
        intensity_level_json = {level.name: level.value for level in INTENSITY_LEVELS}
        return [
            "You are part of the system which is responsible for conducting interview for a candidate.\n"
            "You have already figured out the information about the different panelists that should be part of the interview.\n"
            "You have also generated their background profiles with a comprehensive set of information.\n"
            "You now have to generate big 5 personality traits profile for the panelist.\n"
            "Each of the personality traits has an intensity level associated with it.\n"
            f"These intensity levels are categorized into three levels: mentioned here: {intensity_level_json}\n",
            "Along with the intensity levels, you also provide a very short description of how they exhibit that trait during a conversation.\n"
            f"You must respond in JSON with the following structure {personality.model_dump_json()}.\n",
        ]

    def build_user_prompt(self, background: Background, character_data):
        user_prompt = (
            "The following is the background information about the character for which personality information has to be generated:\n"
            f"background: {background.model_dump_json()}\n"
        )
        return user_prompt

    def build_prompt(self, background, character_data):
        system_message = ChatMessage.system(self.system_prompt)
        user_prompt = self.build_user_prompt(background, character_data)
        user_message = ChatMessage.user(user_prompt)
        chat_prompt = ChatPrompt(messages=[system_message, user_message])
        return chat_prompt

    @staticmethod
    def parse_response_content(response):
        print("personality callback is triggered")
        json_data = json.loads(response.content)
        personality = Personality.model_validate(json_data)
        return personality


async def generate_personality_info(
    llm_provider, background: Background, character_data: CharacterData
):
    print("Personality Generator")
    default_configuration = PersonalityGeneratorConfiguration()
    default_configuration.modeltype = LanguageModelClassification.SMART_MODEL
    agent_profile_generator = PersonalityGenerator(**default_configuration.dict())
    prompts = agent_profile_generator.build_prompt(background, character_data)
    output = await llm_provider.create_chat_completion(
        chat_messages=prompts,
        model_name=llm_provider.default_settings.name,
        completion_parser=PersonalityGenerator.parse_response_content,
        is_json_mode=True,
    )
    # output is a ChatModelResponse object. The callback that gets triggered is saved in parsed_response
    return output.parsed_response
