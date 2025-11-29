from core.prompting.base import BasePanelistPromptStrategy
from core.prompting.schema import LanguageModelClassification
from core.resource.model_providers.schema import AssistantChatMessage, ReasoningChatMessage, ChatMessage, ReflectionChatMessage, MasterChatMessage
from core.prompting.schema import ChatPrompt
import json
import os 
from typing import List, cast
from panelist_agent.base import DomainKnowledgeOutputMessage, PromptInput, BasePanelistConfiguration, Profile, ReasoningOutputMessage, ReflectionOutputMessage, EvaluationOutputMessage, ResponseOutputMessage
from master_agent.base import CommunicationMessage, MasterMessageStructure, SubTopicData, InterviewTopicData, InterviewRound, TOPICS_TECHNICAL_ROUND, SUBTOPICS_HR_ROUND, SUBTOPICS_TECHNICAL_ROUND, TOPICS_HR_ROUND
from panelist_agent.base import Profile, CriteriaSpecificScoring, Experience, ResponseWithReasoningOutputMessage
from interview_details_agent.base import BaseInterviewConfiguration, JobDetails
from core.prompting.prompt_strategies.panelist_common_prompts import PanelistCommonPrompts
from activity_agent.base import ActivityProgressAnalysisSummaryForPanelistOutputMessage
from core.database.base import DatabaseInterface

