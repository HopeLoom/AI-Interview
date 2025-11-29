from abc import abstractmethod

from core.memory.base import MemoryConfiguration, Passage, TableType


class StorageConnector:
    def __init__(self, table_type: str, config: MemoryConfiguration, user_id, agent_id=None):
        self.table_type = table_type
        self.config = config
        self.user_id = user_id

        if table_type == TableType.LONG_MEMORY:
            self.table_name = "long_memory_agent"
            self.type = Passage

        elif table_type == TableType.SHORT_MEMORY:
            self.table_name = "short_memory_agent"
            self.type = Passage

        self.filters = {"user_id": self.user_id, "agent_id": agent_id}

    @staticmethod
    def get_storage_connector(table_type: str, config: MemoryConfiguration, user_id, agent_id=None):
        if table_type == TableType.LONG_MEMORY:
            storage_type = config.long_memory_type
        elif table_type == TableType.SHORT_MEMORY:
            storage_type = config.short_memory_type

        if storage_type == "chroma":
            from core.memory.chroma import ChromaStorageConnector

            return ChromaStorageConnector(table_type, config, user_id, agent_id)
        elif storage_type == "sqlite":
            from core.memory.db import SqliteStorageConnector

            return SqliteStorageConnector(table_type, config, user_id, agent_id)

    @staticmethod
    def get_long_memory_storage_connector(config: MemoryConfiguration, user_id, agent_id=None):
        return StorageConnector.get_storage_connector(
            TableType.LONG_MEMORY, config, user_id, agent_id
        )

    @staticmethod
    def get_short_memory_storage_connector(config: MemoryConfiguration, user_id, agent_id=None):
        return StorageConnector.get_storage_connector(
            TableType.SHORT_MEMORY, config, user_id, agent_id
        )

    @abstractmethod
    def get(self, id):
        pass

    @abstractmethod
    def insert(self, passage: Passage):
        pass

    @abstractmethod
    def insert_many(self, passages):
        pass

    @abstractmethod
    def query(self, query, query_vec, top_k, filters):
        pass

    @abstractmethod
    def query_text(self, query):
        pass

    @abstractmethod
    def delete(self, id):
        pass

    @abstractmethod
    def save(self):
        pass
