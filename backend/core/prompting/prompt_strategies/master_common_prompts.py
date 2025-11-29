from typing import List

from core.database.base import DatabaseInterface
from master_agent.base import (
    SUBTOPICS_HR_ROUND,
    SUBTOPICS_TECHNICAL_ROUND,
    TOPICS_HR_ROUND,
    TOPICS_TECHNICAL_ROUND,
    BaseInterviewConfiguration,
    BaseMasterConfiguration,
    InterviewRound,
    InterviewRoundDetails,
    InterviewTopicData,
    SubTopicData,
)


class CommonPrompts:
    def __init__(self, configuration, database=None):
        self.config: BaseMasterConfiguration = configuration
        # load all the interview related information since its used everywhere
        interview_data: BaseInterviewConfiguration = self.config.interview_data
        self.job_details = interview_data.job_details
        self.interview_round_details: InterviewRoundDetails = interview_data.interview_round_details
        self.character_data = interview_data.character_data
        self.activity_details = interview_data.activity_details
        self.database: DatabaseInterface = database
        # Load starter code asynchronously
        import asyncio

        self.starter_code_data = asyncio.run(self.load_activity_code_info()) if database else ""

    async def load_activity_code_info(self) -> str | None:
        code = await self.database.fetch_starter_code_from_url() if self.database else ""
        return code

    def get_speaker_determination_topic_wise_rule_prompt(
        self, topic: InterviewTopicData, subtopic: SubTopicData
    ) -> str:
        if topic.name == TOPICS_TECHNICAL_ROUND.TEAM_INTRODUCTIONS_AND_INTERVIEW_FORMAT.value:
            rules_prompt = """
1 **Interview Kickoff:** If the interview has not started yet, ensure that either of panelists begins by introducing themselves.
2 **Panelist Introductions First:** Ensure that **both panelists introduce themselves** before the candidate speaks.
3 **Candidate Introduction:** Once both panelists have introduced themselves, the candidate should be given a turn to introduce themselves.
4 **Transition to Interview Format:** After introductions are complete, the panel should transition into explaining the **interview structure** with either of the panelist leading the discussion.
                """

        elif (
            topic.name
            == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        ):
            if subtopic.name == SUBTOPICS_TECHNICAL_ROUND.TECHNCAL_PROBLEM_OVERVIEW.value:
                rules_prompt = """
1 **Initiating the Topic:** PM should begin this topic by introducing the technical problem to the candidate.
2 **Primary Responsibility:** The problem explanation should be **primarily led by the MLE** since it is a technical challenge.
3 **Candidate’s Turn:** Once the problem has been introduced, the candidate must be given an opportunity to ask **clarifying questions**.
4 **Clarification Handling:**
   - If the candidate asks about **technical aspects (e.g., algorithms, constraints, data handling)** → The MLE should respond.
   - If the candidate asks about **product-related aspects (e.g., user impact, business relevance, trade-offs)** → The PM should respond.
5. If the panelist has asked a question to candidate, then make sure candidate is given the chance to respond to it.
                """
            elif subtopic.name == SUBTOPICS_TECHNICAL_ROUND.PROBLEM_SOLVING.value:
                rules_prompt = """
1 **Candidate in Control:** The candidate should be actively working on solving the problem independently.
2 **Panelists in Observation Mode:** The panelists should remain in observation mode unless the candidate states any form of statement.
3 **Handling Candidate Questions:**
   - If the question is about **technical aspects (e.g., algorithms, constraints, data structures, model details)** → The MLE should respond concisely.
   - If the question is about **product-related aspects (e.g., business relevance, trade-offs, impact on users)** → The PM should respond concisely.
                """
        elif subtopic.name == SUBTOPICS_TECHNICAL_ROUND.TASK_SPECIFIC_DISCUSSION.value:
            rules_prompt = """
1 **Initiating the topic:** The MLE should begin this topic.
2 **Candidate's Turn:** The Candidate must be given sufficient time to explain their thought process before any follow-up questions are posed.
3 **PM's Role:** The Product Manager (PM) should only be selected as the next speaker if the discussion naturally shifts towards **product relevance, business impact, or cross-functional considerations**.
4 **Limit on Questions:**
   - No more than **three questions** with one followup each should be asked by the panelists in this section.
                """

        elif subtopic.name == SUBTOPICS_TECHNICAL_ROUND.CONCEPTUAL_KNOWLEDGE_CHECK.value:
            rules_prompt = """
1 **Initiating the topic:** The discussion should primarily involve the Machine Learning Engineer (MLE) and the Candidate.
2 **Limit on Questions:**
   - **Only three questions** with atleast one followup should be asked by the panelists in this section.
   - After every question, the **candidate must be given a chance to respond** before the next question is posed.
                """

        elif subtopic.name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
            rules_prompt = """  
1 **Initiating the topic:** The discussion should be primarily led by the Product Manager (PM).
2 **PM’s Focus Areas:**
   - The PM should take the lead when discussing:
     - **Product impact**.
     - **Cross-functional collaboration**.
     - ** Behavioral Aspect** .
3 **MLE’s Role:**
   - The Machine Learning Engineer (MLE) should **only** be selected as the next speaker **if the discussion shifts towards:**
     - **Technical depth**
4 **Limit on Questions:**
   - **Only three questions** with atleast one followup should be asked by the panelists in this section.
   - After every question, the **candidate must be given a chance to respond** before the next question is posed.
5. If one of the panelist has thanked and decided to end the interview, then ensure candidate is made the next speaker and the interview ends.
                """

        return rules_prompt

    def get_topic_completion_topic_wise_prompt(
        self,
        topic_data: InterviewTopicData,
        subtopic_data: SubTopicData,
        current_section: str,
        subtopic_sections: List[str],
    ) -> str:
        if topic_data.name == TOPICS_HR_ROUND.INTRODUCTION_ROLE_FIT.value:
            if subtopic_data.name == SUBTOPICS_HR_ROUND.INTRODUCTIONS_INTERVIEW_FORMAT.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Introduction Section:
   1.1 Has the HR manager introduced themselves (name, role, brief background)?
   1.2 Has the HR manager asked the candidate to introduce themselves?
   1.3 If the candidate has already provided these details in their response, this section is complete.
                    """

                elif current_section == subtopic_sections[1]:
                    rules_prompt = """
