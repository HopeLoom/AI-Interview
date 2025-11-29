import json
from typing import List
from core.prompting.base import BaseInterviewPromptStrategy
from core.prompting.schema import LanguageModelClassification
from core.resource.model_providers.schema import AssistantChatMessage, ChatMessage
from core.prompting.schema import ChatPrompt
from interview_details_agent.base import PromptInput
from interview_details_agent.base import CharacterDataOutput, CharacterData, JobDetails, InterviewRoundDetails
from interview_details_agent.base import StarterCodeData, ActivityDetailsOutputMessage

class InterviewGenerationPromptStrategy(BaseInterviewPromptStrategy):

    def __init__(self, configuration):
        self.config = configuration 
        self.response_schema = None                                  

    def model_classification(self):
        return LanguageModelClassification.SMART_MODEL
    
    def build_prompt(self, prompt_input:PromptInput):
        response_type = prompt_input.response_type
        if response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.ACTIVITY_DETAILS.value:
            system_message = self._generate_activity_details_prompt(prompt_input)
        elif response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.CHARACTER_INFO.value:
            system_message = self._generate_character_info_prompt(prompt_input)
        elif response_type == BaseInterviewPromptStrategy.RESPONSE_TYPE.STARTER_CODE_GENERATION.value:
            system_message = self._generate_starter_code_generation_prompt(prompt_input)
        
        prompt = ChatPrompt(
            messages = [
                ChatMessage.system(system_message)
            ]
        ) 
        return prompt
    
    def _generate_activity_details_prompt(self, prompt_input:PromptInput):
        
        job_details:JobDetails = prompt_input.job_details
        job_title = job_details.job_title
        job_description = job_details.job_description
        job_requirements = job_details.job_requirements
        job_qualifications = job_details.job_qualifications
        company_name = job_details.company_name
        company_description = job_details.company_description
        example_activity_details_output:List[ActivityDetailsOutputMessage] = prompt_input.example_activity_details_output
        example_job_details:List[JobDetails] = prompt_input.example_job_details
        output = ActivityDetailsOutputMessage()
        
        prompt = f"""
You are part of an interview simulation where candidate and panelists are involved.
Candidate in this stage is supposed to perform an activity during the interview which is mainly related to coding.
Coding activity is supposed to be relevant to the job they are applying. This information is contained in the job description, job requirements, job qualifications. 
Apart from the job specific information, which company the job is for is also relevant. This information is contained in the company name and description.
                
The following are some of such details:
1. Job Title: {job_title}
2. Job Description: {job_description}
3. Job Requirements: {job_requirements}
4. Job Qualifications: {job_qualifications}
5. Company Name: {company_name}
6. Company Description: {company_description}

To generate the coding activity, there are multiple steps involved. The first step is to generate a realistic work scenario which the team they are interviewing is facing in their day-day work.
In the second step, once the scenario is generated, the next step is to figure out starter code that will be provided to the candidate to help them solve the activity.
You are reponsible for the first step which is generating the scenario.
When you generate coding activity scenario details, it should include the following:
1. Scenario description
2. Task description for the candidate to complete
3. Data to be used for the activty (if applicable)

Scenario description should be a high level description of the challenge that the team is currently facing in their day-day work.
Task for the candidate should be a high level description of what the candidate is expected to do in the coding activity related to the scenario. 
This should be written in a form that one of the interviewers will read to the candidate.
Since task requires a candidate to write code, we should make sure that the task description mentions that starter code will be provided to help them solve the task.
If the task involves data, then the data to be used to solve the task should be mentioned here. Here we should only mention the data attributes and not the data itself.

Respond in JSON format with the structure mentioned here: {output}
Here is an example of a scenario relevant to another job whose details can be found here: {example_job_details}
The generated coding activity scenario relevant to this job can be found here: {example_activity_details_output}
Its important to understand different aspects when generating the scenario which are the following:
1. The coding activity is supposed to be completed by the candidate in 10 mins.
2. Scenario should be relevant to the job and company details.
3. Scenario should be realistic and not too easy or too hard.
4. Make use of simple language and avoid technical jargon beyond the job description
5. Generate the output in a similar format as the example provided.
"""
        return prompt
    
    def _generate_starter_code_generation_prompt(self, prompt_input:PromptInput):
        
        starter_code = StarterCodeData(code="", description="")
        #job_details:JobDetails = prompt_input.job_details
        generated_activity_details:ActivityDetailsOutputMessage = prompt_input.generated_activity_details_output
        # job_title = job_details.job_title
        # job_description = job_details.job_description
        # job_requirements = job_details.job_requirements
        # job_qualifications = job_details.job_qualifications
        # company_name = job_details.company_name
        # company_description = job_details.company_description

        example_activity_details_output:List[ActivityDetailsOutputMessage] = prompt_input.example_activity_details_output
        example_starter_code_output:List[StarterCodeData] = prompt_input.example_starter_code_output
        
        prompt = f"""
You are part of interview simulation engine responsible for generating details regarding the interview.
Candidate in this stage is supposed to perform an activity during the interview which is mainly related to coding.
Coding activity is supposed to be relevant to the job they are applying. This information is contained in the job description, job requirements, job qualifications. 
Apart from the job specific information, which company the job is for is also relevant. This information is contained in the company name and description.
To generate the coding activity, there are multiple steps involved. The first step is to generate a realistic work scenario which the team they are interviewing is facing in their day-day work.
In the second step, once the scenario is generated, the next step is to figure out starter code that will be provided to the candidate to help them solve the activity.
You have already completed the first step which is generating the scenario details. Now, you are supposed to generate the starter code for the coding activity.
Starter code should follow certain guidelines which are the following:
1. Starter code should have comments explaining the code.
2. If the scenario involves data, then data should be included in the starter code. Scenario includes data attributes and not the data itself. You should make sure to include some random data associated with the attributes to help the candidate understand the data.
3. The function signature that the candidate is expected to write code for should be included in the starter code with a TODO comment.
The generated scenario details for which the starter code must be generated can be found here : {generated_activity_details.model_dump_json()}
You must respond in JSON format with the starter codestructure mentioned here: {starter_code.model_dump_json()}
To help you with this task, here is an example of the starter code relevant to another scenario:
1. Example coding activity scenario details: {example_activity_details_output}
2. Starter code relevant to the example activity details: {example_starter_code_output}
        """
        return prompt


    def _generate_character_info_prompt(self, prompt_input:PromptInput):

        character_data = CharacterData()
        character_data_output = CharacterDataOutput(
            data = [character_data]
        )

        example_character_data_output:List[CharacterDataOutput] = prompt_input.example_character_data_output
        example_job_details:List[JobDetails] = prompt_input.example_job_details
        example_activity_output:List[ActivityDetailsOutputMessage] = prompt_input.example_activity_details_output
        generated_activity_data = prompt_input.generated_activity_details_output
        job_details:JobDetails = prompt_input.job_details
        job_title = job_details.job_title
        job_description = job_details.job_description
        job_requirements = job_details.job_requirements
        job_qualifications = job_details.job_qualifications
        company_name = job_details.company_name
        company_description = job_details.company_description
        interview_round_details = prompt_input.interview_round_details

        prompt = f"""
You are part of interview simulation engine responsible for generating details regarding the interview.
In this phase, you only care about the panelists participating in this interview with the candidate.
You have to generate the character information for the panelist who are representing the company and interviewing the candidate for a particular job.
To perform this task, the following information is provided to you regarding the job and the company:
1. Job Title:{job_title}
2. Job Description:{job_description}
3. Job Requirements:{job_requirements}
4. Job Qualifications:{job_qualifications}
5. Company Name:{company_name}
6. Company Description:{company_description}

Interview round details are as follows: {interview_round_details.model_dump_json()}
During the interview, candidate will be performing a coding activity which is related to the job they are applying for. The details for the activity can be found here:
{generated_activity_data.model_dump_json()}
The following are the type of panelists who can participate in the interview:
1. ML Engineer
2. Data Scientist
3. Product Manager
4. UI/UX Designer
5. Backend Developer
6. Full Stack Engineer
7. QA Engineer
8. Business Analyst
You can select upto 2 panelists for the technical interview
You must respond in JSON format with the structure mentioned here: {character_data_output.model_dump_json()}
Example character data output can be found here:
{example_character_data_output}
These characters correspond to the following job details:
{example_job_details}
and have the following activity details:
{example_activity_output}
Please note that the HR manager and HR round is optional and hence you can ignore it.
When selecting panelists, make sure to select in a way that they are not only relevant to the job but also they cover both the technical and non technical aspects of the job.
        """
        return prompt


    def parse_response_content(self, response: AssistantChatMessage):
        # Assistant chat message consists of the following
        # content: str
        # role: str
        try:
            json_data = json.loads(response.content) if response.content is not None else {}
        except json.JSONDecodeError:
            json_data = {}

        return json_data