import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
from pydantic import BaseModel


@dataclass
class MemoryConfiguration(BaseModel):
    long_memory_storage_type: str = "chroma"
    long_memory_storage_path: str = os.path.join(os.getcwd(), "long_memory")
    long_memory_storage_uri: str = None

    short_memory_storage_type: str = "sqlite"
    short_memory_storage_path: str = os.path.join(os.getcwd(), "short_memory")
    short_memory_storage_uri: str = None


class TableType:
    LONG_MEMORY = "long_memory"
    SHORT_MEMORY = "short_memory"


def create_uuid_from_string(val: str):
    """
    Generate consistent UUID from a string
    from: https://samos-it.com/posts/python-create-uuid-from-random-string-of-words.html
    """
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return uuid.UUID(hex=hex_string)


class Passage:
    def __init__(
        self,
        text: str,
        embedding: Optional[np.ndarray] = None,
        embedding_dim: Optional[int] = None,
        data_source: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
        created_at: Optional[datetime] = None,
    ):
        if id is None:
            self.id = create_uuid_from_string(text)

        self.text = text
        self.embedding = embedding
        self.embedding_dim = embedding_dim
        self.data_source = data_source
        self.metadata = metadata
        self.created_at = created_at if created_at else datetime.now()