1. Interview Overview Section:
   1.1 Has the HR manager explained the interview structure and format to the candidate?
   1.2 Has the HR manager outlined the topics that will be covered during the interview?
   1.3 If the candidate has already addressed these points, this section is complete.
                    """

            elif subtopic_data.name == SUBTOPICS_HR_ROUND.JOB_ROLE_FIT.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Responsibilities & Role Expectations Section:
   1.1 Has the HR manager explained the key responsibilities of the role?
   1.2 Has the HR manager outlined expected day-to-day tasks?
   1.3 If the candidate has already addressed these points, this section is complete.
                    """

                elif current_section == subtopic_sections[1]:
                    rules_prompt = """
1. Required Skills & Qualifications Section:
   1.1 Has the HR manager described the essential skills and qualifications?
   1.2 Has the HR manager asked about the candidate’s experience with these skills?
   1.3 If the candidate has already provided relevant details, this section is complete.
                    """

            elif subtopic_data.name == SUBTOPICS_HR_ROUND.MOTIVATIONS_CAREER_GOALS.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Reason for Job Change:
   1.1 Has the HR manager asked why the candidate is leaving their current role?
   1.2 If not asked, has the candidate already explained their reason for leaving?
                    """

                elif current_section == subtopic_sections[1]:
                    rules_prompt = """
1. Long-Term Career Aspirations:
   1.1 Has the HR manager asked about the candidate’s future career goals?
   1.2 If not asked, has the candidate already discussed their ambitions?
   1.3 If the candidate has already addressed these points, this section is complete.
                    """

                elif current_section == subtopic_sections[2]:
                    rules_prompt = """
1. Interest in This Role & Company:
   1.1 Has the HR manager asked what excites the candidate about this role?
   1.2 If not asked, has the candidate already mentioned why they are interested?
   1.3 If the candidate has already addressed these points, this section is complete.
                    """

        elif (
            topic_data.name == TOPICS_TECHNICAL_ROUND.TEAM_INTRODUCTIONS_AND_INTERVIEW_FORMAT.value
        ):
            if subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.PANEL_MEMBER_INTRODUCTIONS.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Panel Member Introductions:
   1.1 Has each panelist introduced themselves?
   1.2 Has the candidate responded?
   1.3 If both the panelist has introduced themselves and candidate has responded, this section is complete.
                    """

            elif subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.INTERVIEW_ROUND_OVERVIEW.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Interview Round Overview:
   1.1 Has one of the panel members explained the focus areas of the interview round?
   1.2 Has the candidate acknowledged their readiness to proceed in some form or the other?
   1.3 If the round overview has been discussed and the candidate is ready, this section is complete.
                    """

        elif (
            topic_data.name
            == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        ):
            if subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.TECHNCAL_PROBLEM_OVERVIEW.value:
                if current_section == subtopic_sections[0]:
                    rules_prompt = """
