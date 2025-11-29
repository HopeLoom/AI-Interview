import json

from interview_details_agent.base import CharacterData
from pydantic import BaseModel

from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import ChatMessage
from panelist_agent.background import (
    Background,
    CurrentOccupation,
    Education,
    Experience,
    Projects,
    Skills,
)


class BackgroundGeneratorConfiguration(BaseModel):
    modeltype: str = LanguageModelClassification.SMART_MODEL


class BackgroundGenerator:
    def __init__(self, modeltype):
        self.modeltype = modeltype
        self.system_prompt = self.build_system_prompt()

    def build_system_prompt(self):
        system_prompt_parts = self._generate_intro_prompt()
        self.system_message = "\n".join(system_prompt_parts)
        return self.system_message

    def _generate_intro_prompt(self):
        background = Background()
        education = Education()
        experience = Experience()
        skills = Skills()
        projects = Projects()
        background.education = [education]
        background.experience = [experience]
        background.skills = [skills]
        background.projects = [projects]
        background.current_occupation = CurrentOccupation()

        return [
            "You are part of the system which is responsible for conducting interview for a candidate.\n"
            "You have already figured out the information about the different candidates that should be part of the interview.\n"
            "You now have to generate background profile for the panelist ffor which user will provide you with the character data:\n"
            f"You must respond in JSON with the following structure: {background.model_dump_json()}\n"
            "Make sure the background is as realistic as possible to real life.\n"
            "Make use of all the information provided by the user to generate the background profile.\n"
            "Also ensure you generate all background information in the right format that is provided to you.\n"
            "Do not change anything with respect to the details provided about the character by the user.\n"
        ]

    def build_user_prompt(self, character_data: CharacterData):
        user_prompt = (
            "The following is the information about the character for which background information has to be generated:\n"
            f"Character ID: {character_data.character_id}\n"
            f"Character Name: {character_data.character_name}\n"
            f"Role: {character_data.role}\n"
            f"Objective: {character_data.objective}\n"
            f"Job Description: {character_data.job_description}\n"
            f"Interview Round Part Of: {character_data.interview_round_part_of}\n"
        )

        return user_prompt

    def build_prompt(self, character_data: CharacterData):
        user_prompt = self.build_user_prompt(character_data=character_data)
        print("system prompt is:", self.system_prompt)
        system_message = ChatMessage.system(self.system_prompt)
        user_message = ChatMessage.user(user_prompt)
        chat_prompt = ChatPrompt(messages=[system_message, user_message])
        return chat_prompt

    @staticmethod
    def parse_response_content(response):
        print("callback is triggered")
        # extract ai profile and directives from json response
        json_data = json.loads(response.content)
        print("json_data background:", json_data)
        background = Background()
        background.name = json_data["name"]
        background.age = json_data["age"]
        background.bio = json_data["bio"]
        background.gender = json_data["gender"]
        background.current_occupation = CurrentOccupation(
            **json.loads(json_data["current_occupation"])
        )
        background.education = [
            Education(**json.loads(education)) for education in json_data["education"]
        ]
        background.experience = [
            Experience(**json.loads(experience)) for experience in json_data["experience"]
        ]
        background.skills = [Skills(**json.loads(skill)) for skill in json_data["skills"]]
        background.projects = [Projects(**json.loads(project)) for project in json_data["projects"]]
        print("background completed")
        return background


async def generate_background_info(llm_provider, character_data: CharacterData):
    print("Background Generator")
    default_configuration = BackgroundGeneratorConfiguration()
    default_configuration.modeltype = LanguageModelClassification.SMART_MODEL
    background_generator = BackgroundGenerator(**default_configuration.dict())
    prompt = background_generator.build_prompt(character_data)

    output = await llm_provider.create_chat_completion(
        chat_messages=prompt,
        model_name=llm_provider.default_settings.name,
        completion_parser=BackgroundGenerator.parse_response_content,
        is_json_mode=True,
    )
    # output is a ChatModelResponse object. The callback that gets triggered is saved in parsed_response
    return output.parsed_response
