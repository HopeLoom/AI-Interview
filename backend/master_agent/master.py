"""
This is the master agent responsible for running the simulation.
Master agent has to launch multiple agents including panelists, actvity while also performing tasks needed for interview.
"""

import asyncio
import contextlib
import datetime
import json
import random
from asyncio import Queue
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, cast

from candidate_agent.configurator import create_candidate_instance
from interview_details_agent.base import (
    ActivityDetailsOutputMessage,
    CharacterDataOutput,
    InterviewTopicData,
    SubTopicData,
)
from panelist_factory.configurators import create_panelist_instance

from activity_agent.activity import Activity
from activity_agent.base import BaseActivityConfiguration
from activity_agent.configurators import create_activity_instance
from core.config.config_manager import get_config
from core.database.base import DatabaseInterface
from core.image_generator.generator import Text2ImageConfig, TextToImageProvider
from core.prompting.prompt_strategies.master_one_shot import MasterPromptStrategy
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelProvider,
    ChatModelResponse,
    MasterChatMessage,
)
from core.speech.base import SpeechConfig
from core.speech.speech_services_provider import SpeechServiceProvider
from master_agent.base import (
    SUBTOPICS_TECHNICAL_ROUND,
    TOPICS_TECHNICAL_ROUND,
    ActivityDataToClient,
    BaseInterviewConfiguration,
    BaseMaster,
    BaseMasterConfiguration,
    CommunicationMessage,
    ConversationalAdviceInputMessage,
    ConversationalAdviceOutputMessage,
    InstructionDataToClient,
    InterviewDetails,
    InterviewEndDataToClient,
    InterviewMessageDataToClient,
    InterviewRound,
    InterviewStartDataToClient,
    MasterMessageStructure,
    NextSpeakerInfoToClient,
    PanelData,
    PromptInput,
    RulesAndRegulationsOutputMessage,
    SimulationIntroductionInputMessage,
    SimulationIntroductionOutputMessage,
    SimulationRole,
    SlaveMessageStructure,
    SpeakerDeterminationInputMessage,
    SpeakerDeterminationOutputMessage,
    SystemMessageStructure,
    SystemMessageType,
    TopicSectionCompletionInputMessage,
    TopicSectionCompletionOutputMessage,
    WebSocketMessageFromClient,
    WebSocketMessageToClient,
    WebSocketMessageTypeFromClient,
    WebSocketMessageTypeToClient,
)
from master_agent.interview_topic_tracker import InterviewTopicTracker
from panelist_agent.base import Profile
from panelist_agent.panelist import Panelist


