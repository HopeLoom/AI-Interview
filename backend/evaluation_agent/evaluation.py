import asyncio
import json
import os
from pathlib import Path
from queue import Queue
from typing import Any, List, Optional

from candidate_agent.candidate import Profile
from interview_details_agent.base import BaseInterviewConfiguration, CharacterDataOutput
from panelist_factory.configurators import create_panelist_instance

from activity_agent.activity import Activity
from activity_agent.base import (
    ActivityProgressAnalysisSummaryForPanelistOutputMessage,
    BaseActivityConfiguration,
)
from activity_agent.configurators import create_activity_instance
from core.database.base import DatabaseInterface
from core.prompting.prompt_strategies.evaluation_one_shot import (
    EvaluationPromptStrategy,
)
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelProvider,
)
from evaluation_agent.base import (
    BaseEvaluation,
    BaseEvaluationConfiguration,
    BaseEvaluationPromptStrategy,
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
    TOPICS_TECHNICAL_ROUND,
    BaseMasterConfiguration,
    CandidateEvaluationVisualisationReport,
    CodeAnalysisVisualSummary,
    CodeSubmissionVisualSummary,
    CriteriaScoreVisualSummary,
    CriteriaScoreVisualSummaryList,
    CriteriaSpecificScoring,
    EvaluationInputMessage,
    EvaluationMessageToFrontEnd,
    InterviewRound,
    OldEvaluationMessage,
    OverallVisualSummary,
    PanelistFeedbackVisualSummary,
    PanelistFeedbackVisualSummaryList,
    QuestionSpecificEvaluationOutputMessage,
)
from master_agent.interview_topic_tracker import InterviewTopicTracker
from panelist_agent.panelist import Panelist


