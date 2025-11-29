from memory.base import MemoryConfiguration, TableType, Passage
from memory.storage_connector import StorageConnector
import numpy as np
from datetime import datetime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    LargeBinary
)
Base = declarative_base()

def get_db_model(
    config: MemoryConfiguration,
    table_name: str,
    table_type: TableType
):
    
    def create_or_get_model(class_name, base_model, table_name):
        if class_name in globals():
            return globals()[class_name]
        
        Model = type(class_name, (base_model,), {"__tablename__": table_name, "__table_args__": {"extend_existing": True}})
        globals()[class_name] = Model
        return Model
    
    class PassageModel(Base):
        id = Column(String)
        text= Column(String)
        data_source = Column(String)
        metadata = Column(String)
        created_at = Column(DateTime(timezone=True))

        def __repr__(self):
            return f"<PassageModel(id={self.id}, text={self.text})>"

        def to_record(self):
            return Passage(
                text=self.text,
                data_source=self.data_source,
                metadata=self.metadata,
                created_at=self.created_at
            )
    class_name = f"{table_name.capitalize()}PassageModel"
    return create_or_get_model(class_name, PassageModel, table_name)


class SqliteStorageConnector(StorageConnector):

    def __init__(self, table_type, config, user_id, agent_id=None):
        super().__init__(table_type, config, user_id, agent_id)
        self.config = config
        self.db_model = get_db_model(config, self.table_name, table_type, user_id, agent_id)
        self.session_maker = sessionmaker()

    def get_filters(self):
        filter_conditions = self.filters 

        all_filters = [getattr(self.db_model, key) == value for key, value in filter_conditions.items()]

        return all_filters
    

    def get(self, id):
        with self.session_maker() as session:
            record = session.query(self.db_model).filter_by(id=id).first()
            return record.to_record() if record else None
        
    def insert(self, passage: Passage):
        with self.session_maker() as session:
            record = self.db_model(
                id=passage.id,
                text=passage.text,
                data_source=passage.data_source,
                metadata=passage.metadata,
                created_at=datetime.now()
            )
            session.add(record)
            session.commit()
            return record.to_record()
        
    def get_all(self):
        with self.session_maker() as session:
            records = session.query(self.db_model).all()
            return [record.to_record() for record in records]
        
    def insert_many(self, passages):
        with self.session_maker() as session:
            records = [
                self.db_model(
                    id=passage.id,
                    text=passage.text,
                    data_source=passage.data_source,
                    metadata=passage.metadata,
                    created_at=datetime.now()
                )
                for passage in passages
            ]
            session.add_all(records)
            session.commit()
            return [record.to_record() for record in records]
        

    def query_date(self, start_date, end_date, filters):
        with self.session_maker() as session:
            all_filters = self.get_filters()
            all_filters.append(self.db_model.created_at >= start_date)
            all_filters.append(self.db_model.created_at <= end_date)
            records = session.query(self.db_model).filter(*all_filters).all()
            return [record.to_record() for record in records]
        
    def query(self, query: str, query_vec, top_k, filters):
        pass
    
    def query_text(self, query):
        with self.session_maker() as session:
            all_filters = self.get_filters()
            all_filters.append(self.db_model.text.like(f"%{query}%"))
            records = session.query(self.db_model).filter(*all_filters).all()
            return [record.to_record() for record in records]


    def delete(self, id):
        with self.session_maker() as session:
            record = session.query(self.db_model).filter_by(id=id).first()
            session.delete(record)
            session.commit()
            return record.to_record() if record else None
        
    def delete_all(self):
        with self.session_maker() as session:
            session.query(self.db_model).delete()
            session.commit()