1. Problem Explanation and Clarification from Candidate:
   1.1 Has one of the panel members clearly explained the technical problem to the candidate?
   1.2 Has any of the panel members given an opportunity to ask clarifying questions about the task to the candidate?
   1.3 If the candidate has indicated their readiness to proceed in any form then this section is complete.
                    """
            elif subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.PROBLEM_SOLVING.value:
                rules_prompt = """
1. Candidate Problem-Solving:
   1.1 Has the time limit for the problem solving task exceeded?
   1.2 Has the candidate summitted the problem?
                    """

        elif subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.TASK_SPECIFIC_DISCUSSION.value:
            if current_section == subtopic_sections[0]:
                rules_prompt = """
1. Task Specific Discussion:
   1.1 Has any of the panelists asked the candidate regarding the task they just completed?
   1.2 Has atleast one followup question been asked by the panelist to their question?
   1.3 If total of three questions (similar or different) have been asked by the panelists, then, this section is complete.
                    """

        elif subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.CONCEPTUAL_KNOWLEDGE_CHECK.value:
            if current_section == subtopic_sections[0]:
                rules_prompt = """
1. Core ML/Data Science Concepts
  1.1 Has any of the panel members asked the candidate about machine learning or data science concepts?
  1.2 Has atleast one followup question been asked by the panelist to their question?
  1.3 If total of three questions (similar or different) have been asked by the panelists, this section is complete.
                    """

        elif subtopic_data.name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
            if current_section == subtopic_sections[0]:
                rules_prompt = """
1. Past Experience Related Discussion:
 1.1 Has any of the panel members asked the candidate about their past work experience or related?
 1.2 Has atleast one followup question been asked by the panelist to their question?
 1.3 If total of three questions (similar or different) have been asked by the panelists, this section is complete.
 1.4 If panelist has thanked the candidate, then this section is marked as complete 
                    """

        return rules_prompt

    def get_evaluation_topic_wise_question_prompt(
        self,
        interview_round,
        topic_name,
        subtopic_name,
        activity_progress,
        activity_code_from_candidate,
    ) -> str:
        prompt = ""
        if interview_round == InterviewRound.ROUND_TWO:
            if (
                topic_name
                == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
            ):
                prompt = f"""
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {self.starter_code_data}
- **Analysis of the Candidate’s Approach in solving the problem is mentioned here:**
1. Performance summary: {activity_progress.candidate_performance_summary}
2. Percentage of question solved (between 0 and 1): {activity_progress.percentage_of_question_solved}
3. Things left to be solved: {activity_progress.things_left_to_do_with_respect_to_question}
-4. The raw code written by the candidate within the starter code:{activity_code_from_candidate}

In this topic, the primary focus is on the candidate’s problem-solving ability through coding. You must pay attention to the code written by the candidate but ignore the starter code since it was provided to them"
While limited communication may occur, the evaluation should center on how effectively the candidate approached, reasoned about, and implemented the solution.
When answering any of the questions, you must consider the following:
"1. When looking at the efficiency of the code, you must consider code within the functions written by candidate. Also, linear time complexity as part of preprocessing is efficient but functions must avoid using such methods. \n"
"2. When considering evaluation on the grounds of structured level, do not consider comments, error handling or edge cases being handled by the candidate"
"3. Ensure for each of the questions, do not consider edge cases, error handling and starter code in answering the question until and unless the question explcitly says so"  

Answer the following questions to evaluate the candidate's performance for each of the criterions:

***Criteria: coding***
Q1. Did the candidate implement a correct and functional solution beyond the provided starter code?
Q2. Does the candidate's code (excluding started code) produce the correct output for expected inputs? Ignore edge cases and syntax errors.
Q3. Was the candidate’s approach logically sound with respect to the problem statement, disregarding edge cases?
Q4. Did the candidate address all relevant edge cases in their solution beyond the starter code?
Q5. Does the candidate’s code (excluding starter code) follow the python language’s syntax rules? Ignore logic/edge cases. 
Q6. Did the candidate demonstrate a solid understanding of the problem’s requirements and constraints through their code (excluding edge cases and starter code)?
Q7. Was the overall structure and strategy of the candidate’s solution well-organized? Ignore logic/edge cases
Q8. Did the candidate arrive at an optimal solution in terms of time and space complexity, ignoring syntax issues and edge case handling?
Q9. Is the candidate’s code, beyond the starter code, readable and understandable for a junior engineer, assuming edge case handling and error management are not prioritized?
Q10. Would the candidate’s solution, excluding the starter code, scale to large datasets and perform in real-time, assuming edge cases and error handling are not critical?
Q11. Does the candidate’s code (excluding starter code) avoid major resource leaks?
Q12. Did the candidate select appropriate data structures?

