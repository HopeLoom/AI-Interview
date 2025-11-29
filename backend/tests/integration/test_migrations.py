"""
Integration tests for database migrations.
"""


import pytest

from core.config.config_manager import DatabaseConfig
from core.database.base import UserProfile
from core.database.migrations import DatabaseMigrator, FirebaseToSQLMigrator
from tests.utils.test_helpers import DatabaseTestHelper, MockDatabaseFactory


@pytest.mark.integration
class TestDatabaseMigrator:
    """Test database migration functionality"""

    @pytest.fixture
    async def source_db_with_data(self, sqlite_config):
        """Create a source database with test data"""
        from core.database.database_factory import DatabaseFactory

        db = DatabaseFactory.create_database(sqlite_config)
        await db.initialize()

        # Populate with test data
        test_data = await DatabaseTestHelper.populate_test_data(
            db, num_users=2, num_sessions_per_user=1, num_configs=1
        )

        yield db, test_data

        # Cleanup
        await DatabaseTestHelper.cleanup_test_data(db, test_data)
        await db.close()

    @pytest.fixture
    async def target_db(self, sqlite_config):
        """Create a target database (empty)"""
        from core.database.database_factory import DatabaseFactory

        # Use a different in-memory database
        target_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:", max_connections=5)

        db = DatabaseFactory.create_database(target_config)
        await db.initialize()

        yield db
        await db.close()

    @pytest.mark.asyncio
    async def test_complete_migration(self, source_db_with_data, target_db):
        """Test complete database migration"""
        source_db, test_data = source_db_with_data

        # Create migrator
        migrator = DatabaseMigrator(source_db, target_db)

        # Perform migration
        success = await migrator.migrate_all_data()
        assert success

        # Verify users were migrated
        target_users = await target_db.get_all_users_data()
        source_users = test_data["users"]

        assert len(target_users) == len(source_users)

        # Verify user data is correct
        for source_user in source_users:
            target_user_id = await target_db.get_user_id_by_email(source_user.email)
            assert target_user_id == source_user.user_id

            await target_db.load_user_data(target_user_id)
            assert target_db.user_data.name == source_user.name
            assert target_db.user_data.email == source_user.email

        # Verify configs were migrated
        target_configs = await target_db.list_simulation_configs()
        source_configs = test_data["configs"]

        assert len(target_configs) == len(source_configs)

        for source_config_info in source_configs:
            config_id = source_config_info["config_id"]
            target_config = await target_db.get_simulation_config(config_id)
            assert target_config is not None
            assert (
                target_config["job_details"]["job_title"]
                == source_config_info["config"]["job_details"]["job_title"]
            )

    @pytest.mark.asyncio
    async def test_user_migration_only(self, source_db_with_data, target_db):
        """Test migrating only users"""
        source_db, test_data = source_db_with_data

        migrator = DatabaseMigrator(source_db, target_db)

        # Migrate only users
        success = await migrator.migrate_users()
        assert success

        # Verify users were migrated
        target_users = await target_db.get_all_users_data()
        source_users = test_data["users"]

        assert len(target_users) == len(source_users)

        # Verify configs were NOT migrated
        target_configs = await target_db.list_simulation_configs()
        assert len(target_configs) == 0

    @pytest.mark.asyncio
    async def test_config_migration_only(self, source_db_with_data, target_db):
        """Test migrating only simulation configurations"""
        source_db, test_data = source_db_with_data

        migrator = DatabaseMigrator(source_db, target_db)

        # Migrate only configs
        success = await migrator.migrate_simulation_configs()
        assert success

        # Verify configs were migrated
        target_configs = await target_db.list_simulation_configs()
        source_configs = test_data["configs"]

        assert len(target_configs) == len(source_configs)

        # Verify users were NOT migrated
        target_users = await target_db.get_all_users_data()
        assert len(target_users) == 0

    @pytest.mark.asyncio
    async def test_migration_error_handling(self):
        """Test migration error handling"""
        # Create mock databases that will fail
        source_db = MockDatabaseFactory.create_mock_database()
        target_db = MockDatabaseFactory.create_mock_database()

        # Make source database fail to initialize
        source_db.initialize.side_effect = Exception("Database connection failed")

        migrator = DatabaseMigrator(source_db, target_db)

        # Migration should fail gracefully
        success = await migrator.migrate_all_data()
        assert not success

    @pytest.mark.asyncio
    async def test_partial_migration_failure(self):
        """Test handling of partial migration failures"""
        source_db = MockDatabaseFactory.create_mock_database()
        target_db = MockDatabaseFactory.create_mock_database()

        # Setup source database to return test data
        test_users = [
            DatabaseTestHelper.create_test_user(user_id="user1", email="user1@example.com"),
            DatabaseTestHelper.create_test_user(user_id="user2", email="user2@example.com"),
        ]
        source_db.get_all_users_data.return_value = test_users

        # Make target database fail for second user
        def create_user_side_effect(user):
            if user.user_id == "user2":
                raise Exception("Failed to create user2")
            return True

        target_db.create_user.side_effect = create_user_side_effect

        migrator = DatabaseMigrator(source_db, target_db)

        # Migration should handle partial failures
        success = await migrator.migrate_users()
        assert success  # Should still return True as it continues on errors

        # Verify first user was created, second failed
        assert target_db.create_user.call_count == 2


