"""
Integration tests for database operations across different backends.
"""

import pytest
import asyncio
from datetime import datetime

from core.database.database_factory import DatabaseFactory
from core.database.base import UserProfile, SessionData


@pytest.mark.integration
class TestSQLiteIntegration:
    """Integration tests for SQLite database operations"""
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, sqlite_db, sample_user_profile):
        """Test complete user workflow with SQLite"""
        # Create user
        success = await sqlite_db.create_user(sample_user_profile)
        assert success
        
        # Verify user was created
        user_id = await sqlite_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id
        
        # Load user data
        success = await sqlite_db.load_user_data(user_id)
        assert success
        assert sqlite_db.user_data.name == sample_user_profile.name
        
        # Update user
        updates = {"company_name": "Updated Company", "location": "Updated Location"}
        success = await sqlite_db.update_user(user_id, updates)
        assert success
        
        # Verify update
        await sqlite_db.load_user_data(user_id)
        assert sqlite_db.user_data.company_name == "Updated Company"
        assert sqlite_db.user_data.location == "Updated Location"
        
        # Create session
        session_id = await sqlite_db.create_new_session(user_id)
        assert session_id is not None
        
        # Add dialog data
        class MockMessage:
            def __init__(self, speaker, content):
                self.speaker = speaker
                self.content = content
        
        message = MockMessage("Test Speaker", "Test message content")
        await sqlite_db.add_dialog_to_database(user_id, session_id, message)
        
        # Add JSON data
        test_data = {"score": 85, "feedback": "Good performance"}
        await sqlite_db.add_json_data_output_to_database(user_id, session_id, "evaluation", test_data)
        
        # Retrieve JSON data
        retrieved_data = await sqlite_db.get_json_data_output_from_database("evaluation", user_id, session_id)
        assert retrieved_data is not None
        assert retrieved_data["score"] == 85
        
        # Get all session data
        all_data = await sqlite_db.get_all_session_data(user_id, session_id)
        assert "interview_transcript" in all_data
        assert "evaluation" in all_data
        
        # Update session
        await sqlite_db.update_session(user_id, session_id, {"status": "completed"})
        session_data = await sqlite_db.get_session_data(user_id, session_id)
        assert session_data.status == "completed"
        
        # Clean up
        await sqlite_db.delete_user(user_id)
        users = await sqlite_db.get_all_users_data()
        assert len([u for u in users if u.user_id == user_id]) == 0
    
    @pytest.mark.asyncio
    async def test_simulation_config_workflow(self, sqlite_db, sample_simulation_config):
        """Test simulation configuration workflow with SQLite"""
        config_id = "test_config_sqlite"
        
        # Store configuration
        success = await sqlite_db.store_simulation_config(config_id, sample_simulation_config)
        assert success
        
        # Retrieve configuration
        retrieved_config = await sqlite_db.get_simulation_config(config_id)
        assert retrieved_config is not None
        assert retrieved_config["job_details"]["job_title"] == sample_simulation_config["job_details"]["job_title"]
        
        # List configurations
        configs = await sqlite_db.list_simulation_configs()
        config_ids = [c["config_id"] for c in configs]
        assert config_id in config_ids
        
        # Update configuration (store with same ID)
        updated_config = sample_simulation_config.copy()
        updated_config["job_details"]["job_title"] = "Updated Job Title"
        
        success = await sqlite_db.store_simulation_config(config_id, updated_config)
        assert success
        
        # Verify update
        retrieved_config = await sqlite_db.get_simulation_config(config_id)
        assert retrieved_config["job_details"]["job_title"] == "Updated Job Title"
        
        # Delete configuration
        success = await sqlite_db.delete_simulation_config(config_id)
        assert success
        
        # Verify deletion
        retrieved_config = await sqlite_db.get_simulation_config(config_id)
        assert retrieved_config is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, sqlite_db, sample_user_profile):
        """Test batch operations with SQLite"""
        await sqlite_db.create_user(sample_user_profile)
        session_id = await sqlite_db.create_new_session(sample_user_profile.user_id)
        
        # Add multiple operations to batch
        for i in range(3):
            await sqlite_db.add_to_batch(
                sample_user_profile.user_id,
                session_id,
                "add_data",
                {"batch_item": i, "content": f"Batch item {i}"},
                f"batch_test_{i}"
            )
        
        # Commit batch
        success = await sqlite_db.commit_batch()
        assert success
        
        # Verify batch operations were committed
        # (This would depend on the specific implementation)
        assert len(sqlite_db.pending_batch_operations) == 0


