from pydantic import Field
from candidate_agent.base import BaseCandidate, BaseCandidateConfiguration
import datetime 
from core.resource.model_providers.schema import ChatMessage, AssistantChatMessage, ChatModelProvider, ReflectionChatMessage
from core.prompting.prompt_strategies.candidate_one_shot import CandidatePromptStrategy
from core.memory.character_memory import SimpleMemory
from typing import List, Any, Optional
from panelist_agent.base import Profile
import asyncio
import os
from queue import Queue
from pathlib import Path
import logging

class Candidate(BaseCandidate):
    
    simple_memory: SimpleMemory = SimpleMemory(conversation_memory=[], reflection_memory=[])
    config_data: BaseCandidateConfiguration = BaseCandidateConfiguration()
    prompt_strategy: Any = None
    
    def __init__(self, 
                 config: BaseCandidateConfiguration, 
                 llm_provider: ChatModelProvider, 
                 receiving_message_queue: Queue, 
                 sending_message_queue: Queue,
                 logger: Optional[Any] = None):
        
        self.prompt_strategy = CandidatePromptStrategy(config)
        self.config_data = config
        self.logger = logger or logging.getLogger(__name__)

        super().__init__(
            user_config=self.config_data,
            llm_provider=llm_provider,
            prompt_strategy=self.prompt_strategy
        )
        
        self.receiving_message_queue = receiving_message_queue
        self.sending_message_queue = sending_message_queue
        self.name = self.config_data.profile.background.name
        self.data_dir = Path(__file__).parent.parent / "data"
        self.previous_conversation_counter = 0
        self.candidate_input_tracker = []
        
        self.logger.info(f"Candidate with name: {self.name} is initialized")

    def send_response(self, response: Any) -> None:
        try:
            self.logger.info("Sending response from candidate")
            self.sending_message_queue.put(response)
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
    
    def get_candidate_profile(self) -> Profile:
        return self.config_data.profile
        
    def get_conversation_history(self) -> List[Any]:
        return self.simple_memory.get_all()
    
    def get_last_conversation_message(self) -> Optional[Any]:
        return self.simple_memory.recall()
    
    def update_conversation_history(self, candidate_input: str) -> None:
        try:
            message = ChatMessage(role=ChatMessage.Role.USER, content=candidate_input)
            self.simple_memory.remember(message)
        except Exception as e:
            self.logger.error(f"Error updating conversation history: {e}")

    def get_panelist_info(self, panelist_profile_list: List[Profile]) -> List[Profile]:
        return panelist_profile_list

    def parse_process_decision_model(self, response: AssistantChatMessage, prompt: ChatMessage) -> Any:
        try:
            output = self.prompt_strategy.parse_response_decision_content(response)
            chatmessage = ChatMessage(role=ChatMessage.Role.USER, content=output.dialog)
            self.simple_memory.remember(chatmessage)
            return output
        except Exception as e:
            self.logger.error(f"Error parsing decision model: {e}")
            raise
    
    def update_candidate_input_list(self, candidate_input: str) -> None:
        try:
            self.candidate_input_tracker.append(candidate_input)
        except Exception as e:
            self.logger.error(f"Error updating candidate input: {e}")

    async def process_message(self, message: Any) -> None:
        """Process incoming messages"""
        try:
            self.logger.info(f"Processing message: {message}")
            # Add your message processing logic here
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    async def run(self) -> None:
        self.candidate_start_time = datetime.datetime.now()
        self.logger.info("Candidate agent started")
        
        while True:
            try:
                message = self.receiving_message_queue.get_nowait()
                await self.process_message(message)
            except asyncio.QueueEmpty:
                pass
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
            
            await asyncio.sleep(0.1)