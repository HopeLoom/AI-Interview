import datetime
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union
from core.memory.base import Passage
from core.memory.storage_connector import StorageConnector


class RecallMemory(ABC):
    @abstractmethod
    def text_search(self, query_string, count=None, start=None):
        """Search messages that match query_string in recall memory"""

    @abstractmethod
    def date_search(self, start_date, end_date, count=None, start=None):
        """Search messages between start_date and end_date in recall memory"""

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def insert(self, message: Passage):
        """Insert message into recall memory"""


class BaseRecallMemory(RecallMemory):
    """Recall memory based on base functions implemented by storage connectors"""

    def __init__(self, agent_settings, restrict_search_to_summaries=False):
        # If true, the pool of messages that can be queried are the automated summaries only
        # (generated when the conversation window needs to be shortened)
        #self.restrict_search_to_summaries = restrict_search_to_summaries
        self.agent_settings = agent_settings

        # create embedding model
        #self.embed_model = embedding_model(agent_state.embedding_config)
        #self.embedding_chunk_size = agent_state.embedding_config.embedding_chunk_size

        # create storage backend
        self.storage = StorageConnector.get_short_memory_storage_connector(user_id=agent_settings.user_id, agent_id=agent_settings.id)
        # TODO: have some mechanism for cleanup otherwise will lead to OOM
        self.cache = {}

    def get_all(self, start=0, count=None):
        results = self.storage.get_all(start, count)
        results_json = [message for message in results]
        return results_json, len(results)

    def text_search(self, query_string, count=None, start=None):
        results = self.storage.query_text(query_string, count, start)
        results_json = [message for message in results]
        return results_json, len(results)

    def date_search(self, start_date, end_date, count=None, start=None):
        results = self.storage.query_date(start_date, end_date, count, start)
        results_json = [message for message in results]
        return results_json, len(results)

    def __repr__(self) -> str:
        total = self.storage.size()
        system_count = self.storage.size(filters={"role": "system"})
        user_count = self.storage.size(filters={"role": "user"})
        assistant_count = self.storage.size(filters={"role": "assistant"})
        function_count = self.storage.size(filters={"role": "function"})
        other_count = total - (system_count + user_count + assistant_count + function_count)

        memory_str = (
            f"Statistics:"
            + f"\n{total} total messages"
            + f"\n{system_count} system"
            + f"\n{user_count} user"
            + f"\n{assistant_count} assistant"
            + f"\n{function_count} function"
            + f"\n{other_count} other"
        )
        return f"\n### RECALL MEMORY ###" + f"\n{memory_str}"

    def insert(self, message: Passage):
        self.storage.insert(message)

    def insert_many(self, messages: List[Passage]):
        self.storage.insert_many(messages)

    def save(self):
        self.storage.save()

    def __len__(self):
        return self.storage.size()