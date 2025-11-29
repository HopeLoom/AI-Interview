"""
Example script demonstrating how to use the new database abstraction layer.
This shows how to initialize and use different database backends.

Run with: python -m tests.examples.database_examples
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from core.config.config_manager import ConfigManager, DatabaseConfig
from core.database.database_factory import DatabaseFactory, initialize_database


async def example_firebase_usage():
    """Example of using Firebase database"""
    print("\n=== Firebase Database Example ===")

    # Create Firebase configuration
    firebase_config = DatabaseConfig(
        type="firebase",
        firebase_credentials_path="interview-simulation-firebase.json",
        firebase_storage_bucket="interview-simulation-c96c7.firebasestorage.app",
    )

    # Create database instance
    db = DatabaseFactory.create_database(firebase_config)

    try:
        # Initialize database
        await db.initialize()
        print("✅ Firebase database initialized")

        # Example: Get user by email
        user_id = await db.get_user_id_by_email("test@example.com")
        if user_id:
            print(f"✅ Found user: {user_id}")

            # Load user data
            success = await db.load_user_data(user_id)
            if success:
                print(f"✅ Loaded user data: {db.user_data.name}")
        else:
            print("ℹ️  User not found")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db.close()


async def example_postgresql_usage():
    """Example of using PostgreSQL database"""
    print("\n=== PostgreSQL Database Example ===")

    # Create PostgreSQL configuration
    postgres_config = DatabaseConfig(
        type="postgresql",
        host=os.getenv("TEST_POSTGRES_HOST", "localhost"),
        port=int(os.getenv("TEST_POSTGRES_PORT", "5432")),
        name=os.getenv("TEST_POSTGRES_DB", "interview_sim_test"),
        username=os.getenv("TEST_POSTGRES_USER", "interview_user"),
        password=os.getenv("TEST_POSTGRES_PASSWORD", "password123"),
        max_connections=10,
    )

    # Create database instance
    db = DatabaseFactory.create_database(postgres_config)

    try:
        # Initialize database
        await db.initialize()
        print("✅ PostgreSQL database initialized")

        # Example: Create a test user
        from core.database.base import UserProfile

        test_user = UserProfile(
            user_id="test_user_123",
            name="Test User",
            email="testuser@example.com",
            company_name="Test Company",
            location="Test City",
            role="candidate",
        )

        success = await db.create_user(test_user)
        if success:
            print("✅ Test user created")

            # Load the user back
            loaded = await db.load_user_data(test_user.user_id)
            if loaded:
                print(f"✅ Loaded user: {db.user_data.name}")

                # Clean up test user
                await db.delete_user(test_user.user_id)
                print("✅ Test user cleaned up")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db.close()


async def example_sqlite_usage():
    """Example of using SQLite database"""
    print("\n=== SQLite Database Example ===")

    # Create SQLite configuration
    sqlite_config = DatabaseConfig(type="sqlite", sqlite_path="./data/example.db")

    # Create database instance
    db = DatabaseFactory.create_database(sqlite_config)

    try:
        # Initialize database
        await db.initialize()
        print("✅ SQLite database initialized")

        # Example: Create a test user
        from core.database.base import UserProfile

        test_user = UserProfile(
            user_id="test_user_sqlite",
            name="SQLite Test User",
            email="sqlite@example.com",
            company_name="SQLite Company",
            location="Test City",
            role="candidate",
        )

        # Create user
        success = await db.create_user(test_user)
        if success:
            print("✅ Test user created")

            # Create a session
            session_id = await db.create_new_session(test_user.user_id)
            print(f"✅ Created session: {session_id}")

            # Add some JSON data
            test_data = {"key": "value", "timestamp": "2024-01-01T00:00:00Z"}
            await db.add_json_data_output_to_database(
                test_user.user_id, session_id, "test_data", test_data
            )
            print("✅ Added JSON data")

            # Retrieve the data
            retrieved_data = await db.get_json_data_output_from_database(
                "test_data", test_user.user_id, session_id
            )
            if retrieved_data:
                print(f"✅ Retrieved data: {retrieved_data}")

            # Test simulation config
            config_data = {
                "job_details": {"job_title": "Software Engineer", "company_name": "Test Company"},
                "interview_rounds": [],
            }

            config_id = "test_config_123"
            await db.store_simulation_config(config_id, config_data, test_user.user_id)
            print("✅ Stored simulation config")

            # Retrieve config
            retrieved_config = await db.get_simulation_config(config_id)
            if retrieved_config:
                print(f"✅ Retrieved config: {retrieved_config['job_details']['job_title']}")

            # Clean up
            await db.delete_simulation_config(config_id)
            await db.delete_user(test_user.user_id)
            print("✅ Test data cleaned up")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db.close()


async def example_config_manager_usage():
    """Example of using the configuration manager"""
    print("\n=== Configuration Manager Example ===")

    try:
        # Initialize configuration manager
        config_manager = ConfigManager("./config.yaml")
        config = config_manager.load_config()

        print(f"✅ Loaded configuration for environment: {config.environment}")
        print(f"✅ Database type: {config.database.type}")
        print(f"✅ Number of LLM providers: {len(config.llm_providers)}")

        # Get database configuration
        db_config = config_manager.get_database_config()
        print(f"✅ Database configuration: {db_config.type}")

        # Check feature flags
        practice_mode = config_manager.is_feature_enabled("enable_practice_mode")
        print(f"✅ Practice mode enabled: {practice_mode}")

        # Get enabled LLM providers
        enabled_providers = config_manager.get_enabled_llm_providers()
        print(f"✅ Enabled LLM providers: {[p.name for p in enabled_providers]}")

        # Initialize database using configuration
        db = initialize_database(db_config)
        await db.initialize()
        print("✅ Database initialized from configuration")
        await db.close()

    except FileNotFoundError:
        print("ℹ️  Configuration file not found. Create config.yaml to test this example.")
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_migration():
    """Example of database migration"""
    print("\n=== Database Migration Example ===")

    try:
        from core.database.migrations import migrate_firebase_to_sqlite

        # Source: Firebase
        firebase_config = DatabaseConfig(
            type="firebase",
            firebase_credentials_path="interview-simulation-firebase.json",
            firebase_storage_bucket="interview-simulation-c96c7.firebasestorage.app",
        )

        # Target: SQLite
        sqlite_config = DatabaseConfig(type="sqlite", sqlite_path="./data/migrated.db")

        print("🔄 Starting migration from Firebase to SQLite...")
        success = await migrate_firebase_to_sqlite(firebase_config, sqlite_config)

        if success:
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed")

    except Exception as e:
        print(f"❌ Migration error: {e}")


async def example_comprehensive_workflow():
    """Example of a comprehensive workflow using the database abstraction"""
    print("\n=== Comprehensive Workflow Example ===")

    # Use in-memory SQLite for this example
    sqlite_config = DatabaseConfig(type="sqlite", sqlite_path=":memory:")

    db = DatabaseFactory.create_database(sqlite_config)

    try:
        await db.initialize()
        print("✅ Database initialized")

        # 1. Create a user
        from core.database.base import UserProfile

        user = UserProfile(
            user_id="workflow_user",
            name="Workflow Test User",
            email="workflow@example.com",
            company_name="Workflow Company",
            location="Test Location",
            role="candidate",
        )

        await db.create_user(user)
        print("✅ User created")

        # 2. Create a session
        session_id = await db.create_new_session(user.user_id)
        print(f"✅ Session created: {session_id}")

        # 3. Add interview transcript
        class MockMessage:
            def __init__(self, speaker, content):
                self.speaker = speaker
                self.content = content

        messages = [
            MockMessage("Interviewer", "Hello, please introduce yourself."),
            MockMessage("Candidate", "Hi, I'm a software engineer with 5 years of experience."),
            MockMessage("Interviewer", "Great! Can you tell me about your experience with Python?"),
            MockMessage(
                "Candidate", "I've been using Python for web development and data analysis."
            ),
        ]

        for msg in messages:
            await db.add_dialog_to_database(user.user_id, session_id, msg)
        print("✅ Interview transcript added")

        # 4. Add evaluation data
        evaluation_data = {
            "technical_score": 85,
            "communication_score": 90,
            "overall_feedback": "Strong candidate with good technical skills",
        }

        await db.add_json_data_output_to_database(
            user.user_id, session_id, "evaluation", evaluation_data
        )
        print("✅ Evaluation data added")

        # 5. Retrieve all session data
        all_data = await db.get_all_session_data(user.user_id, session_id)
        print(f"✅ Retrieved session data with {len(all_data)} collections")

        # 6. Update session status
        await db.update_session(user.user_id, session_id, {"status": "completed"})
        print("✅ Session status updated")

        # 7. Create and store simulation config
        config_data = {
            "job_details": {
                "job_title": "Senior Python Developer",
                "company_name": user.company_name,
                "required_skills": ["Python", "Django", "PostgreSQL"],
            },
            "interview_rounds": [
                {
                    "round_name": "Technical Interview",
                    "duration_minutes": 60,
                    "topics": ["Python", "Databases", "System Design"],
                }
            ],
        }

        config_id = f"config_{user.user_id}"
        await db.store_simulation_config(config_id, config_data, user.user_id)
        print("✅ Simulation config stored")

        # 8. List all configs for user
        configs = await db.list_simulation_configs(user.user_id)
        print(f"✅ Found {len(configs)} configurations")

        # 9. Get user statistics
        users = await db.get_all_users_data()
        print(f"✅ Total users in database: {len(users)}")

        print("✅ Comprehensive workflow completed successfully!")

    except Exception as e:
        print(f"❌ Workflow error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await db.close()


async def main():
    """Run all examples"""
    print("🚀 Database Abstraction Layer Examples")
    print("=" * 50)

    # Configuration manager example
    await example_config_manager_usage()

    # SQLite example (most likely to work without external dependencies)
    await example_sqlite_usage()

    # Comprehensive workflow example
    await example_comprehensive_workflow()

    # PostgreSQL example (requires PostgreSQL server)
    if os.getenv("TEST_POSTGRES_AVAILABLE", "").lower() == "true":
        await example_postgresql_usage()
    else:
        print("\nℹ️  PostgreSQL example skipped (set TEST_POSTGRES_AVAILABLE=true to enable)")

    # Firebase example (requires Firebase credentials)
    if os.path.exists("interview-simulation-firebase.json"):
        await example_firebase_usage()
    else:
        print("\nℹ️  Firebase example skipped (Firebase credentials not found)")

    # Migration example (requires both Firebase and target database)
    if os.path.exists("interview-simulation-firebase.json"):
        await example_migration()
    else:
        print("\nℹ️  Migration example skipped (Firebase credentials not found)")

    print("\n✨ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
