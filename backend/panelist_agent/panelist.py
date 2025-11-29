import asyncio
import json
import os
from pathlib import Path
from typing import List, cast

from interview_details_agent.base import BaseInterviewConfiguration

from core.database.base import DatabaseInterface
from core.memory.character_memory import SimpleMemory
from core.prompting.prompt_strategies.panelist_one_shot import PanelistPromptStrategy
from core.prompting.schema import ChatPrompt
from core.resource.model_providers.schema import (
    AssistantChatMessage,
    ChatMessage,
    ChatModelProvider,
    ReasoningChatMessage,
    ReflectionChatMessage,
)
from core.speech.base import SpeechConfig
from master_agent.base import (
    CommunicationMessage,
    InterviewRound,
    MasterMessageStructure,
    SimulationRole,
    SlaveMessageStructure,
    SpeakerDeterminationOutputMessage,
    SystemMessageStructure,
    SystemMessageType,
    TopicSectionCompletionOutputMessage,
)
from panelist_agent.base import (
    BasePanelist,
    BasePanelistConfiguration,
    DomainKnowledgeOutputMessage,
    EvaluationOutputMessage,
    Profile,
    PromptInput,
    ReasoningOutputMessage,
    ReflectionOutputMessage,
    ResponseOutputMessage,
    ResponseWithReasoningOutputMessage,
)


