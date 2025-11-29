import json

from interview_details_agent.base import InterviewRoundDetails, JobDetails

from activity_agent.base import ActivityProgressAnalysisSummaryForPanelistOutputMessage
from core.prompting.base import BaseEvaluationPromptStrategy
from core.prompting.prompt_strategies.master_common_prompts import CommonPrompts
from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    MasterChatMessage,
)
from evaluation_agent.base import (
    BaseEvaluationConfiguration,
    CodeSummaryVisualizationInputMessage,
    CriteriaVisualizationInputMessage,
    OverallVisualizationInputMessage,
    PanelistFeedbackVisualizationInputMessage,
    PromptInput,
    SubqueryDataExtractionInputMessage,
    SubqueryDataExtractionOutputMessage,
    SubqueryGeneratorInputMessage,
    SubqueryGeneratorOutputMessage,
)
from master_agent.base import (
    BaseInterviewConfiguration,
    CodeAnalysisVisualSummary,
    CodeDimensions,
    CodeDimensionSummary,
    CriteriaScoreVisualSummary,
    CriteriaScoreVisualSummaryList,
    EvaluationInputMessage,
    InterviewRound,
    InterviewTopicData,
    OverallVisualSummary,
    PanelistFeedbackVisualSummary,
    PanelistFeedbackVisualSummaryList,
    QuestionCriteriaSpecificScoring,
    QuestionSpecificEvaluationOutputMessage,
    QuestionSpecificScoring,
    SubTopicData,
)
from panelist_agent.base import Profile


