import json

from interview_details_agent.base import BaseInterviewConfiguration, InterviewRoundDetails

from activity_agent.base import (
    ActivityProgressAnalysisOutputMessage,
    ActivityProgressAnalysisSummaryForPanelistOutputMessage,
    ActivityProgressWithRespectToQuestionOutputMessage,
    PromptInput,
)
from core.prompting.base import BaseActivityPromptStrategy
from core.prompting.schema import ChatPrompt, LanguageModelClassification
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
)


class ActivityPromptStrategy(BaseActivityPromptStrategy):
    def __init__(self, configuration, interview_config):
        self.config = configuration
        self.interview_config: BaseInterviewConfiguration = interview_config
        self.job_details = self.interview_config.job_details
        self.interview_round_details: InterviewRoundDetails = (
            self.interview_config.interview_round_details
        )
        self.character_data = self.interview_config.character_data
        self.activity_details = self.interview_config.activity_details

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL

    def build_prompt(self, prompt_input: PromptInput) -> ChatPrompt:
        response_type = prompt_input.response_type

        if response_type == ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_HIGH_LEVEL_ANALYSIS:
            system_message = self._generate_activity_progress_prompt(prompt_input)

        elif (
            response_type
            == ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_ANALYSIS_WITH_RESPECT_TO_QUESTION
        ):
            system_message = (
                self._generate_monitor_activity_progress_with_respect_to_question_prompt(
                    prompt_input
                )
            )

        elif (
            response_type
            == ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_ANALYSIS_SUMMARY_FOR_PANELIST
        ):
            system_message = self._generate_monitor_activity_analysis_for_panelist_prompt(
                prompt_input
            )

        prompt = ChatPrompt(messages=[ChatMessage.system(system_message)])

        return prompt

    def _generate_activity_progress_prompt(self, prompt_input: PromptInput) -> str:
        output = ActivityProgressAnalysisOutputMessage()
        interview_round_two_description = self.interview_round_details.rounds[
            "interview_round_2"
        ].description

        activity_progress_history = prompt_input.activity_progress_history
        if len(activity_progress_history) > 0:
            activity_progress_history = ",".join(activity_progress_history)
        else:
            activity_progress_history = "None"

        code_data_from_candidate = prompt_input.activity_code_from_candidate
        starter_code = prompt_input.starter_code

        prompt = f"""
You are a code monitoring agent assisting an interview panel by interpreting the candidate’s code and converting it into a concise, high-level natural language summary.
Interview round details: {interview_round_two_description}.

The candidate is actively writing code as part of their response. Your task is to analyze their code and generate a summary that clearly describes what has been implemented.
You will be provided with:
- The starter code provided to the candidate: {starter_code}.
- The latest code written by the candidate: {code_data_from_candidate}.
- The previous code analysis history, including mappings of analyzed code and corresponding summaries: {activity_progress_history}.

Respond in JSON format using the following structure: {output.model_dump_json()}.
### **Rules for Code Interpretation:**
1. Your summary must cover **all newly written lines of code**—do not skip any part of the implementation.
2. Starter code should not be included in the summary.
3. If parts of the code have already been analyzed in the previous progress history, reuse the corresponding summaries instead of reanalyzing them.
4. Keep the summary **high-level**, describing functionality rather than line-by-line syntax.
5. Maintain **clarity and conciseness**—the summary must not exceed **100 words**.
6. Focus purely on interpreting the code into natural language without making assumptions about intent or correctness.
7. Avoid any speculation—base your interpretation strictly on the written code and past progress.
8. Ensure technical accuracy while making the explanation accessible for non-technical panelists.
9. Do not include starter code information in your analysis. You must analyze the code written by the candidate only

You must NOT care about edge cases, error handling, syntax errors and return statements in the candidate provided code. We care more about the logic.

        """
        return prompt

    def _generate_monitor_activity_progress_with_respect_to_question_prompt(
        self, prompt_input: PromptInput
    ) -> str:
        output = ActivityProgressWithRespectToQuestionOutputMessage()
        interview_round_two = self.interview_round_details.rounds["interview_round_2"].description
        starter_code = prompt_input.starter_code
        code_data_from_candidate = prompt_input.activity_code_from_candidate

        progress: ActivityProgressAnalysisOutputMessage = prompt_input.activity_progress_analysis

        code_intrepretation = progress.code_intrepretation
        complexity_analysis = progress.complexity_analysis
        logic_analysis = progress.logic_analysis

        prompt = f"""
You are a code monitoring agent assisting an interview panel in evaluating the candidate’s progress in the current interview round.
Interview round details: {interview_round_two}.

The candidate is solving a coding question as part of the interview where the starter code is provided here: {starter_code}
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {starter_code}
5. Latest code written by the candidate: {code_data_from_candidate}

You have already generated a high-level summary of the candidate's progress, which can be found here:
1. Code Interpretation: {code_intrepretation}
2. Complexity Analysis: {complexity_analysis}
3. Logic Analysis: {logic_analysis}

Your task now is to analyze how the candidate is doing with respect to the question asked to them.
Compare their current progress against the expected solution and determine whether key components of the solution have been implemented or are still missing.

Respond in JSON format using the following structure: {output.model_dump_json()}.
Output consists of the following:
1. code_intrepretation_with_respect_to_question: Here you are just interpreting the code written by the candidate specifically with respect to the question and starter code provided
2. logic_analysis_with_respect_to_question: Here you are analysing the code logic written by the candidate with respect to the question asked and starter code provided. Logic here is with respect to answering the question
3. complexity_analysis_with_respect_to_question: Here you are analysing the time and space complexity of the code written by the candidate
4. remaining_things_to_do_with_respect_to_question: Here you have to mention what are the remaining things in the code to completed with respect to the question asked and starter code provided. Do not go beyond this

### **Rules for Progress Evaluation:**
1. Assess how much of the problem has been addressed based on the candidate's code.
2. Identify whether the core logic needed to solve the problem is present.
3. Determine if major components are missing without making assumptions about correctness.
4. Keep the summary **concise** (no more than **100 words**), focusing only on progress towards the solution.
5. Avoid evaluating minor optimizations or edge cases—focus on whether the candidate is conceptually on track.
6. Also don't consider edge cases as part of the remaining things to do
7. if the candidate has answered the question completely, then keep the remaining_things_to_do_with_respect_to_question as empty
8. Do not include starter code information in your analysis. You must analyze the code written by the candidate only
9. You must NOT care about edge cases, error handling, syntax errors and return statements in the candidate provided code. We care more about the logic.
10. if the question is completely solved in terms of logic with exceptions to edge cases, error handling, syntax errors and return statements, make sure that the remaining_things_to_do_with_respect_to_question is empty
        """
        return prompt

    def _generate_monitor_activity_analysis_for_panelist_prompt(
        self, prompt_input: PromptInput
    ) -> str:
        output = ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        self.interview_round_details.rounds["interview_round_2"].description

        activity_progress_with_respect_to_question: ActivityProgressWithRespectToQuestionOutputMessage = prompt_input.activity_progress_with_respect_to_question
        starter_code = prompt_input.starter_code
        code_data_from_candidate = prompt_input.activity_code_from_candidate


        code_intrepretation_with_respect_to_question = (
            activity_progress_with_respect_to_question.code_intrepretation_with_respect_to_question
        )
        complexity_analysis_with_respect_to_question = (
            activity_progress_with_respect_to_question.complexity_analysis_with_respect_to_question
        )
        logic_analysis_with_respect_to_question = (
            activity_progress_with_respect_to_question.logic_analysis_with_respect_to_question
        )
        remaining_things_to_do_with_respect_to_question = activity_progress_with_respect_to_question.remaining_things_to_do_with_respect_to_question

        prompt = f"""
You are a code monitoring agent assisting an interview panel in evaluating the candidate’s progress in the current interview round.
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {starter_code}
5. Latest code written by the candidate: {code_data_from_candidate}

You have already conducted analysis which includes:
1. A progress evaluation, determining how the candidate is doing with respect to the question asked which is mentioned below:
1.1 Code Interpretation with respect to the question: {code_intrepretation_with_respect_to_question}
2.2 Complexity Analysis with respect to the question: {complexity_analysis_with_respect_to_question}
2.3 Logic Analysis with respect to the question: {logic_analysis_with_respect_to_question}
2.4 Remaining things to do with respect to the question: {remaining_things_to_do_with_respect_to_question}

"### **Your Task:**
You must now generate a **comprehensive summary** for the panelists, combining insights from the information provided to you.
This summary should help the interview panel quickly understand the candidate's overall progress
Ensure you are able to encapsulate all the information provided in the previous stages of analysis. Do not make any assumptions beyond this
Note that starter code is provided to the candidate so your summary must only about what the candidate added to the starter code
Latest code wriiten by the candidate is provided to you and it contains code in addition to the starter code
Respond in JSON format using the following structure: {output.model_dump_json()}.
percentage_of_question_solved should be a float value between 0 and 1.
things_left_to_do_with_respect_to_question should only contain information about the remaining things to do with respect to the question and starter code. Don't consider edge cases
candidate_performance_summary should be a concise summary of the candidate's progress which should include the main jist of the code they have written.
Ensure when computing the percentage of question solved, you consider the complexity of the function and the logic implemented.
If the candidate has answered the question completely, then keep the remaining_things_to_do_with_respect_to_question as empty.
Do not include starter code information in your analysis. You must analyze the code written by the candidate only

You must NOT care about edge cases, error handling, syntax errors and return statements in the candidate provided code. We care more about the logic.
if the question is completely solved in terms of logic with exceptions to edge cases, error handling, syntax errors and return statements, make sure that the remaining_things_to_do_with_respect_to_question is empty

        """
        return prompt

    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            json_data = json.loads(response.content) if response.content is not None else {}
        except json.JSONDecodeError:
            json_data = response.content if response.content is not None else {}

        return json_data
