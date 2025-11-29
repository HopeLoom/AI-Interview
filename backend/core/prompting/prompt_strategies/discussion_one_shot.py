from core.prompting.base import BaseDiscussionPromptStrategy
from core.prompting.schema import LanguageModelClassification
from core.resource.model_providers.schema import AssistantChatMessage, ChatMessage
from core.prompting.schema import ChatPrompt
import json
from discussion.base import FeedbackOutput, ConsensusOutput, ActivityDetailsInputMessage, FeedbackInput, ConsensusInput, ActivityCodeInputMessage
from typing import List
from activity_agent.base import BaseActivityConfiguration

class DiscussionPromptStrategy(BaseDiscussionPromptStrategy):

    def __init__(self, configuration):
        self.config = configuration 
        self.response_schema = None # JSON schema for response validation
        self.system_message = None

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL
    
    def build_prompt(self, **kwargs):
        
        response_type = kwargs.get("response_type")
        prompt_details = kwargs.get("prompt_details")

        if response_type == DiscussionPromptStrategy.RESPONSE_TYPE.FEEDBACK_INFO:
            activity_data = prompt_details.activity_data
            isCode = prompt_details.isCode

            if isCode:
                user_prompt = f"Here are the code details:{activity_data.activity_code_generation}\n" + f"Here are the activity details:{activity_data.activity_details}" + "\n"
            else:
                activity_details = activity_data.activity_details
                user_prompt = f"Here are the activity details: {activity_details}" + "\n"
        
        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_INFO:
            activity_data = prompt_details.activity_data
            consensus_output:ConsensusOutput = prompt_details.consensus_output
            interview_config = activity_data.interview_config

            job_details = interview_config.job_details
            interview_details = interview_config.interview_details
            character_data = interview_config.character_data

            user_prompt = "Here is the job description: " + job_details.model_dump_json() + "\n" + "Here are the interview details for which you should generate the activity: " + interview_details.model_dump_json() + "\n"
            user_prompt += "Here is the panelist involved in the interview: " + character_data.model_dump_json() + "\n"
            user_prompt += "Here is the overall feedback from the panelists for your previous activity generation: " + consensus_output.model_dump_json() + "\n"
            user_prompt += "Here is the previous activity details you generated: " + activity_data.activity_details.model_dump_json() + "\n"

        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_CODE_INFO:

            activity_data = prompt_details.activity_data
            consensus_output:ConsensusOutput = prompt_details.consensus_output
            interview_config = activity_data.interview_config

            job_details = interview_config.job_details
            interview_details = interview_config.interview_details
            character_data = interview_config.character_data
            
            user_prompt = "Here is the job description: " + job_details.model_dump_json() + "\n" + "Here are the interview details for which you should generate the activity: " + interview_details.model_dump_json() + "\n"
            user_prompt += "Here is the panelist involved in the interview: " + character_data.model_dump_json() + "\n"
            user_prompt += "Here is the overall feedback from the panelists for your previous code generation: " + consensus_output.model_dump_json() + "\n"
            user_prompt += "Here is the previous activity details you generated: " + activity_data.activity_code_generation.model_dump_json() + "\n"

        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.CONSENSUS_INFO:
            feedbackData = prompt_details.feedbackData 
            activity_data = prompt_details.activity_data
            activity_details = activity_data.activity_details

            user_prompt = "Here are the feedback details: " + str(feedbackData) + "\n"  + "Here are the activity details: " + activity_details.model_dump_json() + "\n"
        
        self.system_message = self.build_system_prompt(**kwargs)
        
        prompt = ChatPrompt(
            messages = [
                ChatMessage.system(self.system_message),
                ChatMessage.user(user_prompt)
            ]
        ) 

        return prompt
    
    def build_system_prompt(self, **kwargs):
        response_type = kwargs.get("response_type")
        prompt_details = kwargs.get("prompt_details")
        if response_type == DiscussionPromptStrategy.RESPONSE_TYPE.FEEDBACK_INFO:
            system_message = self._generate_feedback_info_prompt(prompt_details)
        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_INFO:
            system_message = self._generate_activity_info_prompt(prompt_details)
        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.ACTIVITY_CODE_INFO:
            system_message = self._generate_activity_code_info_prompt(prompt_details)
        elif response_type == DiscussionPromptStrategy.RESPONSE_TYPE.CONSENSUS_INFO:
            system_message = self._generate_consensus_info_prompt(prompt_details)
        
        return system_message
    


    def _generate_feedback_info_prompt(self, prompt_details:FeedbackInput):

        output = FeedbackOutput()

        activity_data = prompt_details.activity_data

        interview_config = activity_data.interview_config
        job_details = interview_config.job_details


        character_data = prompt_details.character_data
        previous_feedback:List[FeedbackOutput] = prompt_details.previous_feedback 
        
        return (f"You are acting as one of the interviewers in the panel with information about your character mentioned here: {character_data}.\n"
                "You are reviewing information about the details of the interview that has to be conducted with a candidate particularly the activity during the interview.\n"
                f"Here is the other information including the job description that the interview is for: {job_details}\n"
                "Your goal is to generate your feedback on what you think about the activity that has been designed for the interview. Activity details will be provided to you by the user\n"
                f"If you have provided any feedback before, it will be mentioned here: {previous_feedback}\n"
                f"Respond in JSON format with the structure mentioned here: {output.model_dump_json()}"
                "You must generate a generic scenario but don't make it exactly match with the job description. You must deviate from it while ensuring the same set of skills are evaluated\n"
                "Feedback type can be either positive or negative. Its has be realistic activity that the candidate will face in their day-to-day work so ensure its done like that\n"
                "Make sure your feedback is not more than 2 sentences long\n"
                "Be critical while providing feedback and ensure you provide a valid reason for your feedback\n"
                )
    

    def _generate_activity_info_prompt(self, prompt_details:ActivityDetailsInputMessage):
        
        output = ""
        return (
            "You are a data science/machine learning interview's technical round activity generator\n"
            "Your goal is to come up with the exact details of the technical round activity that will be conducted during the interview.\n"
            "You have already generated activity details and have received feedback from the interviewers in the panel regarding it. You will be provided with this feedback\n"
            "You must consider the feedback and generate a better version of the activity details that the interviewers will accept by making changes to the previously generated activity information\n"
            "Activity is mainly about simulating a realistic scenario that the team of the specific company faces in their day-to-day work. The AI/ML/Data science team is responsible for building and shipping the models that are used in the different products\n"
            "Activity should be solved via coding. To make the activity more interesting, some additional information can also be considered to complete the coding problem. This information can be anything from logs to raw data. This is more like what information can be made use of \n"
            "There are different types of activity that is possible which includes: fixing a bug, implementing a feature, building evaluation metrics or running analysis on raw data etc.\n"
            "For the candidate, they only have access to a notepad editor so consider this when generating the scenario\n"
            f"Respond in JSON format with the following structure: {output}\n"
            "An example to consider: \n"
            "description: There is some issue with the existing results of a model that is trained to predict heartattack from smartwatch sensor data. " + 
            "Smartwatch sensor data includes heart rate, step count data recorded at fixed frequencies. We are already using decision tree model for the prediction trained on the smartwatch data but somehow the results are coming out to be highly skewed towards one class. The goal is to fix this issue\n"
            "reason: We are evaluating the candidate on their skills of understanding the problem, figuring out the details and fixing the issue. Here the issue is focussing on machine learning/data science where candidate has to consider the whole pipeline to ensure the results come out to be good\n"
            )
    

    def _generate_activity_code_info_prompt(self, prompt_details:ActivityCodeInputMessage):

        output = ""
        return (
            "You are a code snippet generator for the technical round activity\n"
            "You have already determined the details of the technical round activity that will be conducted during the interview.\n"
            "Your goal is to come up with the starter code that will used by the candidate to solve the technical round activity.\n"
            "Generate code in python language\n"
            "The code must be generic and not involve any specific libraries\n"
            "Only response with code and no other information\n"
            f"Respond in JSON format with the following structure: {output}\n"
            "The code you generate will be used by another system to generate the additional information\n"
            "Note that you have already received feedback from the interviewers in the panel regarding the quality of your previously generated code \n"
            "Based on the feedback, make sure you generate a better version of the code that the panelists are looking for\n"
        )

    def _generate_consensus_info_prompt(self, prompt_details):

        output = ConsensusOutput()

        return (
            "You are figuring out whether different panelists have reached a consensus regarding the feedback they have generated with regards to the interview that is conducted for the candidate.\n"
            "You will be provided with the feedback from all the candidates.\n"
            "You will also be provided with the activity details which is in question.\n"
            f"You must respond in JSON format with the structure mentioned here: {output.model_dump_json()}\n"
            "Consensus type can be REACHED or NOT_REACHED\n"
            "Consensus can only be reached if all the panelists have the same positive opinion about the activity details and they are satisfied about it\n"
        )


    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            json_data = json.loads(response.content)
        except json.JSONDecodeError:
            json_data = response.content

        return json_data