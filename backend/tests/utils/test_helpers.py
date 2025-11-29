"""
Test helper utilities and fixtures for the interview simulation backend tests.
"""

import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from core.database.base import DatabaseInterface, SessionData, UserProfile


class DatabaseTestHelper:
    """Helper class for database testing"""

    @staticmethod
    def create_test_user(
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        name: str = "Test User",
        company_name: str = "Test Company",
        location: str = "Test City",
        role: str = "candidate",
    ) -> UserProfile:
        """Create a test user profile"""
        return UserProfile(
            user_id=user_id or f"test_user_{uuid.uuid4().hex[:8]}",
            name=name,
            email=email or f"test{uuid.uuid4().hex[:8]}@example.com",
            company_name=company_name,
            location=location,
            role=role,
            created_at=datetime.now().isoformat(),
        )

    @staticmethod
    def create_test_session(
        user_id: str, session_id: Optional[str] = None, status: str = "active"
    ) -> SessionData:
        """Create a test session"""
        return SessionData(
            session_id=session_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
            user_id=user_id,
            start_time=datetime.now().isoformat(),
            status=status,
            metadata={"test": True},
        )

    @staticmethod
    def create_test_simulation_config(
        job_title: str = "Software Engineer", company_name: str = "Test Company"
    ) -> Dict[str, Any]:
        """Create a test simulation configuration"""
        return {
            "job_details": {
                "job_title": job_title,
                "company_name": company_name,
                "job_description": f"Test job description for {job_title}",
                "required_skills": ["Python", "JavaScript", "SQL"],
                "experience_level": "Mid-level",
                "location": "Remote",
            },
            "interview_rounds": [
                {
                    "round_name": "Technical Round",
                    "duration_minutes": 45,
                    "topics": [
                        {
                            "topic_name": "Algorithms",
                            "subtopics": ["Sorting", "Searching", "Dynamic Programming"],
                            "time_allocation_minutes": 20,
                            "difficulty_level": "Medium",
                        },
                        {
                            "topic_name": "System Design",
                            "subtopics": ["Scalability", "Database Design", "API Design"],
                            "time_allocation_minutes": 25,
                            "difficulty_level": "Hard",
                        },
                    ],
                },
                {
                    "round_name": "Behavioral Round",
                    "duration_minutes": 30,
                    "topics": [
                        {
                            "topic_name": "Leadership",
                            "subtopics": ["Team Management", "Conflict Resolution"],
                            "time_allocation_minutes": 15,
                        },
                        {
                            "topic_name": "Problem Solving",
                            "subtopics": ["Analytical Thinking", "Decision Making"],
                            "time_allocation_minutes": 15,
                        },
                    ],
                },
            ],
            "panelists": [
                {
                    "name": "John Doe",
                    "role": "Senior Engineer",
                    "expertise": ["Algorithms", "System Design"],
                    "experience_years": 8,
                },
                {
                    "name": "Jane Smith",
                    "role": "Engineering Manager",
                    "expertise": ["Leadership", "Team Management"],
                    "experience_years": 10,
                },
            ],
            "evaluation_criteria": [
                {
                    "criterion": "Technical Knowledge",
                    "weight": 0.4,
                    "description": "Understanding of technical concepts and problem-solving ability",
                },
                {
                    "criterion": "Communication",
                    "weight": 0.3,
                    "description": "Clarity of explanation and ability to articulate ideas",
                },
                {
                    "criterion": "Problem Solving",
                    "weight": 0.3,
                    "description": "Approach to solving problems and analytical thinking",
                },
            ],
            "settings": {
                "allow_notes": True,
                "time_limit_strict": False,
                "recording_enabled": True,
                "real_time_feedback": False,
            },
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
        }

    @staticmethod
    async def populate_test_data(
        db: DatabaseInterface,
        num_users: int = 3,
        num_sessions_per_user: int = 2,
        num_configs: int = 2,
    ) -> Dict[str, Any]:
        """Populate database with test data"""
        test_data = {"users": [], "sessions": [], "configs": []}

        # Create users
        for i in range(num_users):
            user = DatabaseTestHelper.create_test_user(
                name=f"Test User {i + 1}",
                email=f"user{i + 1}@example.com",
                company_name=f"Company {i + 1}",
            )
            await db.create_user(user)
            test_data["users"].append(user)

            # Create sessions for each user
            for j in range(num_sessions_per_user):
                session_id = await db.create_new_session(user.user_id)
                session = await db.get_session_data(user.user_id, session_id)
                test_data["sessions"].append(session)

                # Add some sample dialog
                class MockMessage:
                    def __init__(self, speaker, content):
                        self.speaker = speaker
                        self.content = content

                messages = [
                    MockMessage("Interviewer", f"Question {j + 1} for {user.name}"),
                    MockMessage("Candidate", f"Answer {j + 1} from {user.name}"),
                ]

                for msg in messages:
                    await db.add_dialog_to_database(user.user_id, session_id, msg)

                # Add evaluation data
                evaluation_data = {
                    "session_id": session_id,
                    "user_id": user.user_id,
                    "overall_score": 75 + (i * 5) + (j * 2),
                    "technical_score": 80 + (i * 3),
                    "communication_score": 70 + (j * 5),
                    "feedback": f"Good performance in session {j + 1}",
                    "timestamp": datetime.now().isoformat(),
                }

                await db.add_json_data_output_to_database(
                    user.user_id, session_id, "evaluation", evaluation_data
                )

        # Create simulation configs
        for i in range(num_configs):
            config = DatabaseTestHelper.create_test_simulation_config(
                job_title=f"Test Job {i + 1}", company_name=f"Test Company {i + 1}"
            )
            config_id = f"test_config_{i + 1}"

            await db.store_simulation_config(config_id, config)
            test_data["configs"].append({"config_id": config_id, "config": config})

        return test_data

    @staticmethod
    async def cleanup_test_data(db: DatabaseInterface, test_data: Dict[str, Any]):
        """Clean up test data from database"""
        # Clean up users (this should cascade delete sessions)
        for user in test_data.get("users", []):
            try:
                await db.delete_user(user.user_id)
            except Exception:
                pass  # Ignore cleanup errors

        # Clean up configs
        for config_info in test_data.get("configs", []):
            try:
                await db.delete_simulation_config(config_info["config_id"])
            except Exception:
                pass  # Ignore cleanup errors


