from typing import List

import chromadb

from core.memory.base import Passage
from core.memory.storage_connector import StorageConnector


class ChromaStorageConnector(StorageConnector):
    def __init__(self, table_type, config, user_id, agent_id=None):
        super().__init__(table_type, config, user_id, agent_id)
        self.client = chromadb.PersistentClient(config.long_memory_storage_path)
        self.collection = self.client.get_or_create_collection(self.table_name)
        self.include = ["documents", "embeddings", "metadatas"]
        self.uuid_fields = ["ids", "user_id", "agent_id", "source_id", "doc_id"]

    def get_filters(self):
        filter_conditions = self.filters  # this is defined in storage connector
        chroma_filters = []
        ids = []

        for key, value in filter_conditions.items():
            if key == "id":
                ids = [str(value)]
                continue

            if key in self.uuid_fields:
                chroma_filters.append({key: {"$eq": str(value)}})

            else:
                chroma_filters.append({key: {"$eq": value}})

        if len(chroma_filters) > 1:
            chroma_filters = {"$and": chroma_filters}
        elif len(chroma_filters) == 0:
            chroma_filters = {}
        else:
            chroma_filters = chroma_filters[0]

        return ids, chroma_filters

    # Separate our the passage data into the different fields
    def format_records(self, records: List[Passage]):
        recs = []
        ids = []
        documents = []
        embeddings = []

        exist_ids = set()

        for i in range(len(records)):
            record = records[i]
            if record.id in exist_ids:
                continue

            exist_ids.add(record.id)
            ids.append(str(record.id))
            documents.append(record.text)
            embeddings.append(record.embedding)
            recs.append(record)

        metadatas = []
        for record in recs:
            metadata = vars(record)
            metadata.pop("id")
            metadata.pop("text")
            metadata.pop("embedding")

            metadata["created_at"] = metadata["created_at"].isoformat()

            for key, value in metadata.items():
                if key in self.uuid_fields:
                    metadata[key] = str(value)

            metadatas.append(metadata)

        return ids, documents, embeddings, metadatas

    # Insert single record
    def insert(self, record: Passage):
        ids, documents, embeddings, metadatas = self.format_records([record])
        self.collection.upsert(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    # Insert multiple records
    def insert_many(self, records):
        ids, documents, embeddings, metadatas = self.format_records(records)
        self.collection.upsert(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    # delete the record
    def delete_all(self):
        ids, filters = self.get_filters()
        self.collection.delete(ids=ids, where=filters)

    def delete_record(self, record):
        self.collection.delete(ids=[str(record.id)])

    def delete_id(self, id):
        self.collection.delete(ids=[str(id)])

    def delete_table(self):
        self.client.delete_collection(self.collection.name)

    def query(self, query: str, query_vec, top_k: int, filters: dict):
        ids, chroma_filters = self.get_filters()
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=self.include,
            where=chroma_filters,
        )
        return results

    def query_text(self, query: str, top_k: int, filters: dict):
        ids, chroma_filters = self.get_filters()
        results = self.collection.query(
            query_texts=[query], n_results=top_k, include=self.include, where=chroma_filters
        )
        return results
