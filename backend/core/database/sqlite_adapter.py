"""
SQLite database adapter for the interview simulation platform.
Implements the DatabaseInterface for SQLite backend - ideal for local development.
"""

import json
import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import DatabaseInterface, UserProfile, SessionData


class SQLiteAdapter(DatabaseInterface):
    """SQLite implementation of the database interface"""
    
    def __init__(self, config, logger=None):
        super().__init__(logger)
        self.config = config
        self.db_path = config.sqlite_path or "./data/interview_sim.db"
        self._connection = None
    
    async def initialize(self) -> bool:
        """Initialize SQLite database"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create tables if they don't exist
            await self._create_tables()
            
            self.log_info(f"SQLite database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to initialize SQLite database: {e}")
            return False
    
    async def close(self):
        """Close the database connection"""
        if self._connection:
            await self._connection.close()
            self.log_info("SQLite database connection closed")
    
    async def _get_connection(self):
        """Get database connection"""
        return await aiosqlite.connect(self.db_path)
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        async with self._get_connection() as conn:
            # Enable foreign key constraints
            await conn.execute("PRAGMA foreign_keys = ON")
            
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    company_name TEXT,
                    location TEXT,
                    resume_url TEXT,
                    starter_code_url TEXT,
                    profile_json_url TEXT,
                    simulation_config_json_url TEXT,
                    panelist_profiles TEXT,  -- JSON string
                    panelist_images TEXT,    -- JSON string
                    role TEXT DEFAULT 'candidate',
                    organization_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Interview transcripts
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS interview_transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    dialog TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Evaluation outputs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    evaluation_type TEXT NOT NULL,
                    evaluation_data TEXT NOT NULL,  -- JSON string
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Simulation configurations
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS simulation_configs (
                    config_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    config_name TEXT NOT NULL,
                    config_data TEXT NOT NULL,  -- JSON string
                    is_template BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                )
            """)
            
            # Generic JSON data storage
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS json_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    data_name TEXT NOT NULL,
                    data_content TEXT NOT NULL,  -- JSON string
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_session ON interview_transcripts(user_id, session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_session ON evaluation_outputs(user_id, session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_json_data_session ON json_data(user_id, session_id, data_name)")
            
            await conn.commit()
            self.log_info("SQLite database tables created successfully")
    
    # User Management
    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                result = await cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.log_error(f"Error getting user ID by email {email}: {e}")
            return None
    
    async def load_user_data(self, user_id: str) -> bool:
        """Load user profile data"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                result = await cursor.fetchone()
                if result:
                    # Convert row to dict
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, result))
                    
                    self.user_data = UserProfile(
                        user_id=row_dict['user_id'],
                        name=row_dict['name'],
                        email=row_dict['email'],
                        company_name=row_dict['company_name'],
                        location=row_dict['location'],
                        resume_url=row_dict['resume_url'],
                        starter_code_url=row_dict['starter_code_url'],
                        profile_json_url=row_dict['profile_json_url'],
                        simulation_config_json_url=row_dict['simulation_config_json_url'],
                        panelist_profiles=json.loads(row_dict['panelist_profiles']) if row_dict['panelist_profiles'] else None,
                        panelist_images=json.loads(row_dict['panelist_images']) if row_dict['panelist_images'] else None,
                        role=row_dict['role'],
                        organization_id=row_dict['organization_id'],
                        created_at=row_dict['created_at']
                    )
                    return True
                return False
        except Exception as e:
            self.log_error(f"Error loading user data for {user_id}: {e}")
            return False
    
    async def create_user(self, user_profile: UserProfile) -> bool:
        """Create a new user"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO users (user_id, name, email, company_name, location, 
                                     resume_url, starter_code_url, profile_json_url, 
                                     simulation_config_json_url, panelist_profiles, 
                                     panelist_images, role, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_profile.user_id, user_profile.name, user_profile.email,
                      user_profile.company_name, user_profile.location, user_profile.resume_url,
                      user_profile.starter_code_url, user_profile.profile_json_url,
                      user_profile.simulation_config_json_url, 
                      json.dumps(user_profile.panelist_profiles) if user_profile.panelist_profiles else None,
                      json.dumps(user_profile.panelist_images) if user_profile.panelist_images else None,
                      user_profile.role, user_profile.organization_id))
                await conn.commit()
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
            
            for key, value in updates.items():
                if key in ['panelist_profiles', 'panelist_images'] and value is not None:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(user_id)  # For WHERE clause
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
            
            async with self._get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
                self.log_info(f"User updated successfully: {user_id}")
                return True
        except Exception as e:
            self.log_error(f"Error updating user {user_id}: {e}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                await conn.commit()
                self.log_info(f"User deleted successfully: {user_id}")
                return True
        except Exception as e:
            self.log_error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def get_all_users_data(self) -> List[UserProfile]:
        """Get all user profiles"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("SELECT * FROM users ORDER BY created_at DESC")
                results = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                users = []
                for result in results:
                    row_dict = dict(zip(columns, result))
                    user = UserProfile(
                        user_id=row_dict['user_id'],
                        name=row_dict['name'],
                        email=row_dict['email'],
                        company_name=row_dict['company_name'],
                        location=row_dict['location'],
                        resume_url=row_dict['resume_url'],
                        starter_code_url=row_dict['starter_code_url'],
                        profile_json_url=row_dict['profile_json_url'],
                        simulation_config_json_url=row_dict['simulation_config_json_url'],
                        panelist_profiles=json.loads(row_dict['panelist_profiles']) if row_dict['panelist_profiles'] else None,
                        panelist_images=json.loads(row_dict['panelist_images']) if row_dict['panelist_images'] else None,
                        role=row_dict['role'],
                        organization_id=row_dict['organization_id'],
                        created_at=row_dict['created_at']
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
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO sessions (session_id, user_id, start_time, status)
                    VALUES (?, ?, ?, ?)
                """, (session_id, user_id, datetime.now().isoformat(), "active"))
                await conn.commit()
            
            self.session_id = session_id
            self.log_info(f"New session created: {session_id} for user: {user_id}")
            return session_id
        except Exception as e:
            self.log_error(f"Error creating session for user {user_id}: {e}")
            raise
    
    async def get_session_data(self, user_id: str, session_id: str) -> Optional[SessionData]:
        """Get session data"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT * FROM sessions WHERE user_id = ? AND session_id = ?
                """, (user_id, session_id))
                result = await cursor.fetchone()
                
                if result:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, result))
                    
                    return SessionData(
                        session_id=row_dict['session_id'],
                        user_id=row_dict['user_id'],
                        start_time=row_dict['start_time'],
                        status=row_dict['status'],
                        end_time=row_dict['end_time'],
                        metadata=json.loads(row_dict['metadata']) if row_dict['metadata'] else None
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
            
            for key, value in updates.items():
                if key == 'metadata' and value is not None:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.extend([user_id, session_id])
            query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE user_id = ? AND session_id = ?"
            
            async with self._get_connection() as conn:
                await conn.execute(query, values)
                await conn.commit()
                self.log_info(f"Session updated: {session_id}")
                return True
        except Exception as e:
            self.log_error(f"Error updating session {session_id}: {e}")
            return False
    
    async def get_most_recent_session_id_by_user_id(self, user_id: str) -> Optional[str]:
        """Get the most recent session ID for a user"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT session_id FROM sessions 
                    WHERE user_id = ? 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """, (user_id,))
                result = await cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.log_error(f"Error getting recent session for user {user_id}: {e}")
            return None
    
    async def get_all_session_data(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all data for a session"""
        if not session_id:
            session_id = self.session_id
        
        if not session_id:
            return {}
        
        result = {}
        try:
            async with self._get_connection() as conn:
                # Get interview transcripts
                cursor = await conn.execute("""
                    SELECT speaker, dialog, timestamp FROM interview_transcripts 
                    WHERE user_id = ? AND session_id = ? 
                    ORDER BY timestamp
                """, (user_id, session_id))
                transcripts = await cursor.fetchall()
                result['interview_transcript'] = {
                    str(i): {'speaker': t[0], 'dialog': t[1]} 
                    for i, t in enumerate(transcripts)
                }
                
                # Get evaluation outputs
                cursor = await conn.execute("""
                    SELECT evaluation_type, evaluation_data FROM evaluation_outputs 
                    WHERE user_id = ? AND session_id = ? 
                    ORDER BY timestamp
                """, (user_id, session_id))
                evaluations = await cursor.fetchall()
                for eval_data in evaluations:
                    eval_type = eval_data[0]
                    if eval_type not in result:
                        result[eval_type] = {}
                    result[eval_type][str(len(result[eval_type]))] = json.loads(eval_data[1])
                
                # Get JSON data
                cursor = await conn.execute("""
                    SELECT data_name, data_content FROM json_data 
                    WHERE user_id = ? AND session_id = ? 
                    ORDER BY timestamp
                """, (user_id, session_id))
                json_data_results = await cursor.fetchall()
                for data in json_data_results:
                    data_name = data[0]
                    if data_name not in result:
                        result[data_name] = {}
                    result[data_name][str(len(result[data_name]))] = json.loads(data[1])
            
            return result
        except Exception as e:
            self.log_error(f"Error getting all session data for {user_id}/{session_id}: {e}")
            return {}
    
    # Interview Data Management
    async def add_dialog_to_database(self, user_id: str, session_id: str, message: Any):
        """Add dialog message to database"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO interview_transcripts (user_id, session_id, speaker, dialog)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_id, message.speaker, message.content))
                await conn.commit()
                self.log_info(f"Dialog added: {message.speaker}")
        except Exception as e:
            self.log_error(f"Error adding dialog: {e}")
    
    async def add_evaluation_output_to_database(self, user_id: str, session_id: str, output: Any):
        """Add evaluation output to database"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO evaluation_outputs (user_id, session_id, evaluation_type, evaluation_data)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_id, "evaluation_output", json.dumps(output.model_dump())))
                await conn.commit()
                self.log_info("Evaluation output added")
        except Exception as e:
            self.log_error(f"Error adding evaluation output: {e}")
    
    async def add_final_evaluation_output_to_database(self, user_id: str, session_id: str, output: Any):
        """Add final evaluation output to database"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO evaluation_outputs (user_id, session_id, evaluation_type, evaluation_data)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_id, "final_evaluation_output", json.dumps(output.model_dump())))
                await conn.commit()
                self.log_info("Final evaluation output added")
        except Exception as e:
            self.log_error(f"Error adding final evaluation output: {e}")
    
    async def get_final_evaluation_output_from_database(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get final evaluation output from database"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT evaluation_data FROM evaluation_outputs 
                    WHERE user_id = ? AND session_id = ? AND evaluation_type = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id, session_id, "final_evaluation_output"))
                result = await cursor.fetchone()
                return json.loads(result[0]) if result else None
        except Exception as e:
            self.log_error(f"Error getting final evaluation output: {e}")
            return None
    
    # Configuration Management
    async def store_simulation_config(self, config_id: str, config_data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Store simulation configuration"""
        try:
            config_name = config_data.get('job_details', {}).get('job_title', 'Untitled Configuration')
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO simulation_configs (config_id, user_id, config_name, config_data, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (config_id, user_id, config_name, json.dumps(config_data), datetime.now().isoformat()))
                await conn.commit()
                self.log_info(f"Simulation config stored: {config_id}")
                return True
        except Exception as e:
            self.log_error(f"Error storing simulation config {config_id}: {e}")
            return False
    
    async def get_simulation_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation configuration"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT config_data FROM simulation_configs WHERE config_id = ?
                """, (config_id,))
                result = await cursor.fetchone()
                return json.loads(result[0]) if result else None
        except Exception as e:
            self.log_error(f"Error getting simulation config {config_id}: {e}")
            return None
    
    async def list_simulation_configs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List simulation configurations"""
        try:
            async with self._get_connection() as conn:
                if user_id:
                    cursor = await conn.execute("""
                        SELECT config_id, config_name, is_template, is_public, created_at, updated_at 
                        FROM simulation_configs 
                        WHERE user_id = ? OR is_public = 1
                        ORDER BY updated_at DESC
                    """, (user_id,))
                else:
                    cursor = await conn.execute("""
                        SELECT config_id, config_name, is_template, is_public, created_at, updated_at 
                        FROM simulation_configs 
                        WHERE is_public = 1 OR is_template = 1
                        ORDER BY updated_at DESC
                    """)
                
                results = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                configs = []
                for result in results:
                    row_dict = dict(zip(columns, result))
                    config = {
                        'config_id': row_dict['config_id'],
                        'config_name': row_dict['config_name'],
                        'is_template': bool(row_dict['is_template']),
                        'is_public': bool(row_dict['is_public']),
                        'created_at': row_dict['created_at'],
                        'updated_at': row_dict['updated_at']
                    }
                    configs.append(config)
                return configs
        except Exception as e:
            self.log_error(f"Error listing simulation configs: {e}")
            return []
    
    async def delete_simulation_config(self, config_id: str) -> bool:
        """Delete simulation configuration"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("DELETE FROM simulation_configs WHERE config_id = ?", (config_id,))
                await conn.commit()
                self.log_info(f"Simulation config deleted: {config_id}")
                return True
        except Exception as e:
            self.log_error(f"Error deleting simulation config {config_id}: {e}")
            return False
    
    # Batch Operations
    async def add_to_batch(self, user_id: str, session_id: str, operation_type: str, data: Any, collection_path: str):
        """Add operation to batch queue"""
        self.pending_batch_operations.append({
            "operation_type": operation_type,
            "data": data,
            "collection_path": collection_path,
            "user_id": user_id,
            "session_id": session_id
        })
        
        if len(self.pending_batch_operations) >= self.batch_size_limit:
            await self.commit_batch()
    
    async def commit_batch(self) -> bool:
        """Commit batch operations"""
        if not self.pending_batch_operations:
            return True
        
        try:
            async with self._get_connection() as conn:
                for operation in self.pending_batch_operations:
                    # Map collection_path to appropriate table operation
                    if operation["collection_path"] == "interview_transcript":
                        await conn.execute("""
                            INSERT INTO interview_transcripts (user_id, session_id, speaker, dialog)
                            VALUES (?, ?, ?, ?)
                        """, (operation["user_id"], operation["session_id"], 
                              operation["data"].get("speaker"), operation["data"].get("dialog")))
                    else:
                        # Generic JSON data storage
                        await conn.execute("""
                            INSERT INTO json_data (user_id, session_id, data_name, data_content)
                            VALUES (?, ?, ?, ?)
                        """, (operation["user_id"], operation["session_id"], 
                              operation["collection_path"], json.dumps(operation["data"])))
                
                await conn.commit()
            
            self.pending_batch_operations = []
            self.log_info("Batch operations committed successfully")
            return True
        except Exception as e:
            self.log_error(f"Error committing batch operations: {e}")
            return False
    
    # Generic Data Operations
    async def add_json_data_output_to_database(self, user_id: str, session_id: str, name: str, json_data: Dict[str, Any]):
        """Add JSON data to database"""
        try:
            async with self._get_connection() as conn:
                await conn.execute("""
                    INSERT INTO json_data (user_id, session_id, data_name, data_content)
                    VALUES (?, ?, ?, ?)
                """, (user_id, session_id, name, json.dumps(json_data)))
                await conn.commit()
                self.log_info(f"JSON data added: {name}")
        except Exception as e:
            self.log_error(f"Error adding JSON data {name}: {e}")
    
    async def get_json_data_output_from_database(self, name: str, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get JSON data from database"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT data_content FROM json_data 
                    WHERE user_id = ? AND session_id = ? AND data_name = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (user_id, session_id, name))
                result = await cursor.fetchone()
                return json.loads(result[0]) if result else None
        except Exception as e:
            self.log_error(f"Error getting JSON data {name}: {e}")
            return None