class PanelistPromptStrategy(BasePanelistPromptStrategy):

    def __init__(self, configuration, interview_config, database):
        print ("PanelistPrompt is initialized")
        self.panelist_config:BasePanelistConfiguration = configuration
        self.interview_config:BaseInterviewConfiguration = interview_config
        self.job_details:JobDetails = self.interview_config.job_details
        self.interview_round_details = self.interview_config.interview_round_details
        self.interview_round_one_details = self.interview_round_details.rounds["interview_round_1"].description
        self.interview_round_two_details = self.interview_round_details.rounds["interview_round_2"].description
        self.character_data = self.interview_config.character_data
        self.activity_details = self.interview_config.activity_details
        self.database:DatabaseInterface = database
        # Load starter code asynchronously
        import asyncio
        self.starter_code_data = asyncio.run(self.load_activity_code_info()) if database else ""
        self.my_profile:Profile = self.panelist_config.profile        
        self.panelist_common_prompts = PanelistCommonPrompts(self.panelist_config,self.interview_config, database)

    async def load_activity_code_info(self):
        code = await self.database.fetch_starter_code_from_url() if self.database else ""
        return code 

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL
    
    def convert_simulation_type(self, simulation_history: List[MasterChatMessage]) -> List[str]:
        conversation_history = [f"Speaker:{message.speaker}, dialog:{message.content}\n" for message in simulation_history]
        return conversation_history
    
    def convert_reflection_type(self, reflection_history: List[ReflectionChatMessage]) -> str:
        reflection_strings = [f"{message.character_name}: {message.reflection}" for message in reflection_history]
        reflection_history_string = "\n".join(reflection_strings)
        return reflection_history_string
    
    def convert_reasoning_type(self, reasoning_history: List[ReasoningChatMessage]) -> str:
        reasoning_strings = [f"{message.interview_thoughts_for_myself}" for message in reasoning_history]
        reasoning_history_string = "\n".join(reasoning_strings)
        return reasoning_history_string
    
    def parse_process_response_model(self, response: AssistantChatMessage):
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return ResponseOutputMessage()
                decision_output = ResponseOutputMessage.model_validate(json_data)
            else:
                decision_output = ResponseOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            decision_output = ResponseOutputMessage()
            
        return decision_output
    
    def parse_response_reason_content(self, response: AssistantChatMessage):
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return ReasoningOutputMessage()
                think_output = ReasoningOutputMessage.model_validate(json_data)
            else:
                think_output = ReasoningOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            think_output = ReasoningOutputMessage()
        return think_output
    
    def parse_response_evaluate_content(self, response: AssistantChatMessage):
        try:    
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return EvaluationOutputMessage()
                feedback_output = EvaluationOutputMessage.model_validate(json_data)
            else:
                feedback_output = EvaluationOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            feedback_output = EvaluationOutputMessage()
        return feedback_output

    def parse_response_reflect_content(self, response: AssistantChatMessage):
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return ReflectionOutputMessage()
                reflection_output = ReflectionOutputMessage.model_validate(json_data)
            else:
                reflection_output = ReflectionOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            reflection_output = ReflectionOutputMessage()
        return reflection_output

    def parse_response_domain_knowledge_content(self, response):
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return DomainKnowledgeOutputMessage()
                domain_knowledge_output = DomainKnowledgeOutputMessage.model_validate(json_data)
            else:
                domain_knowledge_output = DomainKnowledgeOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            domain_knowledge_output = DomainKnowledgeOutputMessage()
        return domain_knowledge_output


    def parse_process_respond_with_reasoning_model(self, response: AssistantChatMessage):
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
                if "error" in json_data.keys():
                    return ResponseWithReasoningOutputMessage()
                decision_output = ResponseWithReasoningOutputMessage.model_validate(json_data)
            else:
                decision_output = ResponseWithReasoningOutputMessage()
        except Exception as e:
            print (f"Error parsing response: {e}")
            decision_output = ResponseWithReasoningOutputMessage()
        return decision_output
    
    def build_prompt(self, prompt_input:PromptInput) -> ChatPrompt:
        
        response_type = prompt_input.response_type
        candidate_profile = prompt_input.candidate_profile
        message = prompt_input.message
        reasoning_output = prompt_input.reason
        domain_knowledge_output = prompt_input.domain_knowledge
        activity_progress = prompt_input.activity_progress
        activity_code_from_candidate = prompt_input.activity_code_from_candidate
        subqueries_data = prompt_input.subqueries_data
        reflection_history = prompt_input.reflection_history

        if response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.REASON:
            system_prompt = self._generate_reasoning_prompt(candidate_profile, 
                                                            message, 
                                                            activity_progress)
            
        elif response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.RESPOND:
            system_prompt = self._generate_response_prompt(candidate_profile, 
                                                           message, 
                                                           reasoning_output, 
                                                           domain_knowledge_output,
                                                           activity_progress)

        elif response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.REFLECT:
            system_prompt = self._generate_reflection_prompt(candidate_profile, 
                                                             message, 
                                                             reflection_history)
            
        elif response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.EVALUATE:
            system_prompt = self._generate_evaluation_prompt(candidate_profile, 
                                                             message,
                                                             activity_progress,
                                                             activity_code_from_candidate, subqueries_data)

        elif response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.DOMAIN_KNOWLEDGE:
            system_prompt = self._generate_domain_knowledge_prompt(candidate_profile, 
                                                                   message, 
                                                                   reasoning_output, 
                                                                   activity_progress)
        
        elif response_type == BasePanelistPromptStrategy.RESPONSE_TYPE.RESPOND_WITH_REASONING:
            system_prompt = self._generate_response_with_reasoning_prompt(candidate_profile, 
                                                                         message, 
                                                                         activity_progress)
        prompt = ChatPrompt(
            messages = [
                ChatMessage.system(system_prompt),
                ]
            ) 

        return prompt


    def _generate_reasoning_prompt(self, 
                                   candidate_profile:Profile,
                                   input_message:CommunicationMessage, 
                                   activity_progress):
        
        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message.content)
        speaker:Profile = cast(Profile, master_message.speaker)
        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        remaining_topics = master_message.remaining_topics
        remaining_time = master_message.remaining_time
        topic_completion = master_message.topic_completion_message
        speaker_determination_reason = master_message.speaker_determination_message.reason_for_selecting_next_speaker
        advice_for_speaker = master_message.advice.advice_for_speaker
        should_wrap_up_current_topic = master_message.advice.should_wrap_up_current_topic
        should_end_interview = master_message.advice.should_end_the_interview
        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(speaker_occupation.lower())
        
        speaker_name = speaker.background.name
        topic:InterviewTopicData = master_message.topic
        subtopic:SubTopicData = master_message.sub_topic
        current_section = master_message.current_section
        interview_round = master_message.current_interview_round
        panelist_thoughts = master_message.panelist_thoughts
        # panelist thoughts is a dict of key being name and value being list of thoughts which is ReasoningChatMessage
        panelist_thoughts_string_representation = []
        for name, thoughts in panelist_thoughts.items():
            if len(thoughts) > 0:
                panelist_thoughts_string_representation.append(f"{name}: {self.convert_reasoning_type(thoughts)}")

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_description = self.interview_round_one_details
        else:
            interview_round_description = self.interview_round_two_details
    
        reason_output = ReasoningOutputMessage()

        background_prompt = (
            f"You are an employee at {self.job_details.company_name}, with your name being {speaker_name} and your role as {speaker_occupation}.\n"
            "You are currently conducting an interview with a candidate.\n"
        )

        candidate_experience:List[Experience] = candidate_profile.background.experience

        candidate_experience_data = []
        for experience in candidate_experience:
            candidate_experience_data.append(experience.model_dump_json())

        base_prompt = (
            "**Candidate Profile:**\n"
            f"1. Candidate Name:{candidate_profile.background.name}\n"
            f"2. Candidate Bio:{candidate_profile.background.bio}\n"
            f"3. Candidate Current Occupation: {candidate_profile.background.current_occupation.model_dump_json()}\n"
            f"4. Candidate Experience: {candidate_experience_data}\n"
            f"**Current Interview Round Description:** {interview_round_description}\n"
            f"**Job Description:** {self.job_details.job_description}\n\n"
            f"** Job Position:** {self.job_details.job_title}\n"
            f"**Job Requirements:** {self.job_details.job_requirements}\n"
            f"**Job Qualifications:** {self.job_details.job_qualifications}\n"
            "### **Preparing to Speak**\n"
            "Before responding, you must **frame your thoughts** to ensure a structured and relevant conversation.\n\n"
        )

        if interview_round == InterviewRound.ROUND_TWO:

            panelist_profiles = master_message.panelist_profiles
            other_panelist_profiles = [profile for profile in panelist_profiles if profile.background.name != speaker.background.name]

            other_panelist_names = ','.join([profile.background.name for profile in other_panelist_profiles])
            other_panelist_occupations = ','.join([profile.background.current_occupation.occupation for profile in other_panelist_profiles])

            base_prompt += (f"You have also other panelist members in the interview. Their name is mentioned here: {other_panelist_names} and their occupation is mentioned here: {other_panelist_occupations}.\n")
            

            output_prompt = (
                f"Your response must be in JSON format, following this structure: {reason_output.model_dump_json()}.\n\n"
                
                "### **What to Consider when generating the output:**\n"
                
                "**What Has Already Been Covered:**\n"
                "- Use the interview transcript to track what has been discussed.\n"
                "- Avoid repeating what the other panelist has already said but you can add to it if it leads to a more productive discussion.\n"
                f"- Your previous set of thoughts along with the the other panelist's thoughts are mentioned here: {panelist_thoughts_string_representation}. This will help you understand how you and the other panelist thought about when generating the response\n"
                "You will find the actual responses in the conversation history.\n"
                f" **Current Discussion Topic:** {subtopic.name}\n"
                f" **Topic Description:** {subtopic.description}\n"
                f" **Current Section Being Discussed:** {current_section}\n\n"

                "**Advice from the Hiring Manager (Optional):**\n"
                f"- Optional Guidance provided by the hiring manager supervising the interview that you can follow but not mandatory: {advice_for_speaker}.\n"
                
                f"Why the current topic is still being discussed is mentioned here: {topic_completion.reason}. This will tell you why the current topic is still being discussed and what are the pending things to make the topic complete\n"
                f"Should you wrap up the current topic? Indicated here: {should_wrap_up_current_topic}.\n"
                "- If `True`,transition towards closing the current topic and don't ask any question but instead figure out what you need to do based on the topic completion reason to finish conversation in this topic.\n" 
                "- If `False`, continue the conversation on the current topic.\n"
                "- Avoid mentioning anything about wrapping up the topic to anyone. This information is only for you.\n"
                f"Should you end the interview? Indicated here: {should_end_interview}.\n"
                "- If `True`, transition towards closing the interview.\n"
                "- If `False`, continue the interview.\n"
                " **Remaining topics that need to be covered after the current topic is completed:**\n"
                f"   - {remaining_topics}.\n"
                "### **Important Instructions:**\n"
                "- **Think in the first-person perspective** as the role assigned to you.\n"
                "- **Ensure you integrate the last response in the conversation in your next response**.\n"
                "- **Only ask one question at a time**—avoid asking multiple questions in a single response.\n"
                "- ** Do not repeat your question more than twice**. Select a completely different question after two repetitions.\n"
                "- DO NOT wrap up the interview until and unless should_end_interview is True.\n"
                "- If there is no conversation history and the interview just began, then ensure the other panelist is requested after you to provide their response.\n"
                "### **Additional Instructions:**\n"
                "Your output will be used as input for the next step, where a response will be crafted for the candidate or the panelist.\n"
                "Do not let the candidate know on how they are doing in the interview.\n"
                "Do not provide any kind of hints to the candidate. if they are requesting for guidance, just tell them on a high level. No code logic or metric calculation should be provided.\n"
                "Do not say thank you until the end of the interview. Do not provide any kind of feedback to the candidate.\n"
                "Do not let the candidate know why the question is being asked. Just ask the question and let them answer.\n"
                "If the candidate is asking something, then make sure you include that in your response.\n"
                "If you plan to ask a question to candidate, then ensure you consider their previous response if applicable\n"
                "In the context of areas to cover in the next response, make sure it aligns with the current topic and reason behind why the current topic is being discussed\n"
                "Facts corresponding to the areas to cover are more on the lines of what information is needed to back the areas to be addressed. For eg, if the areas to cover include introduction, then the facts should be all the information you need to provide an introduction\n"                
                "Everything has to be grounded to the current discussion topic and its description with the current section within it.\n"
                "Structure of the interview defined using topics and sections has to be adhered to.\n"
                "If the candidate is asking for clarification or more details to the previously posted question to them, make sure you don't provide any kind of answer that helps them in answering your original question\n"
                "Another important point is to ensure that if you are asking a new question and you have already asked some question just before this, then make sure you form a logical connection between the two\n"
                "Make sure you follow the real life interview process\n"
                "You are free to speak with the other panelist as well.Remember that interview is being conducted by yourself and the other panelist in a collaborative manner\n"
                "In addition, follow the rules relevant to the topic mentioned here:\n"
            )
                    
        conversation_history_for_current_subtopic = master_message.conversation_history_for_current_subtopic
        last_completed_conversation_history = master_message.last_completed_conversation_history
        conversation_summary_for_current_topic = master_message.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = master_message.conversation_summary_for_completed_topics

        additional_prompt = ''
        conversation_data = ''
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"
        
        conversation_data = ''
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_simulation_type(conversation_history_for_current_subtopic)
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        else:
            additional_prompt += "Conversation has not started yet\n"

        interview_round_specific_prompt = self.panelist_common_prompts.get_topic_interview_round_specific_prompt(topic.name, subtopic.name, activity_progress, interview_round, BasePanelistPromptStrategy.RESPONSE_TYPE.REASON)
        
        conversation_usage_prompt = self.panelist_common_prompts.get_conversation_usage_prompt()

        overall_prompt = background_prompt + role_prompt + base_prompt + conversation_usage_prompt + additional_prompt + output_prompt + interview_round_specific_prompt

        return overall_prompt


    def _generate_response_with_reasoning_prompt(self, 
                                                 candidate_profile:Profile, 
                                                 input_message:CommunicationMessage, 
                                                 activity_progress):
        
        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message.content)
        speaker:Profile = cast(Profile, master_message.speaker)
        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        remaining_topics = master_message.remaining_topics
        remaining_time = master_message.remaining_time
        topic_completion = master_message.topic_completion_message
        speaker_determination_reason = master_message.speaker_determination_message.reason_for_selecting_next_speaker
        advice_for_speaker = master_message.advice.advice_for_speaker
        should_wrap_up_current_topic = master_message.advice.should_wrap_up_current_topic
        should_end_interview = master_message.advice.should_end_the_interview
        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(speaker_occupation.lower())
        
        speaker_name = speaker.background.name
        topic:InterviewTopicData = master_message.topic
        subtopic:SubTopicData = master_message.sub_topic
        current_section = master_message.current_section
        interview_round = master_message.current_interview_round
        panelist_thoughts = master_message.panelist_thoughts
        # panelist thoughts is a dict of key being name and value being list of thoughts which is ReasoningChatMessage
        panelist_thoughts_string_representation = []
        for name, thoughts in panelist_thoughts.items():
            if len(thoughts) > 0:
                panelist_thoughts_string_representation.append(f"{name}: {self.convert_reasoning_type(thoughts)}")

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_description = self.interview_round_one_details
        else:
            interview_round_description = self.interview_round_two_details
    
        reason_output = ResponseWithReasoningOutputMessage()

        background_prompt = (
            f"You are an employee at {self.job_details.company_name}, with your name being {speaker_name} and your role as {speaker_occupation}.\n"
            "You are currently conducting an interview with a candidate.\n"
        )

        candidate_experience:List[Experience] = candidate_profile.background.experience

        candidate_experience_data = []
        for experience in candidate_experience:
            candidate_experience_data.append(experience.model_dump_json())

        base_prompt = (
            "**Candidate Profile:**\n"
            f"1. Candidate Name:{candidate_profile.background.name}\n"
            f"2. Candidate Bio:{candidate_profile.background.bio}\n"
            f"3. Candidate Current Occupation: {candidate_profile.background.current_occupation.model_dump_json()}\n"
            f"4. Candidate Experience: {candidate_experience_data}\n"
            f"**Current Interview Round Description:** {interview_round_description}\n"
            f"**Job Description:** {self.job_details.job_description}\n\n"
            f"** Job Position:** {self.job_details.job_title}\n"
            f"**Job Requirements:** {self.job_details.job_requirements}\n"
            f"**Job Qualifications:** {self.job_details.job_qualifications}\n"
            "### **Preparing to Speak**\n"
            "Before generating the dialog response, you must **frame your thoughts** to ensure a structured and relevant conversation.\n\n"
        )

        if interview_round == InterviewRound.ROUND_TWO:

            panelist_profiles = master_message.panelist_profiles
            other_panelist_profiles = [profile for profile in panelist_profiles if profile.background.name != speaker.background.name]

            other_panelist_names = ','.join([profile.background.name for profile in other_panelist_profiles])
            other_panelist_occupations = ','.join([profile.background.current_occupation.occupation for profile in other_panelist_profiles])

            base_prompt += (f"You have also other panelist members in the interview. Their name is mentioned here: {other_panelist_names} and their occupation is mentioned here: {other_panelist_occupations}.\n")
            

            output_prompt = (
                f"Your response must be in JSON format, following this structure: {reason_output.model_dump_json()}.\n\n"
                
                "### **What to Consider when generating the output:**\n"
                
                "**What Has Already Been Covered:**\n"
                "- Use the interview transcript to track what has been discussed.\n"
                "- Avoid repeating what the other panelist has already said but you can add to it if it leads to a more productive discussion.\n"
                f"- Your previous set of thoughts along with the the other panelist's thoughts are mentioned here: {panelist_thoughts_string_representation}. This will help you understand how you and the other panelist thought about when generating the response\n"
                "You will find the actual responses in the conversation history.\n"
                f" **Current Discussion Topic:** {subtopic.name}\n"
                f" **Topic Description:** {subtopic.description}\n"
                f" **Current Section Being Discussed:** {current_section}\n\n"

                "**Advice from the Hiring Manager (Optional):**\n"
                f"- Optional Guidance provided by the hiring manager supervising the interview that you can follow but not mandatory: {advice_for_speaker}.\n"
                
                f"Why the current topic is still being discussed is mentioned here: {topic_completion.reason}. This will tell you why the current topic is still being discussed and what are the pending things to make the topic complete\n"
                f"Should you wrap up the current topic? Indicated here: {should_wrap_up_current_topic}.\n"
                "- If `True`,transition towards closing the current topic and don't ask any question but instead figure out what you need to do based on the topic completion reason to finish conversation in this topic.\n" 
                "- If `False`, continue the conversation on the current topic.\n"
                "- Avoid mentioning anything about wrapping up the topic to anyone. This information is only for you.\n"
                f"Should you end the interview? Indicated here: {should_end_interview}.\n"
                "- If `True`, transition towards closing the interview.\n"
                "- If `False`, continue the interview.\n"
                " **Remaining topics that need to be covered after the current topic is completed:**\n"
                f"   - {remaining_topics}.\n"
                "### **Important Instructions:**\n"
                "- **Think in the first-person perspective** as the role assigned to you.\n"
                "- **Ensure you integrate the last response in the conversation in your response**.\n"
                "- **Only ask one question at a time**—avoid asking multiple questions in a single response.\n"
                "- ** Do not repeat your question more than twice**. Select a completely different question after two repetitions.\n"
                "- DO NOT wrap up the interview until and unless should_end_interview is True.\n"
                "- If there is no conversation history and the interview just began, then ensure the other panelist is requested after you to provide their response.\n"
                "### **Additional Instructions:**\n"
                "Do not let the candidate know on how they are doing in the interview.\n"
                "When generating the actual dialog response, consider all the thoughts. Also add emotions to make it sound like a real human.\n"
                "Do not provide any kind of hints to the candidate. if they are requesting for guidance, just tell them on a high level. No code logic or metric calculation should be provided.\n"
                "Do not say thank you until the end of the interview. Do not provide any kind of feedback to the candidate.\n"
                "Do not let the candidate know why the question is being asked. Just ask the question and let them answer.\n"
                "If the candidate is asking something, then make sure you include that in your response.\n"
                "If you plan to ask a question to candidate, then ensure you consider their previous response if applicable\n"
                "In the context of areas to cover in the response, make sure it aligns with the current topic and reason behind why the current topic is being discussed\n"
                "Facts corresponding to the areas to cover are more on the lines of what information is needed to back the areas to be addressed. For eg, if the areas to cover include introduction, then the facts should be all the information you need to provide an introduction\n"                
                "Everything has to be grounded to the current discussion topic and its description with the current section within it.\n"
                "Structure of the interview defined using topics and sections has to be adhered to.\n"
                "If the candidate is asking for clarification or more details to the previously posted question to them, make sure you don't provide any kind of answer that helps them in answering your original question\n"
                "Another important point is to ensure that if you are asking a new question and you have already asked some question just before this, then make sure you form a logical connection between the two\n"
                "Make sure you follow the real life interview process\n"
                "You are free to speak with the other panelist as well.Remember that interview is being conducted by yourself and the other panelist in a collaborative manner\n"
                "In addition, follow the rules relevant to the topic mentioned here:\n"
            )
                    
        conversation_history_for_current_subtopic = master_message.conversation_history_for_current_subtopic
        last_completed_conversation_history = master_message.last_completed_conversation_history
        conversation_summary_for_current_topic = master_message.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = master_message.conversation_summary_for_completed_topics

        additional_prompt = ''
        conversation_data = ''
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"
        
        conversation_data = ''
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_simulation_type(conversation_history_for_current_subtopic)
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        else:
            additional_prompt += "Conversation has not started yet\n"

        interview_round_specific_prompt = self.panelist_common_prompts.get_topic_interview_round_specific_prompt(topic.name, subtopic.name, activity_progress, interview_round, BasePanelistPromptStrategy.RESPONSE_TYPE.REASON)
        
        conversation_usage_prompt = self.panelist_common_prompts.get_conversation_usage_prompt()

        overall_prompt = background_prompt + role_prompt + base_prompt + conversation_usage_prompt + additional_prompt + output_prompt + interview_round_specific_prompt

        return overall_prompt
    

    def _generate_domain_knowledge_prompt(self, 
                                        candidate_profile:Profile, 
                                        input_message:CommunicationMessage, 
                                        reasoning_output, 
                                        activity_progress:ActivityProgressAnalysisSummaryForPanelistOutputMessage):

        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message.content)
        speaker:Profile = cast(Profile, master_message.speaker)
        topic:InterviewTopicData = master_message.topic
        subtopic:SubTopicData = master_message.sub_topic
        interview_round = master_message.current_interview_round
        current_section = master_message.current_section
     
        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        speaker_name = speaker.background.name
        
        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(speaker_occupation.lower())

        domain_output_message = DomainKnowledgeOutputMessage()

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_details = self.interview_round_one_details
        else:
            interview_round_details = self.interview_round_two_details

        candidate_experience:List[Experience] = candidate_profile.background.experience

        candidate_experience_data = []
        for experience in candidate_experience:
            candidate_experience_data.append(experience.model_dump_json())

        background_prompt = (
            f"### **Role: Interviewer at {self.job_details.company_name}**\n"
            f"**Your Name:** {speaker_name} | **Your Role:** {speaker_occupation}\n\n"
            
            "### **Candidate Information**\n"
            f"1. Candidate Name:{candidate_profile.background.name}\n"
            f"2. Candidate Bio:{candidate_profile.background.bio}\n"
            f"3. Candidate Current Occupation: {candidate_profile.background.current_occupation.model_dump_json()}\n"
            f"4. Candidate Experience: {candidate_experience_data}\n"

            f"**Interview Round Details:** {interview_round_details}\n"
            f"**Job Description:** {self.job_details.job_description}\n\n"
            f"**Job Requirements:** {self.job_details.job_requirements}\n"
            f"**Job Qualifications:** {self.job_details.job_qualifications}\n\n"

            "### **Current Discussion Focus**\n"
            f"**Topic:** {subtopic.name}\n"
            f"**Topic Description:** {subtopic.description}\n"
            f"**Current Section Being Discussed:** {current_section}\n\n"

            "⚡ **Your goal is to conduct a structured and insightful interview while ensuring a logical flow in the conversation.**\n"
        )


        base_prompt = (
            "### **Structuring Your Response to the Candidate**\n"
            
            "To generate an appropriate and well-informed response, follow this structured process:\n\n"

            "1**Frame Your Response:** Think about what to say in response to the candidate, ensuring clarity and relevance.\n"
            "2**Assess the Need for Domain Knowledge:** Determine if specialized expertise is required to formulate a precise response.\n\n"
            
            f"**Your Thought Process So Far:** {reasoning_output.model_dump_json()}\n"
            "**Next Step:** Generate the necessary domain-specific information to support your response, ensuring that it aligns with the interview topic and candidate's discussion.\n"
        )


        conversation_history_for_current_subtopic = master_message.conversation_history_for_current_subtopic
        last_completed_conversation_history = master_message.last_completed_conversation_history
        conversation_summary_for_current_topic = master_message.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = master_message.conversation_summary_for_completed_topics

        additional_prompt = ''
        conversation_data = ''
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"
        
        conversation_data = ''
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_simulation_type(conversation_history_for_current_subtopic)
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        else:
            additional_prompt += "Conversation has not started yet\n"

        output_prompt = (
            "**Goal:**\n"
            "Retrieve the necessary domain knowledge based on the conversation context and reasoning step. Ensure the information is **precise, relevant, and strictly necessary**.\n\n"
            
            "**Guidelines:**\n"
            "1 **Extract only the knowledge needed** to provide a well-informed response—avoid unnecessary details.\n"
            "2 **Ensure relevance** by connecting the retrieved knowledge directly to the candidate’s inquiry or the conversation.\n"
            "3 **Avoid speculation**—base the knowledge strictly on factual, established principles.\n"
            "4 **Keep it concise**—the explanation should be **clear, direct, and not overly technical unless required**.\n\n"
            f"Respond in JSON format following this structure: {domain_output_message.model_dump_json()}.\n"
            "You must strictly adhere to the character assigned to you and ensure that your response stays within their abilities and knowledge.\n"
            "Do not provide any kind of hints to the candidate. if they are requesting for guidance, just tell them on a high level. No code logic or metric calculation should be provided.\n"
            "In addition, follow the rules relevant to the topic mentioned here:\n"
        )

        interview_round_specific_prompt = self.panelist_common_prompts.get_topic_interview_round_specific_prompt(topic.name,subtopic.name, activity_progress, interview_round, BasePanelistPromptStrategy.RESPONSE_TYPE.DOMAIN_KNOWLEDGE)

        conversation_prompt = self.panelist_common_prompts.get_conversation_usage_prompt()
        
        overall_prompt = background_prompt + base_prompt + role_prompt + domain_prompt + conversation_prompt + additional_prompt + output_prompt + interview_round_specific_prompt

        return overall_prompt

    
    def _generate_response_prompt(self, 
                                  candidate_profile:Profile, 
                                  input_message:CommunicationMessage, 
                                  think_output:ReasoningOutputMessage,
                                  domain_knowledge_output:DomainKnowledgeOutputMessage,
                                  activity_progress:ActivityProgressAnalysisSummaryForPanelistOutputMessage):

        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message.content)
        speaker:Profile = cast(Profile, master_message.speaker)
        topic:InterviewTopicData = master_message.topic
        interview_round = master_message.current_interview_round
        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        speaker_name = speaker.background.name
        subtopic:SubTopicData = master_message.sub_topic
        current_section = master_message.current_section

        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(speaker_occupation.lower())

        response_output = ResponseOutputMessage()

        candidate_experience:List[Experience] = candidate_profile.background.experience

        candidate_experience_data = []
        for experience in candidate_experience:
            candidate_experience_data.append(experience.model_dump_json())

        background_prompt = (
            f"You are an employee at {self.job_details.company_name}, with your name as {speaker_name} and your occupation as {speaker_occupation}.\n"
            "You are currently conducting an interview with a candidate.\n"
            "**Candidate Profile:**\n"
            f"1. Candidate Name:{candidate_profile.background.name}\n"
            f"2. Candidate Bio:{candidate_profile.background.bio}\n"
            f"3. Candidate Current Occupation: {candidate_profile.background.current_occupation.model_dump_json()}\n"
            f"4. Candidate Experience: {candidate_experience_data}\n"

            f"Interview is conducted for the job position of: {self.job_details.job_title}\n"
        )

        if interview_round == InterviewRound.ROUND_TWO:

            panelist_profiles = master_message.panelist_profiles
            other_panelist_profiles = [profile for profile in panelist_profiles if profile.background.name != speaker.background.name]

            other_panelist_names = ','.join([profile.background.name for profile in other_panelist_profiles])
            other_panelist_occupations = ','.join([profile.background.current_occupation.occupation for profile in other_panelist_profiles])

            background_prompt += (f"You have also other panelist member in the interview. Their name is mentioned here: {other_panelist_names} and their occupation is mentioned here: {other_panelist_occupations}.\n")

        if think_output.is_domain_knowledge_access_needed == False:
            domain_knowledge_output = DomainKnowledgeOutputMessage()
            domain_knowledge_output.topic = "No domain knowledge is needed for this response."
        
        output_prompt = (
            "Its now your turn to say something in the ongoing conversation to keep the interview progressing.\n\n"
            "You have been following a structured approach to generate the response which includes:\n"
            f"1 **Your feelings about how the interview is going and what should be in focus in the next response:** {think_output.interview_thoughts_for_myself}\n"
            f"2. **Should I ask a new question in this response:** {think_output.should_i_ask_a_new_question}\n"
            f"3. **Are my questions too repetitive and if True, then i should change anything in my response :** {think_output.are_my_questions_too_repetitive}\n"
            f"4. **Areas to focus in the Next Response. if the areas are empty, then i can use the conversation context:** {think_output.areas_to_cover_in_next_response}\n"
            f"5. **Facts Corresponding to Areas to Cover in the Response:** {think_output.facts_corresponding_to_areas_to_cover_in_next_response}\n"
            f"6. **Areas covered previously:** {think_output.areas_already_covered}\n"
            f"7. **Is Domain Knowledge Access Needed:** {think_output.is_domain_knowledge_access_needed}\n\n"
            f"8. **Relevant Domain Knowledge (if applicable):** {domain_knowledge_output.model_dump_json()}\n\n"
            f"9. **Current Discussion Topic:** {subtopic.name}\n"
            f"10. **Topic Description:** {subtopic.description}\n"
            f"11. **Current Section Being Discussed:** {current_section}\n\n"
            "### **Guidelines for Your Response:**\n"
            "- ** Make use of your thought process to structure your response effectively.\n"
            "- **Adhere to Your Role:** Respond strictly as per your assigned character's knowledge and expertise.\n"
            "- ** Ensure that your response follows the thought process and is not adding any extra information to it.\n"
            "- ** Consider the last response from the user and smoothly integrate with the new response you will generate using your thought process.\n"
            
            "### **Format for Your Response:**\n"
            f"Respond in JSON format following this structure: {response_output.model_dump_json()}.\n\n"
            "Here the key is response and value is the dialog you will generate.\n"
            "Please make sure response only contains the final dialog to be said since you will say this out loud.\n"
            "Also add emotions to make it sound like a real human.\n"
            "** Style: ** Maintain a professional tone but ensure response is easy to understand.\n"
            "If your response is ending the interview, then make sure you don't ask any question in the response.\n"
            "Do not provide any kind of hints to the candidate. if they are requesting for guidance, just tell them on a high level. No code logic or metric calculation should be provided.\n"
            "Do not say thank you until the end of the interview. Do not provide any kind of feedback to the candidate.\n"
            "Do not let the candidate know why the question is being asked. Just ask the question and let them answer.\n"
            "Do not mention what you will get to know from the candidate's response. Just ask the question and let them answer.\n"
            "Do not tell the candidate how are they doing in the interview. Do not give them any praise or criticism. You are neutral in your tone.\n"
            "Just follow your thought process. Nothing beyond that\n"
            "Everything has to be grounded to the current discussion topic and its description with the current section within it.\n"
            "Structure of the interview defined using topics and sections has to be adhered to.\n"
            "If the candidate is asking for clarification or more details to the previously posted question to them, make sure you don't provide any kind of answer that helps them in answering your original question\n"
            "if you are about to end the interview, don't let the candidate ask you or the other panelist any question.\n"
            "Do not output an empty string as dialog in the output. You have to say something in the dialog.\n"
        )


        if interview_round == InterviewRound.ROUND_TWO:
            output_prompt += ("If the other panelist has already said something, you don't have to repeat the same thing. You can add your thoughts on top of what the other panelist has said.\n"
                              "You can find this information in the conversation history and conversation summary.\n")
   
            if topic.name == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value or topic.name == TOPICS_TECHNICAL_ROUND.DEEP_DIVE_QA.value:

                if subtopic.name == SUBTOPICS_TECHNICAL_ROUND.TASK_SPECIFIC_DISCUSSION.value or subtopic.name == SUBTOPICS_TECHNICAL_ROUND.PROBLEM_SOLVING.value or subtopic.name == SUBTOPICS_TECHNICAL_ROUND.CONCEPTUAL_KNOWLEDGE_CHECK.value:
                    
                    output_prompt += (
                        "- **Technical Problem Details presented to the candidate:**\n"
                        f"1. Scenario: {self.activity_details.scenario}\n"
                        f"2. Data Available: {self.activity_details.data_available}\n"
                        f"3. Task for the Candidate: {self.activity_details.task_for_the_candidate}\n\n" 
                        f"4. Starter Code provided to the candidate:** {self.starter_code_data}\n\n"
                        " 5. Time for coding round and clarification: 15 minutes\n\n"         
                        "- **Analysis of the Candidate’s Approach in solving the problem is mentioned here:**\n" 
                        f"1. Performance summary: {activity_progress.candidate_performance_summary}\n"
                        f"2. Percentage of question solved: {activity_progress.percentage_of_question_solved}\n"
                        #f"3. Things left to be solved: {activity_progress.things_left_to_do_with_respect_to_question}\n"
                    )

        output_prompt += ("Do not mention things like: this will inform us or this will help us or this will give us insights. You should not mention anything to the candidate about why you are asking the question. Just have a normal conversation and don't let the candidate feel that the interview is going on\n")
        
        conversation_history_for_current_subtopic = master_message.conversation_history_for_current_subtopic
        last_completed_conversation_history = master_message.last_completed_conversation_history
        conversation_summary_for_current_topic = master_message.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = master_message.conversation_summary_for_completed_topics

        additional_prompt = ''
        conversation_data = ''

        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"
        
        conversation_data = ''
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_simulation_type(conversation_history_for_current_subtopic)
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        else:
            additional_prompt += "Conversation has not started yet\n"

        conversation_usage_prompt = self.panelist_common_prompts.get_conversation_usage_prompt()

        overall_prompt = background_prompt + role_prompt + conversation_usage_prompt + additional_prompt + output_prompt

        return overall_prompt
    
    def _generate_reflection_prompt(self, candidate_profile, 
                                    input_message:CommunicationMessage, 
                                    reflection_history:List[ReflectionChatMessage]):
        
        reflection_output = ReflectionOutputMessage()
        reflection_history_string = self.convert_reflection_type(reflection_history)

        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message.content)
        interview_round = master_message.current_interview_round
        topic:InterviewTopicData = master_message.topic
        subtopic:SubTopicData = master_message.sub_topic

        name = self.my_profile.background.name
        my_occupation = self.my_profile.background.current_occupation.occupation.lower()
        name = self.my_profile.background.name

        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(my_occupation.lower())
        
        conversation_history_for_current_subtopic = master_message.conversation_history_for_current_subtopic
        last_completed_conversation_history = master_message.last_completed_conversation_history
        conversation_summary_for_current_topic = master_message.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = master_message.conversation_summary_for_completed_topics

        additional_prompt = ''
        conversation_data = ''
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"
        
        conversation_data = ''
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_simulation_type(conversation_history_for_current_subtopic)
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        else:
            additional_prompt += "Conversation has not started yet\n"


        reflection_prompt = f"""
"You are one of the panelists conducting an interview with your name being: {name}. Your profile is mentioned here: {self.my_profile.model_dump_json()} 
"The interview is about the job description mentioned here: {self.job_details.job_description}.
"The job responsibilities are mentioned here: {self.job_details.job_requirements}.
"The job qualifications are mentioned here: {self.job_details.job_qualifications}.
"The current interview round is mentioned here: {interview_round}.
"The current topic being discussed is mentioned here: {subtopic.model_dump_json()}.
"You goal is to reflect on the interview process and the candidate getting interviewed. 
"You will be provided with the interview transcript consisting of the panelists including yourself and the candidate in the interiew.
"Reflection is more about how you feel interview is going, your opinions about the candidate and the interview process.
        """

        output_prompt = (
            f"Based on all the information you are provided with, you must respond in JSON format and need to generate the reflection in the following format{reflection_output.model_dump_json()}.\n"
        )
        
        reflection_data_prompt = self._add_reflection_history(reflection_history_string)

        overall_prompt = reflection_prompt + role_prompt + reflection_data_prompt + output_prompt + additional_prompt

        return overall_prompt
    
    def _generate_evaluation_prompt(self,candidate_profile:Profile, 
                                    input_message:MasterMessageStructure,
                                    activity_progress,
                                    activity_code_from_candidate,
                                    subqueries_data):
        
        master_message:MasterMessageStructure = cast(MasterMessageStructure, input_message)

        speaker:Profile = cast(Profile, master_message.speaker)
        topic:InterviewTopicData = master_message.topic
        subtopic:SubTopicData = master_message.sub_topic
        interview_round = master_message.current_interview_round
        current_section = master_message.current_section

        name = self.my_profile.background.name
        evaluation_criteria = master_message.evaluation_criteria

        evaluationOutput = EvaluationOutputMessage()
        evaluationOutput.feedback_to_the_hiring_manager_about_candidate = ""
        evaluationOutput.score = 0
        
        candidate_name = candidate_profile.background.name
        my_occupation = self.my_profile.background.current_occupation.occupation.lower()
        name = self.my_profile.background.name
        
        role_prompt, domain_prompt = self.panelist_common_prompts.get_role_specific_prompt(my_occupation.lower())

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_details = self.interview_round_one_details
        else:
            interview_round_details = self.interview_round_two_details

        candidate_experience:List[Experience] = candidate_profile.background.experience

        candidate_experience_data = []
        for experience in candidate_experience:
            candidate_experience_data.append(experience.model_dump_json())

        
        background_prompt = f"""
"You are an interviewer at {self.job_details.company_name}, with your name as {name} and your role as {my_occupation}.
"You are currently conducting an interview with a candidate whose profile is provided here:.
"**Candidate Profile:**
1. Candidate Name:{candidate_profile.background.name}
2. Candidate Bio:{candidate_profile.background.bio}
3. Candidate Current Occupation: {candidate_profile.background.current_occupation.model_dump_json()}
4. Candidate Experience: {candidate_experience_data}

"Interview is conducted for the following job position: {self.job_details.job_title}.
"job description is mentioned here: {self.job_details.job_description}.
"job requirements are mentioned here: {self.job_details.job_requirements}.
"job qualifications are mentioned here: {self.job_details.job_qualifications}.

"Interview is structured with multiple topics and each topic is divided into multiple sections.
"**Topic:** {subtopic.name}
"**Topic Description:** {subtopic.description}

"### **Evaluation Process:**
"- The discussion on the current topic has now concluded, and it's time to evaluate the candidate ({candidate_name}).
"- You will be provided with the **interview transcript**.
        """

        output_prompt = f"""
"Respond in JSON format using the structure defined here: {evaluationOutput.model_dump_json()}.

"As the interviewer, you are expected to provide both:
"1. A **score** between 1 and 5 for each evaluation criterion.
"2. A **written summary for the hiring manager**, explaining the candidate’s strengths, weaknesses, and overall performance in this topic.

"### **Evaluation Approach:**
"- Base your assessment **strictly on what the candidate said or did** during the interview.
"- Do **not infer or assume skills** that were not clearly demonstrated.
"- Your evaluation should be **fair, objective, and consistent** across all candidates.
"- Stay focused on your role in this round and evaluate only the topic assigned to you.

"### **Scoring Scale (0 to 5):**
"**0 (Not Assessed):** Not enough evidence to evaluate this criterion.
"**1 (Poor):** Very limited or no understanding. Responses were incorrect, off-topic, or unclear.
"**2 (Below Expectations):** Superficial or partial understanding with key gaps or confusion.
"**3 (Developing / Average):** Some understanding shown; responses had merit but lacked completeness, structure, or clarity.
"**4 (Meets Expectations):** Solid understanding with clear, well-reasoned, and relevant responses. Some small gaps acceptable.
"**5 (Excellent):** Candidate showed exceptional clarity, confidence, and structured thinking. They demonstrated a wide range of relevant knowledge and explained ideas effectively within the time constraints — even if no single topic was covered in great depth.

"### **Important Instructions:**
"- The interview is structured with only **3–4 questions and one optional follow-up** per topic.
"- As a result, candidates may not go deeply into every topic. Focus your evaluation on the **breadth, clarity, and relevance** of what was shared.
"- Provide **specific feedback** in your summary to help the hiring manager understand how the candidate performed in this topic.
"- **Do not penalize the candidate for lack of technical depth or deep examples.** The format does not allow for it.
"- Focus your evaluation on whether the candidate demonstrated a **broad and well-structured understanding** across the key ideas that were discussed.
"- Give credit for **range, clarity, and relevance**, even if the candidate did not go deep into any one area.
"- A candidate who references multiple relevant concepts briefly should be scored higher than one who goes deep into only one topic.

"Another important aspect is ensuring your perspective/skillset is reflected in the feedback to the hiring manager. Since you are an {my_occupation}, ensure your feedback is aligned with the role you are playing in the interview.
"You have to be critical in your evaluation since you are part of the hiring team and you have to ensure high quality candidates are selected for the job
"Also, don't be too optmistic in your evaluation. You have to be realistic in your evaluation and ensure that the candidate is not getting over evaluated.
"For evaluation, if certain facts are present to back your analysis, then it will be found here: {subqueries_data.model_dump_json()}.
"Facts are important to fact check the candidate responses as well catch any contradictions that might exist in their responses.
"You must only use the facts provided to determine the accuracy of the responses. Do not consider your own knowledge in this case
"In addition, follow the rules relevant to the topic mentioned here:
        """

        last_completed_conversation_history = master_message.last_completed_conversation_history

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_simulation_type(last_completed_conversation_history)
        else:
            last_completed_conversation_history = []

        additional_prompt = (f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n")
        
        evaluation_topic_wise_prompt =  self.panelist_common_prompts.get_evaluation_topic_wise_prompt(interview_round, topic.name, subtopic.name, activity_progress, activity_code_from_candidate)
        
        overall_prompt = background_prompt + role_prompt +  additional_prompt + output_prompt + evaluation_topic_wise_prompt

        return overall_prompt

    def _add_conversation_history(self, conversation_history:List[str]) -> List[str]:
        if not conversation_history:
            return [
                "There is no conversation history between the candidate and the interviewer yet."
            ]
        return [
            f"Here is the recent conversation history between the candidate and the interviewer.\n \
            {conversation_history}"
        ]
    
    def _add_reflection_history(self, reflection_history:str) -> str:
        if not reflection_history:
            return (
                "You did not have any reflections in the past"
            )
        return (
            f"Here is the history of the reflection.\n \
            {reflection_history}"
        )