# when creating a new agent, we need to pass the settings and llm_provider
class Master(BaseMaster):
    config: BaseMasterConfiguration = BaseMasterConfiguration(
        description="Master configuration", name="Master"
    )

    def __init__(
        self,
        user_id: str,
        firebase_user_id: str,
        session_id: str,
        config: BaseMasterConfiguration,
        candidate_name: str,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        grok_provider: ChatModelProvider,
        deepseek_provider: ChatModelProvider,
        database: DatabaseInterface,
        logger: Any,
        data_dir: str,
    ):
        # prompt strategy is used to build prompt and parse response content
        self.prompt_strategy = MasterPromptStrategy(config, database)
        self.config = config

        # this calls the __init__ method of the base agent
        super().__init__(
            master_config=config,
            llm_provider=llm_provider,
            gemini_provider=gemini_provider,
            groq_provider=groq_provider,
            grok_provider=grok_provider,
            deepseek_provider=deepseek_provider,
            prompt_strategy=self.prompt_strategy,
        )

        self.receiving_message_queue = asyncio.Queue()
        self.logger = logger
        self.user_id = user_id
        self.session_id = session_id
        self.firebase_user_id = firebase_user_id
        self.data_dir = data_dir + f"{self.user_id}/"
        self.logger.info(f"Data directory: {self.data_dir}")
        self.interview_start_time = datetime.now(timezone.utc)
        self.database: DatabaseInterface = database
        self.database.set_logger(self.logger)
        self.candidate_name = candidate_name

        # Load configuration
        self.config = get_config()

        # important variables
        self.llm_provider = llm_provider
        self.interview_data: BaseInterviewConfiguration = config.interview_data

        self.interview_topic_tracker = InterviewTopicTracker(interview_data=self.interview_data)
        self.interview_topic_tracker.load_interview_configuration(self.logger)

        # instances part of the interview
        self.panelist_instances: list[Panelist] = []
        self.panelist_tasks: list[asyncio.Task] = []
        self.panelist_data_for_frontend: list[PanelData] = []
        self.activity_instance: Optional[Activity] = None
        self.websocket_connection_manager = None
        self.simulation_introduction_output_message: SimulationIntroductionOutputMessage = (
            SimulationIntroductionOutputMessage()
        )
        self.media_dir = "static/" + self.user_id

        # voice configuration
        self.master_voice_gender: str = "male"
        self.selected_voice_ids: list = []
        self._set_image_config()
        self.speech_service_provider = SpeechServiceProvider(
            config=SpeechConfig(
                provider="eleven_labs",
                speak_mode=True,
                api_key=self.config.speech.elevenlabs_api_key or "",
            ),
            main_logger=self.logger,
        )
        self._set_tts_config()

        # conversation summary variables
        self.token_counter: int = 0
        self.warning_token_threshold: int = 3000

        # interview round variables
        self.current_interview_round = InterviewRound.ROUND_TWO
        self.is_interview_round_changed = False
        self.current_topic_data: InterviewTopicData = InterviewTopicData()
        self.current_subtopic_data: SubTopicData = SubTopicData()
        self.current_section_data: str = ""
        self.topic_completion_output_message: TopicSectionCompletionOutputMessage = (
            TopicSectionCompletionOutputMessage()
        )
        self.speaker_determination_output_message: SpeakerDeterminationOutputMessage = (
            SpeakerDeterminationOutputMessage()
        )
        self.conversational_advice_output_message: ConversationalAdviceOutputMessage = (
            ConversationalAdviceOutputMessage()
        )
        self.topic_just_got_completed = False
        self.last_speaker = ""
        # frontend message variables
        self.messages_from_frontend = asyncio.Queue()
        self.candidate_state_tracker = None
        self.waiting_for_response_from_candidate = False
        self.waiting_for_response_from_panelist = False
        self.is_audio_playback_completed = True
        self.is_interview_completed = False
        # tasks
        self.processing_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()

        # server address and port number
        self.port_number = self.config.port
        self.address = self.config.address

        self.server_media_address = (
            f"http://{self.address}:{self.port_number}/static/{self.user_id}"
        )
        self.logger.info(f"Server media address: {self.server_media_address}")

        # check if files are present. if yes, then delete them
        self.cleanup_files()

        self._cached_panelist_profiles = None

        self.logger.info("Master agent created")

        # data = self.firebase_database.get_json_data_output_from_database(self.firebase_user_id, session_id, "memory_graph.json")
        # self.logger.info(f"Data from firebase: {data}")

    def cleanup_files(self):
        data_path = Path(self.data_dir)
        for file_pattern in [
            "_speaker_determination.json",
            "_topic_section_completion.json",
            "_rules_and_regulations.json",
            "_conversational_advice.json",
        ]:
            for file in data_path.glob(file_pattern):
                file.unlink(missing_ok=True)

    def prepare_interview_details_data(self) -> InterviewDetails:
        interview_details_data = InterviewDetails()
        job_details = self.master_config.interview_data.job_details
        interview_details_data.candidate_name = self.candidate_name
        interview_details_data.role = job_details.job_title
        interview_details_data.company = job_details.company_name
        interview_details_data.duration = 30
        interview_details_data.interviewType = InterviewRound.ROUND_TWO.value
        interview_details_data.expectations = [
            "Introduction",
            "Coding Challenge",
            "Technical Discussion",
        ]
        return interview_details_data

    def load_data_into_memory(self, json_file_path: str):
        self.interview_topic_tracker.load_data_into_memory_graph(json_file_path)
        self.logger.info(f"Data loaded into memory from {json_file_path}")

    # used to get the voice id for eleven labs to assign voice to a particular character
    def _get_voice_name(self, gender):
        location = self.database.user_data.location

        if location.lower() == "india":
            male_options = self.speech_service_provider.get_available_voices(
                provider="eleven_labs", gender="male", region="india"
            )
            female_options = self.speech_service_provider.get_available_voices(
                provider="eleven_labs", gender="female", region="india"
            )
        else:
            male_options = self.speech_service_provider.get_available_voices(
                provider="eleven_labs", gender="male", region="us"
            )
            female_options = self.speech_service_provider.get_available_voices(
                provider="eleven_labs", gender="female", region="us"
            )

        if gender.lower() == "male":
            voice_index = random.randint(0, len(male_options) - 1)
            voice_name = male_options[voice_index]
        else:
            voice_index = random.randint(0, len(female_options) - 1)
            voice_name = female_options[voice_index]

        return voice_name

    # get npc profiles list
    def get_all_panelist_profiles(self):
        profiles = []
        for panelist in self.panelist_instances:
            profiles.append(panelist.get_my_profile())
        return profiles

    # get user profile
    def get_candidate_profile(self):
        return self.candidate_instance.get_candidate_profile()

    # get profile given the name
    def _get_profile_from_name(self, name):
        for panelist in self.panelist_instances:
            if panelist.get_my_profile().background.name.lower() in name.lower():
                return panelist.get_my_profile()

        if self.candidate_instance.get_candidate_profile().background.name.lower() in name.lower():
            return self.candidate_instance.get_candidate_profile()

        return None

    @lru_cache(maxsize=128)
    def get_panelist_profiles_for_current_interview_round(self):
        if self._cached_panelist_profiles is None:
            profiles = []
            for panelist in self.panelist_instances:
                if (
                    panelist.get_my_profile().interview_round_part_of
                    == self.current_interview_round
                ):
                    profiles.append(panelist.get_my_profile())
            self._cached_panelist_profiles = profiles
        return self._cached_panelist_profiles

    def get_panelist_thoughts(self):
        panelist_thoughts_name_mapping = {}

        for panelist in self.panelist_instances:
            if panelist.get_my_profile().interview_round_part_of == self.current_interview_round:
                panelist_thoughts_name_mapping[panelist.get_my_profile().background.name] = (
                    panelist.get_reasoning_history()
                )

        return panelist_thoughts_name_mapping

    def set_panelist_data_for_frontend(
        self, simulation_introduction_output_message: SimulationIntroductionOutputMessage
    ):
        panelist_data = simulation_introduction_output_message.panelists
        self.panelist_data_for_frontend = panelist_data
        self.simulation_introduction_output_message = simulation_introduction_output_message

    def convert_candidate_profile_to_participant_data(self):
        candidate_profile = self.get_candidate_profile()
        panel_data = PanelData()
        panel_data.name = candidate_profile.background.name
        panel_data.id = candidate_profile.character_id
        panel_data.intro = candidate_profile.background.bio
        panel_data.interview_round_part_of = self.current_interview_round
        panel_data.avatar = ""
        panel_data.isAI = False
        panel_data.isActive = False
        panel_data.connectionStatus = "connected"
        return panel_data

    def get_participants_data_for_frontend_for_current_interview_round(self):
        participant_data = []
        for panel in self.panelist_data_for_frontend:
            if panel.interview_round_part_of == self.current_interview_round:
                participant_data.append(panel)
        candidate_data = self.convert_candidate_profile_to_participant_data()
        participant_data.append(candidate_data)
        return participant_data

    # function to send message to frontend
    async def _send_message_to_frontend(self, message: Any, message_type=None):
        # convert the message in json format to text and then send it to the frontend. Ensure user id is included
        if self.websocket_connection_manager is None:
            self.logger.warning(
                "Websocket connection manager is not set. Cannot send message to frontend."
            )
            return

        websocket_message_to_client = WebSocketMessageToClient(
            message_type=message_type if message_type is not None else "",
            message=message,
            id=self.user_id,
        )

        await self.websocket_connection_manager.broadcast(
            websocket_message_to_client.model_dump_json()
        )

    # this sets the tts configuration for the master instance. not sure, if we need this
    def _set_tts_config(self):
        while True:
            voice_id = self._get_voice_name(self.master_voice_gender)
            if voice_id not in self.selected_voice_ids:
                self.selected_voice_ids.append(voice_id)
                break

        master_tts_config = SpeechConfig()
        master_tts_config.provider = "eleven_labs"
        master_tts_config.api_key = self.config.speech.elevenlabs_api_key or ""
        master_tts_config.voice_id = voice_id
        master_tts_config.speak_mode = True
        master_tts_config.data_dir = self.media_dir + "/audio/"
        self.tts_config = master_tts_config

    def _set_image_config(self):
        image_config = Text2ImageConfig()
        image_config.provider = "openai"
        # Get OpenAI provider config
        openai_provider = next(
            (p for p in self.config.llm_providers if p.name.lower() == "openai"), None
        )
        image_config.api_key = openai_provider.api_key if openai_provider else ""
        image_config.data_dir = self.media_dir + "/images/"

        self.image_provider = TextToImageProvider(image_config)

    # get the time remaining for the topic
    def get_topic_time_remaining(self):
        current_time = datetime.now(timezone.utc)
        time_since_topic_start_mins = (current_time - self.topic_start_time).total_seconds() / 60
        current_topic_time_limit = self.current_subtopic_data.time_limit
        time_remaining = current_topic_time_limit - time_since_topic_start_mins
        self.logger.info(f"Time remaining for topic in mins: {time_remaining}")
        self.logger.info(f"Time since topic start in mins: {time_since_topic_start_mins}")
        return time_remaining

    # function to send user input to user instance.User instance just keeps track of user responses. not doing anything else.
    def _send_user_input_to_candidate_agent(self, user_input):
        self.candidate_instance.update_candidate_input_list(user_input)

    # creating user instance. not needed for now but still doing it.
    async def _create_candidate_agent(self):
        sending_message_queue = asyncio.Queue()
        self.candidate_instance = await create_candidate_instance(
            llm_provider=self.llm_provider,
            resume_data=None,
            receiving_message_queue=sending_message_queue,
            sending_message_queue=self.receiving_message_queue,
            data_dir=self.data_dir,
            user_id=self.user_id,
            database=self.database,
        )
        # create task to run the candidate instance. we don't await since we want to run it in the background
        self.candidate_instance_task = asyncio.create_task(self.candidate_instance.run())

    # Creating npc instances for each of the character data present in the interview config file. We are generating profile and then creating npc instance
    async def _create_panelist_agents(self):
        # get the character data list
        self.logger.info("Creating panelist agents")
        character_data_output: CharacterDataOutput = self.interview_data.character_data
        character_data_list = character_data_output.data
        # create npc instance for each character data
        for character_data in character_data_list:
            self.logger.info(f"Creating panelist for {character_data.character_name}")
            sending_message_queue = Queue()
            # sending message queue for npc will be receiving message queue for simulation
            # receiving message queue for npc will be sending message queue for simulation
            panelist: Panelist = await create_panelist_instance(
                interview_config=self.config.interview_data,
                llm_provider=self.llm_provider,
                gemini_provider=self.gemini_provider,
                groq_provider=self.groq_provider,
                grok_provider=self.grok_provider,
                deepseek_provider=self.deepseek_provider,
                character_data=character_data,
                sending_message_queue=self.receiving_message_queue,
                receiving_message_queue=sending_message_queue,
                data_dir=self.data_dir,
                user_id=self.user_id,
                firebase_user_id=self.firebase_user_id,
                session_id=self.session_id,
                server_address=self.server_media_address,
                database=self.database,
                logger=self.logger,
            )

            panelist_profile = panelist.get_my_profile()
            gender = panelist_profile.background.gender
            # Select voice for each character
            while True:
                voice_id = self._get_voice_name(gender)
                if voice_id not in self.selected_voice_ids:
                    self.selected_voice_ids.append(voice_id)
                    break

            tts_config = SpeechConfig()
            tts_config.provider = "eleven_labs"
            tts_config.api_key = self.config.speech.elevenlabs_api_key or ""
            tts_config.voice_id = voice_id
            tts_config.speak_mode = True
            tts_config.data_dir = self.media_dir + "/audio/"

            panelist.set_tts_config(tts_config)
            panelist.set_master_instance(self)
            # add panelist instance to a list
            self.panelist_instances.append(panelist)
            panelist.set_activity_instance(self.activity_instance)
            # create task to run the panelist instance. we don't await since we want to run it in the background
            self.panelist_task = asyncio.create_task(panelist.run())
            self.panelist_tasks.append(self.panelist_task)
            self.logger.info(
                f"Panelist {panelist_profile.background.name} created with voice id {voice_id}"
            )

    # create activity instance which is mainly responsible for monitoring the activity of the user in round 2
    async def _create_activity_agent(self):
        # create activity configuration
        sending_message_activity_queue = asyncio.Queue()

        activity_configuration: BaseActivityConfiguration = BaseActivityConfiguration(
            name="Activity",
            description="Activity",
            activity_code_file_path=self.config.interview_data.activity_code_path,
            activity_details=self.config.interview_data.activity_details,
        )
        activity_configuration.activity_info_file_path = (
            self.config.interview_data.activity_raw_data_path
        )

        # create activity instance with sending message queue as receiving message queue for simulation and vice versa
        self.activity_instance = await create_activity_instance(
            llm_provider=self.llm_provider,
            gemini_provider=self.gemini_provider,
            groq_provider=self.groq_provider,
            user_id=self.user_id,
            firebase_user_id=self.firebase_user_id,
            session_id=self.session_id,
            config=activity_configuration,
            interview_config=self.config.interview_data,
            database=self.database,
            receiving_message_queue=sending_message_activity_queue,
            sending_message_queue=self.receiving_message_queue,
            logger=self.logger,
        )

        self.activity_instance.set_master_instance(self)
        # create task to run the activity instance. we don't await since we want to run it in the background
        self.activity_task = asyncio.create_task(self.activity_instance.run())

    # this is used to add the connection manager reference
    def add_connection_manager_reference(self, manager):
        self.websocket_connection_manager = manager

    # this is triggered from the frontend when message is sent to the backend
    def message_from_frontend(self, message: WebSocketMessageFromClient):
        self.logger.info(f"Message from frontend: {message.message_type}")
        self.messages_from_frontend.put_nowait(message)

    # this is triggered when we want to send message to other agents
    def send_command(self, command: CommunicationMessage):
        self.logger.info("Command sent to other agents")
        for panelist_instance in self.panelist_instances:
            panelist_instance.get_receiving_message_queue().put_nowait(command)

    def send_command_to_activity(self, command: CommunicationMessage):
        self.logger.info("Command sent to activity")
        if self.activity_instance is None:
            self.logger.error("Activity instance is not set. Cannot send command to activity.")
            return

        self.activity_instance.get_receiving_message_queue().put_nowait(command)

    def parse_and_process_response_introduction(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        output: SimulationIntroductionOutputMessage = (
            self.prompt_strategy.parse_response_introduction_content(response)
        )
        return output

    def parse_and_process_response_summarized_conversation(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        summary = self.prompt_strategy.parse_response_summarized_conversation_content(response)
        return summary

    def parse_and_process_response_conversational_advice(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        advice_message: ConversationalAdviceOutputMessage = (
            self.prompt_strategy.parse_response_advice_content(response)
        )
        return advice_message

    def parse_and_process_response_rules_regulation(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        rules_and_regulations_message: RulesAndRegulationsOutputMessage = (
            self.prompt_strategy.parse_rules_and_regulation_content(response)
        )
        return rules_and_regulations_message

    def parse_and_process_response_speaker_determination(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        speaker_message: SpeakerDeterminationOutputMessage = (
            self.prompt_strategy.parse_response_speaker_determination_content(response)
        )
        return speaker_message

    def parse_and_process_response_topic_completion(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        topic_completion: TopicSectionCompletionOutputMessage = (
            self.prompt_strategy.parse_topic_section_completion_content(response)
        )
        return topic_completion

    def parse_and_process_summary_model(self, response: AssistantChatMessage, prompt: ChatMessage):
        summary = self.prompt_strategy.parse_summary_content(response)
        return summary

    def convert_saved_conversation_to_list(self, conversation_history: list[MasterChatMessage]):
        conversation_history_strings = [
            f"Speaker:{message.speaker}, dialog:{message.content}"
            for message in conversation_history
        ]
        return conversation_history_strings

    def get_candidate_name(self):
        return self.get_candidate_profile().background.name

    def get_conversation_data(self, topic_name, subtopic_name):
        # conversation history will be for the current subtopic that is being discussed
        conversation_history_for_current_subtopic = (
            self.interview_topic_tracker.get_conversation_history_for_subtopic(
                self.current_interview_round, topic_name, subtopic_name
            )
        )

        if conversation_history_for_current_subtopic is None:
            self.logger.info(
                f"Conversation history is None for topic: {topic_name} and subtopic: {subtopic_name}"
            )
            conversation_history_for_current_subtopic = []

        last_completed_subtopic = self.interview_topic_tracker.get_last_completed_subtopic_name(
            self.current_interview_round, topic_name
        )

        if last_completed_subtopic is not None:
            last_completed_conversation_history = (
                self.interview_topic_tracker.get_conversation_history_for_subtopic(
                    self.current_interview_round, topic_name, last_completed_subtopic
                )
            )
            if last_completed_conversation_history is None:
                self.logger.info(
                    f"Last completed conversation history is None for topic: {topic_name} and subtopic: {last_completed_subtopic}"
                )
                last_completed_conversation_history = []

        elif last_completed_subtopic is None:
            last_completed_topic = self.interview_topic_tracker.get_last_completed_topic_name(
                self.current_interview_round
            )
            if last_completed_topic is not None:
                last_completed_conversation_history = (
                    self.interview_topic_tracker.get_conversation_history_for_topic(
                        self.current_interview_round, last_completed_topic
                    )
                )
            else:
                last_completed_conversation_history = []
        else:
            last_completed_conversation_history = []

        conversation_summary_for_current_topic = self.interview_topic_tracker.get_topic_summary(
            self.current_interview_round, topic_name
        )

        if conversation_summary_for_current_topic is None:
            self.logger.info(f"Conversation summary is None for topic: {topic_name}")
            conversation_summary_for_current_topic = []

        conversation_summary_for_completed_topics = (
            self.interview_topic_tracker.get_topic_summary_of_all_completed_topics(
                self.current_interview_round
            )
        )

        if conversation_summary_for_completed_topics is None:
            self.logger.info("Conversation summary is None for completed topics")
            conversation_summary_for_completed_topics = []

        return (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        )

    # this will generate conversation summary after token limit is exceeded or when subtopic is completed
    async def generate_subtopic_summary(self):
        self.logger.info("Generating subtopic summary")
        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name

        (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        ) = self.get_conversation_data(topic_name, subtopic_name)

        prompt_input = PromptInput(
            conversation_history_for_current_subtopic=conversation_history_for_current_subtopic,
            conversation_summary_for_current_topic=conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics=conversation_summary_for_completed_topics,
            last_completed_conversation_history=last_completed_conversation_history,
            candidate_profile=self.get_candidate_profile(),
            response_type=MasterPromptStrategy.RESPONSE_TYPE.SUBTOPIC_SUMMARY,
        )

        prompt = super().build_prompt(prompt_input)

        output: ChatModelResponse = await super().run_subtopic_summarizer(prompt)
        summary = output.parsed_response
        self.logger.info(f"Summary generated: {summary}")
        # message_strings = [f"{msg['speaker']}: {msg['content']}" for msg in summary]
        self.interview_topic_tracker.add_subtopic_summary_to_memory(
            self.current_interview_round, topic_name, subtopic_name, [summary]
        )
        self.logger.info("Subtopic summary added to memory")
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            f"subtopic_summary_{topic_name}_{subtopic_name}",
            {
                "interview_round": self.current_interview_round.value,
                "topic": topic_name,
                "subtopic": subtopic_name,
                "summary": summary,
            },
        )

        # if (topic_name == TOPICS_TECHNICAL_ROUND.PROBLEM_SOLVING):
        #    self.interview_topic_tracker.add_topic_summary_to_memory(self.current_interview_round, topic_name, [summary])
        #    self.firebase_database.add_topic_summary_to_database(self.current_interview_round, topic_name, summary)

    # this generates the introduction and instructions for the user before the simulation begins.
    async def generate_introduction(self) -> SimulationIntroductionOutputMessage:
        self.logger.info("Generating introduction")
        simulation_introduction_message = SimulationIntroductionInputMessage(
            panelists=self.get_panelist_profiles_for_current_interview_round()
        )

        prompt_input = PromptInput(
            message=simulation_introduction_message,
            candidate_profile=self.get_candidate_profile(),
            response_type=MasterPromptStrategy.RESPONSE_TYPE.INTRO,
        )

        prompt = super().build_prompt(prompt_input)

        json_schema = SimulationIntroductionOutputMessage.model_json_schema()
        self.logger.info(f"Json schema: {json_schema}")
        output: ChatModelResponse = await super().generate_introduction(prompt)
        intro: SimulationIntroductionOutputMessage = output.parsed_response

        for index, panelist in enumerate(intro.panelists):
            # text_prompt = (f"Generate image for an interviewer with age :{panelist.background.age}, gender: {panelist.background.gender} and bio {panelist.background.bio}. Ensure its a formal headshot of the person. Only generate face of the person with no other objects")
            filename = panelist.name + ".png"
            image_url = await self.database.get_image_url_from_name(filename)
            if image_url is None:
                # image_path = await self.image_provider.generate_image(text_prompt, filename)
                # print ("Image path:", image_path)
                self.logger.info(f"Image url not found for {filename}")
                # default image url
                image_url = ""
                # image_url = self.firebase_database.upload_image_to_firebase(image_path, filename)

            intro.panelists[index].avatar = image_url

        self.set_panelist_data_for_frontend(intro)
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "introduction_output",
            intro.model_dump() if hasattr(intro, "model_dump") else intro,
        )
        return intro

    # during interview, we need to determine who will be the next speaker
    async def speaker_determination(self) -> SpeakerDeterminationOutputMessage:
        self.logger.info("Determining speaker")
        panelist_profiles = self.get_panelist_profiles_for_current_interview_round()

        speaker_determination_message = SpeakerDeterminationInputMessage(
            panelists=panelist_profiles,
            candidate_profile=self.get_candidate_profile(),
            current_topic=self.current_topic_data,
            current_subtopic=self.current_subtopic_data,
            current_section=self.current_section_data,
            interview_round=self.current_interview_round,
            topic_completion_message=self.topic_completion_output_message,
            topic_just_got_completed=self.topic_just_got_completed,
            last_speaker=self.last_speaker,
        )
        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name

        (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        ) = self.get_conversation_data(topic_name, subtopic_name)

        topic_time_remaining = self.get_topic_time_remaining()

        prompt_input = PromptInput(
            topic_time_remaining=topic_time_remaining,
            message=speaker_determination_message,
            conversation_history_for_current_subtopic=conversation_history_for_current_subtopic,
            conversation_summary_for_current_topic=conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics=conversation_summary_for_completed_topics,
            last_completed_conversation_history=last_completed_conversation_history,
            candidate_profile=self.get_candidate_profile(),
            response_type=MasterPromptStrategy.RESPONSE_TYPE.SPEAKER_DETERMINATION,
        )

        prompt = super().build_prompt(prompt_input)

        output: ChatModelResponse = await super().generate_speaker_determination_information(prompt)
        speaker_data: SpeakerDeterminationOutputMessage = output.parsed_response
        self.logger.info(f"Speaker determination output: {speaker_data}")
        # if speaker was not identified, then switch to the candidate
        if speaker_data.next_speaker == "":
            speaker_data.next_speaker = self.get_candidate_profile().background.name

        with open(self.data_dir + "_speaker_determination.json", "a") as f:
            json.dump(speaker_data.model_dump(), f, indent=4)
            f.write("\n")

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "speaker_determination_output",
            {
                "next_speaker": speaker_data.next_speaker,
                "reason": speaker_data.reason_for_selecting_next_speaker,
            }
            if hasattr(speaker_data, "next_speaker")
            else speaker_data.model_dump(),
        )

        return speaker_data

    # this will check for subtopic completion for every topic in the interview round
    async def check_section_topic_completion(self) -> TopicSectionCompletionOutputMessage:
        self.logger.info("Checking topic completion")
        topic_completion_message = TopicSectionCompletionInputMessage(
            topic_data=self.current_topic_data,
            subtopic_data=self.current_subtopic_data,
            interview_round=self.current_interview_round,
            candidate_profile=self.get_candidate_profile(),
            panelists=self.get_panelist_profiles_for_current_interview_round(),
            section=self.current_section_data,
            topic_just_got_completed=self.topic_just_got_completed,
        )

        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name

        (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        ) = self.get_conversation_data(topic_name, subtopic_name)
        topic_time_remaining = self.get_topic_time_remaining()

        remaining_subtopics = self.interview_topic_tracker.get_all_uncompleted_subtopics(
            self.current_interview_round, topic_name
        )
        if remaining_subtopics is None:
            remaining_subtopics = []

        self.logger.info(f"Remaining subtopics: {remaining_subtopics}")

        prompt_input = PromptInput(
            remaining_subtopics=remaining_subtopics,
            topic_time_remaining=topic_time_remaining,
            message=topic_completion_message,
            conversation_history_for_current_subtopic=conversation_history_for_current_subtopic,
            conversation_summary_for_current_topic=conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics=conversation_summary_for_completed_topics,
            last_completed_conversation_history=last_completed_conversation_history,
            candidate_profile=self.get_candidate_profile(),
            response_type=MasterPromptStrategy.RESPONSE_TYPE.TOPIC_SECTION_COMPLETION,
        )

        prompt = super().build_prompt(prompt_input)

        output: ChatModelResponse = await super().generate_topic_completion(prompt)
        topic_section_completion: TopicSectionCompletionOutputMessage = output.parsed_response

        self.logger.info(f"Topic section completion: {topic_section_completion}")
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "topic_section_completion_output",
            {
                "topic": topic_name,
                "decision": topic_section_completion.decision,
                "reason": topic_section_completion.reason,
            }
            if hasattr(topic_section_completion, "decision")
            else topic_section_completion.model_dump(),
        )

        with open(self.data_dir + "_topic_section_completion.json", "a") as f:
            json.dump(topic_section_completion.model_dump(), f, indent=4)
            f.write("\n")

        if topic_section_completion.decision == "YES":
            self.logger.info("Topic Section completed")

            self.interview_topic_tracker.update_topic_completion_status(
                self.current_interview_round, topic_name, subtopic_name, self.current_section_data
            )  # move to next topic
            self.topic_just_got_completed = True

            if self.interview_topic_tracker.is_topic_completed(
                self.current_interview_round, topic_name
            ):
                self.logger.info("Topic completed")

            if self.interview_topic_tracker.is_subtopic_completed(
                self.current_interview_round, topic_name, subtopic_name
            ):
                self.logger.info("Subtopic completed")
                await self.generate_subtopic_summary()  # generate conversation summary
                self.topic_start_time = datetime.now(
                    timezone.utc
                )  # update the topic start time since a new topic has started

        else:
            self.topic_just_got_completed = False
            self.logger.info("Topic Section not completed")

        return topic_section_completion

    # generate advice for the next speaker before they speak. Not sure if we need this
    async def get_conversational_advice(
        self, next_speaker: str
    ) -> ConversationalAdviceOutputMessage:
        self.logger.info("Generating conversational advice")

        speaker_profile = self._get_profile_from_name(next_speaker)
        conversational_advice_message = ConversationalAdviceInputMessage(
            next_speaker=speaker_profile if speaker_profile is not None else Profile(),
            topic_data=self.current_topic_data,
            subtopic_data=self.current_subtopic_data,
            section=self.current_section_data if self.current_section_data is not None else "",
            interview_round=self.current_interview_round,
            topic_just_got_completed=self.topic_just_got_completed,
            speaker_determination_output=self.speaker_determination_output_message,
            topic_completion_output=self.topic_completion_output_message,
        )
        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name
        # conversation history will be for the current subtopic that is being discussed
        (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        ) = self.get_conversation_data(topic_name, subtopic_name)

        topic_time_remaining = self.get_topic_time_remaining()

        remaining_subtopics = self.interview_topic_tracker.get_all_uncompleted_subtopics(
            self.current_interview_round, topic_name
        )
        if remaining_subtopics is None:
            remaining_subtopics = []

        prompt_input = PromptInput(
            remaining_subtopics=remaining_subtopics,
            topic_time_remaining=topic_time_remaining,
            message=conversational_advice_message,
            conversation_history_for_current_subtopic=conversation_history_for_current_subtopic,
            conversation_summary_for_current_topic=conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics=conversation_summary_for_completed_topics,
            last_completed_conversation_history=last_completed_conversation_history,
            candidate_profile=self.get_candidate_profile(),
            response_type=MasterPromptStrategy.RESPONSE_TYPE.CONVERSATIONAL_ADVICE,
        )

        prompt = super().build_prompt(prompt_input)

        output: ChatModelResponse = await super().generate_conversational_advice(prompt)

        conversational_advice: ConversationalAdviceOutputMessage = output.parsed_response

        # if its time to wrap up the last topic of the interview, then end the interview
        if topic_name == SUBTOPICS_TECHNICAL_ROUND.BROADER_EXPERTISE_ASSESMENT.value:
            if conversational_advice.should_wrap_up_current_topic:
                conversational_advice.should_end_the_interview = True

        self.conversational_advice_output_message = conversational_advice
        with open(self.data_dir + "_conversational_advice.json", "a") as f:
            json.dump(conversational_advice.model_dump(), f, indent=4)
            f.write("\n")

        self.logger.info(f"Conversational advice generated: {conversational_advice}")
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            "conversational_advice_output",
            {
                "advice_for_speaker": conversational_advice.advice_for_speaker,
                "should_wrap_up_current_topic": conversational_advice.should_wrap_up_current_topic,
            }
            if hasattr(conversational_advice, "advice_for_speaker")
            else conversational_advice.model_dump(),
        )

        return conversational_advice

    # prepare and send message to panelist
    def prepare_and_send_message(
        self, speaker: str, activity_code_from_candidate="", receiver=SimulationRole.PANELIST
    ):
        speaker_profile = self._get_profile_from_name(speaker)
        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name

        remaining_subtopics_names = self.interview_topic_tracker.get_all_uncompleted_subtopics(
            self.current_interview_round, topic_name
        )

        if remaining_subtopics_names is None:
            remaining_subtopics_names = []

        remaining_time = self.get_topic_time_remaining()

        (
            conversation_history_for_current_subtopic,
            last_completed_conversation_history,
            conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics,
        ) = self.get_conversation_data(topic_name, subtopic_name)

        panelist_thought_mapping = self.get_panelist_thoughts()

        message = MasterMessageStructure(
            speaker=speaker_profile,
            conversation_history_for_current_subtopic=conversation_history_for_current_subtopic,
            conversation_summary_for_current_topic=conversation_summary_for_current_topic,
            conversation_summary_for_completed_topics=conversation_summary_for_completed_topics,
            last_completed_conversation_history=last_completed_conversation_history,
            candidate_profile=self.get_candidate_profile(),
            panelist_profiles=self.get_panelist_profiles_for_current_interview_round(),
            topic=self.current_topic_data,
            sub_topic=self.current_subtopic_data,
            current_interview_round=self.current_interview_round,
            evaluation_criteria=self.interview_topic_tracker.get_metrics_covered_for_current_interview_round(
                self.current_interview_round
            ),
            activity_code_from_candidate=activity_code_from_candidate,
            current_section=self.current_section_data
            if self.current_section_data is not None
            else "",
            remaining_topics=remaining_subtopics_names,
            remaining_time=remaining_time,
            topic_completion_message=self.topic_completion_output_message,
            speaker_determination_message=self.speaker_determination_output_message,
            advice=self.conversational_advice_output_message,
            panelist_thoughts=panelist_thought_mapping,
        )

        # package this message into a communication message and send it to the speaker
        self.logger.info(f"Sending message to {receiver}")
        communication_message = CommunicationMessage.message_to_slave(
            sender=SimulationRole.MASTER, receiver=receiver, content=message
        )
        if receiver == SimulationRole.PANELIST:
            self.waiting_for_response_from_panelist = True
            self.send_command(communication_message)

        elif receiver == SimulationRole.ACTIVITY:
            self.send_command_to_activity(communication_message)

    # prepare and send system message to npc
    def prepare_and_send_system_message(
        self,
        system_message_type: SystemMessageType,
        system_message: str,
        receiver=SimulationRole.ALL,
    ):
        message = SystemMessageStructure(
            system_message_type=system_message_type,
            system_message=system_message,
            system_message_receiver=receiver,
        )

        # package this message into a communication message and send it to the speaker
        self.logger.info("Sending system message to all")
        # here receiver being ALL will differentiate between system message and normal message apart from the contents
        communication_message = CommunicationMessage.message_to_slave(
            sender=SimulationRole.MASTER, receiver=receiver, content=message
        )
        self.send_command(communication_message)
        self.send_command_to_activity(communication_message)

    def reset(self):
        self.messages_from_frontend = Queue()
        self.waiting_for_response_from_candidate = False
        self.waiting_for_response_from_panelist = False
        self.is_audio_playback_completed = True
        self.current_interview_round = InterviewRound.ROUND_TWO
        self.logger.info("Resetting master agent")

    # this function is used to handle the messages received from the frontend
    async def handle_frontend_messages(self, message: WebSocketMessageFromClient):
        self.logger.info("Handling frontend message")
        message_type: WebSocketMessageTypeFromClient = message.message_type
        self.logger.info(f"Message type: {message_type}")
        # fronend is requesting for instruction data
        if message_type == WebSocketMessageTypeFromClient.INSTRUCTION:
            # we should respond back by sending instruction data to user
            self.candidate_state_tracker = WebSocketMessageTypeFromClient.INSTRUCTION
            self.logger.info("Generating instruction message")
            intro_output: SimulationIntroductionOutputMessage = await self.generate_introduction()
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "metadata",
                {"is_interview_completed": self.is_interview_completed},
            )
            self.logger.info(f"Instruction message: {intro_output}")
            self.set_panelist_data_for_frontend(intro_output)
            # add new fields to the output message
            instruction_data = InstructionDataToClient()
            instruction_data.introduction = intro_output.introduction
            instruction_data.panelists = intro_output.panelists
            instruction_data.role = self.master_config.interview_data.job_details.job_title
            instruction_data.company = self.master_config.interview_data.job_details.company_name
            instruction_data.interview_type = self.current_interview_round.value
            await self._send_message_to_frontend(
                instruction_data.model_dump_json(), WebSocketMessageTypeToClient.INSTRUCTION.value
            )
            return

        # frontend if requesting for information before the interview starts. This will be done for the first time
        elif message_type == WebSocketMessageTypeFromClient.INTERVIEW_START:
            self.candidate_state_tracker = WebSocketMessageTypeFromClient.INTERVIEW_START
            self.prepare_and_send_system_message(
                SystemMessageType.START, "Interview round is started"
            )
            # we should respond back by sending interview start data to user
            panelist_data = self.get_participants_data_for_frontend_for_current_interview_round()
            interview_data: InterviewStartDataToClient = InterviewStartDataToClient()
            interview_data.round = self.current_interview_round
            interview_data.voice_name = (
                self.tts_config.voice_id if self.tts_config.voice_id is not None else ""
            )
            interview_data.participants = panelist_data
            if self.current_interview_round == InterviewRound.ROUND_ONE:
                interview_data.message = (
                    "Welcome to the prescreening round. We will now begin the HR interview round. This interview will be conducted by "
                    + panelist_data[0].name
                    + "."
                    + panelist_data[0].intro
                )
            else:
                # data.message = "We will now begin the technical interview round. This interview will be conducted by " + panelist_data[0].name +"." + panelist_data[0].intro
                # data.message += "In addition, we also have another team member who will be part of the interview :" + panelist_data[1].name + "." + panelist_data[1].intro
                interview_data.message = "lets begin the interview !!!"
            await self._send_message_to_frontend(
                interview_data.model_dump_json(), WebSocketMessageTypeToClient.INTERVIEW_START.value
            )
            self.is_audio_playback_completed = False
            return

        # frontend is requesting activity info so just send back the activity info. Activity info is the data corresponding to this question
        elif message_type == WebSocketMessageTypeFromClient.ACTIVITY_INFO:
            # we should respond back by sending activity data
            data: ActivityDataToClient = ActivityDataToClient()
            activity_details: ActivityDetailsOutputMessage = self.interview_data.activity_details
            data.scenario = activity_details.scenario
            data.data_available = activity_details.data_available
            data.task_for_the_candidate = activity_details.task_for_the_candidate
            code = await self.database.fetch_starter_code_from_url()
            data.starter_code = code if code is not None else ""
            await self._send_message_to_frontend(
                data.model_dump_json(), WebSocketMessageTypeToClient.ACTIVITY_INFO.value
            )
            return

        # frontend is requesting for information when the interview round is ended
        elif message_type == WebSocketMessageTypeFromClient.INTERVIEW_END:
            self.is_interview_completed = False
            await self.database.add_json_data_output_to_database(
                self.firebase_user_id,
                self.session_id,
                "metadata",
                {"is_interview_completed": self.is_interview_completed},
            )
            self.candidate_state_tracker = WebSocketMessageTypeFromClient.INTERVIEW_END
            return

        elif message_type == WebSocketMessageTypeFromClient.DONE_PROBLEM_SOLVING:
            interview_data_message = message.message
            user_response = interview_data_message["message"]
            activity_data = interview_data_message["activity_data"]

            topic, subtopic, _section_name, is_interview_round_changed = (
                self.interview_topic_tracker.get_topic_subtopic_for_discussion(
                    self.current_interview_round
                )
            )
            if topic is None or subtopic is None:
                self.logger.error("Topic or subtopic is None")
                return

            if (
                topic.name
                == TOPICS_TECHNICAL_ROUND.PROBLEM_INTRODUCTION_AND_CLARIFICATION_AND_PROBLEM_SOLVING.value
            ):
                topic_name = self.current_topic_data.name
                subtopic_name = self.current_subtopic_data.name

                masterchatmessage = MasterChatMessage()
                masterchatmessage.speaker = interview_data_message["speaker"]
                masterchatmessage.content = "I am done with the coding question\n"

                status = self.interview_topic_tracker.add_dialog_to_memory(
                    self.current_interview_round, topic_name, subtopic_name, masterchatmessage
                )
                if status:
                    self.logger.info("Dialog added to memory")
                else:
                    self.logger.error("Dialog not added to memory")

                self.interview_topic_tracker.update_all_subtopics_within_topic_status(
                    self.current_interview_round, topic_name
                )  # move to next topic
                if self.interview_topic_tracker.is_topic_completed(
                    self.current_interview_round, topic_name
                ):
                    self.logger.info("*** Topic completed ***")
                    self.topic_just_got_completed = True

                await self.generate_subtopic_summary()  # generate conversation summary

                self.topic_start_time = datetime.now(
                    timezone.utc
                )  # update the topic start time since a new topic has started

                self.waiting_for_response_from_candidate = False

                # sending message to activity agent
                if len(activity_data) > 0:
                    self.prepare_and_send_message(
                        speaker="",
                        activity_code_from_candidate=activity_data,
                        receiver=SimulationRole.ACTIVITY,
                    )
                else:
                    self.logger.info("No activity data received")

            else:
                self.logger.info("Not a coding question")

            return

        # candidate input is received from the frontend. this can be in response or if they press ask
        elif message_type == WebSocketMessageTypeFromClient.INTERVIEW_DATA:
            self.logger.info("Received interview data")
            interview_data_message = message.message
            user_response = interview_data_message["message"]
            activity_data = interview_data_message["activity_data"]

            # sending message to activity agent
            if len(activity_data) > 0:
                self.prepare_and_send_message(
                    speaker="",
                    activity_code_from_candidate=activity_data,
                    receiver=SimulationRole.ACTIVITY,
                )
            else:
                self.logger.info("No activity data received")

            # if frontend has sent some candidate response, only then process it
            if len(user_response) > 0:
                topic, subtopic, _, is_interview_round_changed = (
                    self.interview_topic_tracker.get_topic_subtopic_for_discussion(
                        self.current_interview_round
                    )
                )

                self.is_interview_round_changed = is_interview_round_changed

                # since we have received response from user, we should update the conversation history. Other panelists would access the conversation history
                self._send_user_input_to_candidate_agent(user_response)
                masterchatmessage = MasterChatMessage()
                masterchatmessage.speaker = interview_data_message["speaker"]
                masterchatmessage.content = user_response

                if topic is None or subtopic is None:
                    self.logger.error("Topic or subtopic is None")
                    return

                status = self.interview_topic_tracker.add_dialog_to_memory(
                    self.current_interview_round, topic.name, subtopic.name, masterchatmessage
                )
                if status:
                    self.logger.info("Dialog added to memory")
                else:
                    self.logger.error("Dialog not added to memory")

                self.topic_completion_output_message = await self.check_section_topic_completion()
                self.logger.info("topic section completed")
                self.waiting_for_response_from_candidate = False
                self.interview_topic_tracker.save_memory_graph(self.data_dir)
                await self.database.add_dialog_to_database(
                    self.firebase_user_id, self.session_id, masterchatmessage
                )
                self.logger.info("added dialog to database")

                self.last_speaker = interview_data_message["speaker"]

            else:
                self.logger.info("No user response received")

            return

        elif message_type == WebSocketMessageTypeFromClient.EVALUATION_DATA:
            self.logger.info("Send evaluation data")
            # evaluation_data = await self.generate_evaluation_for_output()
            # await self._send_message_to_frontend(evaluation_data.model_dump_json(), WebSocketMessageTypeToClient.EVALUATION_DATA.value)
            return

        # this will be triggered once the audio playback is completed on the frontend
        elif message_type == WebSocketMessageTypeFromClient.AUDIO_PLAYBACK_COMPLETED:
            self.is_audio_playback_completed = True
            return

        # this will be triggered once the user has logged in
        elif message_type == WebSocketMessageTypeFromClient.USER_LOGIN:
            self.candidate_state_tracker = WebSocketMessageTypeFromClient.USER_LOGIN
            return

        # this will be triggered once the user has logged out
        elif message_type == WebSocketMessageTypeFromClient.USER_LOGOUT:
            self.candidate_state_tracker = WebSocketMessageTypeFromClient.USER_LOGOUT
            return

    # this function runs the master agent functionality and sends the message to the panelist or the candidate
    async def process_and_send_message(self):
        self.logger.info("Processing and sending message")
        topic_name = self.current_topic_data.name
        subtopic_name = self.current_subtopic_data.name
        self.logger.info(f"Topic: {topic_name}, Subtopic: {subtopic_name}")
        # check if conversation history has any messages. If not, then we have just started the simulation so lets record the start time
        if (
            len(
                self.interview_topic_tracker.get_conversation_history_for_topic(
                    self.current_interview_round, topic_name
                )
            )
            == 0
        ):
            self.topic_start_time = datetime.now(timezone.utc)
            self.logger.info(f"Topic start time: {self.topic_start_time}")

        # lets determine who gets to speak next and who listens
        # speaker_determination_output:SpeakerDeterminationOutputMessage = await self.speaker_determination()
        # we should run advice generation in parallel and gather using asyncio.gather
        panelist_profiles = self.get_panelist_profiles_for_current_interview_round()

        results = await asyncio.gather(
            self.speaker_determination(),
            *[
                self.get_conversational_advice(panelist_profile.background.name)
                for panelist_profile in panelist_profiles
            ],  # run advice generation in parallel
        )
        if results and len(results) > 0:
            speaker_determination_output = cast(SpeakerDeterminationOutputMessage, results[0])
            advice_outputs = cast(list[ConversationalAdviceOutputMessage], results[1:])

            if speaker_determination_output:
                self.logger.info("Speaker determination output is not None")
                speaker = speaker_determination_output.next_speaker
            else:
                self.logger.info("Speaker determination output is None")
                speaker = None
        else:
            speaker = None
            advice_outputs = []

        if speaker:
            self.speaker_determination_output_message = speaker_determination_output
            self.logger.info(f"Speaker determination: {speaker_determination_output}")
            self.last_speaker = speaker

            # lets send the speaker info as a separate message to the frontend
            next_speaker_info_message_to_be_sent = NextSpeakerInfoToClient()
            next_speaker_info_message_to_be_sent.speaker = speaker

            if speaker.lower() == self.get_candidate_profile().background.name.lower():
                next_speaker_info_message_to_be_sent.is_user_input_required = True
            else:
                next_speaker_info_message_to_be_sent.is_user_input_required = False

            # Here we are sending message to either user or the panelist.
            if speaker.lower() == self.get_candidate_profile().background.name.lower():
                # if speaker is the candidate, then we need to get the input from frontend
                interview_message_data_to_be_sent = InterviewMessageDataToClient()
                interview_message_data_to_be_sent.speaker = speaker
                interview_message_data_to_be_sent.interview_round = self.current_interview_round
                interview_message_data_to_be_sent.is_user_input_required = True
                interview_message_data_to_be_sent.current_topic = self.current_topic_data.name
                interview_message_data_to_be_sent.current_subtopic = self.current_subtopic_data.name
                await self._send_message_to_frontend(
                    interview_message_data_to_be_sent.model_dump_json(),
                    WebSocketMessageTypeToClient.INTERVIEW_DATA.value,
                )
                self.waiting_for_response_from_candidate = True
                self.logger.info("Waiting for response from candidate")
            else:
                await self._send_message_to_frontend(
                    next_speaker_info_message_to_be_sent.model_dump_json(),
                    WebSocketMessageTypeToClient.NEXT_SPEAKER_INFO.value,
                )
                possible_speakers = [
                    panelist_profile.background.name for panelist_profile in panelist_profiles
                ]
                # Based on the speaker, we need to get the corresponding advice
                advice = advice_outputs[possible_speakers.index(speaker)]
                self.logger.info(f"Advice: {advice}")
                # send message to the panelist
                self.prepare_and_send_message(speaker=speaker, receiver=SimulationRole.PANELIST)
                self.waiting_for_response_from_panelist = True
                self.logger.info("Waiting for response from panelist")
        else:
            # raise an exception
            self.logger.error("Speaker determination output is None")
            raise Exception("Speaker determination output is None")

    # check if we have received any messages from frontend
    async def process_frontend_messages(self):
        while True:
            try:
                websocketmessagefromclient = (
                    self.messages_from_frontend.get_nowait()
                )  # pop out the message from the queue
                async with self.lock:
                    self.logger.info(
                        f"Received message from frontend: {websocketmessagefromclient}"
                    )
                    await self.handle_frontend_messages(
                        websocketmessagefromclient
                    )  # here we can either respond back, update the user state or do some other processing
            except asyncio.QueueEmpty:
                pass  # No messages available
            await asyncio.sleep(0.1)  # process other tasks in the event loop

    async def _manage_processing_task(self):
        """Manages the processing task with proper cleanup and error handling"""
        try:
            # If there's an existing task, wait for it to complete
            if self.processing_task is not None and not self.processing_task.done():
                self.logger.info("Waiting for existing processing task to complete")
                try:
                    # Wait for the task to complete with a timeout
                    await asyncio.wait_for(self.processing_task, timeout=30.0)  # 30 second timeout
                except asyncio.TimeoutError:
                    # If task is taking too long, cancel it
                    self.logger.warning("Processing task taking too long, cancelling")
                    self.processing_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self.processing_task
                except asyncio.CancelledError:
                    self.logger.info("Processing task was cancelled externally")
                except Exception as e:
                    self.logger.exception(f"Processing task failed: {e}")

                # Add error handling callback
                def handle_task_exception(task):
                    try:
                        self.logger.info("Processing task completed")
                        task.result()
                    except asyncio.CancelledError:
                        self.logger.info("Processing task was cancelled")
                    except Exception as e:
                        self.logger.exception(f"Processing task failed: {e}")

                self.processing_task.add_done_callback(handle_task_exception)
            else:
                self.logger.info("No processing task found so we can start the processing task")
                self.processing_task = asyncio.create_task(self.process_and_send_message())

        except Exception as e:
            self.logger.exception(f"Error managing processing task: {e}")

    def is_ready_for_next_message(self) -> bool:
        return (
            not self.waiting_for_response_from_panelist
            and not self.waiting_for_response_from_candidate
            and self.is_audio_playback_completed
        )

    """
    The main logic for simulation
    """

    async def run(self):
        try:
            self.logger = self.logger.bind(user_id=self.user_id, session_id=self.session_id)
            self.logger.info("Starting master agent...")
            # create activity agent.
            await self._create_activity_agent()
            # create candidate agent. Just using it to keep track of user responses. Not doing anything else
            await self._create_candidate_agent()
            # create panelist agents. These are the npcs who will be part of the interview process. pass the activity agent instance
            await self._create_panelist_agents()
            # We would want to handle the messages from the frontend in parallel
            self.frontend_task = asyncio.create_task(self.process_frontend_messages())
            self.logger.info("Initialization completed. Sending interview details to frontend")
            # await self._send_message_to_frontend(self.get_candidate_profile().background.model_dump_json(), WebSocketMessageTypeToClient.USER_PROFILE.value)
            interview_details_data = self.prepare_interview_details_data()
            await self._send_message_to_frontend(
                interview_details_data.model_dump_json(),
                WebSocketMessageTypeToClient.INTERVIEW_DETAILS.value,
            )
            # run until the simulation is completed
            while True:
                async with self.lock:
                    # candidate state tracker keeps track of the state based on the frontend message. If the state is interview_start, then simulation is running
                    if (
                        self.candidate_state_tracker
                        == WebSocketMessageTypeFromClient.INTERVIEW_START
                    ):
                        # apart from checking if we are waiting for response from npc or user, we also need to check if the audio playback is completed.
                        # this step should be optimized. We should be ready with the next response while the audio playback is happening if its not the user's turn
                        # Audio playback completed message is sent by the frontend. We don't want to send anything before this.
                        if self.is_ready_for_next_message():
                            # get the topic and subtopic for the current interview round. this will be used by the characters for discussion
                            topic, subtopic, section, interview_round_changed = (
                                self.interview_topic_tracker.get_topic_subtopic_for_discussion(
                                    self.current_interview_round
                                )
                            )
                            if topic is None or subtopic is None:
                                self.logger.error("Topic or subtopic is None")
                                return
                            self.logger.info(
                                f"Topic: {topic}, Subtopic: {subtopic}, Section: {section}"
                            )
                            self.logger.info(
                                f"Current interview round: {self.current_interview_round}"
                            )
                            self.is_interview_round_changed = interview_round_changed
                            self.current_topic_data = topic
                            self.current_subtopic_data = subtopic
                            self.current_section_data = section if section is not None else ""
                            # We want to check if interview round has ended and transitioned to a new one. Inform the frontend, if this is the case
                            if self.is_interview_round_changed:
                                self.logger.info("Interview round changed")
                                self.current_interview_round = InterviewRound.ROUND_TWO
                                # We should also inform the agents that the interview has completed
                                self.prepare_and_send_system_message(
                                    SystemMessageType.INTERVIEW_ROUND_CHANGED,
                                    "Interview round is changed from 1 to 2",
                                )
                                # here we send the message to the frontend to update the UI for the next interview round
                                self.is_interview_round_changed = False  # reset the flag
                                # prepare the message to be sent to the frontend
                                interview_data: InterviewStartDataToClient = (
                                    InterviewStartDataToClient()
                                )
                                interview_data.round = self.current_interview_round
                                interview_data.voice_name = (
                                    self.tts_config.voice_id
                                    if self.tts_config.voice_id is not None
                                    else ""
                                )
                                interview_data.participants = self.get_participants_data_for_frontend_for_current_interview_round()
                                interview_data.message = "Thank you for completing the first round of interview. We will now begin the second round of interview."
                                interview_data.message += (
                                    "This interview will be conducted by "
                                    + interview_data.participants[0].name
                                    + "."
                                    + interview_data.participants[0].intro
                                )
                                interview_data.message += (
                                    "The other interviewer will be "
                                    + interview_data.participants[1].name
                                    + "."
                                    + interview_data.participants[1].intro
                                )
                                await self._send_message_to_frontend(
                                    interview_data.model_dump_json(),
                                    WebSocketMessageTypeToClient.INTERVIEW_START.value,
                                )
                                self.is_audio_playback_completed = False
                                continue
                            # if topic and subtopic is None, then we have completed the interview so send the end command to the frontend
                            if topic is None and subtopic is None:
                                # this means we have completed all the topics and subtopics so send the end message to the frontend and the npcs
                                self.candidate_state_tracker = (
                                    WebSocketMessageTypeFromClient.INTERVIEW_END
                                )
                                self.logger.info("Interview is completed")
                                self.is_interview_completed = True
                                await self.database.add_json_data_output_to_database(
                                    self.firebase_user_id,
                                    self.session_id,
                                    "metadata",
                                    {"is_interview_completed": self.is_interview_completed},
                                )
                            else:
                                # here we are sending message to either the panelist or the candidate.
                                # start the processing task
                                await self._manage_processing_task()

                        # we are waiting for response from the panelist.
                        elif (
                            self.waiting_for_response_from_panelist
                        ) and self.is_audio_playback_completed:
                            # This will contain messages from the panelists
                            if not self.receiving_message_queue.empty():
                                self.logger.info("Received message from panelist")
                                try:
                                    response: CommunicationMessage = (
                                        self.receiving_message_queue.get_nowait()
                                    )  # this will be of type CommunicationMessage
                                except asyncio.QueueEmpty:
                                    self.logger.info("No message received from panelist")
                                    continue

                                # parse the response as the sender was Panelist and receiver was master
                                sender = response.sender
                                receiver = response.receiver
                                if (
                                    sender == SimulationRole.PANELIST
                                    and receiver == SimulationRole.MASTER
                                ):
                                    self.waiting_for_response_from_panelist = (
                                        False  # we have received the response
                                    )
                                    self.is_audio_playback_completed = (
                                        False  # we will start the audio playback now
                                    )

                                    if isinstance(response.content, SlaveMessageStructure):
                                        response_data: SlaveMessageStructure = response.content
                                    else:
                                        self.logger.error(
                                            "Response is not of type SlaveMessageStructure"
                                        )
                                        return

                                    # parse the response
                                    speaker = response_data.speaker
                                    messages = response_data.message[0]
                                    voice_name = response_data.voice_name
                                    # once we have the response, we may need to check the rules and regulations and flag it. not doing it for now
                                    self.logger.info(f"Speaker: {speaker}, Message: {messages}")
                                    chatMessage = MasterChatMessage()
                                    chatMessage.speaker = speaker
                                    chatMessage.content = messages
                                    status = self.interview_topic_tracker.add_dialog_to_memory(
                                        self.current_interview_round,
                                        self.current_topic_data.name,
                                        self.current_subtopic_data.name,
                                        chatMessage,
                                    )
                                    if status:
                                        self.logger.info("Dialog added to memory")
                                    else:
                                        self.logger.error("Dialog not added to memory")
                                    await self.database.add_dialog_to_database(
                                        self.firebase_user_id, self.session_id, chatMessage
                                    )
                                    # send the message to the frontend with panelist response
                                    message_to_be_sent = InterviewMessageDataToClient()
                                    message_to_be_sent.speaker = speaker
                                    message_to_be_sent.interview_round = (
                                        self.current_interview_round
                                    )
                                    message_to_be_sent.is_user_input_required = False
                                    message_to_be_sent.voice_name = voice_name
                                    message_to_be_sent.text_message = messages
                                    message_to_be_sent.current_topic = self.current_topic_data.name
                                    message_to_be_sent.current_subtopic = (
                                        self.current_subtopic_data.name
                                    )

                                    await self._send_message_to_frontend(
                                        message_to_be_sent.model_dump_json(),
                                        WebSocketMessageTypeToClient.INTERVIEW_DATA.value,
                                    )

                    elif (
                        self.candidate_state_tracker == WebSocketMessageTypeFromClient.INTERVIEW_END
                    ):
                        # when the interview is completed, we should save all kinds of json data to the database
                        self.logger.info("Interview is Ended")
                        memory_graph = self.interview_topic_tracker.memory_graph
                        await self.database.add_json_data_output_to_database(
                            self.firebase_user_id,
                            self.session_id,
                            "memory_graph.json",
                            memory_graph.model_dump(),
                        )

                        data: InterviewEndDataToClient = InterviewEndDataToClient()
                        data.message = (
                            "Thank you for participating. Your Interview is completed !!!"
                        )
                        data.voice_name = (
                            self.tts_config.voice_id if self.tts_config.voice_id is not None else ""
                        )
                        await self._send_message_to_frontend(
                            data.model_dump_json(), WebSocketMessageTypeToClient.INTERVIEW_END.value
                        )
                        self.candidate_state_tracker = (
                            WebSocketMessageTypeFromClient.USER_LOGIN
                        )  # setting to something random

                    elif self.candidate_state_tracker == WebSocketMessageTypeFromClient.USER_LOGOUT:
                        self.prepare_and_send_system_message(
                            SystemMessageType.END, "Interview is completed"
                        )
                        self.reset()
                        break

                # Yield control back to the event loop
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Cancel sub-tasks
            self.logger.info("Master agent cancelling")

            tasks_to_cancel = []

            # Cancel + collect only existing tasks
            for task in [
                self.frontend_task,
                self.processing_task,
                self.activity_task,
                self.candidate_instance_task,
                *self.panelist_tasks,
            ]:
                if task is not None:
                    task.cancel()
                    tasks_to_cancel.append(task)

            # Wait for all cancelled tasks to finish
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            self.logger.info("Master agent cancelled")
            raise

        except Exception as e:
            self.logger.exception(f"Error in main loop of master agent: {e}")
            await self._send_message_to_frontend(
                "There was an error.", WebSocketMessageTypeToClient.ERROR.value
            )
            # send error message to frontend if connected
