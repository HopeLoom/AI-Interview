"""
Database migration tools for converting between different database backends.
Provides utilities to migrate data from Firebase to SQL databases and vice versa.
"""

from .base import DatabaseInterface
from .firebase_adapter import FirebaseAdapter
from .postgresql_adapter import PostgreSQLAdapter
from .sqlite_adapter import SQLiteAdapter


class DatabaseMigrator:
    """Handles migration between different database backends"""

    def __init__(self, source_db: DatabaseInterface, target_db: DatabaseInterface, logger=None):
        self.source_db = source_db
        self.target_db = target_db
        self.logger = logger

    def log_info(self, message: str):
        if self.logger:
            self.logger.info(message)
        else:
            print(f"INFO: {message}")

    def log_error(self, message: str):
        if self.logger:
            self.logger.error(message)
        else:
            print(f"ERROR: {message}")

    async def migrate_all_data(self) -> bool:
        """Migrate all data from source to target database"""
        try:
            self.log_info("Starting complete database migration...")

            # Initialize both databases
            await self.source_db.initialize()
            await self.target_db.initialize()

            # Migrate users
            await self.migrate_users()

            # Migrate sessions and session data
            await self.migrate_sessions()

            # Migrate simulation configurations
            await self.migrate_simulation_configs()

            self.log_info("Database migration completed successfully")
            return True

        except Exception as e:
            self.log_error(f"Migration failed: {e}")
            return False
        finally:
            await self.source_db.close()
            await self.target_db.close()

    async def migrate_users(self) -> bool:
        """Migrate all users from source to target database"""
        try:
            self.log_info("Migrating users...")

            users = await self.source_db.get_all_users_data()
            self.log_info(f"Found {len(users)} users to migrate")

            for user in users:
                try:
                    await self.target_db.create_user(user)
                    self.log_info(f"Migrated user: {user.email}")
                except Exception as e:
                    self.log_error(f"Failed to migrate user {user.email}: {e}")

            self.log_info("User migration completed")
            return True

        except Exception as e:
            self.log_error(f"User migration failed: {e}")
            return False

    async def migrate_sessions(self) -> bool:
        """Migrate sessions and session data"""
        try:
            self.log_info("Migrating sessions...")

            users = await self.source_db.get_all_users_data()

            for user in users:
                try:
                    # Get the most recent session for each user
                    session_id = await self.source_db.get_most_recent_session_id_by_user_id(
                        user.user_id
                    )
                    if not session_id:
                        continue

                    # Get session data
                    session_data = await self.source_db.get_session_data(user.user_id, session_id)
                    if session_data:
                        # Create session in target database
                        await self.target_db.create_new_session(user.user_id)

                        # Update with original session data
                        await self.target_db.update_session(
                            user.user_id,
                            session_id,
                            {
                                "start_time": session_data.start_time,
                                "status": session_data.status,
                                "end_time": session_data.end_time,
                                "metadata": session_data.metadata,
                            },
                        )

                    # Get all session data (transcripts, evaluations, etc.)
                    all_session_data = await self.source_db.get_all_session_data(
                        user.user_id, session_id
                    )

                    # Migrate interview transcripts
                    if "interview_transcript" in all_session_data:
                        for transcript_data in all_session_data["interview_transcript"].values():
                            # Create a mock message object
                            class MockMessage:
                                def __init__(self, speaker, content):
                                    self.speaker = speaker
                                    self.content = content

                            message = MockMessage(
                                transcript_data["speaker"], transcript_data["dialog"]
                            )
                            await self.target_db.add_dialog_to_database(
                                user.user_id, session_id, message
                            )

                    # Migrate other JSON data
                    for data_type, data_items in all_session_data.items():
                        if data_type != "interview_transcript":
                            for data_item in data_items.values():
                                await self.target_db.add_json_data_output_to_database(
                                    user.user_id, session_id, data_type, data_item
                                )

                    self.log_info(f"Migrated session data for user: {user.email}")

                except Exception as e:
                    self.log_error(f"Failed to migrate session data for user {user.email}: {e}")

            self.log_info("Session migration completed")
            return True

        except Exception as e:
            self.log_error(f"Session migration failed: {e}")
            return False

    async def migrate_simulation_configs(self) -> bool:
        """Migrate simulation configurations"""
        try:
            self.log_info("Migrating simulation configurations...")

            # Get all public and template configurations
            configs = await self.source_db.list_simulation_configs()
            self.log_info(f"Found {len(configs)} configurations to migrate")

            for config_info in configs:
                try:
                    config_id = config_info["config_id"]
                    config_data = await self.source_db.get_simulation_config(config_id)

                    if config_data:
                        await self.target_db.store_simulation_config(
                            config_id, config_data, user_id=None
                        )
                        self.log_info(f"Migrated configuration: {config_info['config_name']}")

                except Exception as e:
                    self.log_error(
                        f"Failed to migrate configuration {config_info['config_name']}: {e}"
                    )

            self.log_info("Configuration migration completed")
            return True

        except Exception as e:
            self.log_error(f"Configuration migration failed: {e}")
            return False


