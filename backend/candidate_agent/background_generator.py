from pydantic import BaseModel
from core.prompting.schema import LanguageModelClassification, ChatPrompt
from core.resource.model_providers.schema import ChatMessage
from panelist_agent.background import Background, Education, Experience, Skills, Projects, CurrentOccupation
import json

class BackgroundGeneratorConfiguration(BaseModel):
    modeltype:str = LanguageModelClassification.SMART_MODEL

class BackgroundGenerator():
    
    def __init__(self,
                 modeltype):
        self.modeltype = modeltype
        self.system_prompt = self.build_system_prompt()
        
    
    def build_system_prompt(self):
        self.system_message = self._generate_profile_prompt()
        return self.system_message
    

    def _generate_profile_prompt(self):
        background = Background()
        background.name = ""
        background.age = 0
        background.current_occupation = CurrentOccupation()
        background.education = [Education()]
        background.experience = [Experience()]
        background.skills = [Skills()]
        background.projects = [Projects()]


        return (
            "Your task is to generate professional profile of a user in a specific format given the resume/cv of the user.\n"
            "Ensure you extract information from the provided resume contents in the correct manner.\n"
            "If there is no information about gender and age mentioned in the resume, you can try to extract it from the rest of the details mentioned in the resume.\n"
            "Please note that gender can either be male or female and age can be any number between 18 and 65.\n"
            "Skill level must be between 0 and 5\n"
            f"You must respond with JSON with the following structure: {background.model_dump_json()}\n"
        )
    
    def build_user_prompt(self, resume):
        user_prompt = f"Resume data can be here: {resume}"
        return user_prompt
        
    def build_prompt(self, resume_data):
        user_prompt = self.build_user_prompt(resume_data)
        system_message = ChatMessage.system(self.system_prompt)
        user_message = ChatMessage.user(user_prompt)
        chat_prompt = ChatPrompt(messages=[system_message, user_message])
        return chat_prompt

    @staticmethod
    def parse_response_content(response):
        print ("callback is triggered")
        # extract ai profile and directives from json response
        json_data = json.loads(response.content)
        print (json_data)
        background = Background.model_validate(json_data)
        return background

async def generate_background_info(llm_provider, resume_data):
    print ("Background Generator")
    default_configuration = BackgroundGeneratorConfiguration()
    default_configuration.modeltype = LanguageModelClassification.SMART_MODEL
    background_generator = BackgroundGenerator(**default_configuration.dict())
    prompt = background_generator.build_prompt(resume_data)
    output = await llm_provider.create_chat_completion(
        chat_messages = prompt,
        model_name = llm_provider.default_settings.name,
        completion_parser = BackgroundGenerator.parse_response_content,
        is_json_mode = True
    )
    return output.parsed_response
