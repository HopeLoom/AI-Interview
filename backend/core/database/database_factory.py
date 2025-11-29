"""
Database factory for creating database instances based on configuration.
Provides a unified way to instantiate different database adapters.
"""

from typing import Optional
from .base import DatabaseInterface, DatabaseType
from .firebase_adapter import FirebaseAdapter
from .postgresql_adapter import PostgreSQLAdapter
from .sqlite_adapter import SQLiteAdapter


class DatabaseFactory:
    """Factory class for creating database instances"""
    
    @staticmethod
    def create_database(config, logger=None) -> DatabaseInterface:
        """
        Create a database instance based on the configuration
        
        Args:
            config: Database configuration object
            logger: Optional logger instance
            
        Returns:
            DatabaseInterface: Database instance
            
        Raises:
            ValueError: If database type is not supported
        """
        db_type = config.type.lower()
        
        if db_type == DatabaseType.FIREBASE.value:
            return FirebaseAdapter(config, logger)
        elif db_type == DatabaseType.POSTGRESQL.value:
            return PostgreSQLAdapter(config, logger)
        elif db_type == DatabaseType.SQLITE.value:
            return SQLiteAdapter(config, logger)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def get_supported_databases():
        """Get list of supported database types"""
        return [db_type.value for db_type in DatabaseType]


# Global database instance
_database_instance: Optional[DatabaseInterface] = None


def get_database() -> Optional[DatabaseInterface]:
    """Get the global database instance"""
    return _database_instance


def set_database(database: DatabaseInterface):
    """Set the global database instance"""
    global _database_instance
    _database_instance = database


def initialize_database(config, logger=None) -> DatabaseInterface:
    """
    Initialize and return a database instance
    
    Args:
        config: Database configuration
        logger: Optional logger
        
    Returns:
        DatabaseInterface: Initialized database instance
    """
    database = DatabaseFactory.create_database(config, logger)
    set_database(database)
    return database