class Evaluation(BaseEvaluation):
    # Constants
    EVALUATION_OUTPUT_FILE = "_evaluation_output.json"
    IMAGE_EXTENSION = ".jpg"
    STATIC_IMAGES_DIR = "static"

    # Question weights for coding evaluation
    QUESTION_WEIGHTS = {
        1: 0.20,  # Functional correctness
        2: 0.10,  # Output correctness
        3: 0.10,  # Logical approach
        4: 0.10,  # Edge case handling
        5: 0.02,  # Syntax correctness
        6: 0.02,  # Understanding constraints
        7: 0.03,  # Code structure
        8: 0.15,  # Time and space efficiency
        9: 0.03,  # Readability
        10: 0.10,  # Scalability
        11: 0.03,  # Resource safety
        12: 0.10,  # Data structure selection
    }

    prompt_strategy: Any = None

    def __init__(
        self,
        user_id: str,
        firebase_user_id: str,
        session_id: str,
        logger,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        perplexity_provider: ChatModelProvider,
        database: DatabaseInterface,
    ):
        config: BaseEvaluationConfiguration = BaseEvaluationConfiguration()
        # Load configuration data asynchronously
        json_data = asyncio.run(database.get_simulation_config_json_data())

        # Ensure required fields are present in JSON data before validation
        if json_data and isinstance(json_data, dict):
            if "description" not in json_data:
                json_data["description"] = "Master configuration"
            if "name" not in json_data:
                json_data["name"] = "Master"

        master_config = BaseMasterConfiguration.model_validate(json_data)
        interview_config = master_config.interview_data
        prompt_strategy = EvaluationPromptStrategy(master_config, interview_config, database)

        # Initialize base class
        super().__init__(
            evaluation_config=config,
            llm_provider=llm_provider,
            gemini_provider=gemini_provider,
            groq_provider=groq_provider,
            perplexity_provider=perplexity_provider,
            prompt_strategy=prompt_strategy,
        )

        # Initialize instance variables
        self.user_id = user_id
        self.firebase_user_id = firebase_user_id
        self.session_id = session_id
        self.logger = logger
        self.prompt_strategy = prompt_strategy
        self.database = database
        self.interview_config = interview_config
        self.interview_round_part_of = InterviewRound.ROUND_TWO
        self.evaluation_topic_subtopic_mapping = {}
        self.lock = asyncio.Lock()
        self.data_dir = os.path.dirname(os.path.realpath(__file__)) + "/../data/" + user_id + "/"
        self.interview_data: BaseInterviewConfiguration = interview_config

        # Initialize components
        self._initialize_components()
        asyncio.run(self._setup_interview_metadata())
        asyncio.run(self._handle_image_upload())

        # Initialize agent instances
        self.panelist_instances = []
        self.activity_instance: Optional[Activity] = None

    def _initialize_components(self):
        """Initialize interview components and load data."""
        try:
            self.interview_topic_tracker = InterviewTopicTracker(interview_data=self.interview_data)
            self.interview_topic_tracker.load_interview_configuration(self.logger)
            self.load_data_into_memory(self.data_dir + "memory_graph.json")

            # Load candidate profile asynchronously
            asyncio.run(self._load_candidate_profile())

        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise

    async def _load_candidate_profile(self):
        """Load candidate profile data from database."""
        try:
            profile_json_data = await self.database.get_profile_json_data()
            if profile_json_data:
                self.candidate_profile = Profile(**profile_json_data)
            else:
                self.logger.warning("No profile data found")
                self.candidate_profile = None
        except Exception as e:
            self.logger.error(f"Error loading candidate profile: {e}")
            self.candidate_profile = None

    async def _setup_interview_metadata(self):
        """Setup interview completion status."""
        try:
            interview_metadata = await self.database.get_metadata_from_database(
                self.firebase_user_id, self.session_id
            )

            if interview_metadata:
                self.is_interview_completed = interview_metadata["is_interview_completed"]
                self.logger.info(f"Interview completed: {self.is_interview_completed}")
            else:
                self.is_interview_completed = True
                self.logger.info(
                    "Interview metadata not found. Setting interview completed to True"
                )

        except Exception as e:
            self.logger.error(f"Error setting up interview metadata: {e}")
            self.is_interview_completed = True

    async def _handle_image_upload(self):
        """Handle image upload to Firebase."""
        try:
            # Clean up existing evaluation output file
            evaluation_output_path = os.path.join(self.data_dir, self.EVALUATION_OUTPUT_FILE)
            if os.path.exists(evaluation_output_path):
                os.remove(evaluation_output_path)

            # Upload image
            image_path = self.get_latest_image_path()
            if image_path:
                self.logger.info(f"Uploading image: {image_path}")
                await self.database.upload_image(
                    image_path, self.firebase_user_id, f"{self.user_id}{self.IMAGE_EXTENSION}"
                )
            else:
                self.logger.info("No image found for upload")

        except Exception as e:
            self.logger.error(f"Error handling image upload: {e}")

    def get_latest_image_path(self) -> Optional[Path]:
        """Get the latest image path from the static directory."""
        try:
            image_dir = Path(f"{self.STATIC_IMAGES_DIR}/{self.user_id}/images/")
            if not image_dir.exists():
                return None

            images_list = list(image_dir.glob(f"*{self.IMAGE_EXTENSION}"))
            return max(images_list, key=lambda f: f.stat().st_mtime) if images_list else None

        except Exception as e:
            self.logger.error(f"Error getting latest image path: {e}")
            return None

    async def _create_activity_agent(self):
        """Create activity agent instance."""
        try:
            sending_message_activity_queue = Queue()
            activity_configuration = BaseActivityConfiguration()
            activity_configuration.activity_name = "Activity"
            activity_configuration.activity_details = self.interview_data.activity_details

            self.activity_instance = await create_activity_instance(
                llm_provider=self.llm_provider,
                gemini_provider=self.gemini_provider,
                groq_provider=self.groq_provider,
                user_id=self.user_id,
                firebase_user_id=self.firebase_user_id,
                session_id=self.session_id,
                config=activity_configuration,
                interview_config=self.interview_data,
                database=self.database,
                receiving_message_queue=sending_message_activity_queue,
                sending_message_queue=Queue(),
                logger=self.logger,
                is_evaluating=True,
            )
        except Exception as e:
            self.logger.error(f"Error creating activity agent: {e}")
            raise

    async def _create_panelist_agents(self):
        """Create panelist agent instances."""
        try:
            self.logger.info("Creating panelist agents")
            character_data_output: CharacterDataOutput = self.interview_data.character_data
            character_data_list = character_data_output.data

            for character_data in character_data_list:
                if character_data.interview_round_part_of == InterviewRound.ROUND_TWO.value:
                    self.logger.info(f"Creating panelist for {character_data.character_name}")

                    panelist: Panelist = await create_panelist_instance(
                        interview_config=self.interview_config,
                        llm_provider=self.llm_provider,
                        gemini_provider=self.gemini_provider,
                        groq_provider=self.groq_provider,
                        grok_provider=self.groq_provider,
                        deepseek_provider=self.groq_provider,
                        character_data=character_data,
                        sending_message_queue=Queue(),
                        receiving_message_queue=Queue(),
                        data_dir=self.data_dir,
                        user_id=self.user_id,
                        firebase_user_id=self.firebase_user_id,
                        session_id=self.session_id,
                        server_address="",
                        database=self.database,
                        logger=self.logger,
                    )

                    panelist.set_activity_instance(self.activity_instance)
                    panelist_profile = panelist.get_my_profile()
                    self.panelist_instances.append(panelist)
                    self.logger.info(f"Panelist {panelist_profile.background.name} created")

        except Exception as e:
            self.logger.error(f"Error creating panelist agents: {e}")
            raise

    def get_panelist_profiles_for_current_interview_round(self) -> List[Profile]:
        """Get panelist profiles for current interview round with caching."""
        if not hasattr(self, "_cached_panelist_profiles"):
            self._cached_panelist_profiles = [
                p.get_my_profile()
                for p in self.panelist_instances
                if p.get_my_profile().interview_round_part_of == InterviewRound.ROUND_TWO.value
            ]
        return self._cached_panelist_profiles

    async def load_activity_code_info(self) -> Optional[str]:
        """Load activity code information from Firebase."""
        try:
            code = await self.database.fetch_starter_code_from_url()
            self.logger.info(f"Code from firebase: {code}")
            return code
        except Exception as e:
            self.logger.error(f"Error loading activity code: {e}")
            return None

    def load_data_into_memory(self, json_file_path: str):
        """Load data into memory graph."""
        try:
            self.interview_topic_tracker.load_data_into_memory_graph(json_file_path)
        except Exception as e:
            self.logger.error(f"Error loading data into memory: {e}")

    def parse_response_evaluation_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        evaluation_output: QuestionSpecificEvaluationOutputMessage = (
            self.prompt_strategy.parse_response_evaluation_content(response)
        )
        return evaluation_output

    def parse_response_subquery_generation_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        subquery_data: SubqueryGeneratorOutputMessage = (
            self.prompt_strategy.parse_response_subquery_generation_content(response)
        )
        return subquery_data

    def parse_response_subquery_data_extraction_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        subquery_data: SubqueryDataExtractionOutputMessage = (
            self.prompt_strategy.parse_response_subquery_data_extraction_content(response)
        )
        return subquery_data

    def parse_response_evaluation_summary_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        summary = self.prompt_strategy.parse_response_evaluation_summary_content(response)
        return summary

    def parse_response_code_analysis_visual_summary_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        code_analysis_visual_summary: CodeAnalysisVisualSummary = (
            self.prompt_strategy.parse_response_code_analysis_visual_summary_content(response)
        )
        return code_analysis_visual_summary

    def parse_response_overall_visual_summary_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        overall_visual_summary: OverallVisualSummary = (
            self.prompt_strategy.parse_response_overall_visual_summary_content(response)
        )
        return overall_visual_summary

    def parse_response_panelist_feedback_visual_summary_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        panelist_feedback_visual_summary: PanelistFeedbackVisualSummary = (
            self.prompt_strategy.parse_response_panelist_feedback_visual_summary_content(response)
        )
        return panelist_feedback_visual_summary

    def parse_response_criteria_visual_summary_content(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        criteria_visual_summary: CriteriaScoreVisualSummary = (
            self.prompt_strategy.parse_response_criteria_visual_summary_content(response)
        )
        return criteria_visual_summary

    async def run_subquery_generator(self, topic_conversation) -> SubqueryGeneratorOutputMessage:
        """Run subquery generator with error handling."""
        try:
            self.logger.info("Running subquery generator")

            subquery_generator_message = SubqueryGeneratorInputMessage(
                candidate_profile=self.candidate_profile,
                panelists=self.get_panelist_profiles_for_current_interview_round(),
            )

            prompt_input = PromptInput(
                message=subquery_generator_message,
                conversation_history_for_current_subtopic=[],
                conversation_summary_for_current_topic=[],
                conversation_summary_for_completed_topics=[],
                last_completed_conversation_history=topic_conversation,
                candidate_profile=self.candidate_profile,
                response_type=EvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_GENERATION,
                activity_analysis=self.activity_instance.get_recent_progress()
                if self.activity_instance
                else None,
            )

            prompt = super().build_prompt(prompt_input)
            output = await super().run_subquery_generation(prompt)
            subquery_data: SubqueryGeneratorOutputMessage = output

            self.logger.info(f"Subquery data: {subquery_data}")
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "subquery_data",
                subquery_data.model_dump()
                if hasattr(subquery_data, "model_dump")
                else subquery_data,
            )

            return SubqueryGeneratorOutputMessage(subqueries=subquery_data.subqueries)

        except Exception as e:
            self.logger.error(f"Error in subquery generator: {e}")
            raise

    async def run_subquery_data_extraction(self, subqueries) -> SubqueryDataExtractionOutputMessage:
        """Run subquery data extraction with error handling."""
        try:
            self.logger.info("Running subquery data extraction")

            subquery_data_extraction_message = SubqueryDataExtractionInputMessage(
                subqueries=subqueries
            )

            prompt_input = PromptInput(
                message=subquery_data_extraction_message,
                conversation_history_for_current_subtopic=[],
                conversation_summary_for_current_topic=[],
                conversation_summary_for_completed_topics=[],
                last_completed_conversation_history=[],
                candidate_profile=self.candidate_profile,
                response_type=EvaluationPromptStrategy.RESPONSE_TYPE.SUBQUERY_DATA_EXTRACTION,
                activity_analysis=self.activity_instance.get_recent_progress()
                if self.activity_instance
                else None,
            )

            prompt = super().build_prompt(prompt_input)
            output = await super().run_subquery_data_extraction(prompt)
            subquery_data: SubqueryDataExtractionOutputMessage = output

            self.logger.info(f"Subquery data extraction: {subquery_data}")
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "subquery_data_extraction_output",
                subquery_data.model_dump()
                if hasattr(subquery_data, "model_dump")
                else subquery_data,
            )

            return subquery_data

        except Exception as e:
            self.logger.error(f"Error in subquery data extraction: {e}")
            raise

    async def run_evaluation_per_topic(self, topic_name: str) -> None:
        """Run evaluation for a specific topic with improved error handling."""
        try:
            self.logger.info(f"Running evaluation for topic: {topic_name}")

            topic_data = self.interview_topic_tracker.get_topic_data_based_on_name(
                InterviewRound.ROUND_TWO, topic_name
            )
            subtopic_names = self.interview_topic_tracker.get_all_uncompleted_subtopics(
                InterviewRound.ROUND_TWO, topic_name
            )

            if not subtopic_names or not topic_data:
                self.logger.warning(f"No subtopics or topic data found for {topic_name}")
                return

            self.logger.info(f"Subtopic names: {subtopic_names}")

            for subtopic_name in subtopic_names:
                await self._evaluate_subtopic(topic_name, subtopic_name, topic_data)

        except Exception as e:
            self.logger.error(f"Error running evaluation for topic {topic_name}: {e}")
            raise

    async def _evaluate_subtopic(self, topic_name: str, subtopic_name: str, topic_data):
        """Evaluate a specific subtopic."""
        try:
            subtopic_data = self.interview_topic_tracker.get_subtopic_data_based_on_name(
                InterviewRound.ROUND_TWO, topic_name, subtopic_name
            )

            if not subtopic_data:
                self.logger.warning(f"No subtopic data found for {subtopic_name}")
                return

            evaluation_message = EvaluationInputMessage(
                topic_data=topic_data,
                subtopic_data=subtopic_data,
                interview_round=InterviewRound.ROUND_TWO,
                candidate_profile=self.candidate_profile,
                evaluation_criteria=topic_data.evaluation_criteria,
                panelists=self.get_panelist_profiles_for_current_interview_round(),
            )

            key = self._get_evaluation_key(topic_name, subtopic_name)

            if key in self.evaluation_topic_subtopic_mapping:
                self.logger.info(f"Evaluation already exists for {key}")
                return

            topic_conversation = self._get_topic_conversation(topic_name, subtopic_name)
            if not topic_conversation:
                self.logger.info(f"No conversation found for {key}")
                return

            subqueries_data = await self._process_subqueries(topic_name, topic_conversation)
            await self._perform_evaluation(
                evaluation_message,
                topic_conversation,
                subqueries_data,
                key,
                topic_name,
                subtopic_name,
                topic_data,
                subtopic_data,
            )

        except Exception as e:
            self.logger.error(f"Error evaluating subtopic {subtopic_name}: {e}")
            raise

    def _get_evaluation_key(self, topic_name: str, subtopic_name: str) -> str:
        """Get evaluation key for topic/subtopic combination."""
        if (
            topic_name
            == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        ):
            return TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        return f"{topic_name},{subtopic_name}"

    def _get_topic_conversation(self, topic_name: str, subtopic_name: str):
        """Get conversation for topic/subtopic."""
        if (
            topic_name
            == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
        ):
            return self.interview_topic_tracker.get_conversation_history_for_topic(
                InterviewRound.ROUND_TWO, topic_name
            )
        return self.interview_topic_tracker.get_conversation_history_for_subtopic(
            InterviewRound.ROUND_TWO, topic_name, subtopic_name
        )

    async def _process_subqueries(
        self, topic_name: str, topic_conversation
    ) -> SubqueryDataExtractionOutputMessage:
        """Process subqueries for deep dive QA topic."""
        if topic_name == TOPICS_TECHNICAL_ROUND.DEEP_DIVE_QA.value:
            self.logger.info("Running subquery generator")
            subqueries = await self.run_subquery_generator(topic_conversation)
            self.logger.info(f"Subqueries: {subqueries}")
            subqueries_data = await self.run_subquery_data_extraction(subqueries)
            self.logger.info(f"Subqueries data: {subqueries_data}")
            return subqueries_data
        return SubqueryDataExtractionOutputMessage()

    async def _perform_evaluation(
        self,
        evaluation_message,
        topic_conversation,
        subqueries_data,
        key,
        topic_name,
        subtopic_name,
        topic_data,
        subtopic_data,
    ):
        """Perform the actual evaluation."""
        try:
            evaluation_message.subqueries_data = subqueries_data
            activity_analysis = (
                self.activity_instance.get_recent_progress() if self.activity_instance else None
            )

            prompt_input = PromptInput(
                message=evaluation_message,
                conversation_history_for_current_subtopic=[],
                conversation_summary_for_current_topic=[],
                conversation_summary_for_completed_topics=[],
                last_completed_conversation_history=topic_conversation,
                candidate_profile=self.candidate_profile,
                response_type=EvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION,
                activity_analysis=activity_analysis,
            )

            prompt = super().build_prompt(prompt_input)
            self.logger.info("Running evaluation prompt")
            evaluation_output: QuestionSpecificEvaluationOutputMessage = (
                await super().run_evaluation(prompt)
            )
            self.logger.info("Evaluation prompt completed")
            self.logger.info(f"Evaluation output: {evaluation_output}")

            self.last_evaluation_output = evaluation_output
            self.evaluation_topic_subtopic_mapping[key] = evaluation_output

            # Save evaluation output to file
            await self._save_evaluation_output(evaluation_output)

            # Save to database
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "evaluation_output",
                evaluation_output.model_dump()
                if hasattr(evaluation_output, "model_dump")
                else evaluation_output,
            )

            # Evaluation from panelists
            await self.evaluation_from_panelists(
                topic_name,
                subtopic_name,
                topic_data,
                subtopic_data,
                topic_conversation,
                subqueries_data,
            )

        except Exception as e:
            self.logger.error(f"Error performing evaluation: {e}")
            raise

    async def _save_evaluation_output(self, evaluation_output):
        """Save evaluation output to file with error handling."""
        try:
            evaluation_output_path = os.path.join(self.data_dir, self.EVALUATION_OUTPUT_FILE)
            os.makedirs(os.path.dirname(evaluation_output_path), exist_ok=True)

            with open(evaluation_output_path, "a") as f:
                json.dump(evaluation_output.model_dump(), f, indent=4)
                f.write("\n")
        except Exception as e:
            self.logger.error(f"Error saving evaluation output: {e}")

    async def evaluation_from_panelists(
        self,
        topic_name,
        subtopic_name,
        topic_data,
        subtopic_data,
        topic_conversation,
        subqueries_data,
    ):
        """Evaluation from panelists for the given topic/subtopic."""
        try:
            for panelist_instance in self.panelist_instances:
                await panelist_instance.evaluate(
                    topic_name,
                    subtopic_name,
                    topic_data,
                    subtopic_data,
                    topic_conversation,
                    self.candidate_profile,
                    self.get_panelist_profiles_for_current_interview_round(),
                    topic_data.evaluation_criteria,
                    subqueries_data,
                )
        except Exception as e:
            self.logger.error(f"Error evaluating panelists: {e}")

    async def generate_summary(self, text: str) -> str:
        """Generate summary with error handling."""
        try:
            prompt_input = PromptInput(
                message=text,
                response_type=BaseEvaluationPromptStrategy.RESPONSE_TYPE.EVALUATION_SUMMARY,
            )
            prompt = super().build_prompt(prompt_input)
            output = await super().generate_summary(prompt)
            return output
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Summary generation failed"

    async def merge_evaluation_output(self):
        """Merge evaluation outputs with improved error handling and performance."""
        try:
            final_evaluation_output = OldEvaluationMessage()
            final_evaluation_output.criteria_specific_scoring = []

            metrics_covered = self._get_metrics_covered()
            criteria_scoring_list, criteria_counter_list = self._initialize_criteria_scoring(
                metrics_covered
            )

            # Process evaluation outputs
            self._process_evaluation_outputs(
                criteria_scoring_list, criteria_counter_list, metrics_covered
            )

            # Calculate final scores
            overall_score, overall_analysis = self._calculate_final_scores(
                criteria_scoring_list, criteria_counter_list
            )

            overall_analysis_summary = await self.generate_summary(overall_analysis)
            final_evaluation_output.criteria_specific_scoring = criteria_scoring_list

            self.logger.info(f"Overall score: {overall_score}")
            self.logger.info(f"Overall analysis: {overall_analysis_summary}")

            return final_evaluation_output, overall_analysis_summary, overall_score

        except Exception as e:
            self.logger.error(f"Error merging evaluation output: {e}")
            raise

    def _get_metrics_covered(self) -> List[str]:
        """Get metrics covered for current interview round."""
        metrics = self.interview_topic_tracker.get_metrics_covered_for_current_interview_round(
            InterviewRound.ROUND_TWO
        )
        return [metric.lower() for metric in metrics]

    def _initialize_criteria_scoring(self, metrics_covered: List[str]):
        """Initialize criteria scoring lists."""
        criteria_scoring_list = []
        criteria_counter_list = []

        for metric in metrics_covered:
            criteria_scoring = CriteriaSpecificScoring()
            criteria_scoring.criteria = metric
            criteria_scoring.score = 0
            criteria_scoring.reason = ""
            criteria_scoring.key_phrases_from_conversation = []
            criteria_scoring_list.append(criteria_scoring)
            criteria_counter_list.append(0)

        return criteria_scoring_list, criteria_counter_list

    def _process_evaluation_outputs(
        self, criteria_scoring_list, criteria_counter_list, metrics_covered
    ):
        """Process all evaluation outputs."""
        for evaluation_output in self.evaluation_topic_subtopic_mapping.values():
            for question_criteria_scoring in evaluation_output.question_criteria_specific_scoring:
                self._process_criteria_scoring(
                    question_criteria_scoring,
                    criteria_scoring_list,
                    criteria_counter_list,
                    metrics_covered,
                )

    def _process_criteria_scoring(
        self,
        question_criteria_scoring,
        criteria_scoring_list,
        criteria_counter_list,
        metrics_covered,
    ):
        """Process individual criteria scoring."""
        current_criteria = question_criteria_scoring.criteria
        if current_criteria.lower() not in metrics_covered:
            return

        index = metrics_covered.index(current_criteria.lower())
        criteria_scoring_instance = criteria_scoring_list[index]
        question_specific_scoring_list = question_criteria_scoring.question_specific_scoring

        total_points, reason_list, counter = self._calculate_criteria_points(
            question_specific_scoring_list, current_criteria
        )

        criteria_scoring_instance.key_phrases_from_conversation.extend(
            question_criteria_scoring.key_phrases_from_conversation
        )
        criteria_scoring_instance.score += total_points
        criteria_scoring_instance.reason += "\n".join(reason_list) + "\n"
        criteria_counter_list[index] += counter

    def _calculate_criteria_points(self, question_specific_scoring_list, current_criteria):
        """Calculate points for criteria with improved question weight handling."""
        total_points = 0
        reason_list = []
        counter = 0

        for question_specific_scoring in question_specific_scoring_list:
            decision = question_specific_scoring.decision.lower()

            if decision == "na":
                continue

            if decision == "yes":
                if current_criteria.lower() == "coding":
                    question_number = question_specific_scoring.question_number
                    if question_number == 0:
                        question_number = 1

                    # Safe weight lookup
                    weight = self.QUESTION_WEIGHTS.get(question_number, 0.1)
                    total_points += weight
                else:
                    total_points += 1
            elif decision == "no":
                total_points += 0

            reason_list.append(question_specific_scoring.reason)
            counter += 1

        return total_points, reason_list, counter

    def _calculate_final_scores(self, criteria_scoring_list, criteria_counter_list):
        """Calculate final scores and overall analysis."""
        overall_score = 0
        overall_analysis = ""
        counter = 0

        for index, criteria in enumerate(criteria_scoring_list):
            if criteria_counter_list[index] > 0:
                if criteria.criteria.lower() == "coding":
                    criteria_scoring_list[index].score = 5 * round(criteria.score, 1)
                else:
                    criteria_scoring_list[index].score = 5 * round(
                        criteria.score / criteria_counter_list[index], 1
                    )

                self.logger.info(f"Criteria: {criteria.criteria}, Score: {criteria.score}")
                overall_score += criteria.score
                overall_analysis += criteria.reason + "\n"
                counter += 1

        if counter > 0:
            overall_score = round(overall_score / counter, 1)

        return overall_score, overall_analysis

    async def generate_evaluation_report(self) -> EvaluationMessageToFrontEnd:
        self.logger.info("Generating evaluation report")
        filename = self.user_id + ".jpg"
        image_url = await self.database.get_image_url(self.firebase_user_id, filename)
        self.logger.info(f"Image URL: {image_url}")
        if image_url is None:
            image_url = ""

        if self.is_interview_completed:
            self.logger.info("Interview is completed")

            # we need to send all of the transcript for the different topics to the frontend
            conversation_history = (
                self.interview_topic_tracker.get_conversation_history_for_all_topics(
                    InterviewRound.ROUND_TWO
                )
            )

            (
                merged_evaluation_output,
                overall_analysis_summary,
                overall_score,
            ) = await self.merge_evaluation_output()

            activity_code_from_candidate = (
                self.activity_instance.get_activity_code_from_candidate()
                if self.activity_instance is not None
                else ""
            )

            activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
                self.activity_instance.get_recent_progress()
                if self.activity_instance is not None
                else ActivityProgressAnalysisSummaryForPanelistOutputMessage()
            )

            evaluation_data = EvaluationMessageToFrontEnd()
            evaluation_data.transcript = conversation_history
            evaluation_data.evaluation_output = merged_evaluation_output
            evaluation_data.overall_analysis = overall_analysis_summary
            evaluation_data.overall_score = overall_score
            evaluation_data.code_from_candidate = (
                activity_code_from_candidate if activity_code_from_candidate is not None else ""
            )
            evaluation_data.activity_analysis = activity_analysis
            evaluation_data.candidate_profile_image = image_url

            evaluation_messages = []
            panelist_names = []
            for panelist_instance in self.panelist_instances:
                if (
                    panelist_instance.my_profile.interview_round_part_of
                    == InterviewRound.ROUND_TWO.value
                ):
                    overall_feedback = panelist_instance.get_overall_feedback()
                    self.logger.info(f"Overall feedback: {overall_feedback}")
                    feedback = await self.generate_summary(overall_feedback)
                    self.logger.info(f"Feedback: {feedback}")
                    panelist_names.append(panelist_instance.my_profile.background.name)
                    evaluation_messages.append(feedback)

            evaluation_data.panelist_feedback = evaluation_messages
            evaluation_data.panelist_names = panelist_names
            evaluation_data.candidate_name = (
                self.candidate_profile.background.name if self.candidate_profile is not None else ""
            )
            evaluation_data.candidate_profile = (
                self.candidate_profile.background if self.candidate_profile is not None else ""
            )
            evaluation_data.candidate_id = self.user_id

        else:
            self.logger.info("Interview is not completed")
            evaluation_data = EvaluationMessageToFrontEnd()
            evaluation_data.transcript = []
            evaluation_data.evaluation_output = OldEvaluationMessage()
            evaluation_data.overall_analysis = ""
            evaluation_data.overall_score = 0
            evaluation_data.code_from_candidate = ""
            evaluation_data.activity_analysis = (
                ActivityProgressAnalysisSummaryForPanelistOutputMessage()
            )
            evaluation_data.panelist_feedback = []
            evaluation_data.panelist_occupations = []
            evaluation_data.panelist_names = []
            evaluation_data.candidate_name = (
                self.candidate_profile.background.name if self.candidate_profile is not None else ""
            )
            evaluation_data.candidate_profile = (
                self.candidate_profile.background if self.candidate_profile is not None else ""
            )
            evaluation_data.candidate_id = self.user_id
            evaluation_data.candidate_profile_image = image_url

        self.logger.info(f"Evaluation data: {evaluation_data}")
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "final_evaluation_output",
            evaluation_data.model_dump()
            if hasattr(evaluation_data, "model_dump")
            else evaluation_data,
        )

        return evaluation_data

    async def run_code_analysis_visual_summary(
        self, code: str, progress_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage
    ):
        self.logger.info("Running code analysis visual summary")

        message = CodeSummaryVisualizationInputMessage()
        message.code = code
        message.activity_analysis = progress_analysis

        prompt_input = PromptInput(
            message=message,
            response_type=BaseEvaluationPromptStrategy.RESPONSE_TYPE.CODE_ANALYSIS_VISUAL_SUMMARY,
        )

        prompt = super().build_prompt(prompt_input)

        code_analysis_visual_summary: CodeAnalysisVisualSummary = (
            await super().generate_code_analysis_visual_summary(prompt)
        )
        return code_analysis_visual_summary

    async def run_overall_visual_summary(
        self, overall_analysis: str, overall_score: float
    ) -> OverallVisualSummary:
        self.logger.info("Running overall visual summary")

        message = OverallVisualizationInputMessage()
        message.overall_analysis = overall_analysis
        message.overall_score = overall_score

        prompt_input = PromptInput(
            message=message,
            response_type=BaseEvaluationPromptStrategy.RESPONSE_TYPE.OVERALL_VISUAL_SUMMARY,
        )

        prompt = super().build_prompt(prompt_input)

        overall_visual_summary: OverallVisualSummary = (
            await super().generate_overall_visual_summary(prompt)
        )
        return overall_visual_summary

    async def run_panelist_feedback_visual_summary(
        self,
        panelist_feedback: List[str],
        panelist_names: List[str],
        panelist_occupations: List[str],
    ):
        self.logger.info("Running panelist feedback visual summary")

        message = PanelistFeedbackVisualizationInputMessage()
        message.panelist_feedback = panelist_feedback
        message.panelist_names = panelist_names
        message.panelist_occupations = panelist_occupations

        prompt_input = PromptInput(
            message=message,
            response_type=BaseEvaluationPromptStrategy.RESPONSE_TYPE.PANELIST_FEEDBACK_VISUAL_SUMMARY,
        )

        prompt = super().build_prompt(prompt_input)

        panelist_feedback_visual_summary: PanelistFeedbackVisualSummaryList = (
            await super().generate_panelist_feedback_visual_summary(prompt)
        )
        return panelist_feedback_visual_summary

    async def run_criteria_visual_summary(
        self, criteria_specific_scoring: List[CriteriaSpecificScoring]
    ) -> CriteriaScoreVisualSummaryList:
        self.logger.info("Running criteria visual summary")

        message = CriteriaVisualizationInputMessage()
        message.criteria_score_list = criteria_specific_scoring

        prompt_input = PromptInput(
            message=message,
            response_type=BaseEvaluationPromptStrategy.RESPONSE_TYPE.CRITERIA_VISUAL_SUMMARY,
        )

        prompt = super().build_prompt(prompt_input)

        criteria_visual_summary: CriteriaScoreVisualSummaryList = (
            await super().generate_criteria_visual_summary(prompt)
        )
        return criteria_visual_summary

    async def revise_evaluation_report_for_visualization(
        self, evaluation_data: EvaluationMessageToFrontEnd
    ) -> CandidateEvaluationVisualisationReport:
        self.logger.info(
            "Revising evaluation report for visualization and converting to candidate visualization"
        )

        # we need to revise the following: overall analysis, panelist feedback and criteria specific scoring explaination. Basically all text fields
        self.logger.info(f"Evaluation data: {evaluation_data}")
        overall_analysis: str = evaluation_data.overall_analysis
        panelist_feedback: List[str] = evaluation_data.panelist_feedback
        criteria_specific_scoring_list: List[CriteriaSpecificScoring] = (
            evaluation_data.evaluation_output.criteria_specific_scoring
        )
        code_written_by_candidate: str = evaluation_data.code_from_candidate
        activity_analysis: ActivityProgressAnalysisSummaryForPanelistOutputMessage = (
            evaluation_data.activity_analysis
        )

        code_submission_visual_summary: CodeSubmissionVisualSummary = CodeSubmissionVisualSummary()
        code_submission_visual_summary.content = code_written_by_candidate
        code_submission_visual_summary.language = "Python"

        candidate_visualization_report: CandidateEvaluationVisualisationReport = (
            CandidateEvaluationVisualisationReport()
        )
        candidate_visualization_report.candidate_name = evaluation_data.candidate_name
        candidate_visualization_report.candidate_profile = evaluation_data.candidate_profile
        candidate_visualization_report.candidate_id = evaluation_data.candidate_id
        candidate_visualization_report.candidate_profile_image = (
            evaluation_data.candidate_profile_image
        )
        candidate_visualization_report.overall_score = evaluation_data.overall_score

        code_analysis_visual_summary: CodeAnalysisVisualSummary = (
            await self.run_code_analysis_visual_summary(
                code_written_by_candidate, activity_analysis
            )
        )
        self.logger.info(f"Code analysis visual summary: {code_analysis_visual_summary}")
        overall_visual_summary: OverallVisualSummary = await self.run_overall_visual_summary(
            overall_analysis, evaluation_data.overall_score
        )
        self.logger.info(f"Overall visual summary: {overall_visual_summary}")
        panelist_feedback_visual_summary: PanelistFeedbackVisualSummaryList = (
            await self.run_panelist_feedback_visual_summary(
                panelist_feedback,
                evaluation_data.panelist_names,
                evaluation_data.panelist_occupations,
            )
        )
        self.logger.info(f"Panelist feedback visual summary: {panelist_feedback_visual_summary}")
        criteria_visual_summary: CriteriaScoreVisualSummaryList = (
            await self.run_criteria_visual_summary(criteria_specific_scoring_list)
        )
        self.logger.info(f"Criteria visual summary: {criteria_visual_summary}")

        candidate_visualization_report.code_submission = code_submission_visual_summary
        candidate_visualization_report.code_analysis = code_analysis_visual_summary
        candidate_visualization_report.overall_visual_summary = overall_visual_summary
        candidate_visualization_report.panelist_feedback = (
            panelist_feedback_visual_summary.panelist_feedback
        )
        candidate_visualization_report.criteria_scores = criteria_visual_summary.criteria_score_list

        candidate_visualization_report.transcript = evaluation_data.transcript

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "final_visualisation_report",
            candidate_visualization_report.model_dump()
            if hasattr(candidate_visualization_report, "model_dump")
            else candidate_visualization_report,
        )

        return candidate_visualization_report

    # we will call the run method of the evaluation agent
    async def run(self):
        """Main run method with improved error handling and flow control."""
        try:
            await self._create_activity_agent()
            await self._create_panelist_agents()

            self.logger.info("Starting evaluation agent")

            async with self.lock:
                if self.is_interview_completed:
                    technical_topic_names = [
                        TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value,
                        TOPICS_TECHNICAL_ROUND.DEEP_DIVE_QA.value,
                    ]

                    for technical_topic_name in technical_topic_names:
                        self.logger.info(f"Running evaluation for topic: {technical_topic_name}")
                        await self.run_evaluation_per_topic(technical_topic_name)
                else:
                    self.logger.info("Interview is not completed")

                # Generate final report
                self.logger.info("Evaluation completed. Generating report")
                evaluation_report: EvaluationMessageToFrontEnd = (
                    await self.generate_evaluation_report()
                )
                report: CandidateEvaluationVisualisationReport = (
                    await self.revise_evaluation_report_for_visualization(evaluation_report)
                )

        except Exception as e:
            self.logger.error(f"Error in evaluation run: {e}")
            raise
        finally:
            self.logger.info("Evaluation completed. Exiting evaluation agent")
