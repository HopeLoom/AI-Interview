import json

from candidate_agent.base import BaseCandidateConfiguration, Profile

from core.prompting.base import BaseCandidatePromptStrategy
from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    MasterChatMessage,
)
from master_agent.base import (
    CommunicationMessage,
    InterviewRound,
    InterviewTopicData,
    MasterMessageStructure,
    SubTopicData,
)
from panelist_agent.base import (
    DomainKnowledgeOutputMessage,
    PromptInput,
    ReasoningOutputMessage,
    ResponseOutputMessage,
)


class CandidatePromptStrategy(BaseCandidatePromptStrategy):
    def __init__(self, configuration):
        self.candidate_config: BaseCandidateConfiguration = configuration
        self.my_profile: Profile = self.candidate_config.profile

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL

    def convert_simulation_type(self, simulation_history: list[MasterChatMessage]):
        if simulation_history is None:
            return ""
        conversation_history_strings = [
            f"Speaker:{message.speaker}, dialog:{message.content}\n"
            for message in simulation_history
        ]
        conversation_history = "\n".join(conversation_history_strings)
        return conversation_history

    def parse_response_respond_content(self, response: AssistantChatMessage):
        json_data = json.loads(response.content) if response.content is not None else {}
        response_output = ResponseOutputMessage.model_validate(json_data)
        return response_output

    def parse_response_reason_content(self, response: AssistantChatMessage):
        json_data = json.loads(response.content) if response.content is not None else {}
        reason_output = ReasoningOutputMessage.model_validate(json_data)
        return reason_output

    def parse_response_domain_knowledge_content(self, response: AssistantChatMessage):
        json_data = json.loads(response.content) if response.content is not None else {}
        domain_knowledge_output = DomainKnowledgeOutputMessage.model_validate(json_data)
        return domain_knowledge_output

    def build_prompt(self, prompt_input: PromptInput):
        response_type = prompt_input.response_type

        if response_type == BaseCandidatePromptStrategy.RESPONSE_TYPE.REASON:
            print("response type is reason")
            system_prompt = self._generate_reasoning_prompt(prompt_input)

        elif response_type == BaseCandidatePromptStrategy.RESPONSE_TYPE.RESPOND:
            print("response type is response")
            system_prompt = self._generate_response_prompt(prompt_input)

        elif response_type == BaseCandidatePromptStrategy.RESPONSE_TYPE.DOMAIN_KNOWLEDGE:
            print("response type is domain knowledge")
            system_prompt = self._generate_domain_knowledge_prompt(prompt_input)

        prompt = ChatPrompt(
            messages=[
                ChatMessage.system(system_prompt),
            ]
        )

        return prompt

    def _generate_domain_knowledge_prompt(self, input_message: PromptInput):
        message: CommunicationMessage = input_message.message
        master_message: MasterMessageStructure = message.content
        speaker: Profile = master_message.speaker
        job_description = master_message.job_details
        interview_round = master_message.interview_round

        panelist_list = master_message.panelist_profiles

        if interview_round == InterviewRound.ROUND_TWO:
            panelist_data = [
                f"Name:{panelist.background.name}, Occupation:{panelist.background.current_occupation.occupation}"
                for panelist in panelist_list
            ]
            panelist_data = "\n".join(panelist_data)
            panelist_prompt = f"The other panelists in the interview are:{panelist_data}\n"
        else:
            panelist_prompt = (
                "There are no other panelists in the interview and you are the only one\n"
            )

        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        speaker_name = speaker.background.name

        if speaker_occupation.contains("engineer"):
            role_prompt = (
                "A machine learning engineer is skiled in mathematics, programming, statistics and AI\n"
                "There responsibilities include developing machine learning models, deploying systems\n"
            )
        elif speaker_occupation.contains("HR"):
            role_prompt = "A HR manager is responsible for hiring, training, developing and retaining employees\n"
        elif speaker_occupation.contains("product"):
            role_prompt = ""

        domain_output_message = DomainKnowledgeOutputMessage()

        domain_prompt = (
            f"You are one of the interview panelists conducting interview of the candidate for the job description mentioned here: {job_description}."
            f"Your name is {speaker_name}, with your occupation being {speaker_occupation}.\n"
            f"Your work experience is mentioned here: {speaker.background.experience}.\n"
            f"Your educational qualifications are mentioned here: {speaker.background.education}.\n"
            f"Your skills are mentioned here: {speaker.background.skills}.\n"
            f"Being an interviewer in an ongoing interview with the current round being: {interview_round}, you need to think before generating"
        )

        output_prompt = f"Based on all the information you are provided with, you need to generate the domain knowledge in the following format{domain_output_message.model_dump_json()}.\n"

        overall_prompt = domain_prompt + role_prompt + panelist_prompt + output_prompt

        return overall_prompt

    def _generate_reasoning_prompt(self, input_message: PromptInput):
        message: CommunicationMessage = input_message.message
        master_message: MasterMessageStructure = message.content
        speaker: Profile = master_message.speaker
        speaker_occupation = speaker.background.current_occupation.occupation.lower()

        if speaker_occupation.contains("engineer"):
            role_prompt = (
                "A machine learning engineer is skiled in mathematics, programming, statistics and AI\n"
                "There responsibilities include developing machine learning models, deploying systems\n"
            )
        elif speaker_occupation.contains("HR"):
            role_prompt = "A HR manager is responsible for hiring, training, developing and retaining employees\n"
        elif speaker_occupation.contains("product"):
            role_prompt = ""

        speaker_name = speaker.background.name
        listener: Profile = master_message.listener
        advice = master_message.advice
        topic: InterviewTopicData = master_message.topic
        subtopic: SubTopicData = master_message.sub_topic

        job_description = master_message.job_details
        interview_round = master_message.interview_round
        panelist_list = master_message.panelist_profiles

        if interview_round == InterviewRound.ROUND_TWO:
            panelist_data = [
                f"Name:{panelist.background.name}, Occupation:{panelist.background.current_occupation.occupation}"
                for panelist in panelist_list
            ]
            panelist_data = "\n".join(panelist_data)
            panelist_prompt = f"The other panelists in the interview are:{panelist_data}\n"
        else:
            panelist_prompt = (
                "There are no other panelists in the interview and you are the only one\n"
            )

        npc_think_output = ReasoningOutputMessage()

        think_prompt = (
            f"You are one of the interview panelists conducting interview of the candidate for the job description mentioned here: {job_description}."
            f"Your name is {speaker_name}, with your occupation being {speaker_occupation}.\n"
            f"Your work experience is mentioned here: {speaker.background.experience}.\n"
            f"Your educational qualifications are mentioned here: {speaker.background.education}.\n"
            f"Your skills are mentioned here: {speaker.background.skills}.\n"
            f"Being an interviewer in an ongoing interview with the current round being: {interview_round}, you need to think before generating a response.\n"
            "You must consider your skillset and experience to frame your thoughts and opinions before responding.\n"
            f"With respect to the interview, right now, the following topic is being discussed: {topic}.\n"
            f"Within this topic, the primary focus is on the subtopic: {subtopic}.\n"
            f"If there is any previous set of conversation has happened between the panelists and the candidate, then it will be provided to you.\n"
            f"Your response is for {listener.background.name} and the advice given to you regarding what the response should contain is mentioned here: {advice}.\n"
        )

        output_prompt = (
            f"Based on all the information you are provided with, you need to generate your thoughts, opinions and whether expert skillset is required in the following format:{npc_think_output.model_dump_json()}.\n"
            "Skill set required for replying to the listener indicates whether the output flag is set to true or false.\n"
            "Consider the following while generating the output:\n"
            "1. The current state of the interview which is denoted by the current topic and subtopic being discussed.\n"
            "2. Your previous responses, candidates responses and what the other panelists are discussing if there are any.\n"
            "3. Your work experience, educational qualifications and skills.\n"
            "4. Consider candidate's details which will be provided to you by the user\n"
            "Note that your thoughts and opinions will be used to generate a response in the next step.\n"
        )

        overall_prompt = think_prompt + role_prompt + panelist_prompt + output_prompt

        return overall_prompt

    def _generate_response_prompt(self, input_message: PromptInput):
        message: CommunicationMessage = input_message.message
        master_message: MasterMessageStructure = message.content
        speaker: Profile = master_message.speaker
        topic: InterviewTopicData = master_message.topic
        subtopic: SubTopicData = master_message.sub_topic
        job_description = master_message.job_details
        interview_round = master_message.interview_round

        panelist_list = master_message.panelist_profiles

        if interview_round == InterviewRound.ROUND_TWO:
            panelist_data = [
                f"Name:{panelist.background.name}, Occupation:{panelist.background.current_occupation.occupation}"
                for panelist in panelist_list
            ]
            panelist_data = "\n".join(panelist_data)
            panelist_prompt = f"The other panelists in the interview are:{panelist_data}\n"
        else:
            panelist_prompt = (
                "There are no other panelists in the interview and you are the only one\n"
            )

        speaker_occupation = speaker.background.current_occupation.occupation.lower()
        speaker_name = speaker.background.name

        if speaker_occupation.contains("engineer"):
            role_prompt = (
                "A machine learning engineer is skiled in mathematics, programming, statistics and AI\n"
                "There responsibilities include developing machine learning models, deploying systems\n"
            )
        elif speaker_occupation.contains("HR"):
            role_prompt = "A HR manager is responsible for hiring, training, developing and retaining employees\n"
        elif speaker_occupation.contains("product"):
            role_prompt = ""

        npc_dialog_output_message = ResponseOutputMessage()

        dialog_prompt = (
            f"You are one of the interview panelists conducting interview of the candidate for the job description mentioned here: {job_description}."
            f"Your name is {speaker_name}, with your occupation being {speaker_occupation}.\n"
            f"Your work experience is mentioned here: {speaker.background.experience}.\n"
            f"Your educational qualifications are mentioned here: {speaker.background.education}.\n"
            f"Your skills are mentioned here: {speaker.background.skills}.\n"
            f"Being an interviewer in an ongoing interview with the current round being: {interview_round}, you need to think before generating a response.\n"
            "You must consider your skillset and experience to frame your thoughts and opinions before responding.\n"
            f"With respect to the interview, right now, the following topic is being discussed: {topic}.\n"
            f"Within this topic, the primary focus is on the subtopic: {subtopic}.\n"
            f"If there is any previous set of conversation has happened between the panelists and the candidate, then it will be provided to you by the user.\n"
        )

        output_prompt = (
            # f"You have already determined the thoughts and opinions about your response which is mentioned here: {think_output.model_dump_json()}.\n "
            f"Based on all the information you are provided with, you need to generate the response in the following format{npc_dialog_output_message.model_dump_json()}.\n"
            "Your thoughts and opinions must be generated consider the following:\n"
            "1. The current state of the interview which is denoted by the current topic and subtopic being discussed.\n"
            "2. Your previous responses, candidates responses and what the other panelists are discussing if there are any.\n"
            "3. Your work experience, educational qualifications and skills.\n"
            "4. Consider candidate's details which will be provided to you by the user\n"
            "5. Do not reveal any answers to the questions asked to the candidate.\n"
        )

        overall_prompt = dialog_prompt + role_prompt + panelist_prompt + output_prompt

        return overall_prompt

    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            json_data = json.loads(response.content)
        except json.JSONDecodeError:
            json_data = response.content

        return json_data
