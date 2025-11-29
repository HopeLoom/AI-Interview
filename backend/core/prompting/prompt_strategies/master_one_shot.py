import json
from typing import List

from interview_details_agent.base import InterviewRoundDetails, JobDetails

from activity_agent.base import ActivityProgressAnalysisSummaryForPanelistOutputMessage
from core.prompting.base import BaseMasterPromptStrategy
from core.prompting.prompt_strategies.master_common_prompts import CommonPrompts
from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    MasterChatMessage,
)
from master_agent.base import (
    SUBTOPICS_TECHNICAL_ROUND,
    TOPICS_TECHNICAL_ROUND,
    BaseInterviewConfiguration,
    BaseMasterConfiguration,
    ConversationalAdviceInputMessage,
    ConversationalAdviceOutputMessage,
    EvaluationInputMessage,
    InterviewRound,
    InterviewTopicData,
    PanelData,
    PromptInput,
    QuestionCriteriaSpecificScoring,
    QuestionSpecificEvaluationOutputMessage,
    QuestionSpecificScoring,
    RulesAndRegulationsInputMessage,
    RulesAndRegulationsMessage,
    RulesAndRegulationsOutputMessage,
    SimulationIntroductionInputMessage,
    SimulationIntroductionOutputMessage,
    SpeakerDeterminationInputMessage,
    SpeakerDeterminationOutputMessage,
    SubTopicData,
    TopicSectionCompletionInputMessage,
    TopicSectionCompletionOutputMessage,
)
from panelist_agent.base import Profile