# when creating a new agent, we need to pass the settings and llm_provider
class Panelist(BasePanelist):
    memory: SimpleMemory = SimpleMemory()
    config: BasePanelistConfiguration = BasePanelistConfiguration(
        name="Panelist", description="Panelist"
    )
    # prompt_strategy:Any = None

    def __init__(
        self,
        interview_config: BaseInterviewConfiguration,
        panelist_config: BasePanelistConfiguration,
        user_id: str,
        firebase_user_id: str,
        session_id: str,
        llm_provider: ChatModelProvider,
        gemini_provider: ChatModelProvider,
        groq_provider: ChatModelProvider,
        grok_provider: ChatModelProvider,
        deepseek_provider: ChatModelProvider,
        server_address: str,
        database: DatabaseInterface,
        receiving_message_queue: asyncio.Queue,
        sending_message_queue: asyncio.Queue,
        logger,
    ):
        self.prompt_strategy: PanelistPromptStrategy = PanelistPromptStrategy(
            panelist_config, interview_config, database
        )
        # this calls the __init__ method of the base agent
        super().__init__(
            config=panelist_config,
            llm_provider=llm_provider,
            gemini_provider=gemini_provider,
            groq_provider=groq_provider,
            grok_provider=grok_provider,
            deepseek_provider=deepseek_provider,
            prompt_strategy=self.prompt_strategy,
        )

        self.config = panelist_config
        self.master_instance = None
        self.receiving_message_queue: asyncio.Queue = receiving_message_queue
        self.sending_message_queue: asyncio.Queue = sending_message_queue
        self.name = self.config.profile.background.name
        self.token_counter = 0
        self.listener = None
        self.data_dir = os.path.dirname(os.path.realpath(__file__)) + "/../data/" + user_id + "/"
        self.previous_conversation_counter = 0
        self.my_profile: Profile = self.config.profile
        self.interview_round_part_of = self.my_profile.interview_round_part_of
        self.current_state = None
        self.activity_instance = None
        self.server_address = server_address
        self.voice_name = None
        self.evaluation_output_message = None
        self.evaluation_output_messages_topic_subtopic_mapping = {}
        self.database = database
        self.firebase_user_id = firebase_user_id
        self.user_id = user_id
        self.session_id = session_id

        # check if files are present. if yes, then delete them
        for file_pattern in [
            "_respond.json",
            "_think.json",
            "_reflection.json",
            "_domain_knowledge.json",
            "_eval.json",
        ]:
            file_path = Path(self.data_dir) / f"{self.name}{file_pattern}"
            file_path.unlink(missing_ok=True)

        self.logger = logger

    def get_receiving_message_queue(self):
        return self.receiving_message_queue

    def set_tts_config(self, tts_config: SpeechConfig):
        self.tts_config = tts_config
        self.voice_name = tts_config.voice_id
        self.logger.info(f"TTS config name: {self.tts_config.voice_id}")

    def set_master_instance(self, master_instance):
        self.master_instance = master_instance

    def on_command(self, command: CommunicationMessage):
        self.logger.info(f"Received command: {command} in {self.name}")
        self.receiving_message_queue.put_nowait(command)

    def send_response(self, response: CommunicationMessage):
        self.logger.info(f"Sending response from {self.name}")
        self.sending_message_queue.put_nowait(response)

    def get_info_of_other_panelists(self, npc_profile_list: List[Profile]):
        filtered_list = [
            profile for profile in npc_profile_list if profile.background.name != self.name
        ]
        return filtered_list

    def get_my_profile(self):
        return self.config.profile

    def get_conversation_history_from_memory(self):
        return self.memory.get_all_from_memory()

    def get_reflection_history(self):
        return self.memory.get_all_reflection_from_memory()

    def get_reasoning_history(self):
        return self.memory.get_all_reasoning_from_memory()

    def update_reflection_history(self, user_input: ReflectionOutputMessage):
        message = ReflectionChatMessage(
            reflection=user_input.reflection, character_name=user_input.character_name
        )

        self.memory.add_reflection_to_memory(message)

    def update_reasoning_history(self, user_input: ReasoningOutputMessage):
        message = ReasoningChatMessage(
            interview_thoughts_for_myself=user_input.interview_thoughts_for_myself
        )
        self.memory.add_reasoning_to_memory(message)

    def get_last_conversation_message(self):
        return self.memory.recall_last_message()

    def update_conversation_history(self, user_input):
        message = ChatMessage(role=ChatMessage.Role.USER, content=user_input)
        self.memory.add_to_memory(message)

    # this is the abstract method defined in the base class that needs to be implemented. this callback gets triggered when we call the model. Parsing the output is defined inside the prompt strategy class
    def parse_process_response_model(self, response: AssistantChatMessage, prompt: ChatMessage):
        output: ResponseOutputMessage = self.prompt_strategy.parse_process_response_model(response)
        return output

    def parse_process_reason_model(self, response: AssistantChatMessage, prompt: ChatMessage):
        output: ReasoningOutputMessage = self.prompt_strategy.parse_response_reason_content(
            response
        )
        return output

    # this is the abstract method defined in the base class that needs to be implemented
    def parse_process_reflect_model(self, response: AssistantChatMessage, prompt: ChatMessage):
        output: ReflectionOutputMessage = self.prompt_strategy.parse_response_reflect_content(
            response
        )
        return output

    def parse_process_evaluate_model(self, response: AssistantChatMessage, prompt: ChatMessage):
        output: EvaluationOutputMessage = self.prompt_strategy.parse_response_evaluate_content(
            response
        )
        return output

    def parse_process_domain_knowledge_model(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        output: DomainKnowledgeOutputMessage = (
            self.prompt_strategy.parse_response_domain_knowledge_content(response)
        )
        return output

    def parse_process_respond_with_reasoning_model(
        self, response: AssistantChatMessage, prompt: ChatMessage
    ):
        output: ResponseWithReasoningOutputMessage = (
            self.prompt_strategy.parse_process_respond_with_reasoning_model(response)
        )
        return output

    # respond module should be called after the think module. This is where the actual response is generated.
    # The final response should consider the previous conversatio. maybe here, we can set the tone, style.
    async def respond(
        self,
        input_message: CommunicationMessage,
        output_reason: ReasoningOutputMessage,
        activity_progress,
        domain_knowledge_output: DomainKnowledgeOutputMessage,
    ):
        prompt_input = PromptInput(
            response_type=PanelistPromptStrategy.RESPONSE_TYPE.RESPOND,
            reason=output_reason,
            activity_progress=activity_progress,
            domain_knowledge=domain_knowledge_output,
            candidate_profile=self.master_instance.get_candidate_profile()
            if self.master_instance is not None
            else Profile(),
            message=input_message,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        token_count = self.llm_provider.count_message_tokens(
            prompt.messages, self.config.settings.gpt_4o
        )
        self.token_counter += token_count if token_count is not None else 0
        output: ResponseOutputMessage = await super().respond(prompt)

        data_path = Path(self.data_dir) / f"{self.name}_respond.json"
        try:
            with open(data_path, "a") as f:
                json.dump(output.model_dump(), f, indent=4)
                f.write("\n")
        except Exception as e:
            self.logger.error(f"Error writing to file {data_path}: {e}")

        return output

    async def get_domain_knowledge(
        self,
        input_message: CommunicationMessage,
        output_reason: ReasoningOutputMessage,
        activity_progress,
    ):
        prompt_input = PromptInput(
            response_type=PanelistPromptStrategy.RESPONSE_TYPE.DOMAIN_KNOWLEDGE,
            reason=output_reason,
            activity_progress=activity_progress,
            message=input_message,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        token_count = self.llm_provider.count_message_tokens(
            prompt.messages, self.config.settings.gpt_4o
        )
        self.token_counter += token_count if token_count is not None else 0
        output: DomainKnowledgeOutputMessage = await super().get_domain_knowledge(prompt)

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            f"panelist_domain_knowledge_{self.name}",
            output.model_dump() if hasattr(output, "model_dump") else output,
        )

        with open(self.data_dir + self.name + "_domain_knowledge.json", "a") as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        return output

    # think module should be about generating content relevant to their professional profile. Maybe we should consider past responses and reflections here.
    # think module should figure out what aspects to respond to the user, what things to say next based on current topic. Ensure direction is maintained
    async def think(self, input_message: CommunicationMessage, activity_progress):
        prompt_input = PromptInput(
            response_type=PanelistPromptStrategy.RESPONSE_TYPE.REASON,
            activity_progress=activity_progress,
            candidate_profile=self.master_instance.get_candidate_profile()
            if self.master_instance is not None
            else Profile(),
            message=input_message,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        token_count = self.llm_provider.count_message_tokens(
            prompt.messages, self.config.settings.gpt_4o
        )
        self.token_counter += token_count if token_count is not None else 0
        output: ReasoningOutputMessage = await super().reason(prompt)

        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            f"panelist_reasoning_{self.name}",
            output.model_dump() if hasattr(output, "model_dump") else output,
        )
        self.update_reasoning_history(output)

        with open(self.data_dir + self.name + "_think.json", "a") as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        return output

    async def respond_with_reasoning(self, input_message: CommunicationMessage, activity_progress):
        prompt_input = PromptInput(
            response_type=PanelistPromptStrategy.RESPONSE_TYPE.RESPOND_WITH_REASONING,
            activity_progress=activity_progress,
            candidate_profile=self.master_instance.get_candidate_profile()
            if self.master_instance is not None
            else Profile(),
            message=input_message,
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        token_count = self.llm_provider.count_message_tokens(
            prompt.messages, self.config.settings.gpt_4o
        )
        self.token_counter += token_count if token_count is not None else 0
        output: ResponseWithReasoningOutputMessage = await super().respond_with_reasoning(prompt)

        data_path = Path(self.data_dir) / f"{self.name}_respond_with_reasoning.json"
        try:
            with open(data_path, "a") as f:
                json.dump(output.model_dump(), f, indent=4)
                f.write("\n")
        except Exception as e:
            self.logger.error(f"Error writing to file {data_path}: {e}")

        return output

    async def react(self, communicationMessage: CommunicationMessage):
        # here we are getting the activity progress from the activity agent as the first thing
        if self.interview_round_part_of == InterviewRound.ROUND_TWO:
            if self.activity_instance is not None:
                activity_progress = self.activity_instance.get_recent_progress()
                self.logger.info(f"Activity progress: {activity_progress}")
            else:
                activity_progress = None
                self.logger.info("Activity progress is None")
        else:
            activity_progress = None
            self.logger.info("No activity progress for round one")

        # self.logger.info("Thinking")
        # output_reason:ReasoningOutputMessage =  await self.think(communicationMessage,  activity_progress)
        # self.logger.info(f"Reasoning output: {output_reason}")

        # if output_reason.is_domain_knowledge_access_needed:
        #     self.logger.info("Domain knowledge needed")
        #     output_domain_knowledge:DomainKnowledgeOutputMessage = await self.get_domain_knowledge(communicationMessage, output_reason, activity_progress)
        #     self.logger.info(f"Domain knowledge output: {output_domain_knowledge}")
        # else:
        #     self.logger.info("Domain knowledge not needed")
        #     output_domain_knowledge = DomainKnowledgeOutputMessage()

        # output_dialog:ResponseOutputMessage = await self.respond(communicationMessage,
        #                                                          output_reason,
        #                                                          activity_progress,
        #                                                          output_domain_knowledge)
        response_output_with_reasoning = await self.respond_with_reasoning(
            communicationMessage, activity_progress
        )
        self.logger.info(f"Dialog output: {response_output_with_reasoning}")
        dialog = response_output_with_reasoning.response
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            f"panelist_response_reasoning_{self.name}",
            response_output_with_reasoning.model_dump()
            if hasattr(response_output_with_reasoning, "model_dump")
            else response_output_with_reasoning,
        )
        self.update_conversation_history(dialog)

        response = CommunicationMessage.message_to_master(
            sender=SimulationRole.PANELIST,
            receiver=SimulationRole.MASTER,
            content=SlaveMessageStructure(
                message=[dialog],
                speaker=self.name,
                voice_name=self.voice_name if self.voice_name is not None else "",
            ),
        )
        self.send_response(response)

    async def evaluate(
        self,
        topic_name,
        subtopic_name,
        topic_data,
        subtopic_data,
        topic_conversation,
        candidate_profile,
        panelist_profiles,
        evaluation_criteria,
        subqueries_data,
    ):
        self.logger.info(f"Evaluating topic: {topic_name} and subtopic: {subtopic_name}")

        message = MasterMessageStructure(
            speaker=self.my_profile,
            conversation_history_for_current_subtopic=[],
            conversation_summary_for_current_topic=[],
            conversation_summary_for_completed_topics=[],
            last_completed_conversation_history=topic_conversation,
            candidate_profile=candidate_profile,
            panelist_profiles=panelist_profiles,
            topic=topic_data,
            sub_topic=subtopic_data,
            current_interview_round=InterviewRound.ROUND_TWO,
            evaluation_criteria=evaluation_criteria,
            activity_code_from_candidate="",
            current_section="",
            remaining_topics=[],
            remaining_time=0,
            topic_completion_message=TopicSectionCompletionOutputMessage(),
            speaker_determination_message=SpeakerDeterminationOutputMessage(),
            panelist_thoughts={},
        )

        prompt_input = PromptInput(
            response_type=PanelistPromptStrategy.RESPONSE_TYPE.EVALUATE,
            message=message,
            subqueries_data=subqueries_data,
            candidate_profile=candidate_profile,
            activity_code_from_candidate=self.activity_instance.get_activity_code_from_candidate()
            if self.activity_instance is not None
            else "",
            activity_progress=self.activity_instance.get_recent_progress()
            if self.activity_instance is not None
            else "",
        )

        prompt: ChatPrompt = super().build_prompt(prompt_input)
        output: EvaluationOutputMessage = await super().evaluate(prompt)

        self.evaluation_output_message = output
        self.evaluation_output_messages_topic_subtopic_mapping[topic_name + "," + subtopic_name] = (
            output
        )
        await self.database.add_json_data_output_to_database(
            self.firebase_user_id,
            self.session_id,
            f"panelist_evaluation_{self.name}",
            self.evaluation_output_message.model_dump()
            if hasattr(self.evaluation_output_message, "model_dump")
            else self.evaluation_output_message,
        )

        with open(self.data_dir + self.name + "_eval.json", "a") as f:
            json.dump(output.model_dump(), f, indent=4)
            f.write("\n")

        return output

    def get_overall_feedback(self):
        overall_feedback = ""
        for key, value in self.evaluation_output_messages_topic_subtopic_mapping.items():
            overall_feedback += value.feedback_to_the_hiring_manager_about_candidate + "\n"

        return overall_feedback

    def overall_score(self):
        total_score = 0
        counter = 0
        for key, value in self.evaluation_output_messages_topic_subtopic_mapping.items():
            if value.score > 0:
                total_score += value.score
                counter += 1

        return total_score / counter

    def get_last_evaluation_output_message(self):
        return self.evaluation_output_message

    def get_evaluation_output_messages_topic_subtopic_mapping(self):
        return self.evaluation_output_messages_topic_subtopic_mapping

    async def process_system_message(self, communicationMessage: CommunicationMessage):
        system_message: SystemMessageStructure = cast(
            SystemMessageStructure, communicationMessage.content
        )
        self.logger.info(f"System message received: {system_message.system_message_type}")

        if system_message.system_message_type == SystemMessageType.START:
            self.current_state = SystemMessageType.START
            self.logger.info("interview start")

        elif system_message.system_message_type == SystemMessageType.END:
            self.logger.info("interview end")
            self.current_state = SystemMessageType.END

        elif system_message.system_message_type == SystemMessageType.INTERVIEW_ROUND_CHANGED:
            self.logger.info("interview round changed")
            if self.interview_round_part_of == InterviewRound.ROUND_ONE:
                self.logger.info("Change from round one to round two")

        elif system_message.system_message_type == SystemMessageType.ACTIVITY_DATA:
            self.logger.info("activity data received")

    def set_activity_instance(self, activity_instance):
        self.activity_instance = activity_instance
        self.logger.info(f"Activity instance set: {self.activity_instance}")

    def is_message_for_me(self, communicationMessage: CommunicationMessage) -> bool:
        """Check if the message is intended for this panelist"""
        if communicationMessage.sender != SimulationRole.MASTER:
            return False

        if communicationMessage.receiver != SimulationRole.PANELIST:
            return False

        message_content = communicationMessage.content
        if not isinstance(message_content, MasterMessageStructure):
            return False

        speaker = message_content.speaker
        if not speaker:
            return False

        # Check if this panelist is part of the current interview round
        if message_content.current_interview_round != self.interview_round_part_of:
            return False

        # Check if the message is specifically for this panelist
        return speaker.background.name == self.name

    def is_system_message(self, communicationMessage: CommunicationMessage) -> bool:
        """Check if this is a system message for all panelists"""
        return (
            communicationMessage.sender == SimulationRole.MASTER
            and communicationMessage.receiver == SimulationRole.ALL
        )

    def should_stop_agent(self) -> bool:
        """Check if the agent should stop running"""
        if self.current_state == None:
            return False
        return self.current_state == SystemMessageType.END

    def cleanup_on_exit(self):
        """Clean up resources when agent stops"""
        self.get_conversation_history_from_memory().clear()
        self.get_reflection_history().clear()
        self.receiving_message_queue = asyncio.Queue()

    # this is the main method that gets called when the agent is started
    async def run(self):
        self.logger = self.logger.bind(user_id=self.user_id, session_id=self.session_id)
        self.logger.info("Panelist agent started with name: " + self.name)

        while True:
            try:
                communicationMessage: CommunicationMessage = (
                    self.receiving_message_queue.get_nowait()
                )

                # Handle system messages
                if self.is_system_message(communicationMessage):
                    await self.process_system_message(communicationMessage)
                    continue

                # Handle messages for this panelist
                if self.is_message_for_me(communicationMessage):
                    self.logger.info(f"Message for me: {self.name}")
                    await self.react(communicationMessage)
                else:
                    self.logger.info(f"Message not for me: {self.name}")

            except asyncio.QueueEmpty:
                # Check if we should stop
                if self.should_stop_agent():
                    self.logger.info("Interview ended. Stopping the agent with name: " + self.name)
                    self.cleanup_on_exit()
                    break

            await asyncio.sleep(0.1)
