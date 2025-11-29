"""
PostgreSQL database adapter for the interview simulation platform.
Implements the DatabaseInterface for PostgreSQL backend.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from asyncpg import Connection, Pool

from .base import DatabaseInterface, SessionData, UserProfile


class PostgreSQLAdapter(DatabaseInterface):
    """PostgreSQL implementation of the database interface"""

    def __init__(self, config, logger=None):
        super().__init__(logger)
        self.config = config
        self.pool: Optional[Pool] = None
        self._connection: Optional[Connection] = None

    async def initialize(self) -> bool:
        """Initialize PostgreSQL connection pool"""
        try:
            # Build connection string
            if self.config.connection_string:
                dsn = self.config.connection_string
            else:
                dsn = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.name}"

            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.connection_timeout,
            )

            # Create tables if they don't exist
            await self._create_tables()

            self.log_info("PostgreSQL database initialized successfully")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize PostgreSQL database: {e}")
            return False

    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self.log_info("PostgreSQL database connection closed")

    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    company_name VARCHAR(500),
                    location VARCHAR(500),
                    resume_url TEXT,
                    starter_code_url TEXT,
                    profile_json_url TEXT,
                    simulation_config_json_url TEXT,
                    panelist_profiles JSONB,
                    panelist_images JSONB,
                    role VARCHAR(50) DEFAULT 'candidate',
                    organization_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active',
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            # Interview transcripts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS interview_transcripts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    speaker VARCHAR(255) NOT NULL,
                    dialog TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Evaluation outputs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_outputs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    evaluation_type VARCHAR(100) NOT NULL,
                    evaluation_data JSONB NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Simulation configurations
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_configs (
                    config_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    config_name VARCHAR(500) NOT NULL,
                    config_data JSONB NOT NULL,
                    is_template BOOLEAN DEFAULT FALSE,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)

            # Generic JSON data storage
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS json_data (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    data_name VARCHAR(255) NOT NULL,
                    data_content JSONB NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)

            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transcripts_session ON interview_transcripts(user_id, session_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evaluations_session ON evaluation_outputs(user_id, session_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_json_data_session ON json_data(user_id, session_id, data_name)"
            )

            self.log_info("Database tables created successfully")

    # User Management
    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("SELECT user_id FROM users WHERE email = $1", email)
                return result["user_id"] if result else None
        except Exception as e:
            self.log_error(f"Error getting user ID by email {email}: {e}")
            return None

    async def load_user_data(self, user_id: str) -> bool:
        """Load user profile data"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if result:
                    self.user_data = UserProfile(
                        user_id=result["user_id"],
                        name=result["name"],
                        email=result["email"],
                        company_name=result["company_name"],
                        location=result["location"],
                        resume_url=result["resume_url"],
                        starter_code_url=result["starter_code_url"],
                        profile_json_url=result["profile_json_url"],
                        simulation_config_json_url=result["simulation_config_json_url"],
                        panelist_profiles=result["panelist_profiles"],
                        panelist_images=result["panelist_images"],
                        role=result["role"],
                        organization_id=result["organization_id"],
                        created_at=result["created_at"].isoformat()
                        if result["created_at"]
                        else None,
                    )
                    return True
                return False
        except Exception as e:
            self.log_error(f"Error loading user data for {user_id}: {e}")
            return False

    async def create_user(self, user_profile: UserProfile) -> bool:
        """Create a new user"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (user_id, name, email, company_name, location, 
                                     resume_url, starter_code_url, profile_json_url, 
                                     simulation_config_json_url, panelist_profiles, 
                                     panelist_images, role, organization_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                    user_profile.user_id,
                    user_profile.name,
                    user_profile.email,
                    user_profile.company_name,
                    user_profile.location,
                    user_profile.resume_url,
                    user_profile.starter_code_url,
                    user_profile.profile_json_url,
                    user_profile.simulation_config_json_url,
                    json.dumps(user_profile.panelist_profiles)
                    if user_profile.panelist_profiles
                    else None,
                    json.dumps(user_profile.panelist_images)
                    if user_profile.panelist_images
                    else None,
                    user_profile.role,
                    user_profile.organization_id,
                )
                self.log_info(f"User created successfully: {user_profile.user_id}")
                return True
        except Exception as e:
            self.log_error(f"Error creating user {user_profile.user_id}: {e}")
            return False

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            if not updates:
                return True

            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1

            for key, value in updates.items():
                if key in ["panelist_profiles", "panelist_images"] and value is not None:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1

            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.now())
            param_count += 1

            values.append(user_id)  # For WHERE clause

            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ${param_count}"

            async with self.pool.acquire() as conn:
                await conn.execute(query, *values)
                self.log_info(f"User updated successfully: {user_id}")
                return True
        except Exception as e:
            self.log_error(f"Error updating user {user_id}: {e}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
                self.log_info(f"User deleted successfully: {user_id}")
                return True
        except Exception as e:
            self.log_error(f"Error deleting user {user_id}: {e}")
            return False

    async def get_all_users_data(self) -> List[UserProfile]:
        """Get all user profiles"""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
                users = []
                for result in results:
                    user = UserProfile(
                        user_id=result["user_id"],
                        name=result["name"],
                        email=result["email"],
                        company_name=result["company_name"],
                        location=result["location"],
                        resume_url=result["resume_url"],
                        starter_code_url=result["starter_code_url"],
                        profile_json_url=result["profile_json_url"],
                        simulation_config_json_url=result["simulation_config_json_url"],
                        panelist_profiles=result["panelist_profiles"],
                        panelist_images=result["panelist_images"],
                        role=result["role"],
                        organization_id=result["organization_id"],
                        created_at=result["created_at"].isoformat()
                        if result["created_at"]
                        else None,
                    )
                    users.append(user)
                return users
        except Exception as e:
            self.log_error(f"Error getting all users data: {e}")
            return []

    # Session Management
    async def create_new_session(self, user_id: str) -> str:
        """Create a new session and return session ID"""
        try:
            session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO sessions (session_id, user_id, start_time, status)
                    VALUES ($1, $2, $3, $4)
                """,
                    session_id,
                    user_id,
                    datetime.now(),
                    "active",
                )

            self.session_id = session_id
            self.log_info(f"New session created: {session_id} for user: {user_id}")
            return session_id
        except Exception as e:
            self.log_error(f"Error creating session for user {user_id}: {e}")
            raise

    async def get_session_data(self, user_id: str, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT * FROM sessions WHERE user_id = $1 AND session_id = $2
                """,
                    user_id,
                    session_id,
                )

                if result:
                    return SessionData(
                        session_id=result["session_id"],
                        user_id=result["user_id"],
                        start_time=result["start_time"].isoformat(),
                        status=result["status"],
                        end_time=result["end_time"].isoformat() if result["end_time"] else None,
                        metadata=result["metadata"],
                    )
                return None
        except Exception as e:
            self.log_error(f"Error getting session data for {user_id}/{session_id}: {e}")
            return None

    async def update_session(self, user_id: str, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            if not updates:
                return True

            set_clauses = []
            values = []
            param_count = 1

            for key, value in updates.items():
                if key == "metadata" and value is not None:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1

            values.extend([user_id, session_id])
            query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE user_id = ${param_count} AND session_id = ${param_count + 1}"

            async with self.pool.acquire() as conn:
                await conn.execute(query, *values)
                self.log_info(f"Session updated: {session_id}")
                return True
        except Exception as e:
            self.log_error(f"Error updating session {session_id}: {e}")
            return False

    async def get_most_recent_session_id_by_user_id(self, user_id: str) -> Optional[str]:
        """Get the most recent session ID for a user"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT session_id FROM sessions 
                    WHERE user_id = $1 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """,
                    user_id,
                )
                return result["session_id"] if result else None
        except Exception as e:
            self.log_error(f"Error getting recent session for user {user_id}: {e}")
            return None

    async def get_all_session_data(
        self, user_id: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all data for a session"""
        if not session_id:
            session_id = self.session_id

        if not session_id:
            return {}

        result = {}
        try:
            async with self.pool.acquire() as conn:
                # Get interview transcripts
                transcripts = await conn.fetch(
                    """
                    SELECT speaker, dialog, timestamp FROM interview_transcripts 
                    WHERE user_id = $1 AND session_id = $2 
                    ORDER BY timestamp
                """,
                    user_id,
                    session_id,
                )
                result["interview_transcript"] = {
                    str(i): {"speaker": t["speaker"], "dialog": t["dialog"]}
                    for i, t in enumerate(transcripts)
                }

                # Get evaluation outputs
                evaluations = await conn.fetch(
                    """
                    SELECT evaluation_type, evaluation_data FROM evaluation_outputs 
                    WHERE user_id = $1 AND session_id = $2 
                    ORDER BY timestamp
                """,
                    user_id,
                    session_id,
                )
                for eval_data in evaluations:
                    eval_type = eval_data["evaluation_type"]
                    if eval_type not in result:
                        result[eval_type] = {}
                    result[eval_type][str(len(result[eval_type]))] = eval_data["evaluation_data"]

                # Get JSON data
                json_data = await conn.fetch(
                    """
                    SELECT data_name, data_content FROM json_data 
                    WHERE user_id = $1 AND session_id = $2 
                    ORDER BY timestamp
                """,
                    user_id,
                    session_id,
                )
                for data in json_data:
                    data_name = data["data_name"]
                    if data_name not in result:
                        result[data_name] = {}
                    result[data_name][str(len(result[data_name]))] = data["data_content"]

            return result
        except Exception as e:
            self.log_error(f"Error getting all session data for {user_id}/{session_id}: {e}")
            return {}

    # Interview Data Management
    async def add_dialog_to_database(self, user_id: str, session_id: str, message: Any):
        """Add dialog message to database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO interview_transcripts (user_id, session_id, speaker, dialog)
                    VALUES ($1, $2, $3, $4)
                """,
                    user_id,
                    session_id,
                    message.speaker,
                    message.content,
                )
                self.log_info(f"Dialog added: {message.speaker}")
        except Exception as e:
            self.log_error(f"Error adding dialog: {e}")

    async def add_evaluation_output_to_database(self, user_id: str, session_id: str, output: Any):
        """Add evaluation output to database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO evaluation_outputs (user_id, session_id, evaluation_type, evaluation_data)
                    VALUES ($1, $2, $3, $4)
                """,
                    user_id,
                    session_id,
                    "evaluation_output",
                    output.model_dump(),
                )
                self.log_info("Evaluation output added")
        except Exception as e:
            self.log_error(f"Error adding evaluation output: {e}")

    async def add_final_evaluation_output_to_database(
        self, user_id: str, session_id: str, output: Any
    ):
        """Add final evaluation output to database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO evaluation_outputs (user_id, session_id, evaluation_type, evaluation_data)
                    VALUES ($1, $2, $3, $4)
                """,
                    user_id,
                    session_id,
                    "final_evaluation_output",
                    output.model_dump(),
                )
                self.log_info("Final evaluation output added")
        except Exception as e:
            self.log_error(f"Error adding final evaluation output: {e}")

    async def get_final_evaluation_output_from_database(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get final evaluation output from database"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT evaluation_data FROM evaluation_outputs 
                    WHERE user_id = $1 AND session_id = $2 AND evaluation_type = $3
                    ORDER BY timestamp DESC LIMIT 1
                """,
                    user_id,
                    session_id,
                    "final_evaluation_output",
                )
                return result["evaluation_data"] if result else None
        except Exception as e:
            self.log_error(f"Error getting final evaluation output: {e}")
            return None

    # Configuration Management
    async def store_simulation_config(
        self, config_id: str, config_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> bool:
        """Store simulation configuration"""
        try:
            config_name = config_data.get("job_details", {}).get(
                "job_title", "Untitled Configuration"
            )
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO simulation_configs (config_id, user_id, config_name, config_data)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (config_id) 
                    DO UPDATE SET config_data = $4, updated_at = CURRENT_TIMESTAMP
                """,
                    config_id,
                    user_id,
                    config_name,
                    json.dumps(config_data),
                )
                self.log_info(f"Simulation config stored: {config_id}")
                return True
        except Exception as e:
            self.log_error(f"Error storing simulation config {config_id}: {e}")
            return False

    async def get_simulation_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation configuration"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT config_data FROM simulation_configs WHERE config_id = $1
                """,
                    config_id,
                )
                return result["config_data"] if result else None
        except Exception as e:
            self.log_error(f"Error getting simulation config {config_id}: {e}")
            return None

    async def list_simulation_configs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List simulation configurations"""
        try:
            async with self.pool.acquire() as conn:
                if user_id:
                    results = await conn.fetch(
                        """
                        SELECT config_id, config_name, is_template, is_public, created_at, updated_at 
                        FROM simulation_configs 
                        WHERE user_id = $1 OR is_public = TRUE
                        ORDER BY updated_at DESC
                    """,
                        user_id,
                    )
                else:
                    results = await conn.fetch("""
                        SELECT config_id, config_name, is_template, is_public, created_at, updated_at 
                        FROM simulation_configs 
                        WHERE is_public = TRUE OR is_template = TRUE
                        ORDER BY updated_at DESC
                    """)

                configs = []
                for result in results:
                    config = {
                        "config_id": result["config_id"],
                        "config_name": result["config_name"],
                        "is_template": result["is_template"],
                        "is_public": result["is_public"],
                        "created_at": result["created_at"].isoformat()
                        if result["created_at"]
                        else None,
                        "updated_at": result["updated_at"].isoformat()
                        if result["updated_at"]
                        else None,
                    }
                    configs.append(config)
                return configs
        except Exception as e:
            self.log_error(f"Error listing simulation configs: {e}")
            return []

    async def delete_simulation_config(self, config_id: str) -> bool:
        """Delete simulation configuration"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM simulation_configs WHERE config_id = $1", config_id)
                self.log_info(f"Simulation config deleted: {config_id}")
                return True
        except Exception as e:
            self.log_error(f"Error deleting simulation config {config_id}: {e}")
            return False

    # Batch Operations
    async def add_to_batch(
        self, user_id: str, session_id: str, operation_type: str, data: Any, collection_path: str
    ):
        """Add operation to batch queue"""
        self.pending_batch_operations.append(
            {
                "operation_type": operation_type,
                "data": data,
                "collection_path": collection_path,
                "user_id": user_id,
                "session_id": session_id,
            }
        )

        if len(self.pending_batch_operations) >= self.batch_size_limit:
            await self.commit_batch()

    async def commit_batch(self) -> bool:
        """Commit batch operations"""
        if not self.pending_batch_operations:
            return True

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for operation in self.pending_batch_operations:
                        # Map collection_path to appropriate table operation
                        if operation["collection_path"] == "interview_transcript":
                            await conn.execute(
                                """
                                INSERT INTO interview_transcripts (user_id, session_id, speaker, dialog)
                                VALUES ($1, $2, $3, $4)
                            """,
                                operation["user_id"],
                                operation["session_id"],
                                operation["data"].get("speaker"),
                                operation["data"].get("dialog"),
                            )
                        else:
                            # Generic JSON data storage
                            await conn.execute(
                                """
                                INSERT INTO json_data (user_id, session_id, data_name, data_content)
                                VALUES ($1, $2, $3, $4)
                            """,
                                operation["user_id"],
                                operation["session_id"],
                                operation["collection_path"],
                                operation["data"],
                            )

            self.pending_batch_operations = []
            self.log_info("Batch operations committed successfully")
            return True
        except Exception as e:
            self.log_error(f"Error committing batch operations: {e}")
            return False

    # Generic Data Operations
    async def add_json_data_output_to_database(
        self, user_id: str, session_id: str, name: str, json_data: Dict[str, Any]
    ):
        """Add JSON data to database"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO json_data (user_id, session_id, data_name, data_content)
                    VALUES ($1, $2, $3, $4)
                """,
                    user_id,
                    session_id,
                    name,
                    json_data,
                )
                self.log_info(f"JSON data added: {name}")
        except Exception as e:
            self.log_error(f"Error adding JSON data {name}: {e}")

    async def get_json_data_output_from_database(
        self, name: str, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get JSON data from database"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT data_content FROM json_data 
                    WHERE user_id = $1 AND session_id = $2 AND data_name = $3
                    ORDER BY timestamp DESC LIMIT 1
                """,
                    user_id,
                    session_id,
                    name,
                )
                return result["data_content"] if result else None
        except Exception as e:
            self.log_error(f"Error getting JSON data {name}: {e}")
            return None
