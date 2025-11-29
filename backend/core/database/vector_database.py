import shutil

import chromadb

from core.database.base import DatabaseInterface
from core.resource.model_providers.schema import (
    EmbeddingModelProvider,
    EmbeddingModelResponse,
)


class VectorDatabase:
    def __init__(self, llm_provider, database, db_path, user_id, session_id):
        self.db_path = db_path
        self.user_id = user_id
        self.session_id = session_id
        self.database: DatabaseInterface = database
        self.llm_provider: EmbeddingModelProvider = llm_provider
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)

        # Get the list of existing collections
        existing_collections = self.chroma_client.list_collections()

        # Check if collection with user_id exists
        collection_names = [col.name for col in existing_collections]
        print(f"Existing collections: {collection_names}")
        if user_id in collection_names:
            self.collection = self.chroma_client.get_collection(name=user_id)
            print(f"Loaded existing collection for user: {user_id}")
        else:
            self.collection = self.chroma_client.get_or_create_collection(
                name=user_id, metadata={"hnsw:space": "cosine"}
            )

        # # Fetch all document IDs
        # all_docs = self.collection.get()
        # all_ids = all_docs["ids"]

        # #Ensure the collection is not empty before deleting
        # if all_ids:
        #     self.collection.delete(ids=all_ids)
        #     print("All documents deleted from the collection ✅")
        # else:
        #     print("Collection is already empty ✅")

        self.counter = 0

    def parse_and_process_embedding_model(self, response):
        print("Embedding length:", len(response))
        return response

    async def embed_text(self, text):
        response: EmbeddingModelResponse = await self.llm_provider.create_embedding(
            text=text,
            model_name="text-embedding-ada-002",
            embedding_parser=lambda r: self.parse_and_process_embedding_model(r),
        )
        return response.embedding

    async def add_to_vector_database(self, chatmessage):
        speaker = chatmessage["speaker"]
        message = chatmessage["content"]
        # create id
        id = f"{speaker}_{(self.counter)}"
        embedding = await self.embed_text(message)
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[
                {
                    "speaker": speaker,
                    "turn_index": self.counter,
                }
            ],
            documents=[message],
        )
        self.counter += 1

    async def query_vector_database(self, query: str):
        query_embedding = await self.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=1, where={"speaker": "Soumil Chugh"}
        )

        # for i, doc in enumerate(results['documents'][0]):
        #     print ("Rank: ", i+1)
        #     print ("doc: ", doc)

        return results

    def get_neighbours(self, center_index: int):
        window = 2
        neighbor_indices = list(
            range(center_index - window, center_index + window + 1)
        )  # [14, 15, 16, 17, 18]

        results = self.collection.get(
            where={"turn_index": {"$in": neighbor_indices}}, include=["documents", "metadatas"]
        )

        sorted_results = sorted(
            zip(results["metadatas"], results["documents"]), key=lambda x: x[0]["turn_index"]
        )

        return sorted_results

    async def upload_to_firebase(self):
        zip_file_path = "chroma_db.zip"
        shutil.make_archive(zip_file_path, "zip", self.db_path)
        await self.database.upload_file(self.user_id, self.session_id, zip_file_path)
        shutil.rmtree(self.db_path)
        print("Database uploaded successfully")