class MasterPromptStrategy(BaseMasterPromptStrategy):
    def __init__(self, configuration, firebase_database=None):
        self.config: BaseMasterConfiguration = configuration
        # load all the interview related information since its used everywhere
        interview_data: BaseInterviewConfiguration = self.config.interview_data
        self.job_details: JobDetails = interview_data.job_details
        self.interview_round_details: InterviewRoundDetails = interview_data.interview_round_details
        self.character_data = interview_data.character_data
        self.activity_details = interview_data.activity_details
        self.common_prompts = CommonPrompts(configuration, firebase_database)

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL

    def convert_conversation_type(self, conversation_history: List[MasterChatMessage]):
        conversation_history_strings = [
            f"Speaker:{message.speaker}, dialog:{message.content}"
            for message in conversation_history
        ]
        return conversation_history_strings

    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        response_type = prompt_input.response_type

        if response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.INTRO:
            system_message = self._generate_introductory_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.SPEAKER_DETERMINATION:
            system_message = self._generate_speaker_determination_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.TOPIC_SECTION_COMPLETION:
            system_message = self._generate_topic_section_completion_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.CONVERSATIONAL_ADVICE:
            system_message = self._generate_conversational_advice_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.RULES_AND_REGULATIONS:
            system_message = self._generate_rules_and_regulations_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.SUBTOPIC_SUMMARY:
            system_message = self._generate_conversation_summary_prompt(prompt_input)

        elif response_type == BaseMasterPromptStrategy.RESPONSE_TYPE.TOPIC_SUMMARY:
            system_message = self._generate_topic_summary_prompt(prompt_input)

        prompt = ChatPrompt(
            messages=[
                ChatMessage.system(system_message),
            ]
        )

        return prompt

    def parse_response_summarized_conversation_content(self, response: AssistantChatMessage) -> str:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "summary" not in json_data.keys():
                return "No summary provided"
            return json_data["summary"]
        else:
            return "No summary provided"

    def parse_response_introduction_content(
        self, response: AssistantChatMessage
    ) -> SimulationIntroductionOutputMessage:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "error" in json_data.keys():
                return SimulationIntroductionOutputMessage()
            introduction = SimulationIntroductionOutputMessage.model_validate(json_data)
            return introduction
        else:
            return SimulationIntroductionOutputMessage()

    def parse_response_speaker_determination_content(
        self, response: AssistantChatMessage
    ) -> SpeakerDeterminationOutputMessage:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "error" in json_data.keys():
                return SpeakerDeterminationOutputMessage()
            speakerDetermination = SpeakerDeterminationOutputMessage.model_validate(json_data)
            return speakerDetermination
        else:
            return SpeakerDeterminationOutputMessage()

    def parse_response_advice_content(
        self, response: AssistantChatMessage
    ) -> ConversationalAdviceOutputMessage:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "error" in json_data.keys():
                return ConversationalAdviceOutputMessage()
            conversationalAdvice = ConversationalAdviceOutputMessage.model_validate(json_data)
            return conversationalAdvice
        else:
            return ConversationalAdviceOutputMessage()

    def parse_rules_and_regulation_content(
        self, response: AssistantChatMessage
    ) -> RulesAndRegulationsOutputMessage:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "error" in json_data.keys():
                return RulesAndRegulationsOutputMessage()
            rulesAndRegulations = RulesAndRegulationsOutputMessage.model_validate(json_data)
            return rulesAndRegulations
        else:
            return RulesAndRegulationsOutputMessage()

    def parse_topic_section_completion_content(
        self, response: AssistantChatMessage
    ) -> TopicSectionCompletionOutputMessage:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "error" in json_data.keys():
                return TopicSectionCompletionOutputMessage()
            output = TopicSectionCompletionOutputMessage.model_validate(json_data)
            return output
        else:
            return TopicSectionCompletionOutputMessage()

    def parse_summary_content(self, response: AssistantChatMessage) -> str:
        if response.content is not None:
            json_data = json.loads(response.content)
            if "summary" not in json_data.keys():
                return "No summary provided"
            # "we need to make sure summary is a string. If its a list, then we need to convert it to a string"
            if isinstance(json_data["summary"], list):
                return "\n".join(json_data["summary"])
            elif isinstance(json_data["summary"], str):
                return json_data["summary"]
            else:
                return "No summary provided"
        else:
            return "No summary provided"

    def _generate_summary_prompt(self, prompt_input: PromptInput) -> str:
        original_message = prompt_input.message

        base_prompt = (
            "Your goal is to summarize the provided text input in a concise and coherent manner.\n"
            "You must **retain the key information** while **rephrasing the content** in your own words.\n"
            "The summary should be **brief, clear, and well-structured**.\n\n"
            "Here is the text you need to summarize:\n\n"
            f"{original_message}\n"
            "Respond in JSON format with key being the summary and value being the summary text.\n"
            "Make sure summary is short and precise with utmost 4 sentences. Also don't include any irrelevant information\n"
            "Also, if the input contains information which says not enough information then try to keep that out of the summary\n"
            "If the text input contains paragraphs, then make sure summary contains information from all the paragraphs\n"
            "Do not miss important details. This summary will be read by the hiring manager, so it should be **professional and polished**.\n\n"
        )

        return base_prompt

    # this is only used once when the candidate logs in to the system
    # we are generating both the introduction as well as the question information that will be asked to the candidate
    def _generate_introductory_prompt(self, prompt_input: PromptInput) -> str:
        interview_rounds = self.interview_round_details.rounds
        round_description = interview_rounds["interview_round_2"].description
        message: SimulationIntroductionInputMessage = prompt_input.message
        panelists = message.panelists
        panelist_profiles = [panelist.model_dump_json() for panelist in panelists]
        panelists = ", ".join(panelist_profiles)
        simulationintroductionoutputmessage = SimulationIntroductionOutputMessage()
        simulationintroductionoutputmessage.introduction = ""
        paneldata = PanelData()
        paneldata.avatar = ""
        paneldata.interview_round_part_of = InterviewRound.ROUND_ONE
        paneldata.intro = ""
        paneldata.name = ""
        paneldata.id = ""
        simulationintroductionoutputmessage.panelists = [paneldata]

        base_prompt = f"""
### **Candidate Interview Introduction Generation**
You are responsible for generating an introduction for a candidate about the **prescreening interview** they are about to participate in.\n\n
            
**Context:**
- The candidate has **just logged in** and needs to understand what to expect from the interview software.
- The interview is for the **following job:**
    - {self.job_details.model_dump_json()}
- The interview consists of **a technical round ** with description mentioned here: {round_description}
- The panelists conducting the interview are:
    - {panelists}

**Instructions:**
1 **Generate the introduction message** in JSON format following this structure:
    - {simulationintroductionoutputmessage.model_dump_json()}
2 **Keep all information short and precise** to ensure clarity for the candidate.
3 **Ensure consistency** between the panelist data you generate and the provided panelist details.
4 The `avatar` field should be left **empty**, as the system will populate it with the image path later.
5. Panelists are AI agents and they will be conducting the interview. Mention that they are AI agents in the introduction.
            
**Example Introduction Message:**
Welcome to the prescreening interview for the **Machine Learning Engineer** position at **XYZ**.
This interview process consists of a **technical interview** to ensure you are a good fit for the role.
Your interview will be conducted by **A and B panelists** who are AI agents representing the company. You can learn more about them below.
Good luck!
            """

        return base_prompt

    # who gets to speak next is decided here
    def _generate_speaker_determination_prompt(self, prompt_input: PromptInput) -> str:
        message: SpeakerDeterminationInputMessage = prompt_input.message
        interview_round: InterviewRound = message.interview_round
        subtopic: SubTopicData = message.current_subtopic
        topic: InterviewTopicData = message.current_topic
        current_section = message.current_section
        panelists: List[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        interview_occupation = [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name
        topic_completion_output = message.topic_completion_message
        topic_time_remaining = prompt_input.topic_time_remaining
        topic_just_got_completed = message.topic_just_got_completed
        last_speaker = message.last_speaker

        speaker_det_output = SpeakerDeterminationOutputMessage()

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_1"
            ].description

            base_prompt = f"""
You are a hiring manager conducting an interview session consisting of HR manager and a candidate.
While the candidate name is:{candidate_name}, HR Manager name is:{interviewer_names[0]}
            """

            rules_prompt = f"""
### **Speaker Selection Rules for HR Interview**
You are responsible for determining the next speaker between the **HR Manager** and the **Candidate** to ensure a **smooth and natural interview flow**.

**Factors to Consider:**
1 *Maintain a logical conversational flow** between the HR Manager and the Candidate, ensuring the interview resembles a real-life session.
2 **Consider the interview context:** {interview_round_description}, along with the current topic: {subtopic.model_dump_json()}.
3 **Starting the Interview:** If the interview has not yet begun, ensure that the **HR Manager starts the conversation**
4 **Keep the Interview Moving Forward:** Ensure the discussion **does not become stagnant** and that both parties engage without excessive repetition or long pauses.
5 **Review the Last Message:** Check the most recent exchange in the conversation history to determine the next logical speaker.
- **Avoid selecting the same speaker twice in a row unless necessary.**
- If the previous speaker needs to add critical information, allow them to continue.
6 **Consider the Overall Context:** Use both the **conversation history** and the **topic structure** to make an informed decision on the next speaker.

⚡ **Goal:** Facilitate a **structured, efficient, and engaging** interview process by selecting the most appropriate next speaker at each step
            """
        else:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_2"
            ].description

            base_prompt = f"""
You are a Hiring manager overseeing an interview session involving multiple interviewers and a candidate.

### **Interview Context:**
- **Candidate Name:** {candidate_name}
- **Interviewers:** {interviewer_names} (Occupations: {interview_occupation})
- The interview is structured into **multiple topics**, each with specific **sections/subtopics**.

### **Current Discussion Focus:**
- **Topic Name:** {subtopic.name}
- **Topic Description:** {subtopic.description}
- **Current Section Under Discussion:** {current_section}
            """

            common_rules_prompt = f"""
### **Speaker Determination Guidelines**
You must decide who speaks next amongst the candidate and interviewers to ensure the interview runs smoothly.

**Ensure Correct Speaker Assignment:**
- The next speaker **must be correctly identified** based on the provided interviewer and candidate names.
- Speaker selection should follow a natural conversation flow, avoiding unnecessary repetition.
- Same speaker cannot speak twice in a row. You have to select a different speaker compared to the last one
- Last speaker was: {last_speaker}

### **Key Considerations:**
1 **Maintain a logical conversational flow** that resembles a structured real-life interview.
2. If the interviewer has asked a question, then most likely candidate will be the next speaker. However, if the question is meant for the other panelist, then let them answer it.
3 **Context Awareness:** Consider the current discussion focus provided to you.
4 **Prevent Stagnation:** Ensure the conversation progresses smoothly without unnecessary repetition or stagnation.
5 **Last Speaker Analysis:** Check the **last message in the conversation history** to determine the next logical speaker. 
Choose a different speaker everytime until and unless there is a reference to someone in the last message. Make sure you allow that person to speak who is referenced
6 **Conversation History Matters:** Use the context from the **current topic and past topics** to make an informed decision.
7 **Balanced Participation:** Prevent one-sided discussions and ensure both panelists and the candidate have appropriate speaking opportunities.
8. If someone is specifically being mentioned in the last message or being addressed, then ensure that person is the next speaker.

### **Rules for Topic & Section Progression:**

9 **Assess why the current section is still being discussed:** {topic_completion_output.model_dump_json()}.
10 **Topic Completion Handling:** If the **current topic just got completed**, indicated here: {topic_just_got_completed}, 
then the next speaker should be a panelist to introduce the next topic.
11 **Section Initiation:** If a new section is starting, **ignore the last message** and determine the next speaker based on the rules for the current topic.

### **Candidate-Specific Guidelines:**
12 **The candidate must never start a new topic**—a panelist must always introduce it. 
However, during the **Problem Solving section (coding phase),** the candidate can take the lead but interviewer must be selected if candidate is asking a question or stating anything.

### **Time-Based Considerations:**
13 **Time remaining determines the next action.**
- If time remaining is **close to 0 or negative**, then only if conditions in the rule set are met, that the speaker must wrap up**
- Remaining time: {topic_time_remaining}.

### **Important Restrictions:**
**Do not fact-check the candidate’s responses**—your role is to **monitor conversation flow at a high level** rather than analyze the content.
** If a panelist has already asked a question to the candidate specifically, then the candidate must be the next speaker. Do not allow the other panelist to intervene and ask another question**
Additionally, follow the topic specific rules provided here:
            """

            rules_prompt = self.common_prompts.get_speaker_determination_topic_wise_rule_prompt(
                topic, subtopic
            )

        output_prompt = f"""
**JSON Format Compliance:**
- Your response **must** follow this JSON structure: {speaker_det_output.model_dump_json()}.
- The **reason field** should provide a **short and precise** explanation for selecting the speaker.
        """

        conversation_history_for_current_subtopic = (
            prompt_input.conversation_history_for_current_subtopic
        )
        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        conversation_summary_for_current_topic = prompt_input.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = (
            prompt_input.conversation_summary_for_completed_topics
        )

        additional_prompt = ""
        conversation_data = ""

        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"

        conversation_data = ""
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_conversation_type(
                last_completed_conversation_history
            )

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_conversation_type(
                conversation_history_for_current_subtopic
            )
            last_completed_conversation_history.extend(converted_conversation_history)
        else:
            additional_prompt += "Conversation has not started for the current section\n"
        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += f"##### Here are the most recent exchange of messages from the conversation including messages from the previous section:{last_completed_conversation_history}\n"

        else:
            additional_prompt += (
                "Conversation has not started yet so this is beginning of a new topic\n"
            )

        return base_prompt + common_rules_prompt + rules_prompt + additional_prompt + output_prompt

    def _generate_topic_section_completion_prompt(self, prompt_input: PromptInput) -> str:
        message: TopicSectionCompletionInputMessage = prompt_input.message

        topic_data: InterviewTopicData = message.topic_data
        subtopic_data: SubTopicData = message.subtopic_data
        interview_round: InterviewRound = message.interview_round
        current_section = message.section
        subtopic_sections = subtopic_data.sections
        remaining_subtopics = prompt_input.remaining_subtopics
        topic_time_remaining = prompt_input.topic_time_remaining
        topic_just_got_completed = message.topic_just_got_completed

        panelists: List[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        interview_occupation = [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name

        topic_completion_output = TopicSectionCompletionOutputMessage()
        topic_completion_output.decision = ""
        topic_completion_output.reason = ""

        if interview_round == InterviewRound.ROUND_ONE:
            base_prompt = f"""
You are responsible for monitoring the interview process between the candidate and HR manager in an HR round.
While the candidate name is: {candidate_name}, HR Manager name is: {interviewer_names[0]}
            """

        else:
            base_prompt = f"""
You are responsible for monitoring conversation between the candidate and two interviewers.
Conversation is structured into **multiple topics**, each with specific **sections**.
### **Interview Context:**
- **Candidate Name:** {candidate_name}.
- **Interviewers:** {interviewer_names}.
            """

        if (
            topic_data.name
            == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        ):
            common_prompt = f"""
### **Current Topic Context:**
- **Topic:** {subtopic_data.name}
- **Description:** {subtopic_data.description}
### **Your Task:**
"- Determine whether the **current section should be marked as complete** based on the conversation between the candidate and interviewers.\n"
            """

        else:
            common_prompt = f"""
### **Current Topic Context:**
- **Topic:** {subtopic_data.name}
- **Description:** {subtopic_data.description}
- **Current Section Under Review:** {current_section}

### **Your Task:**
- Determine whether the **current section should be marked as complete** based on the conversation between the candidate and interviewers.
- Your decision should be guided by **conversation flow**, **coverage of discussion points**, and **remaining time**.

### **Factors to Consider:**
1 **Ruleset for the current topic provided to you**
2 **Previous Conversation Summary** – What has been discussed before this topic?
3 **Current Topic Summary** – What has been covered so far within this topic?
4 **Recent Message Exchange** – The latest interactions between candidate and interviewers for this section
5 **Remaining Time only if conditions in the ruleset are met** – Time left for this topic’s completion (current time remaining: {topic_time_remaining}).

### **Important Instructions:**
- Do not fact-check the conversation—evaluate the flow of discussion instead.
- Do not assess/evaluate the candidate’s responses—focus solely on monitoring the structure and completeness of the conversation.
- It doesn't matter if candidate is giving incorrect/correct/partial or complete answers. You must just consider the rules for the current topic

If the previous topic just got completed with it being True or False as mentioned here:{topic_just_got_completed},
You must determine the conditions of the rules have been met or not based on the conversation that will happen from now on. All the conversation provided to you so far must be used as context
            """

        output_prompt = f"""
Respond in JSON format following the structure mentioned here: {topic_completion_output.model_dump_json()}. Decision of completion can be either YES or NO.
Do not judge/evaluate candidate's responses. We must follow the topic structure and ruleset
        """

        rules_prompt = self.common_prompts.get_topic_completion_topic_wise_prompt(
            topic_data, subtopic_data, current_section, subtopic_sections
        )

        conversation_history_for_current_subtopic = (
            prompt_input.conversation_history_for_current_subtopic
        )
        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        conversation_summary_for_current_topic = prompt_input.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = (
            prompt_input.conversation_summary_for_completed_topics
        )

        additional_prompt = ""
        conversation_data = ""
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"

        conversation_data = ""
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        # if len(last_completed_conversation_history) > 0:
        #     last_completed_conversation_history = self.convert_conversation_type(last_completed_conversation_history)

        # else:
        #     last_completed_conversation_history = []

        last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_conversation_type(
                conversation_history_for_current_subtopic
            )
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n"

        else:
            additional_prompt += "Conversation has not started yet for this topic.\n"

        return base_prompt + rules_prompt + common_prompt + additional_prompt + output_prompt

    def _generate_evaluation_verification_prompt(self, prompt_input: PromptInput) -> str:
        message: EvaluationInputMessage = prompt_input.message
        panelists: List[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        interview_occupation = [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name
        topic_data: InterviewTopicData = message.topic_data
        subtopic_data: SubTopicData = message.subtopic_data
        interview_round: InterviewRound = message.interview_round
        activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            prompt_input.activity_analysis
        )
        activity_code_from_candidate = prompt_input.activity_code_from_candidate
        evaluation_output = prompt_input.evaluation_output

        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_1"
            ].description
        else:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_2"
            ].description

        evaluation_criteria = message.evaluation_criteria

        question_specific_criteria = QuestionSpecificScoring()
        question_specific_criteria.question_number = 0
        question_specific_criteria.decision = ""
        question_specific_criteria.reason = ""

        questionCriteriaSpecificQuestion = QuestionCriteriaSpecificScoring()
        questionCriteriaSpecificQuestion.criteria = ""
        questionCriteriaSpecificQuestion.question_specific_scoring = [question_specific_criteria]
        questionCriteriaSpecificQuestion.key_phrases_from_conversation = []

        output_message = QuestionSpecificEvaluationOutputMessage()
        output_message.question_criteria_specific_scoring = [questionCriteriaSpecificQuestion]

        if interview_round == InterviewRound.ROUND_TWO:
            base_prompt = f"""
You are a hiring manager responsible for evaluating a candidate in a technical interview.

### **Interview Context:**
- **Current Interview Round Description:** {interview_round_description}.
- **Candidate Name:** {candidate_name}.
- **Panelist Details:** {interviewer_names} (Occupations: {interview_occupation}).
- **Job Description for which candidate is interviewing:** {self.job_details.job_description}.
- **Job Title for which candidate is interviewing:** {self.job_details.job_title}.

- **Current Discussion Topic:** {subtopic_data.description}.

### **Evaluation Process:**
- The discussion on the current topic has now concluded, and it's time to evaluate the candidate ({candidate_name}).
- Assess the candidate based on the following **criteria**: {evaluation_criteria}.
- You will be provided with the **interview transcript** containing the conversation between the candidate and panelists.
You have already evaluated the candidate and now you are verifying and re-evaluating so that any mistakes you made in the previous evaluation can be corrected
The previous evaluation is mentioned here: {evaluation_output.model_dump_json()}
- If the interview round involves the coding question, then you will be provided with the code written by the candidate, a summary of the code analysis by another agent and the problem statement
            """

        else:
            base_prompt = f"""
You are a hiring manager responsible for monitoring and evaluating an interview between the HR Manager and the candidate.

### **Interview Context:**
- **Current Interview Round:** {interview_round_description}.
- **Candidate Name:** {candidate_name}.
- **HR Manager Name:** {interviewer_names[0]}.
- **Job Role Under Evaluation:** {self.job_details.model_dump_json()}.
- **Current Discussion Topic:** {subtopic_data.model_dump_json()}.

### **Evaluation Process:**
- The discussion on the current topic has now concluded, and it's time to evaluate the candidate ({candidate_name}).
- Assess the candidate based on the following **criteria**: {evaluation_criteria}.
- You will be provided with the **interview transcript** containing the conversation between the candidate and the HR Manager.
You have already evaluated the candidate and now you are verifying and re-evaluating so that any mistakes you made in the previous evaluation can be corrected
The previous evaluation is mentioned here: {evaluation_output.model_dump_json()}
### **What You Must Do:**
- Carefully analyze the previous round of evaluation and correct it if needed**
- Ensure the evaluation is **objective, structured, and aligned** with the provided criteria.
            """

        round_specific_prompt = self.common_prompts.get_evaluation_topic_wise_question_prompt(
            interview_round,
            topic_data.name,
            subtopic_data.name,
            activity_analysis,
            activity_code_from_candidate,
        )

        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        converted_conversation_history = self.convert_conversation_type(
            last_completed_conversation_history
        )
        conversation_history = "\n".join(converted_conversation_history)
        additional_prompt = "##### Here is the interview transcript:\n" + conversation_history

        output_prompt = f"""
Respond in JSON format using the structure defined here: {output_message.model_dump_json()}.

### **Scoring Guidelines:**
- Give a decision of either YES or NO for each of the questions provided to you.
- If a question cannot be evaluated due to insufficient information, leave its value at the default which is NA.
- Question number starts from 1 and goes up to the number of questions provided to you
- Make sure you specify the question number starting from 1 and not 0
### **Evaluation Philosophy:**
- Your assessment must be **strictly grounded in the candidate's responses**. Do **not** infer intent, skill, or depth beyond what was explicitly demonstrated.
- Maintain a **fair, objective, and consistent** evaluation across candidates.

### **Important Context:**
- The interview format includes **only 3–4 questions per topic**, with at most **one follow-up**.
- As a result, candidates may not always demonstrate deep technical depth.
- **Do not penalize the candidate for lack of technical depth or deep examples.** The format does not allow for it.
- Focus your evaluation on whether the candidate demonstrated a **broad and well-structured understanding** across the key ideas that were discussed.
- Give credit for **range, clarity, and relevance**, even if the candidate did not go deep into any one area.


### **Evidence and Citations:**
- Answer to every question must be supported by **citations from the transcript or the code**.
- Include **key phrases or quotes** from the candidate’s responses.

You have to be critical in your evaluation since you are part of the hiring team and you have to ensure high quality candidates are selected for the job
Also, don't be too optmistic in your evaluation. You have to be realistic in your evaluation and ensure that the candidate is not getting over evaluated.
Now, using the data, proceed with your assessment and consider the following information:
        """

        return base_prompt + additional_prompt + output_prompt + round_specific_prompt

    def _generate_evaluation_prompt(self, prompt_input: PromptInput) -> str:
        message: EvaluationInputMessage = prompt_input.message
        panelists: List[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        interview_occupation = [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name
        topic_data: InterviewTopicData = message.topic_data
        subtopic_data: SubTopicData = message.subtopic_data
        interview_round: InterviewRound = message.interview_round
        activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            prompt_input.activity_analysis
        )
        activity_code_from_candidate = prompt_input.activity_code_from_candidate
        if interview_round == InterviewRound.ROUND_ONE:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_1"
            ].description
        else:
            interview_round_description = self.interview_round_details.rounds[
                "interview_round_2"
            ].description

        evaluation_criteria = message.evaluation_criteria

        question_specific_criteria = QuestionSpecificScoring()
        question_specific_criteria.question_number = 0
        question_specific_criteria.reason = ""
        question_specific_criteria.decision = ""

        questionCriteriaSpecificQuestion = QuestionCriteriaSpecificScoring()
        questionCriteriaSpecificQuestion.criteria = ""
        questionCriteriaSpecificQuestion.question_specific_scoring = [question_specific_criteria]
        questionCriteriaSpecificQuestion.key_phrases_from_conversation = []

        output_message = QuestionSpecificEvaluationOutputMessage()
        output_message.question_criteria_specific_scoring = [questionCriteriaSpecificQuestion]

        if interview_round == InterviewRound.ROUND_TWO:
            base_prompt = f"""
You are a hiring manager responsible for evaluating a candidate in a technical interview.

### **Interview Context:**
- **Current Interview Round Description:** {interview_round_description}.
- **Candidate Name:** {candidate_name}.
- **Panelist Details:** {interviewer_names} (Occupations: {interview_occupation}).
- **Job title:** {self.job_details.job_title}.
- **Job Description for which candidate is interviewing:** {self.job_details.job_description}.
- **Job Title for which candidate is interviewing:** {self.job_details.job_title}.
- **Job requirements for which candidate is interviewing:** {self.job_details.job_requirements}.
- **Job qualifications for which candidate is interviewing:** {self.job_details.job_qualifications}.
- **Current Discussion Topic:** {subtopic_data.description}.

### **Evaluation Process:**
- The discussion on the current topic has now concluded, and it's time to evaluate the candidate ({candidate_name}).
- Assess the candidate based on the following **criteria**: {evaluation_criteria}.
- You will be provided with the **interview transcript** containing the conversation between the candidate and panelists.
- If the interview round involves the coding question, then you will be provided with the code written by the candidate, a summary of the code analysis by another agent and the problem statement
            """

        else:
            base_prompt = f"""
You are a hiring manager responsible for monitoring and evaluating an interview between the HR Manager and the candidate.

### **Interview Context:**
- **Current Interview Round:** {interview_round_description}.
- **Candidate Name:** {candidate_name}.
- **HR Manager Name:** {interviewer_names[0]}.
- **Job title:** {self.job_details.job_title}.
- **Job Description for which candidate is interviewing:** {self.job_details.job_description}.
- **Job Title for which candidate is interviewing:** {self.job_details.job_title}.
- **Job requirements for which candidate is interviewing:** {self.job_details.job_requirements}.
- **Job qualifications for which candidate is interviewing:** {self.job_details.job_qualifications}.
- **Current Discussion Topic:** {subtopic_data.model_dump_json()}.

### **Evaluation Process:**
- The discussion on the current topic has now concluded, and it's time to evaluate the candidate ({candidate_name}).
- Assess the candidate based on the following **criteria**: {evaluation_criteria}.
- You will be provided with the **interview transcript** containing the conversation between the candidate and the HR Manager.

### **What You Must Do:**
- Carefully analyze the transcript and evaluate the candidate’s **responses, engagement, and overall interaction**.
- Ensure the evaluation is **objective, structured, and aligned** with the provided criteria.
            """

        round_specific_prompt = self.common_prompts.get_evaluation_topic_wise_question_prompt(
            interview_round,
            topic_data.name,
            subtopic_data.name,
            activity_analysis,
            activity_code_from_candidate,
        )

        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        converted_conversation_history = self.convert_conversation_type(
            last_completed_conversation_history
        )
        conversation_history = "\n".join(converted_conversation_history)
        additional_prompt = "##### Here is the interview transcript:\n" + conversation_history

        output_prompt = f"""
Respond in JSON format using the structure defined here: {output_message.model_dump_json()}.

### **Scoring Guidelines:**
- Give a decision of either YES or NO for each of the questions provided to you.
- If a question cannot be evaluated due to insufficient information, leave its value at the default which is NA.
- Question number starts from 1 and goes up to the number of questions provided to you
- Make sure you specify the question number starting from 1 and not 0

### **Evaluation Philosophy:**
- Your assessment must be **strictly grounded in the candidate's responses**. Do **not** infer intent, skill, or depth beyond what was explicitly demonstrated.
- Maintain a **fair, objective, and consistent** evaluation across candidates.

### **Important Context:**
- The interview format includes **only 3–4 questions per topic**, with at most **one follow-up**.
- As a result, candidates may not always demonstrate deep technical depth.
- **Do not penalize the candidate for lack of technical depth or deep
- Focus your evaluation on whether the candidate demonstrated a **broad and well-structured understanding** across the key ideas that were discussed.
- Give credit for **range, clarity, and relevance**, even if the candidate did not go deep into any one area.

### **Evidence and Citations:**
- Answer to every question must be supported by **citations from the transcript or the code**.
- Include **key phrases or quotes** from the candidate’s responses.

You have to be critical in your evaluation since you are part of the hiring team and you have to ensure high quality candidates are selected for the job
Also, don't be too optmistic in your evaluation. You have to be realistic in your evaluation and ensure that the candidate is not getting over evaluated.
Now, using the following data, proceed with your assessment:
        """

        return base_prompt + additional_prompt + output_prompt + round_specific_prompt

    def _generate_conversational_advice_prompt(self, prompt_input: PromptInput) -> str:
        topic_time_remaining = str(prompt_input.topic_time_remaining)

        message: ConversationalAdviceInputMessage = prompt_input.message
        next_speaker: Profile = message.next_speaker
        topic_data: InterviewTopicData = message.topic_data
        subtopic_data: SubTopicData = message.subtopic_data
        interview_round: InterviewRound = message.interview_round
        topic_just_got_completed = message.topic_just_got_completed
        current_section = message.section
        subtopic_sections = subtopic_data.sections
        remaining_subtopics = prompt_input.remaining_subtopics
        speaker_determination_output: SpeakerDeterminationOutputMessage = (
            message.speaker_determination_output
        )
        topic_completion_output: TopicSectionCompletionOutputMessage = (
            message.topic_completion_output
        )

        conversational_advice_output = ConversationalAdviceOutputMessage()
        conversational_advice_output.advice_for_speaker = ""
        conversational_advice_output.should_wrap_up_current_topic = False
        conversational_advice_output.should_ask_completely_new_question = False
        conversational_advice_output.should_end_the_interview = False

        conversation_history_for_current_subtopic = (
            prompt_input.conversation_history_for_current_subtopic
        )
        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        conversation_summary_for_current_topic = prompt_input.conversation_summary_for_current_topic
        conversation_summary_for_completed_topics = (
            prompt_input.conversation_summary_for_completed_topics
        )

        additional_prompt = ""
        conversation_data = ""
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"

        conversation_data = ""
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        # if len(last_completed_conversation_history) > 0:
        #     last_completed_conversation_history = self.convert_conversation_type(last_completed_conversation_history)

        # else:
        #     last_completed_conversation_history = []

        last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_conversation_type(
                conversation_history_for_current_subtopic
            )
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n"

        else:
            additional_prompt += "Conversation has not started yet within this topic\n"

        if interview_round == InterviewRound.ROUND_ONE:
            base_prompt = f"""
You are responsible for guiding the **HR Manager** through the interview process with the candidate.
**Next Speaker:** The HR Manager **({next_speaker.background.name})** is now expected to continue the conversation.

### **What You Need to Do:**
Before the HR Manager speaks, generate **advice** on what aspects they should consider before responding to the candidate.

**Factors to Consider When Generating Advice:**
1 **Current Topic of Discussion:** Focus on {subtopic_data.model_dump_json()}.
2 **Time Management:** Time remaining before transitioning to the next topic: {topic_time_remaining} minutes.
3 **Conversation History:** Review the past interactions between the HR Manager and the candidate.
- If no conversation history is available, it means this topic **has not yet been discussed**.
4 **Conversation Summary:** A high-level summary of what has been covered so far (empty if no prior discussion exists).

### **Response Format & Guidelines:**
**Respond in JSON format** using this structure: {conversational_advice_output.model_dump_json()}.
🔹 **Keep advice concise and actionable.**
🔹 **If time is running short, include a note about it in the advice.**
🔹 **Ensure the advice helps the HR Manager maintain a structured and effective conversation.**
🔹 **Advice should be framed as a **suggestion** to the HR Manager, not a directive.**

⚡ **Goal:** Help the HR Manager **steer the interview effectively** by providing relevant insights before they respond.
            """
        else:
            base_prompt = f"""
You are a **agent** overseeing an interview between the **candidate** and two **interviewers**.
The interview is structured into **topics and sections** that guide the flow of discussion.

**Context:**
- The next speaker is **{next_speaker.background.name}**, whose role is:
- {next_speaker.background.current_occupation.model_dump_json()}.
**Before allowing the interviewer to speak, generate strategic advice** on what aspects they should consider when responding to the candidate.

**Consider the following factors when formulating advice:**
1 **Current Section Within the current Topic:**
- **{current_section}**
2 **Time Remaining for the Current Section:**
- {topic_time_remaining} minutes left before transitioning to the next topic.
3 **Remaining sections that need to be covered after the current section is marked completed:**
- {remaining_subtopics}.
4 **Conversation History:**
- Previous exchanges between the candidate and interviewers.
- If no conversation exists, assume the discussion has not yet begun.
5 **Conversation Summary:**
- Condensed key points from past discussion (if any). If empty, assume no prior discussion.
6. Why the current topic is still being discussed is mentioned here: {topic_completion_output.model_dump_json()}.
            """

        output_prompt = f"""
Respond in JSON format following this structure: {conversational_advice_output.model_dump_json()}.
advice_for_speaker should be one of the following:
### **Guidelines for Generating Advice:**
- Provide **short and precise** advice for the interviewer, ensuring it is actionable and context-aware.
### **What to Consider When Generating Advice:**
- **Time Sensitivity:**
- If time is **close to 0 or negative**, advise wrapping up the current topic.
- Use the flag `should_wrap_up_current_topic = True` when advising to conclude a section.
- Use the flag `should_end_the_interview = True` when advising to end the interview
- **Interview Flow:**
- The advice should suggest whether the interviewer should **ask a question, provide clarification, or transition to the next topic.**
- Always ensure that the candidate’s **last response is acknowledged** before moving forward.
- Do not mention details about the question to be asked or what clarification to provide
- **Conversation Context:**
- If the current section **just started**, inform the panelist.
- Whether the section just started is indicated here: {topic_just_got_completed}.
- Do **not** mention both ‘section just began’ and ‘time is running out’ in the same advice.
- Also, when its time to wrap the curent section, make sure you only mention wrap up of the current topic. Do not mention anything about the next section or any form of thanks
- Do not mention anything about the next section after wrapping up the current section
### **Rules for the Current Section:**
Provide advice on a high level with no specific details about what they should ask or what they should consider.
When the current topic is about Problem solving and it has just started, then ensure the following:
1. if the panelist is chosen to be the speaker, then make sure they ask the candidate to focus on solving the coding problem, while only answering candidate's question if they have asked any.
2. Make sure panelist doesn't ask questions during the problem solving topic.
3. If panelist is asking similar questions more than twice in a row, then advice them to change questions and ask something else. Set the should_ask_completely_different_question to True
Do not judge/evaluate candidate's responses. We must follow the interview structure and address all the topics
Everything has to be grounded to the current discussion topic and its description with the current section within it.
            """

        if subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
            output_prompt += (
                "This is the last part of the interview. Interview has to end after this section"
            )

        return base_prompt + additional_prompt + output_prompt

    def _generate_conversation_summary_prompt(self, prompt_input: PromptInput) -> str:
        simulation_chat_message = MasterChatMessage()
        conversation_history = prompt_input.conversation_history_for_current_subtopic
        if len(conversation_history) > 0:
            conversation_data = self.convert_conversation_type(conversation_history)
            conversation_data = "\n".join(conversation_data)
        else:
            conversation_data = "No conversation history available"

        summary_prompt = f"""
You are an agent responsible for summarizing the conversation between the panelists and the candidate in an interview.

### **Guidelines for Summarization:**
- Capture all **key points** while ensuring no critical information is lost.
- Maintain the **conversation structure** as per the provided format.
- The conversation format follows this structure: {simulation_chat_message.model_dump_json()}.

### **Conversation Order & Sequence:**
- The order of the conversation provided to you represents the **actual sequence of exchanges** between the different participants.
- Ensure that the summary maintains this sequence while condensing redundant information.

### **Conversation History:**
{conversation_data}

### **Expected Output:**
- Respond in JSON format, with `summary` as the key and the value as the summarized conversation.
- Ensure that each summarized message clearly identifies the **speaker, listener, and message content**.
- The summary must be **concise yet retain all essential details** of the discussion.
Summary must be stringified and not a list of strings
        """

        return summary_prompt

    def _generate_topic_summary_prompt(self, prompt_input: PromptInput) -> str:
        conversation_summary = prompt_input.conversation_summary_for_current_topic

        if len(conversation_summary) > 0:
            conversation_data = ""
            for i in range(len(conversation_summary)):
                conversation_data += str(conversation_summary[i])
            additional_prompt = (
                f"######### Here is the past conversation summary: {conversation_data}"
            )
        else:
            additional_prompt = "#### No conversation summary available"

        base_prompt = """
You are an agent responsible for summarizing multiple rounds of conversation between the panelists and the candidate.

### **Your Task:**
- You have already generated **individual summaries** for different conversation rounds.
- Your goal is to now **compile a high-level summary** that captures the key insights from the conversation so far.

### **Summarization Guidelines:**
- Ensure the summary retains **all critical points** while remaining concise.
- Present the **sequence of discussions logically**, preserving the **flow of topics** across rounds.
- Respond in JSON format, using `summary` as the key and the summarized conversation as the value.

### **Formatting Requirements:**
- The summary must include **speaker, listener, and message information** for clarity.
- Ensure the **speaker and listener are explicitly mentioned** within the summary.
- Focus on capturing the **essence of the discussion** rather than including redundant details.
            """

        overall_prompt = base_prompt + additional_prompt
        return overall_prompt

    # Not using this right now
    def _generate_rules_and_regulations_prompt(self, prompt_details: PromptInput) -> str:
        message: RulesAndRegulationsInputMessage = prompt_details.message
        panelist_profiles: List[Profile] = message.panelists_profile
        candidate_profile = message.candidate_profile
        interview_round: InterviewRound = message.interview_round
        topic: InterviewTopicData = message.topic
        subtopic: SubTopicData = message.subtopic

        panelist_background_info = [
            f"background_info for panelists with name: {profile.background.name}, {profile.background}"
            for profile in panelist_profiles
        ]
        rules_and_regulations = RulesAndRegulationsOutputMessage()
        item1 = RulesAndRegulationsMessage(character_name="", reason="")
        item2 = RulesAndRegulationsMessage(character_name="", reason="")
        rules_and_regulations.data = [item1, item2]

        conversation_history_for_current_subtopic = (
            prompt_details.conversation_history_for_current_subtopic
        )
        last_completed_conversation_history = prompt_details.last_completed_conversation_history
        conversation_summary_for_current_topic = (
            prompt_details.conversation_summary_for_current_topic
        )
        conversation_summary_for_completed_topics = (
            prompt_details.conversation_summary_for_completed_topics
        )

        additional_prompt = ""
        conversation_data = ""
        if len(conversation_summary_for_completed_topics) > 0:
            for i in range(len(conversation_summary_for_completed_topics)):
                conversation_data += str(conversation_summary_for_completed_topics[i])
            additional_prompt = f"##### Here is the summary of the conversation before the current topic: {conversation_data}"

        conversation_data = ""
        if len(conversation_summary_for_current_topic) > 0:
            for i in range(len(conversation_summary_for_current_topic)):
                conversation_data += str(conversation_summary_for_current_topic[i])
            additional_prompt += f"###### Here is the summary of the conversation until now for the current topic: {conversation_data}"

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = self.convert_conversation_type(
                last_completed_conversation_history
            )

        else:
            last_completed_conversation_history = []

        if len(conversation_history_for_current_subtopic) > 0:
            converted_conversation_history = self.convert_conversation_type(
                conversation_history_for_current_subtopic
            )
            last_completed_conversation_history.extend(converted_conversation_history)

        if len(last_completed_conversation_history) > 0:
            last_completed_conversation_history = "\n".join(last_completed_conversation_history)
            additional_prompt += f"##### Here are the most recent exchange of messages from the conversation:{last_completed_conversation_history}\n"

        else:
            additional_prompt += "Conversation has not started yet\n"

        base_prompt = f"""
Your goal is to ensure all characters adhere to the rules and regulations of the simulation given the conversation history.
Basic profiles describing the background for all NPCs is mentioned here: {panelist_background_info}.
Rules and regulations include:
1. NPCs including user are using appropriate language and tone
You must respond in JSON format following the structure as mentioned here:{rules_and_regulations.model_dump_json()}.
While npc_name denotes the character name, reason contains one line of reason as to why you believe the NPC character is following the rule set or not.
        """

        return base_prompt + additional_prompt

    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            if response.content is not None:
                json_data = json.loads(response.content)
            else:
                json_data = {}
        except json.JSONDecodeError:
            json_data = {}

        return json_data