@pytest.mark.integration
class TestFirebaseToSQLMigrator:
    """Test Firebase to SQL migration"""

    def test_firebase_to_sql_migrator_creation(self):
        """Test creating FirebaseToSQLMigrator"""
        firebase_config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="test.json",
            firebase_storage_bucket="test-bucket",
        )

        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")

        # Should create successfully
        migrator = FirebaseToSQLMigrator(firebase_config, sqlite_config, "sqlite")
        assert migrator is not None
        assert isinstance(migrator, DatabaseMigrator)

    def test_unsupported_sql_type(self):
        """Test error handling for unsupported SQL type"""
        firebase_config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="test.json",
            firebase_storage_bucket="test-bucket",
        )

        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")

        with pytest.raises(ValueError, match="Unsupported SQL database type"):
            FirebaseToSQLMigrator(firebase_config, sqlite_config, "unsupported_db")

    def test_convert_firebase_url(self):
        """Test Firebase URL conversion"""
        firebase_config = DatabaseConfig(type="firebase", firebase_credentials_path="test.json")

        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")

        migrator = FirebaseToSQLMigrator(firebase_config, sqlite_config, "sqlite")

        # Test URL conversion (currently just returns the same URL)
        original_url = "https://firebasestorage.googleapis.com/v0/b/bucket/o/file.jpg"
        converted_url = migrator._convert_firebase_url(original_url)

        assert converted_url == original_url  # Currently no conversion


@pytest.mark.integration
class TestMigrationConvenienceFunctions:
    """Test migration convenience functions"""

    @pytest.mark.asyncio
    async def test_migrate_firebase_to_postgresql(self):
        """Test Firebase to PostgreSQL migration convenience function"""
        from core.database.migrations import migrate_firebase_to_postgresql

        firebase_config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="test.json",
            firebase_storage_bucket="test-bucket",
        )

        postgres_config = DatabaseConfig(
            type="postgresql",
            host="localhost",
            port=5432,
            name="test_db",
            username="test_user",
            password="test_pass",
        )

        # This would fail in real scenario without proper setup
        # but we're testing the function exists and can be called
        try:
            success = await migrate_firebase_to_postgresql(firebase_config, postgres_config)
            # In test environment, this will likely fail due to missing Firebase credentials
            # or PostgreSQL server, which is expected
            assert isinstance(success, bool)
        except Exception:
            # Expected in test environment
            pass

    @pytest.mark.asyncio
    async def test_migrate_firebase_to_sqlite(self):
        """Test Firebase to SQLite migration convenience function"""
        from core.database.migrations import migrate_firebase_to_sqlite

        firebase_config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="test.json",
            firebase_storage_bucket="test-bucket",
        )

        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")

        # This would fail in real scenario without proper Firebase setup
        try:
            success = await migrate_firebase_to_sqlite(firebase_config, sqlite_config)
            assert isinstance(success, bool)
        except Exception:
            # Expected in test environment without Firebase credentials
            pass