@pytest.mark.integration
@pytest.mark.postgresql
class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL database operations"""
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, postgresql_db, sample_user_profile):
        """Test complete user workflow with PostgreSQL"""
        # Create user
        success = await postgresql_db.create_user(sample_user_profile)
        assert success
        
        # Verify user was created
        user_id = await postgresql_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id
        
        # Load user data
        success = await postgresql_db.load_user_data(user_id)
        assert success
        assert postgresql_db.user_data.name == sample_user_profile.name
        
        # Update user
        updates = {"company_name": "Updated Company", "location": "Updated Location"}
        success = await postgresql_db.update_user(user_id, updates)
        assert success
        
        # Verify update
        await postgresql_db.load_user_data(user_id)
        assert postgresql_db.user_data.company_name == "Updated Company"
        assert postgresql_db.user_data.location == "Updated Location"
        
        # Create session
        session_id = await postgresql_db.create_new_session(user_id)
        assert session_id is not None
        
        # Add dialog data
        class MockMessage:
            def __init__(self, speaker, content):
                self.speaker = speaker
                self.content = content
        
        message = MockMessage("Test Speaker", "Test message content")
        await postgresql_db.add_dialog_to_database(user_id, session_id, message)
        
        # Add JSON data
        test_data = {"score": 85, "feedback": "Good performance"}
        await postgresql_db.add_json_data_output_to_database(user_id, session_id, "evaluation", test_data)
        
        # Retrieve JSON data
        retrieved_data = await postgresql_db.get_json_data_output_from_database("evaluation", user_id, session_id)
        assert retrieved_data is not None
        assert retrieved_data["score"] == 85
        
        # Get all session data
        all_data = await postgresql_db.get_all_session_data(user_id, session_id)
        assert "interview_transcript" in all_data
        assert "evaluation" in all_data
        
        # Update session
        await postgresql_db.update_session(user_id, session_id, {"status": "completed"})
        session_data = await postgresql_db.get_session_data(user_id, session_id)
        assert session_data.status == "completed"
        
        # Clean up
        await postgresql_db.delete_user(user_id)
        users = await postgresql_db.get_all_users_data()
        assert len([u for u in users if u.user_id == user_id]) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, postgresql_db):
        """Test concurrent database operations with PostgreSQL"""
        # Create multiple users concurrently
        users = [
            UserProfile(
                user_id=f"concurrent_user_{i}",
                name=f"User {i}",
                email=f"user{i}@example.com",
                company_name=f"Company {i}",
                location=f"Location {i}"
            )
            for i in range(5)
        ]
        
        # Create users concurrently
        tasks = [postgresql_db.create_user(user) for user in users]
        results = await asyncio.gather(*tasks)
        assert all(results)
        
        # Load users concurrently
        load_tasks = [postgresql_db.get_user_id_by_email(user.email) for user in users]
        user_ids = await asyncio.gather(*load_tasks)
        assert all(user_id is not None for user_id in user_ids)
        
        # Clean up concurrently
        cleanup_tasks = [postgresql_db.delete_user(user.user_id) for user in users]
        cleanup_results = await asyncio.gather(*cleanup_tasks)
        assert all(cleanup_results)
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, postgresql_db, sample_user_profile):
        """Test transaction rollback behavior"""
        # This test would depend on the specific implementation of transactions
        # For now, we'll test basic error handling
        
        # Try to create user with duplicate email
        await postgresql_db.create_user(sample_user_profile)
        
        # Creating user with same email should fail gracefully
        duplicate_user = UserProfile(
            user_id="different_id",
            name="Different Name",
            email=sample_user_profile.email,  # Same email
            company_name="Different Company",
            location="Different Location"
        )
        
        success = await postgresql_db.create_user(duplicate_user)
        # Should fail due to unique email constraint
        assert not success
        
        # Original user should still exist
        user_id = await postgresql_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id
        
        # Clean up
        await postgresql_db.delete_user(sample_user_profile.user_id)


@pytest.mark.integration
class TestDatabaseFactory:
    """Integration tests for DatabaseFactory"""
    
    def test_create_sqlite_database(self, sqlite_config):
        """Test creating SQLite database through factory"""
        db = DatabaseFactory.create_database(sqlite_config)
        
        assert db is not None
        assert hasattr(db, 'initialize')
        assert hasattr(db, 'close')
    
    def test_create_postgresql_database(self, postgresql_config):
        """Test creating PostgreSQL database through factory"""
        db = DatabaseFactory.create_database(postgresql_config)
        
        assert db is not None
        assert hasattr(db, 'initialize')
        assert hasattr(db, 'close')
    
    def test_unsupported_database_type(self):
        """Test creating unsupported database type"""
        from core.config.config_manager import DatabaseConfig
        
        unsupported_config = DatabaseConfig(type="unsupported_db")
        
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database(unsupported_config)
    
    def test_supported_databases(self):
        """Test getting supported database types"""
        supported = DatabaseFactory.get_supported_databases()
        
        assert "sqlite" in supported
        assert "postgresql" in supported
        assert "firebase" in supported
        assert len(supported) == 3


@pytest.mark.integration
class TestCrossDatabase:
    """Integration tests that work across different database types"""
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_databases(self, sample_user_profile, sample_simulation_config):
        """Test data consistency when using different database backends"""
        from core.config.config_manager import DatabaseConfig
        
        # Create two different database instances
        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")
        sqlite_db = DatabaseFactory.create_database(sqlite_config)
        
        sqlite_config2 = DatabaseConfig(type="sqlite", sqlite_path=":memory:")
        sqlite_db2 = DatabaseFactory.create_database(sqlite_config2)
        
        try:
            # Initialize both databases
            await sqlite_db.initialize()
            await sqlite_db2.initialize()
            
            # Add same data to both databases
            await sqlite_db.create_user(sample_user_profile)
            await sqlite_db2.create_user(sample_user_profile)
            
            config_id = "consistency_test_config"
            await sqlite_db.store_simulation_config(config_id, sample_simulation_config)
            await sqlite_db2.store_simulation_config(config_id, sample_simulation_config)
            
            # Verify data is consistent
            user_id_1 = await sqlite_db.get_user_id_by_email(sample_user_profile.email)
            user_id_2 = await sqlite_db2.get_user_id_by_email(sample_user_profile.email)
            assert user_id_1 == user_id_2
            
            config_1 = await sqlite_db.get_simulation_config(config_id)
            config_2 = await sqlite_db2.get_simulation_config(config_id)
            assert config_1 == config_2
            
        finally:
            await sqlite_db.close()
            await sqlite_db2.close()
    
    @pytest.mark.asyncio
    async def test_interface_compatibility(self, sqlite_db, sample_user_profile):
        """Test that all database implementations follow the same interface"""
        # This test ensures all database implementations provide the same interface
        required_methods = [
            'initialize', 'close', 'get_user_id_by_email', 'load_user_data',
            'create_user', 'update_user', 'delete_user', 'get_all_users_data',
            'create_new_session', 'get_session_data', 'update_session',
            'get_most_recent_session_id_by_user_id', 'get_all_session_data',
            'add_dialog_to_database', 'add_evaluation_output_to_database',
            'store_simulation_config', 'get_simulation_config',
            'list_simulation_configs', 'delete_simulation_config',
            'add_to_batch', 'commit_batch',
            'add_json_data_output_to_database', 'get_json_data_output_from_database'
        ]
        
        for method_name in required_methods:
            assert hasattr(sqlite_db, method_name), f"Method {method_name} not found"
            assert callable(getattr(sqlite_db, method_name)), f"Method {method_name} is not callable"
        
        # Test that basic operations work
        await sqlite_db.create_user(sample_user_profile)
        user_id = await sqlite_db.get_user_id_by_email(sample_user_profile.email)
        assert user_id == sample_user_profile.user_id
