import asyncio
import json
from asyncio import Queue
from pathlib import Path
from typing import Any, cast

from interview_details_agent.base import BaseInterviewConfiguration

from activity_agent.base import (
    ActivityProgressAnalysisOutputMessage,
    ActivityProgressAnalysisSummaryForPanelistOutputMessage,
    ActivityProgressWithRespectToQuestionOutputMessage,
    BaseActivity,
    BaseActivityConfiguration,
    PromptInput,
)
from core.database.base import DatabaseInterface
from core.prompting.prompt_strategies.activity_one_shot import ActivityPromptStrategy, ChatPrompt
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelProvider,
)
from master_agent.base import (
    CommunicationMessage,
    InterviewRound,
    MasterMessageStructure,
    SimulationRole,
    SystemMessageStructure,
    SystemMessageType,
)


# when creating a new agent, we need to pass the settings and llm_provider
class Activity(BaseActivity):
    prompt_strategy: Any = None

    def __init__(
        self,
        activity_config: BaseActivityConfiguration,
        user_id: str,
        firebase_user_id: str,
        session_id: str,
        interview_config: BaseInterviewConfiguration,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        database: DatabaseInterface,
        receiving_message_queue: Queue,
        sending_message_queue: Queue,
        logger,
        is_evaluating: bool = False,
    ):
        prompt_strategy = ActivityPromptStrategy(activity_config, interview_config)
        # this calls the __init__ method of the base agent
        super().__init__(
            activity_config=activity_config,
            llm_provider=llm_provider,
            gemini_provider=gemini_provider,
            groq_provider=groq_provider,
            prompt_strategy=prompt_strategy,
        )
        self.user_id = user_id
        self.session_id = session_id
        self.firebase_user_id = firebase_user_id
        self.logger = logger
        self.prompt_strategy = prompt_strategy
        self.database = database
        self.interview_config = interview_config
        self.receiving_message_queue: Queue = receiving_message_queue
        self.sending_message_queue: Queue = sending_message_queue
        self.info_data_path = activity_config.activity_info_file_path
        self.code_data_path = activity_config.activity_code_file_path
        self.starter_code_data = (
            self.load_activity_code_info()
        )  # Load answer code from file. we are not using this anywhere
        self.starter_code_data = self.starter_code_data
        self.interview_round_part_of = InterviewRound.ROUND_TWO
        self.activity_details = activity_config.activity_details
        self.progress_history = []
        self.recent_progress: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        )
        self.is_processing = False
        self.activity_code_from_candidate = ""
        self.master_instance = None
        self.lock = asyncio.Lock()
        self.data_dir = Path(__file__).parent.parent / "data" / user_id

        if not is_evaluating:
            # check if any previous file is present, if yes then delete
            data_path = Path(self.data_dir)
            for file_pattern in [
                "_progress_analysis_output.json",
                "_progress_analysis_with_respect_to_question_output.json",
                "_progress_analysis_summary_for_panelist.json",
                "_activity_code_from_candidate.json",
            ]:
                file_path = data_path / file_pattern
                file_path.unlink(missing_ok=True)

        else:
            # load data from file
            # we should load data from database instead of file
            asyncio.run(self.load_activity_progress())
            asyncio.run(self.load_activity_code_from_candidate())

        self.logger.info("Activity agent created")

    async def load_activity_progress(self):
        activity_progress = await self.database.get_activity_progress_analysis_output_from_database(
            self.firebase_user_id, self.session_id
        )
        if activity_progress is None:
            self.logger.info("No previous progress history summary for panelist found")
            self.recent_progress = ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        else:
            self.recent_progress = ActivityProgressAnalysisSummaryForPanelistOutputMessage(
                **json.loads(activity_progress["activity_progress_summary_for_panelist"])
            )

    async def load_activity_code_from_candidate(self):
        self.activity_code_from_candidate = await self.database.get_recent_code_data(
            self.firebase_user_id
        )
        if self.activity_code_from_candidate is None:
            self.logger.info("No previous activity code from candidate found")
            self.activity_code_from_candidate = ""
        else:
            self.activity_code_from_candidate = self.activity_code_from_candidate["activity_code"]
            self.logger.info(
                f"Loaded activity code from candidate: {self.activity_code_from_candidate}"
            )

    def set_master_instance(self, master_instance):
        self.master_instance = master_instance

    def get_receiving_message_queue(self):
        return self.receiving_message_queue

    async def load_activity_code_info(self):
        code = await self.database.fetch_starter_code_from_url()
        self.logger.info(f"code from firebase is: {code}")
        return code

    def send_response(self, response: CommunicationMessage):
        self.logger.info(f"Sending response to master: {response}")
        self.sending_message_queue.put_nowait(response)

    def parse_and_process_response_activity_progress(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> ActivityProgressAnalysisOutputMessage:
        try:
            if response.content is None:
                return ActivityProgressAnalysisOutputMessage()

            json_data = json.loads(response.content)
            self.logger.info(f"json_data inside activity analysis is: {json_data}")

            if "error" in json_data:
                return ActivityProgressAnalysisOutputMessage()

            return ActivityProgressAnalysisOutputMessage.model_validate(json_data)

        except json.JSONDecodeError as e:
            self.logger.exception(f"Failed to parse JSON response: {e}")
            return ActivityProgressAnalysisOutputMessage()

        except Exception as e:
            self.logger.exception(f"Error processing activity progress: {e}")
            return ActivityProgressAnalysisOutputMessage()

    def parse_and_process_response_activity_progress_with_respect_to_question(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> ActivityProgressWithRespectToQuestionOutputMessage:
        if response.content is None:
            return ActivityProgressWithRespectToQuestionOutputMessage()
        json_data = json.loads(response.content)
        self.logger.info(
            f"json_data inside activity progress with respect to question is: {json_data}"
        )
        if "error" in json_data:
            return ActivityProgressWithRespectToQuestionOutputMessage()
        output = ActivityProgressWithRespectToQuestionOutputMessage.model_validate(json_data)
        return output

    def parse_and_process_response_activity_progress_summary_for_panelist(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ) -> ActivityProgressAnalysisSummaryForPanelistOutputMessage:
        if response.content is None:
            return ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        json_data = json.loads(response.content)
        self.logger.info(f"json_data inside activity progress summary for panelist is: {json_data}")
        if "error" in json_data:
            return ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        output = ActivityProgressAnalysisSummaryForPanelistOutputMessage.model_validate(json_data)
        return output

    async def get_high_level_analysis(
        self, message: MasterMessageStructure
    ) -> ActivityProgressAnalysisOutputMessage:
        prompt_input = PromptInput(
            response_type=ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_HIGH_LEVEL_ANALYSIS,
            starter_code=self.starter_code_data if self.starter_code_data is not None else "",
            activity_code_from_candidate=message.activity_code_from_candidate
            if message.activity_code_from_candidate is not None
            else "",
            activity_progress_history=self.progress_history,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        output: ActivityProgressAnalysisOutputMessage = (
            await super().run_activity_progress_analysis(prompt)
        )
        self.logger.info(f"output from high level analysis is: {output}")

        with open(self.data_dir / "_progress_analysis_output.json", "w") as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "activity_progress_analysis",
            output.model_dump() if hasattr(output, "model_dump") else output,
        )

        self.progress_history.append(output.code_intrepretation)
        return output

    async def get_activity_progress_analysis_with_respect_to_question(
        self, message: MasterMessageStructure, activity_progress_analysis
    ) -> ActivityProgressWithRespectToQuestionOutputMessage:
        prompt_input = PromptInput(
            response_type=ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_ANALYSIS_WITH_RESPECT_TO_QUESTION,
            starter_code=self.starter_code_data if self.starter_code_data is not None else "",
            activity_code_from_candidate=message.activity_code_from_candidate,
            activity_progress_history=self.progress_history,
            activity_progress_analysis=activity_progress_analysis,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        output: ActivityProgressWithRespectToQuestionOutputMessage = (
            await super().run_activity_progress_analysis_with_respect_question(prompt)
        )
        self.logger.info(f"output from high level analysis with respect to question is: {output}")

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "activity_progress_with_respect_to_question",
            output.model_dump() if hasattr(output, "model_dump") else output,
        )

        with open(
            self.data_dir / "_progress_analysis_with_respect_to_question_output.json", "w"
        ) as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        return output

    async def get_activity_progress_analysis_summary_for_panelist(
        self,
        message: MasterMessageStructure,
        activity_progress_analysis,
        activity_progress_question,
    ) -> ActivityProgressAnalysisSummaryForPanelistOutputMessage:
        prompt_input = PromptInput(
            response_type=ActivityPromptStrategy.RESPONSE_TYPE.ACTIVITY_ANALYSIS_SUMMARY_FOR_PANELIST,
            starter_code=self.starter_code_data if self.starter_code_data is not None else "",
            activity_code_from_candidate=message.activity_code_from_candidate
            if message.activity_code_from_candidate is not None
            else "",
            activity_progress_history=self.progress_history,
            activity_progress_analysis=activity_progress_analysis,
            activity_progress_with_respect_to_question=activity_progress_question,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)

        output: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            await super().run_activity_progress_analysis_summary_for_panelist(prompt)
        )
        self.logger.info(f"output from high level analysis summary for panelist is: {output}")

        with open(self.data_dir / "_progress_analysis_summary_for_panelist.json", "w") as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "activity_progress_analysis_summary_for_panelist",
            output.model_dump() if hasattr(output, "model_dump") else output,
        )

        return output

    def is_processing_result(self):
        return self.is_processing

    def get_recent_progress(self):
        return self.recent_progress

    def get_activity_code_from_candidate(self):
        return self.activity_code_from_candidate

    async def process_message(self, message: MasterMessageStructure):
        async with self.lock:
            self.activity_code_from_candidate = message.activity_code_from_candidate

            # Save data
            await self._save_activity_data()

            # Check if candidate made changes
            if self._has_candidate_made_changes():
                await self._run_analysis_pipeline(message)
            else:
                await self._set_no_progress_state()

    async def _save_activity_data(self):
        """Save activity data to file and database"""
        try:
            # Save to file
            with open(self.data_dir / "_activity_code_from_candidate.json", "w") as f:
                json.dump(
                    {"activity_code_from_candidate": self.activity_code_from_candidate}, f, indent=4
                )

            # Save to database
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "activity_code",
                {"code": self.activity_code_from_candidate},
            )
        except Exception as e:
            self.logger.exception(f"Failed to save activity data: {e}")

    def _has_candidate_made_changes(self) -> bool:
        """Check if candidate has made changes to the code"""
        return self.activity_code_from_candidate != self.starter_code_data

    async def _run_analysis_pipeline(self, message: MasterMessageStructure):
        """Run the complete analysis pipeline"""
        try:
            self.is_processing = True

            # Run analysis steps
            activity_progress_analysis = await self.get_high_level_analysis(message)
            activity_progress_question = (
                await self.get_activity_progress_analysis_with_respect_to_question(
                    message, activity_progress_analysis
                )
            )
            self.recent_progress = await self.get_activity_progress_analysis_summary_for_panelist(
                message, activity_progress_analysis, activity_progress_question
            )

        except Exception as e:
            self.logger.exception(f"Error in analysis pipeline: {e}")
        finally:
            self.is_processing = False

    async def _set_no_progress_state(self):
        """Set state when candidate hasn't made changes"""
        self.recent_progress = ActivityProgressAnalysisSummaryForPanelistOutputMessage()
        self.recent_progress.candidate_performance_summary = "Activity code from candidate is same as starter code so candidate did not do anything\n"
        self.recent_progress.things_left_to_do_with_respect_to_question = (
            "Candidate did not do anything"
        )
        self.recent_progress.percentage_of_question_solved = 0.0

        try:
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "activity_progress_analysis_summary_for_panelist_no_progress",
                self.recent_progress.model_dump()
                if hasattr(self.recent_progress, "model_dump")
                else self.recent_progress,
            )
        except Exception as e:
            self.logger.exception(f"Failed to save no progress state: {e}")

    async def process_system_message(self, message: SystemMessageStructure):
        if message.system_message_type == SystemMessageType.END:
            self.logger.info("Activity received end message")
        elif message.system_message_type == SystemMessageType.START:
            self.logger.info("Activity received start message")
        elif message.system_message_type == SystemMessageType.INTERVIEW_ROUND_CHANGED:
            self.logger.info("Activity received interview round changed message")

    # this is the main loop for the activity agent
    async def run(self):
        self.logger = self.logger.bind(user_id=self.user_id, session_id=self.session_id)
        self.logger.info("Activity agent started")

        while True:
            try:
                communicationMessage = (
                    self.receiving_message_queue.get_nowait()
                )  # if there is no message, it should raise the queue empty exception

                if self.is_message_for_activity(communicationMessage):
                    self.logger.info("Activity agent received message from master agent")
                    master_message = cast(MasterMessageStructure, communicationMessage.content)
                    await self.process_message(master_message)

                elif self.is_system_message(communicationMessage):
                    self.logger.info("Activity agent received system message from master agent")
                    message = cast(SystemMessageStructure, communicationMessage.content)
                    await self.process_system_message(message)

            except asyncio.QueueEmpty:
                pass
            except Exception as e:
                self.logger.exception(f"Error in main loop of activity agent: {e}")

            await asyncio.sleep(0.1)

    def is_message_for_activity(self, communicationMessage: CommunicationMessage) -> bool:
        """Check if message is for this activity agent"""
        if communicationMessage.sender != SimulationRole.MASTER:
            return False
        if communicationMessage.receiver != SimulationRole.ACTIVITY:
            return False

        message_content = communicationMessage.content
        if not isinstance(message_content, MasterMessageStructure):
            return False

        return message_content.current_interview_round == self.interview_round_part_of

    def is_system_message(self, communicationMessage: CommunicationMessage) -> bool:
        """Check if this is a system message"""
        return (
            communicationMessage.sender == SimulationRole.MASTER
            and communicationMessage.receiver == SimulationRole.ALL
        )