***Criteria: non-technical skills ***
Q1. Did the candidate try to understand the question by asking relevant questions?
Q2. Did the candidate demonstrate a clear grasp of the problem requirements and constraints through the questions?
Q3. Would the candidate be able to communicate with fellow team members?
Q4. Do they sound excited and interested in answering the questions?

                """

            elif topic_name == TOPICS_TECHNICAL_ROUND.DEEP_DIVE_QA.value:
                if subtopic_name == SUBTOPICS_TECHNICAL_ROUND.TASK_SPECIFIC_DISCUSSION.value:
                    prompt = f"""
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {self.starter_code_data}

"- **Analysis of the Candidate’s Approach in solving the problem is mentioned here:**
1. Performance summary: {activity_progress.candidate_performance_summary}
2. Percentage of question solved (between 0 and 1): {activity_progress.percentage_of_question_solved}
3. The raw code written by the candidate within the starter code:{activity_code_from_candidate}
"You must not consider the starter code as part the evaluation since it was provided to the candidate.\n"

Answer the following questions to evaluate the candidate's performance:

*** Criteria: knowledge and problem solving:
Q1. Did the candidate clearly explain why their approach works and provide justification for their decisions?
Q2. Did the candidate describe their solution in a clear and understandable way?
Q3. Did the candidate suggest any possible improvements or optimizations to their solution?
Q4. Did the candidate independently identify areas for improvement or optimization?
Q5. Did their explanations reflect the ability to write production-quality code?
Q6. Were their explanations consistent with the code they wrote?
Q7. Did their responses convey confidence and clarity?
Q8. Did they ensure all aspects of the question were addressed in their responses?
Q9. Did they respond to panelist feedback and questions in a thoughtful and constructive manner?


*** Criteria: non-technical skills:
Q1. Did the candidate explain their approach and decision-making process clearly and concisely?
Q2. Does the candidate demonstrate the ability to communicate effectively with non-technical stakeholders?
Q3. Does the candidate appear capable of collaborating well in a team and communicating effectively?
Q4. Did the candidate show enthusiasm and genuine interest while responding to questions?

                    """

                elif subtopic_name == SUBTOPICS_TECHNICAL_ROUND.CONCEPTUAL_KNOWLEDGE_CHECK.value:
                    prompt = """
This topic focuses on the candidate’s understanding of core machine learning and data science concepts, as well as their ability to communicate those concepts clearly.
The goal is to evaluate both **technical correctness** and the **clarity of their reasoning**, especially in contexts where they might need to explain ideas to non-technical stakeholders.
Answer the following questions to evaluate the candidate's performance:

**Criteria: knowledge and problem solving:**
Q1. Did the candidate demonstrate a solid understanding of the machine learning or data science concepts they were asked about?
Q2. Did the candidate support their explanations with relevant examples, references, or reasoning?
Q3. Did the candidate display breadth of knowledge and cover most of the key concepts in their responses?
Q4. Did the candidate’s answers reflect practical experience in the field?
Q5. Did the candidate’s response convey depth and clarity, showing they truly understand the topic?
Q6. Was the candidate’s answer specific and well-articulated, rather than vague or generic?
Q7. Did the candidate respond with visible interest and enthusiasm?


**Criteria: non-technical Skills:**
Q1. Can they communicate their ideas clearly and concisely to non technical stakeholders?
Q2. Can they explain complex concepts in a way that is easy to understand?
Q3. Did the candidate handle followup questions well?
Q4. Do they sound excited and interested in answering the questions?
                    """

                elif subtopic_name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
                    prompt = """
This topic evaluates the candidate's ability to reflect on and communicate past experiences, especially in collaborative, technical, or ambiguous situations.

Answer the following questions to evaluate the candidate's performance:

** Criteria: knowledge and problem solving:**
Q1. Did the candidate provide a relevant example of how they addressed a technical or team-related challenge, if asked?
Q2. Did the candidate demonstrate a structured and logical approach to decision-making in past situations, if asked?
Q3. Was the candidate able to clearly articulate their role and contributions within a team setting, if asked?
Q4. Did the candidate showcase problem-solving skills by explaining how they handled unexpected challenges, if asked?
Q5. Did the candidate demonstrate innovation or creativity in their problem-solving approach?
Q6. Across all questions, did the candidate clearly define their role and individual contributions?
Q7. Did the candidate’s responses feel authentic and natural, rather than forced or overly rehearsed?
Q8. Were the candidate’s answers directly relevant to the questions asked?
Q9. Did their responses provide a clear sense of the impact and value of their contributions?

**Criteria: non-technical Skills:**
Q1. Did the candidate clearly and concisely communicate their past experiences?
Q2. Did the candidate demonstrate the ability to collaborate effectively with cross-functional teams or non-technical stakeholders?
Q3. Did the candidate exhibit emotional intelligence by showing awareness of team dynamics and approaches to conflict resolution?
Q4. Did the candidate highlight their ability to prioritize tasks and manage time effectively in previous projects?
Q5. Did the candidate convey a strong sense of ownership and accountability in their past work?
Q6. Did the candidate reflect self-awareness and thoughtful reflection in sharing their past experiences?
Q7. Did the candidate express humility and a willingness to learn from past challenges or feedback?

                    """
        return prompt

    def get_evaluation_topic_wise_prompt(
        self, interview_round, topic_name, subtopic_name, activity_progress
    ) -> str:
        prompt = ""
        if interview_round == InterviewRound.ROUND_ONE:
            if topic_name == TOPICS_HR_ROUND.INTRODUCTION_ROLE_FIT.value:
                prompt = """
### **What to Evaluate:**
Since this section is about introductions and role fit, you should focus on **communication** and **cultural fit**.
- **Communication:** Assess how clearly and concisely the candidate introduced themselves.
- Did they provide relevant details about their background, experience, and interests?
- Were their responses structured and easy to follow?
- Did they engage appropriately in the conversation?
- **Cultural & Values Fit:** Look for any indications that the candidate aligns with the company’s values.
- Did they express enthusiasm for the role or company?
- Did they mention any experiences or values that align with the company’s culture?
                            """

        elif interview_round == InterviewRound.ROUND_TWO:
            if topic_name == TOPICS_TECHNICAL_ROUND.TEAM_INTRODUCTIONS_AND_INTERVIEW_FORMAT.value:
                prompt = """
- Assess how clearly and concisely the candidate introduced themselves.
- Did they engage appropriately in the conversation?
                """

            if (
                topic_name
                == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
            ):
                prompt = f"""
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {self.starter_code_data}
- **Analysis of the Candidate’s Approach in solving the problem is mentioned here:**
1. Performance summary: {activity_progress.candidate_performance_summary}
2. Percentage of question solved (between 0 and 1): {activity_progress.percentage_of_question_solved}
3. Things left to be solved: {activity_progress.things_left_to_do_with_respect_to_question}

"In this topic, the primary focus is on the candidate’s problem-solving ability through coding.
"While limited communication may occur, the evaluation should center on how effectively the candidate approached, reasoned about, and implemented the solution.

"### **Key Evaluation Criteria:**
- **Problem Completion:** Did the candidate arrive at a working and correct solution?
- **Code Quality:** Were there logical mistakes or bugs? Was the code syntactically and semantically sound?
- **Problem Understanding:** Did the candidate demonstrate a clear grasp of the problem requirements and constraints?
- **Approach & Reasoning:** Was the candidate’s solution strategy structured and reasonable?
- **Clarifying Questions (if any):** Were their questions purposeful and helpful in narrowing down the solution?

"### **Scoring Considerations:**
- Focus primarily on the coding aspect: correctness, structure, and reasoning.
- Do not penalize for lack of communication.
- If the candidate did not fully solve the problem but showed a strong approach or partial working solution, score accordingly.
- High scores require correct implementation.
                """

            elif topic_name == TOPICS_TECHNICAL_ROUND.DEEP_DIVE_QA.value:
                if subtopic_name == SUBTOPICS_TECHNICAL_ROUND.TASK_SPECIFIC_DISCUSSION.value:
                    prompt = f"""
- **Technical Problem Details presented to the candidate:**
1. Scenario: {self.activity_details.scenario}
2. Data Available: {self.activity_details.data_available}
3. Task for the Candidate: {self.activity_details.task_for_the_candidate}
4. Starter Code provided to the candidate:** {self.starter_code_data}

