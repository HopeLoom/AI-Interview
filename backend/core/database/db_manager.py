"""
Global database manager for the interview simulation platform.
Provides a singleton pattern for database access throughout the application.
"""

from typing import Optional

from core.config.config_manager import get_config
from core.database.base import DatabaseInterface
from core.database.database_factory import initialize_database

# Compatibility wrapper removed - using direct database interface


class DatabaseManager:
    """Singleton database manager"""

    _instance: Optional["DatabaseManager"] = None
    _database: Optional[DatabaseInterface] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, logger=None):
        """Initialize the database connection"""
        if self._database is None:
            try:
                config = get_config()
                self._database = initialize_database(config.database, logger)
                await self._database.initialize()
                if logger:
                    logger.info(f"Database initialized: {config.database.type}")
            except Exception as e:
                if logger:
                    logger.exception(f"Failed to initialize database: {e}")
                # Fallback to Firebase for backward compatibility
                from core.config.config_manager import DatabaseConfig
                from core.database.firebase_adapter import FirebaseAdapter

                firebase_config = DatabaseConfig(
                    type="firebase",
                    firebase_credentials_path="interview-simulation-firebase.json",
                    firebase_storage_bucket="interview-simulation-c96c7.firebasestorage.app",
                )

                self._database = FirebaseAdapter(firebase_config, logger)
                await self._database.initialize()
                if logger:
                    logger.warning("Fell back to Firebase database")

    async def get_database(self, logger=None) -> DatabaseInterface:
        """Get the database instance"""
        if self._database is None:
            await self.initialize(logger)
        return self._database

    async def get_database_with_compatibility(self, logger=None) -> DatabaseInterface:
        """Get the database instance (compatibility wrapper removed)"""
        return await self.get_database(logger)

    async def close(self):
        """Close the database connection"""
        if self._database is not None:
            await self._database.close()
            self._database = None

    def is_initialized(self) -> bool:
        """Check if database is initialized"""
        return self._database is not None


# Global database manager instance
db_manager = DatabaseManager()


async def get_database(logger=None) -> DatabaseInterface:
    """Get the global database instance"""
    return await db_manager.get_database(logger)


async def get_database_with_compatibility(logger=None) -> DatabaseInterface:
    """Get the global database instance with backward compatibility wrapper"""
    return await db_manager.get_database_with_compatibility(logger)


async def initialize_global_database(logger=None):
    """Initialize the global database"""
    await db_manager.initialize(logger)


async def close_global_database():
    """Close the global database"""
    await db_manager.close()