class EvaluationPromptStrategy(BaseEvaluationPromptStrategy):
    def __init__(self, configuration, interview_data_config, firebase_database):
        self.config: BaseEvaluationConfiguration = configuration
        # load all the interview related information since its used everywhere
        interview_data: BaseInterviewConfiguration = interview_data_config
        self.job_details: JobDetails = interview_data.job_details
        self.interview_round_details: InterviewRoundDetails = interview_data.interview_round_details
        self.character_data = interview_data.character_data
        self.activity_details = interview_data.activity_details
        self.common_prompts = CommonPrompts(configuration, firebase_database)

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL

    def convert_conversation_type(self, conversation_history: list[MasterChatMessage]):
        if conversation_history is None:
            return []
        conversation_history_strings = [
            f"Speaker:{message.speaker}, dialog:{message.content}"
            for message in conversation_history
        ]
        conversation_history_combined = "\n".join(conversation_history_strings)
        return conversation_history_combined

    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        response_type = prompt_input.response_type
        user_message = None

        if response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION:
            system_message = self._generate_evaluation_prompt(prompt_input)

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION_SUMMARY:
            system_message = self._generate_summary_prompt(prompt_input)

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_GENERATION:
            system_message = self._generate_subquery_generation_prompt(prompt_input)

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_DATA_EXTRACTION:
            system_message = "Be precise and concise."
            user_message = self._generate_subquery_data_extraction_prompt(prompt_input)

        elif (
            response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.CODE_ANALYSIS_VISUAL_SUMMARY
        ):
            system_message = self._generate_code_analysis_visual_summary_prompt(prompt_input)

        elif (
            response_type
            == BaseEvaluationPromptStrategy.RESPONSE_TYPE.PANELIST_FEEDBACK_VISUAL_SUMMARY
        ):
            system_message = self._generate_panelist_feedback_visual_summary_prompt(prompt_input)

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.OVERALL_VISUAL_SUMMARY:
            system_message = self._generate_overall_visual_summary_prompt(prompt_input)

        elif response_type == BaseEvaluationPromptStrategy.RESPONSE_TYPE.CRITERIA_VISUAL_SUMMARY:
            system_message = self._generate_criteria_visual_summary_prompt(prompt_input)

        if user_message is None:
            prompt = ChatPrompt(
                messages=[
                    ChatMessage.system(system_message),
                ]
            )
        else:
            prompt = ChatPrompt(
                messages=[ChatMessage.system(system_message), ChatMessage.user(user_message)]
            )

        return prompt

    def parse_response_evaluation_content(
        self, response: AssistantChatMessage
    ) -> QuestionSpecificEvaluationOutputMessage:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return QuestionSpecificEvaluationOutputMessage()
        evaluation = QuestionSpecificEvaluationOutputMessage.model_validate(json_data)
        return evaluation

    def parse_response_subquery_generation_content(
        self, response: AssistantChatMessage
    ) -> SubqueryGeneratorOutputMessage:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return SubqueryGeneratorOutputMessage()
        return SubqueryGeneratorOutputMessage.model_validate(json_data)

    def parse_response_subquery_data_extraction_content(
        self, response: AssistantChatMessage
    ) -> SubqueryDataExtractionOutputMessage:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return SubqueryDataExtractionOutputMessage()
        return SubqueryDataExtractionOutputMessage.model_validate(json_data)

    def parse_response_evaluation_summary_content(self, response: AssistantChatMessage) -> str:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "summary" not in json_data:
            return ""
        return json_data["summary"]

    def parse_response_code_analysis_visual_summary_content(
        self, response: AssistantChatMessage
    ) -> CodeAnalysisVisualSummary:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return CodeAnalysisVisualSummary()
        print(f"Code analysis visual summary json data: {json_data}")
        parsed_dimensions = [
            json.loads(dim) if isinstance(dim, str) else dim
            for dim in json_data["code_dimension_summary"]
        ]

        # # Now build the Pydantic model correctly
        summary = CodeAnalysisVisualSummary(
            code_overall_summary=json_data["code_overall_summary"],
            code_dimension_summary=[CodeDimensionSummary(**dim) for dim in parsed_dimensions],
            completion_percentage=json_data["completion_percentage"],
        )

        return summary

    def parse_response_panelist_feedback_visual_summary_content(
        self, response: AssistantChatMessage
    ) -> PanelistFeedbackVisualSummaryList:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return PanelistFeedbackVisualSummaryList()
        return PanelistFeedbackVisualSummaryList.model_validate(json_data)

    def parse_response_overall_visual_summary_content(
        self, response: AssistantChatMessage
    ) -> OverallVisualSummary:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return OverallVisualSummary()
        return OverallVisualSummary.model_validate(json_data)

    def parse_response_criteria_visual_summary_content(
        self, response: AssistantChatMessage
    ) -> CriteriaScoreVisualSummaryList:
        json_data = json.loads(response.content) if response.content is not None else {}
        if "error" in json_data:
            return CriteriaScoreVisualSummaryList()
        return CriteriaScoreVisualSummaryList.model_validate(json_data)

    def _generate_code_analysis_visual_summary_prompt(self, prompt_input: PromptInput) -> str:
        message: CodeSummaryVisualizationInputMessage = prompt_input.message
        code_written_by_candidate = message.code
        activity_summary: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            message.activity_analysis
        )

        candidate_performance_summary = activity_summary.candidate_performance_summary
        percentage_of_question_solved = activity_summary.percentage_of_question_solved * 100
        things_left_to_do_with_respect_to_question = (
            activity_summary.things_left_to_do_with_respect_to_question
        )

        output = CodeAnalysisVisualSummary()
        code_dimensions_summary = CodeDimensionSummary()
        code_dimensions_summary.name = ""
        code_dimensions_summary.rating = ""
        code_dimensions_summary.comment = ""
        output.code_dimension_summary = [code_dimensions_summary]

        code_dimensions_list = [
            CodeDimensions.CODE_CORRECTNESS.value,
            CodeDimensions.CODE_READABILITY.value,
            CodeDimensions.CODE_EFFICIENCY.value,
            CodeDimensions.TIME_COMPLEXITY.value,
            CodeDimensions.CODE_STYLE.value,
            CodeDimensions.CODE_REUSABILITY.value,
            CodeDimensions.CODE_READABILITY.value,
            CodeDimensions.CODE_INTERPRETATION.value,
        ]

        base_prompt = f"""
You are tasked with generating a summary analysis of the coding part of the interview written by the candidate.
This information has to be presented on a dashboard
Dashboard wil be used by the hiring manager so how we present the results matter a lot. We cannot just show all the raw text. It has to be in a presentable and visually appealing form
- **Technical Problem Details presented to the candidate during the interview:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {self.common_prompts.starter_code_data}
Based on the above task details, candidate wrote the code mentioned here:{code_written_by_candidate}
We have already analysed the code and generated some analysis which is mentioned here:{candidate_performance_summary}
We have also determined the amount of question solved which is mentioned here: {percentage_of_question_solved} %
Finally, we have also determined if there are any remaining things to do for the candidate with regards to the question asked to them and is mentioned here: {things_left_to_do_with_respect_to_question}
Now given all the above information, you need to respond in JSON format in the following structure:
{output.model_dump_json()}
The code overall summary should include emojis and must be short, precise and visually appealing. Keep it just one line
Code dimension summary is more about evaluating the candidate on different dimensions where the list of dimensions are mentioned here: {code_dimensions_list}
For each dimension, you must return a JSON following the format mentioned here: {code_dimensions_summary.model_dump_json()}:
- a rating symbol (✅ good, ⚠️ needs improvement, ❌ poor)
- a one-line comment explaining your reasoning.
When you are generating the overall code summary, you can following these guidelines:
The tone should be professional and insight-driven — use bullet points, emoji, or short paragraphs to highlight key observations. Mention:
1. 🎯 What the code written by candidate does and whether it works. Need to make sure starter code is not included in the analysis
2. 💡 Notable strengths (e.g. clean logic, modularity, naming) in the code written by the candidate and not the starter code. No comments are expected
3. ⚠️ Weaknesses or risks (e.g. lack of edge case handling, inefficiencies) in the code written by the candidate
4. 🔍 Observations on clarity, structure, or maintainability of the code written by the candidate and whether they can contribute and scale to large code systems
Avoid excessive jargon. Use no more than 4 bullet points. Be specific and clear.
Completion score can be the same as the value provided to you
        """

        return base_prompt

    def _generate_panelist_feedback_visual_summary_prompt(self, prompt_input: PromptInput) -> str:
        message: PanelistFeedbackVisualizationInputMessage = prompt_input.message
        panelist_feedback = message.panelist_feedback
        panelist_names = message.panelist_names
        panelist_occupations = message.panelist_occupations

        panelist_feedback_output: PanelistFeedbackVisualSummaryList = (
            PanelistFeedbackVisualSummaryList()
        )
        panelist_visual_summary: PanelistFeedbackVisualSummary = PanelistFeedbackVisualSummary()
        panelist_visual_summary.name = ""
        panelist_visual_summary.role = ""
        panelist_visual_summary.summary_bullets = [""]
        panelist_feedback_output.panelist_feedback = [panelist_visual_summary]

        base_prompt = f"""
            You are responsible for summarizing the impressions already generated by set of panelists about a candidate's interview. Write a concise visual summary of their feedback.
            This visual summary will be presented on the dashboard for the hiring manager.
            Here is the information you need to use:
            - **Panelist Names:** {panelist_names}.
            - **Panelist Occupations:** {panelist_occupations}.
            - **Panelist Feedback:** {panelist_feedback}.

            Your output should be:
            - A list of 3–5 concise bullet points
            - Each bullet should capture a specific observation or impression
            - Use light emojis to help highlight tone (e.g., 💬, ✅, ⚠️, 💡, 🚧)
            - Avoid repetition and generic praise
            - Be professional but clear

            Return output in JSON format in the following format:
            {panelist_feedback_output.model_dump_json()}
        """

        return base_prompt

    def _generate_criteria_visual_summary_prompt(self, prompt_input: PromptInput) -> str:
        message: CriteriaVisualizationInputMessage = prompt_input.message
        criteria_score_list = message.criteria_score_list

        criteria_scoring_list = [
            criteria_score.model_dump_json() for criteria_score in criteria_score_list
        ]
        criteria_score_visual_summary: CriteriaScoreVisualSummaryList = (
            CriteriaScoreVisualSummaryList()
        )
        criteria_score_summary = CriteriaScoreVisualSummary()
        criteria_score_summary.criteria = ""
        criteria_score_summary.score = 0
        criteria_score_summary.reason_bullets = [""]
        criteria_score_summary.topics_covered = [""]
        criteria_score_visual_summary.criteria_score_list = [criteria_score_summary]

        base_prompt = f"""
You are responsible for summarizing the criteria scores given to the candidate based on the interview that was just conducted
Summary needs to be generated for the hiring manager and will be presented on the dashboard
The following is the criteria specific scoring and reasoning generated already:
{criteria_scoring_list}
Using the above information, generate a visual summary and return output in JSON format in the following structure:
{criteria_score_visual_summary.model_dump_json()}
Criteria and score will remain the same as provided.The main thing to focus on are the reasoning points and topics covered which must be precise and to the point
Topics covered must be the high level topics that a hiring manager can look at and understand what the discussion was about
Only generate upto 3 to 5 bullet points for each criteria and make sure they are not too long
        """

        return base_prompt

    def _generate_overall_visual_summary_prompt(self, prompt_input: PromptInput) -> str:
        message: OverallVisualizationInputMessage = prompt_input.message

        output = OverallVisualSummary()

        base_prompt = f"""
You are responsible for generating a visual summary of the overall interview performance of the candidate
You can find the overall summary here:
{message.overall_analysis}
Overall score mentioned here: {message.overall_score} is something you need to keep that as it is
Your task:
- Extract 4 to 6 concise bullet points that capture the most important insights.
- Use professional tone, but make it easy to scan quickly.
- Add light emojis where appropriate (e.g., ✅ Strength, ⚠️ Concern, 💬 Communication, 💡 Insight, 🚧 Needs Improvement).
- Group similar points and eliminate redundancy.
- Do not rewrite the whole text — summarize key takeaways.
Return JSON in the following format:
{output.model_dump_json()}
Make sure key insights is a list of strings
        """

        return base_prompt

    def _generate_subquery_generation_prompt(self, prompt_input: PromptInput) -> str:
        output = SubqueryGeneratorOutputMessage()
        message: SubqueryGeneratorInputMessage = prompt_input.message
        last_completed_conversation_history = prompt_input.last_completed_conversation_history
        converted_conversation_history = self.convert_conversation_type(
            last_completed_conversation_history
        )
        conversation_history = "\n".join(converted_conversation_history)
        panelists: list[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name

        base_prompt = f"""
You are part of an evaluation engine helping other agents in evaluating a candidate in an interview
You will be provided with a conversation transcript pertaining to the technical discussion between the panelist and the candidate.
We are now trying to evaluate the candidate responses but to do so we need to make sure we have all the relevant facts available to us regarding the questions asked
Facts are present online and only by generating relevant SERP queries and then doing an online search for each of them, we can retrieve the data corresponding to these queries
Here is the conversation history you need to use to generate the relevant subqueries for:
{conversation_history}
Respond in JSON format following the structure mentioned here: {output.model_dump_json()}.
Please note that the candidate name is {candidate_name} and the panelist names are {interviewer_names}.
You can identify them by their names in the provided transcript.
Make sure subquery is short and precise but is in the natural language format. For eg: what is a machine learning, how does machine learning work etc
You should consider both the candidate and the panelist responses to figure out what needs to be searched online to ensure the evaluation is fair and we have all information available to us
Ensure each of the SERP queries is different from the other.
Generate atmost 10 such as SERP queries but you can also generate less if you believe you have covered all the aspects needed covering the factual information regarding the conversation
"""

        return base_prompt

    def _generate_subquery_data_extraction_prompt(self, prompt_input: PromptInput) -> str:
        output = SubqueryDataExtractionOutputMessage()

        message: SubqueryDataExtractionInputMessage = prompt_input.message
        subqueries = message.subqueries

        base_prompt = f"""
Provide facts for the corresponding search queries
Here are the subqueries: {subqueries}
Please output a JSON object with the following structure:
{output.model_dump_json()}
Make sure the facts are relevant to the subquery and are not too long
"""

        return base_prompt

    def _generate_summary_prompt(self, prompt_input: PromptInput) -> str:
        original_message = prompt_input.message

        base_prompt = f"""
Your goal is to summarize the provided text input in a concise and coherent manner.
You must **retain the key information** while **rephrasing the content** in your own words.
The summary should be **brief, clear, and well-structured**.
Here is the text you need to summarize:
{original_message}
Respond in JSON format with key being the summary and value being the summary text.
Make sure summary is short and precise with utmost 4 sentences. Also don't include any irrelevant information
Also, if the input contains information which says not enough information then try to keep that out of the summary
If the text input contains paragraphs, then make sure summary contains information from all the paragraphs
Do not miss important details. This summary will be read by the hiring manager, so it should be **professional and polished**.
"""

        return base_prompt

    def _generate_evaluation_verification_prompt(self, prompt_input: PromptInput) -> str:
        message: EvaluationInputMessage = prompt_input.message
        panelists: list[Profile] = message.panelists
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
- Carefully analyze the previous round of evaluation and correct it if needed
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
        panelists: list[Profile] = message.panelists
        interviewer_names = [f"{profile.background.name}" for profile in panelists]
        interview_occupation = [
            f"{profile.background.current_occupation.occupation}" for profile in panelists
        ]
        candidate_profile: Profile = message.candidate_profile
        candidate_name = candidate_profile.background.name
        topic_data: InterviewTopicData = message.topic_data
        subtopic_data: SubTopicData = message.subtopic_data
        interview_round: InterviewRound = message.interview_round
        subqueries_data: SubqueryDataExtractionOutputMessage = message.subqueries_data
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
- **Do not penalize the candidate for lack of technical depth or deep examples.** The format does not allow for it.
- Focus your evaluation on whether the candidate demonstrated a **broad and well-structured understanding** across the key ideas that were discussed.
- Give credit for **range, clarity, and relevance**, even if the candidate did not go deep into any one area.

### **Evidence and Citations:**
- Answer to every question must be supported by **citations from the transcript or the code**.
- Include **key phrases or quotes** from the candidate’s responses.

You have to be critical in your evaluation since you are part of the hiring team and you have to ensure high quality candidates are selected for the job
Also, don't be too optmistic in your evaluation. You have to be realistic in your evaluation and ensure that the candidate is not getting over evaluated.
If there is factual information to help you evaluate, then it will be present here: {subqueries_data.model_dump_json()}
Facts are important to fact check the candidate responses as well catch any contradictions that might exist in their responses.
You must only use the facts provided to determine the accuracy of the responses. Do not consider your own knowledge in this case
Now, using the following data, proceed with your assessment:
"""
        return base_prompt + additional_prompt + output_prompt + round_specific_prompt

    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            json_data = json.loads(response.content) if response.content is not None else {}
        except json.JSONDecodeError:
            json_data = {}

        return json_data