class ConfigTestHelper:
    """Helper class for configuration testing"""

    @staticmethod
    def create_test_config_data(
        environment: str = "test", database_type: str = "sqlite"
    ) -> Dict[str, Any]:
        """Create test configuration data"""
        return {
            "environment": environment,
            "debug": True,
            "host": "localhost",
            "port": 8000,
            "database": {
                "type": database_type,
                "sqlite_path": ":memory:" if database_type == "sqlite" else None,
                "host": "localhost" if database_type == "postgresql" else None,
                "port": 5432 if database_type == "postgresql" else None,
                "name": "test_db" if database_type == "postgresql" else None,
                "username": "test_user" if database_type == "postgresql" else None,
                "password": "test_pass" if database_type == "postgresql" else None,
                "max_connections": 5,
                "min_connections": 1,
                "connection_timeout": 10,
            },
            "storage": {"type": "local", "local_path": "/tmp/test_storage"},
            "security": {
                "jwt_secret_key": "test-secret-key",
                "jwt_algorithm": "HS256",
                "jwt_expiration_hours": 24,
                "cors_origins": ["http://localhost:3000"],
                "rate_limit_per_minute": 100,
                "max_file_size_mb": 10,
            },
            "email": {
                "provider": "sendgrid",
                "from_email": "test@example.com",
                "api_key": "test-api-key",
                "recipients": ["admin@example.com"],
            },
            "speech": {
                "tts_provider": "openai",
                "stt_provider": "openai",
                "tts_url": "https://api.openai.com/v1/audio/speech",
            },
            "llm_providers": [
                {"name": "openai", "api_key": "test-openai-key", "model": "gpt-4", "enabled": True},
                {"name": "deepseek", "api_key": "test-deepseek-key", "enabled": True},
            ],
            "features": {
                "enable_practice_mode": True,
                "enable_company_mode": True,
                "enable_video_recording": False,
                "enable_real_time_evaluation": True,
                "enable_batch_operations": True,
            },
            "log_level": "DEBUG",
        }

    @staticmethod
    def create_temp_config_file(config_data: Dict[str, Any], file_format: str = "yaml") -> Path:
        """Create a temporary configuration file"""
        import json

        import yaml

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=f".{file_format}", delete=False)

        if file_format == "yaml":
            yaml.dump(config_data, temp_file)
        elif file_format == "json":
            json.dump(config_data, temp_file, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        temp_file.close()
        return Path(temp_file.name)


class MockDatabaseFactory:
    """Factory for creating mock database instances"""

    @staticmethod
    def create_mock_database() -> DatabaseInterface:
        """Create a mock database instance"""
        mock_db = MagicMock(spec=DatabaseInterface)

        # Setup async methods
        mock_db.initialize = AsyncMock(return_value=True)
        mock_db.close = AsyncMock()
        mock_db.get_user_id_by_email = AsyncMock(return_value="test_user_id")
        mock_db.load_user_data = AsyncMock(return_value=True)
        mock_db.create_user = AsyncMock(return_value=True)
        mock_db.update_user = AsyncMock(return_value=True)
        mock_db.delete_user = AsyncMock(return_value=True)
        mock_db.get_all_users_data = AsyncMock(return_value=[])
        mock_db.create_new_session = AsyncMock(return_value="test_session_id")
        mock_db.get_session_data = AsyncMock(return_value=None)
        mock_db.update_session = AsyncMock(return_value=True)
        mock_db.get_most_recent_session_id_by_user_id = AsyncMock(return_value="test_session_id")
        mock_db.get_all_session_data = AsyncMock(return_value={})
        mock_db.add_dialog_to_database = AsyncMock()
        mock_db.add_evaluation_output_to_database = AsyncMock()
        mock_db.add_final_evaluation_output_to_database = AsyncMock()
        mock_db.get_final_evaluation_output_from_database = AsyncMock(return_value=None)
        mock_db.store_simulation_config = AsyncMock(return_value=True)
        mock_db.get_simulation_config = AsyncMock(return_value=None)
        mock_db.list_simulation_configs = AsyncMock(return_value=[])
        mock_db.delete_simulation_config = AsyncMock(return_value=True)
        mock_db.add_to_batch = AsyncMock()
        mock_db.commit_batch = AsyncMock(return_value=True)
        mock_db.add_json_data_output_to_database = AsyncMock()
        mock_db.get_json_data_output_from_database = AsyncMock(return_value=None)

        # Setup properties
        mock_db.user_data = None
        mock_db.session_id = None
        mock_db.pending_batch_operations = []
        mock_db.batch_size_limit = 5

        return mock_db


class TestDataGenerator:
    """Generate test data for various scenarios"""

    @staticmethod
    def generate_interview_transcript(
        num_exchanges: int = 5, speakers: List[str] = None
    ) -> List[Dict[str, str]]:
        """Generate a mock interview transcript"""
        if speakers is None:
            speakers = ["Interviewer", "Candidate"]

        transcript = []
        questions = [
            "Can you tell me about yourself?",
            "What's your experience with Python?",
            "How would you design a scalable web application?",
            "Describe a challenging project you worked on.",
            "Do you have any questions for us?",
        ]

        answers = [
            "I'm a software engineer with 5 years of experience...",
            "I've been working with Python for 4 years in web development...",
            "I would start by considering the expected load and user base...",
            "One challenging project was building a real-time analytics dashboard...",
            "Yes, what does the team structure look like?",
        ]

        for i in range(min(num_exchanges, len(questions))):
            transcript.extend(
                [
                    {"speaker": speakers[0], "dialog": questions[i]},
                    {"speaker": speakers[1], "dialog": answers[i]},
                ]
            )

        return transcript

    @staticmethod
    def generate_evaluation_data(
        user_id: str, session_id: str, overall_score: int = None
    ) -> Dict[str, Any]:
        """Generate mock evaluation data"""
        import random

        if overall_score is None:
            overall_score = random.randint(60, 95)

        return {
            "user_id": user_id,
            "session_id": session_id,
            "overall_score": overall_score,
            "criteria_scores": {
                "technical_knowledge": random.randint(70, 100),
                "communication": random.randint(60, 90),
                "problem_solving": random.randint(65, 95),
                "cultural_fit": random.randint(70, 90),
            },
            "feedback": {
                "strengths": [
                    "Strong technical background",
                    "Clear communication",
                    "Good problem-solving approach",
                ],
                "areas_for_improvement": [
                    "Could provide more specific examples",
                    "Time management during coding exercises",
                ],
                "overall_feedback": f"Solid candidate with a score of {overall_score}. Shows good potential.",
            },
            "recommendations": {
                "hire": overall_score >= 80,
                "next_round": overall_score >= 70,
                "rejection_reason": "Below threshold" if overall_score < 70 else None,
            },
            "timestamp": datetime.now().isoformat(),
            "evaluator": "AI System",
        }