"- **Analysis of the Candidate’s Approach in solving the problem is mentioned here:**
1. Performance summary: {activity_progress.candidate_performance_summary}
2. Percentage of question solved (between 0 and 1): {activity_progress.percentage_of_question_solved}
3. Things left to be solved: {activity_progress.things_left_to_do_with_respect_to_question}

"This topic focuses on the candidate’s ability to verbally reason through the coding problem, explain their approach, and communicate their thought process clearly.
"A complete or working implementation is **not required** in this section. The emphasis is on **structured thinking**, **clarity**, and **how the candidate approaches problem-solving verbally**.

"### **Key Evaluation Criteria:**
"- **Relevance:** Did their explanations align with the questions they were asked?
"- **Confidence & Communication:** Did they respond with clarity and confidence, or were they unsure and inconsistent?
"- **Structured Thinking:** Did they demonstrate a logical, step-by-step way of thinking about the problem?
"- **Awareness of Trade-offs or Alternatives:** Did they consider edge cases, performance, or different approaches when prompted?

"### **Scoring Considerations:**
"- A candidate who did **not** solve the coding problem can still score **high** if they clearly explain a viable approach and show structured reasoning.
"- Candidates who ramble, contradict themselves, or struggle to communicate basic ideas should be scored lower, regardless of whether their code worked.
"- High scores should be reserved for candidates who show **clarity, coherence, and strategic thinking**, even in the absence of code.
"- Score mid-range if the candidate showed partial understanding or was only able to explain some aspects of the solution"
                    """

                elif subtopic_name == SUBTOPICS_TECHNICAL_ROUND.CONCEPTUAL_KNOWLEDGE_CHECK.value:
                    prompt = """
"This topic focuses on the candidate’s understanding of core machine learning and data science concepts, as well as their ability to communicate those concepts clearly.
"The goal is to evaluate both **technical correctness** and the **clarity of their reasoning**, especially in contexts where they might need to explain ideas to non-technical stakeholders.

"### **Key Evaluation Criteria:**
"- **Conceptual Understanding:** Did the candidate demonstrate sound understanding of ML/data science fundamentals if asked?
"- **Clarity of Explanation:** Did they explain their answers in a clear and structured way, avoiding unnecessary jargon?
"- **Audience Awareness:** Could they reasonably explain their approach to someone without a technical background (e.g., a designer, product manager, or executive)?
"- **Confidence & Reasoning:** Did they answer confidently and logically, even if they didn’t cover every technical detail?

"### **Scoring Considerations:**
"- High scores should reflect both **technical accuracy** and the ability to explain ideas clearly to others.
"- If the candidate used real-world examples, analogies, or broke down complex ideas understandably, this is a strong indicator of expertise.
"- Candidates who give correct but overly complex or disorganized answers should be scored in the mid-range.
"- If the candidate struggled to explain basic concepts or gave inconsistent/confusing responses, score accordingly on the lower end.
"- Keep in mind that responses may be brief due to time limits — prioritize **breadth of concepts covered** over depth.
                    """

                elif subtopic_name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
                    prompt = """
"This topic evaluates the candidate's ability to reflect on and communicate past experiences, especially in collaborative, technical, or ambiguous situations.
"The focus is on their **communication**, **self-awareness**, and **ability to navigate real-world scenarios**, particularly in team-based settings.

"### **Key Evaluation Criteria:**
"- **Relevance & Alignment:** Did their responses directly answer the questions asked? Were examples on-topic and specific?
"- **Ownership & Clarity:** Did they clearly explain their own role and contributions, not just what the team did?
"- **Confidence & Communication:** Did they speak with clarity, confidence, and structure (e.g., STAR format or similar)?
"- **Collaboration:** Did they demonstrate the ability to work well with teammates, cross-functional partners, or non-technical stakeholders?
"- **Problem Solving in Context:** Did they share examples of navigating ambiguity, resolving technical challenges, or handling interpersonal conflict?
"- **Stakeholder Awareness:** Could you imagine them communicating effectively in a real job setting with both technical and non-technical peers?

"### **Scoring Considerations:**
"- High scores should reflect candidates who shared **specific, well-articulated stories** showing **initiative, collaboration, and reflection**.
"- Responses that are vague, overly generic, or lack personal ownership should be scored in the mid to lower range.
"- If the candidate demonstrated strong technical thinking but poor interpersonal awareness, reflect that in the relevant scores.
"- Brief but clear responses are acceptable; focus on **quality of insight** over quantity.
                    """

        return prompt