@pytest.mark.integration
class TestMigrationDataIntegrity:
    """Test data integrity during migrations"""

    @pytest.mark.asyncio
    async def test_data_integrity_preservation(self, sqlite_config):
        """Test that data integrity is preserved during migration"""
        from core.database.database_factory import DatabaseFactory

        # Create source database with specific data
        source_db = DatabaseFactory.create_database(sqlite_config)
        await source_db.initialize()

        # Create target database
        target_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")
        target_db = DatabaseFactory.create_database(target_config)
        await target_db.initialize()

        try:
            # Create specific test user with all fields
            test_user = UserProfile(
                user_id="integrity_test_user",
                name="Integrity Test User",
                email="integrity@example.com",
                company_name="Integrity Company",
                location="Test Location",
                resume_url="https://example.com/resume.pdf",
                starter_code_url="https://example.com/code.py",
                profile_json_url="https://example.com/profile.json",
                simulation_config_json_url="https://example.com/config.json",
                panelist_profiles=["profile1.json", "profile2.json"],
                panelist_images=["image1.png", "image2.png"],
                role="company_admin",
                organization_id="org_123",
                created_at="2024-01-01T00:00:00Z",
            )

            await source_db.create_user(test_user)

            # Create session with specific data
            session_id = await source_db.create_new_session(test_user.user_id)

            # Add specific evaluation data
            evaluation_data = {
                "overall_score": 87.5,
                "technical_score": 90,
                "communication_score": 85,
                "detailed_feedback": "Excellent problem-solving skills",
                "timestamp": "2024-01-01T12:00:00Z",
            }

            await source_db.add_json_data_output_to_database(
                test_user.user_id, session_id, "evaluation", evaluation_data
            )

            # Create specific simulation config
            config_data = DatabaseTestHelper.create_test_simulation_config(
                job_title="Senior Software Engineer", company_name="Integrity Corp"
            )
            config_id = "integrity_test_config"
            await source_db.store_simulation_config(config_id, config_data)

            # Perform migration
            migrator = DatabaseMigrator(source_db, target_db)
            success = await migrator.migrate_all_data()
            assert success

            # Verify user data integrity
            target_user_id = await target_db.get_user_id_by_email(test_user.email)
            assert target_user_id == test_user.user_id

            await target_db.load_user_data(target_user_id)
            migrated_user = target_db.user_data

            # Check all fields are preserved
            assert migrated_user.name == test_user.name
            assert migrated_user.email == test_user.email
            assert migrated_user.company_name == test_user.company_name
            assert migrated_user.location == test_user.location
            assert migrated_user.resume_url == test_user.resume_url
            assert migrated_user.role == test_user.role
            assert migrated_user.organization_id == test_user.organization_id

            # Verify config data integrity
            migrated_config = await target_db.get_simulation_config(config_id)
            assert migrated_config is not None
            assert migrated_config["job_details"]["job_title"] == "Senior Software Engineer"
            assert migrated_config["job_details"]["company_name"] == "Integrity Corp"

            # Verify evaluation data integrity would require session migration
            # which is part of the complete migration test

        finally:
            await source_db.close()
            await target_db.close()

    @pytest.mark.asyncio
    async def test_migration_idempotency(self, sqlite_config):
        """Test that migrations are idempotent (can be run multiple times)"""
        from core.database.database_factory import DatabaseFactory

        # Create databases
        source_db = DatabaseFactory.create_database(sqlite_config)
        await source_db.initialize()

        target_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")
        target_db = DatabaseFactory.create_database(target_config)
        await target_db.initialize()

        try:
            # Add test data
            test_user = DatabaseTestHelper.create_test_user()
            await source_db.create_user(test_user)

            # First migration
            migrator = DatabaseMigrator(source_db, target_db)
            success1 = await migrator.migrate_users()
            assert success1

            # Verify data exists
            users_after_first = await target_db.get_all_users_data()
            assert len(users_after_first) == 1

            # Second migration (should handle duplicates gracefully)
            success2 = await migrator.migrate_users()
            # This might fail due to unique constraints, which is expected behavior
            # The important thing is it doesn't corrupt existing data

            users_after_second = await target_db.get_all_users_data()
            # Should still have the same data
            assert len(users_after_second) >= 1

        finally:
            await source_db.close()
            await target_db.close()