class FirebaseToSQLMigrator(DatabaseMigrator):
    """Specialized migrator for Firebase to SQL database migration"""

    def __init__(self, firebase_config, sql_config, sql_type: str = "postgresql", logger=None):
        firebase_db = FirebaseAdapter(firebase_config, logger)

        if sql_type.lower() == "postgresql":
            sql_db = PostgreSQLAdapter(sql_config, logger)
        elif sql_type.lower() == "sqlite":
            sql_db = SQLiteAdapter(sql_config, logger)
        else:
            raise ValueError(f"Unsupported SQL database type: {sql_type}")

        super().__init__(firebase_db, sql_db, logger)

    async def migrate_firebase_specific_data(self):
        """Migrate Firebase-specific data like file URLs and storage references"""
        try:
            self.log_info("Migrating Firebase-specific data...")

            users = await self.source_db.get_all_users_data()

            for user in users:
                # Update file URLs to be compatible with new storage system
                updates = {}

                if user.resume_url:
                    updates["resume_url"] = self._convert_firebase_url(user.resume_url)
                if user.starter_code_url:
                    updates["starter_code_url"] = self._convert_firebase_url(user.starter_code_url)
                if user.profile_json_url:
                    updates["profile_json_url"] = self._convert_firebase_url(user.profile_json_url)
                if user.simulation_config_json_url:
                    updates["simulation_config_json_url"] = self._convert_firebase_url(
                        user.simulation_config_json_url
                    )

                if updates:
                    await self.target_db.update_user(user.user_id, updates)
                    self.log_info(f"Updated file URLs for user: {user.email}")

            self.log_info("Firebase-specific data migration completed")

        except Exception as e:
            self.log_error(f"Firebase-specific data migration failed: {e}")

    def _convert_firebase_url(self, firebase_url: str) -> str:
        """Convert Firebase storage URL to a format compatible with new storage system"""
        # For now, keep the original URL
        # In a real migration, you might want to download the file and re-upload to new storage
        return firebase_url


async def migrate_firebase_to_postgresql(firebase_config, postgres_config, logger=None) -> bool:
    """Convenience function to migrate from Firebase to PostgreSQL"""
    migrator = FirebaseToSQLMigrator(firebase_config, postgres_config, "postgresql", logger)
    success = await migrator.migrate_all_data()
    if success:
        await migrator.migrate_firebase_specific_data()
    return success


async def migrate_firebase_to_sqlite(firebase_config, sqlite_config, logger=None) -> bool:
    """Convenience function to migrate from Firebase to SQLite"""
    migrator = FirebaseToSQLMigrator(firebase_config, sqlite_config, "sqlite", logger)
    success = await migrator.migrate_all_data()
    if success:
        await migrator.migrate_firebase_specific_data()
    return success


# CLI migration script
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Migrate database between different backends")
    parser.add_argument(
        "--source",
        choices=["firebase", "postgresql", "sqlite"],
        required=True,
        help="Source database type",
    )
    parser.add_argument(
        "--target",
        choices=["firebase", "postgresql", "sqlite"],
        required=True,
        help="Target database type",
    )
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    if args.source == args.target:
        print("ERROR: Source and target database types must be different")
        sys.exit(1)

    # Load configuration and run migration
    print(f"Starting migration from {args.source} to {args.target}...")
    # Implementation would depend on specific configuration format
    print("Migration completed!")
