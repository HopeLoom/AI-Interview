import asyncio
import json
import os
import socket
from fastapi import WebSocket, WebSocketDisconnect
from master_agent.configuration import create_master_instance
from master_agent.base import (
    WebSocketMessageFromClient, 
    WebSocketMessageTypeFromClient,
    UserLoginDataMessageFromClient, 
    UserLogoutDataMessageFromClient,
    SpeechDataMessageFromClient, 
    ConvertedSpeechToClient, 
    WebSocketMessageTypeToClient, 
    TextToSpeechDataMessageFromClient,
    WebSocketMessageToClient,
    # Configuration message types
    ConfigurationGenerationRequestFromClient,
    QuestionGenerationRequestFromClient,
    CharacterGenerationRequestFromClient,
    ConfigurationLoadRequestFromClient,
    ConfigurationGeneratedToClient
)
from master_agent.master import Master
from core.database.db_manager import get_database
from core.speech.speech_services_provider import SpeechServiceProvider
from core.speech.base import SpeechConfig, SpeechResult
from globals import main_logger, config, logger_manager

class WebSocketHandler:
    """Handles WebSocket connections and message processing"""
    
    def __init__(self, connection_manager, user_master_instance_manager, data_dir, providers):
        self.connection_manager = connection_manager
        self.user_master_instance_manager = user_master_instance_manager
        self.data_dir = data_dir
        self.providers = providers
        self.last_message_tracker = {}
    
    async def handle_websocket(self, websocket: WebSocket):
        """Main WebSocket handler"""
        await self.connection_manager.connect(websocket)
        user_id = None
        try:
            while True:
                data = await websocket.receive_text()
                parsed_data = json.loads(data)
                user_id = await self.parse_result(parsed_data, websocket)
        
        except WebSocketDisconnect:
            main_logger.info("WebSocket disconnected")
        
        except Exception as e:
            main_logger.error(f"Error in WebSocket connection: {e}")
            await self.send_error_message_to_frontend(user_id)
        
        finally:
            # Clean up in the finally block to ensure it's called only once
            if user_id is not None:
                await self.connection_manager.disconnect(user_id, websocket)
                main_logger.info(f"WebSocket connection closed for user: {user_id}")
                await self.cancel_task(user_id)
    
    async def cancel_task(self, user_id):
        """Cancel and cleanup task for a user"""
        main_logger.info(f"Canceling task for user: {user_id}")
        if user_id in self.last_message_tracker:
            del self.last_message_tracker[user_id]
            main_logger.info(f"Deleted last message tracker for user: {user_id}")
        
        if await self.user_master_instance_manager.check_if_user_exists(user_id):
            master_instance = await self.user_master_instance_manager.get_master_instance(user_id)
            if master_instance is not None and hasattr(master_instance, "cancel") and callable(getattr(master_instance, "cancel")):
                await master_instance.cancel()
                try:
                    await asyncio.wait_for(master_instance, timeout=10)
                except asyncio.CancelledError:
                    main_logger.info(f"Task for user {user_id} was cancelled")
                except asyncio.TimeoutError:
                    main_logger.error(f"Task for user {user_id} did not finish in time")

                await self.user_master_instance_manager.remove_user(user_id)
        main_logger.info(f"Deleted master instance for user: {user_id}")
    
    async def launch_master_agent(self, user_id, session_id, candidate_name, firebase_user_id, master_config, database):
        """Launch the master agent for a user"""
        main_logger.info(f"Launching master agent for user: {user_id}")
        logger = logger_manager.get_logger_for_user(user_id, session_id)
        
        master_instance: Master = await create_master_instance(
            config=master_config, 
            candidate_name=candidate_name,
            llm_provider=self.providers['openai'], 
            gemini_provider=self.providers['gemini'],
            groq_provider=self.providers['groq'],
            grok_provider=self.providers['grok'],
            deepseek_provider=self.providers['deepseek'],
            user_id=user_id,
            firebase_user_id=firebase_user_id,
            session_id=session_id,
            database=database,
            logger=logger,
            data_dir=self.data_dir
        )
        
        master_instance.add_connection_manager_reference(self.connection_manager)
        self.connection_manager.set_master_instance(user_id, master_instance)
        await self.user_master_instance_manager.add_user(user_id, master_instance)
        asyncio.create_task(master_instance.run())
    
    async def send_message_to_master_agent(self, user_id, message):
        """Send message to master agent"""
        main_logger.info(f"Sending message to master agent for user: {user_id}")
        if (self.connection_manager is not None and self.connection_manager.get_master_instance(user_id)):
            master_instance = self.connection_manager.get_master_instance(user_id)
            if master_instance is None:
                main_logger.error(f"Master instance not found for user: {user_id}")
                return {"user_id": user_id, "status": False}
            master_instance.message_from_frontend(message)
        else:
            main_logger.warning(f"Master instance not found for user: {user_id}")
            websocket_message_to_client = WebSocketMessageToClient()
            websocket_message_to_client.message_type = WebSocketMessageTypeToClient.ERROR
            websocket_message_to_client.message = "There was an error processing the request. Please contact team at HopeLoom."
            websocket_message_to_client.id = user_id
            await self.connection_manager.broadcast(websocket_message_to_client.model_dump_json())
    
    async def send_error_message_to_frontend(self, user_id):
        """Send error message to frontend"""
        websocket_message_to_client = WebSocketMessageToClient()
        websocket_message_to_client.message_type = WebSocketMessageTypeToClient.ERROR
        websocket_message_to_client.message = "Error in processing the request. Please contact team at HopeLoom."
        websocket_message_to_client.id = user_id

        await self.connection_manager.broadcast(websocket_message_to_client.model_dump_json())

        if await self.user_master_instance_manager.check_if_user_exists(user_id):
            main_logger.info(f"Master instance found for user: {user_id}")
            master_instance = await self.user_master_instance_manager.get_master_instance(user_id)
            if master_instance is not None and hasattr(master_instance, "cancel") and callable(getattr(master_instance, "cancel")):
                await master_instance.cancel()
                await self.user_master_instance_manager.remove_user(user_id)
            else:
                main_logger.warning(f"Master instance for user {user_id} does not have a cancel method or is None.")
        else:
            main_logger.info(f"Master instance not found for user: {user_id}")
    
    def check_if_last_message_same(self, user_id, message):
        """Check if the last message is the same to avoid duplicates"""
        if user_id in self.last_message_tracker:
            last_message = self.last_message_tracker[user_id]
            if last_message == message:
                return True
            else:
                self.last_message_tracker[user_id] = message
        else:
            self.last_message_tracker[user_id] = message
        return False
    
    async def parse_result(self, parsed_data, websocket_instance):
        """Parse and handle WebSocket messages"""
        main_logger.info("Parsing result from frontend")
        user_id = None
        websocketmessage = WebSocketMessageFromClient(**parsed_data)
       
        if websocketmessage.message_type == WebSocketMessageTypeFromClient.USER_LOGIN:
            user_id = await self._handle_user_login(websocketmessage, websocket_instance)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.START_AUDIO_STREAMING:
            user_id = await self._handle_start_audio_streaming(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.AUDIO_RAW_DATA:
            user_id = await self._handle_audio_raw_data(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.USER_LOGOUT:
            user_id = await self._handle_user_logout(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.INSTRUCTION:
            user_id = await self._handle_instruction(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.ACTIVITY_INFO:
            user_id = await self._handle_activity_info(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.INTERVIEW_START:
            user_id = await self._handle_interview_start(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.INTERVIEW_END:
            user_id = await self._handle_interview_end(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.INTERVIEW_DATA:
            user_id = await self._handle_interview_data(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.DONE_PROBLEM_SOLVING:
            user_id = await self._handle_done_problem_solving(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.AUDIO_PLAYBACK_COMPLETED:
            user_id = await self._handle_audio_playback_completed(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.EVALUATION_DATA:
            user_id = await self._handle_evaluation_data(websocketmessage)
        
        # Configuration-related message handlers
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.GENERATE_CONFIGURATION:
            user_id = await self._handle_generate_configuration(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.GENERATE_QUESTION:
            user_id = await self._handle_generate_question(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.GENERATE_CHARACTERS:
            user_id = await self._handle_generate_characters(websocketmessage)
        
        elif websocketmessage.message_type == WebSocketMessageTypeFromClient.LOAD_CONFIGURATION:
            user_id = await self._handle_load_configuration(websocketmessage)

        return user_id
    
    async def _handle_user_login(self, websocketmessage, websocket_instance):
        """Handle user login message"""
        main_logger.info("User login message received")
        database = await get_database(main_logger)
        message = websocketmessage.message
        user_login_data = UserLoginDataMessageFromClient(**message)
        email = user_login_data.email.strip()
        user_id = email
        candidate_name = user_login_data.name.strip()
        main_logger.info(f"User id: {user_id}")
        firebase_user_id = await database.get_user_id_by_email(email)
        main_logger.info(f"Firebase user id: {firebase_user_id}")
        self.connection_manager.add_user_connection(user_id, websocket_instance)

        if firebase_user_id is None:
            main_logger.warning(f"User id not found in firebase: {user_id}")
            await self.send_error_message_to_frontend(user_id)
            return user_id

        if not os.path.exists("static/" + user_id):
            os.makedirs("static/" + user_id)
            os.makedirs("static/" + user_id + "/audio")
            os.makedirs("static/" + user_id + "/images")

        if self.data_dir is not None and not os.path.exists(self.data_dir + user_id):
            os.makedirs(self.data_dir + user_id)
            
        status = await database.load_user_data(firebase_user_id)
        session_id = await database.create_new_session(firebase_user_id)
        
        if status:
            main_logger.info("User data loaded successfully")
        else:
            main_logger.warning("User data not loaded successfully")
            await self.send_error_message_to_frontend(user_id)
            return user_id
        
        from master_agent.base import BaseMasterConfiguration
        master_config = BaseMasterConfiguration(description="Master configuration", name="Master")
        # Get simulation config data - need to handle Firebase-specific method
        if hasattr(database, 'get_simulation_config_json_data'):
            json_data = database.get_simulation_config_json_data()
        else:
            # For non-Firebase databases, we need to get config differently
            # This is a temporary fallback - in a real scenario, configs would be stored in the database
            json_data = None
        
        # Ensure required fields are present in JSON data before validation
        if json_data and isinstance(json_data, dict):
            if 'description' not in json_data:
                json_data['description'] = "Master configuration"
            if 'name' not in json_data:
                json_data['name'] = "Master"
        
        master_config: BaseMasterConfiguration = BaseMasterConfiguration.model_validate(json_data)
        main_logger.info(f"Logger created for user: {user_id}, session: {session_id}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        main_logger.info(f"IP Address: {ip_address}")

        master_config.address = str(ip_address)
        asyncio.create_task(self.launch_master_agent(user_id, session_id, candidate_name, firebase_user_id, master_config, database))
        return user_id
    
    async def _handle_start_audio_streaming(self, websocketmessage):
        """Handle start audio streaming message"""
        main_logger.info("Start audio streaming message received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)

        if same:
            main_logger.info("Same message received so ignoring")
            return user_id

        text_to_speech_data = TextToSpeechDataMessageFromClient(**message)
        voice_name = text_to_speech_data.voice_name
        text = text_to_speech_data.text
        
        speech_config = SpeechConfig(
            provider="eleven_labs", 
            speak_mode=False, 
            api_key=config.speech.elevenlabs_api_key, 
            voice_id=voice_name, 
            data_dir="", 
            tts_url=""
        )
        speech_service_provider = SpeechServiceProvider(speech_config, main_logger)

        task = asyncio.create_task(speech_service_provider.say(self.connection_manager, user_id, text, voice_name))

        def handle_start_audio_streaming_result(task):
            try:
                result = task.result()
                result = SpeechResult(**result.model_dump())
                user_id = result.user_id
                status = result.status
                main_logger.info("TTS task finished:", result)
                if not status:
                    asyncio.create_task(self.send_error_message_to_frontend(user_id))
            
            except Exception as e:
                main_logger.error("TTS task failed with exception:", e)

        task.add_done_callback(handle_start_audio_streaming_result)
        return user_id
    
    async def _handle_audio_raw_data(self, websocketmessage):
        """Handle audio raw data message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        speech_data = SpeechDataMessageFromClient(**message)
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id

        # Get Groq provider config
        groq_provider = next((p for p in config.llm_providers if p.name.lower() == 'groq'), None)
        groq_api_key = groq_provider.api_key if groq_provider else ""
        
        speech_config = SpeechConfig(
            provider="groq", 
            speak_mode=False, 
            api_key=groq_api_key, 
            voice_id="", 
            data_dir="", 
            tts_url=""
        )
        speech_service_provider = SpeechServiceProvider(speech_config, main_logger)

        task = asyncio.create_task(speech_service_provider.understand(user_id, speech_data.raw_audio_data))
        
        def handle_task_result(task):
            try:
                result = task.result()
                result = SpeechResult(**result.model_dump())
                user_id = result.user_id
                status = result.status
                transcript = result.result
                main_logger.info("Speech processing task finished:", result)
                if not status:
                    asyncio.create_task(self.send_error_message_to_frontend(user_id))
                
                converted_speech = ConvertedSpeechToClient(text=transcript)
                if (self.connection_manager is not None and self.connection_manager.get_master_instance(user_id)):
                    master_instance = self.connection_manager.get_master_instance(user_id)
                    if master_instance is None:
                        main_logger.error(f"Master instance not found for user: {user_id}")
                        return {"user_id": user_id, "status": False}
                    speaker_name  = master_instance.get_candidate_name()
                    converted_speech.speaker_name = speaker_name
                    asyncio.create_task(master_instance._send_message_to_frontend(converted_speech.model_dump_json(), WebSocketMessageTypeToClient.AUDIO_SPEECH_TO_TEXT.value))

            except Exception as e:
                main_logger.error("Speech processing task failed with exception:", e)
        
        task.add_done_callback(handle_task_result)
        return user_id
    
    async def _handle_user_logout(self, websocketmessage):
        """Handle user logout message"""
        user_logout_data = UserLogoutDataMessageFromClient(**websocketmessage.message)
        user_id = user_logout_data.id.strip()
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_instruction(self, websocketmessage):
        """Handle instruction message"""
        main_logger.info("Instruction message received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_activity_info(self, websocketmessage):
        """Handle activity info message"""
        main_logger.info("Activity info message received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_interview_start(self, websocketmessage):
        """Handle interview start message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id

        # Update interview session status to "in_progress"
        try:
            from interview_configuration.database_service import InterviewConfigurationDatabase
            db = InterviewConfigurationDatabase()

            # Find active session for this user/candidate
            from firebase_admin import firestore
            sessions_ref = db.db.collection('interview_sessions')
            query = sessions_ref.where('candidate_id', '==', user_id).where('status', '==', 'scheduled').limit(1)
            docs = list(query.stream())

            if docs:
                session_id = docs[0].id
                await db.update_interview_session(session_id, {
                    "status": "in_progress",
                    "started_at": firestore.SERVER_TIMESTAMP
                })
                main_logger.info(f"Updated interview session {session_id} status to in_progress")
        except Exception as e:
            main_logger.error(f"Error updating interview session status: {e}")

        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_interview_end(self, websocketmessage):
        """Handle interview end message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id

        # Update interview session status to "completed"
        try:
            from interview_configuration.database_service import InterviewConfigurationDatabase
            db = InterviewConfigurationDatabase()

            # Find active session for this user/candidate
            from firebase_admin import firestore
            sessions_ref = db.db.collection('interview_sessions')
            query = sessions_ref.where('candidate_id', '==', user_id).where('status', '==', 'in_progress').limit(1)
            docs = list(query.stream())

            if docs:
                session_id = docs[0].id
                await db.update_interview_session(session_id, {
                    "status": "completed",
                    "completed_at": firestore.SERVER_TIMESTAMP
                })
                main_logger.info(f"Updated interview session {session_id} status to completed")
        except Exception as e:
            main_logger.error(f"Error updating interview session status on end: {e}")

        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_interview_data(self, websocketmessage):
        """Handle interview data message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_done_problem_solving(self, websocketmessage):
        """Handle done problem solving message"""
        main_logger.info("Done problem solving message received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_audio_playback_completed(self, websocketmessage):
        """Handle audio playback completed message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_evaluation_data(self, websocketmessage):
        """Handle evaluation data message"""
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        same = self.check_if_last_message_same(user_id, message)
        
        if same:
            main_logger.info("Same message received so ignoring")
            return user_id
        
        await self.send_message_to_master_agent(user_id, websocketmessage)
        return user_id
    
    async def _handle_generate_configuration(self, websocketmessage):
        """Handle configuration generation request"""
        main_logger.info("Configuration generation request received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        
        try:
            # Import configuration service
            from interview_configuration.service import InterviewConfigurationService
            from interview_configuration.models import FrontendConfigurationInput
            
            # Create configuration service
            config_service = InterviewConfigurationService(self.providers['openai'])
            
            # Parse the configuration input
            config_request = ConfigurationGenerationRequestFromClient(**message)
            config_input = FrontendConfigurationInput(**config_request.config_input)
            
            # Generate configuration
            response = await config_service.generate_full_configuration(config_input, user_id)
            
            # Send response back to frontend
            config_response = ConfigurationGeneratedToClient(
                success=response.success,
                configuration_id=response.configuration_id,
                simulation_config=response.simulation_config,
                errors=response.errors,
                warnings=response.warnings
            )
            
            websocket_response = WebSocketMessageToClient()
            websocket_response.message_type = WebSocketMessageTypeToClient.CONFIGURATION_GENERATED
            websocket_response.message = config_response.model_dump()
            websocket_response.id = user_id
            
            await self.connection_manager.broadcast(websocket_response.model_dump_json())
            
        except Exception as e:
            main_logger.error(f"Configuration generation failed: {e}")
            await self._send_configuration_error(user_id, f"Configuration generation failed: {str(e)}")
        
        return user_id
    
    async def _handle_generate_question(self, websocketmessage):
        """Handle question generation request"""
        main_logger.info("Question generation request received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        
        try:
            from interview_configuration.service import InterviewConfigurationService
            from interview_configuration.models import QuestionGenerationRequest
            
            config_service = InterviewConfigurationService(self.providers['openai'])
            question_request = QuestionGenerationRequestFromClient(**message)
            question_input = QuestionGenerationRequest(**question_request.question_request)
            
            result = await config_service.generate_question_only(question_input, user_id)
            
            websocket_response = WebSocketMessageToClient()
            websocket_response.message_type = WebSocketMessageTypeToClient.QUESTION_GENERATED
            websocket_response.message = result
            websocket_response.id = user_id
            
            await self.connection_manager.broadcast(websocket_response.model_dump_json())
            
        except Exception as e:
            main_logger.error(f"Question generation failed: {e}")
            await self._send_configuration_error(user_id, f"Question generation failed: {str(e)}")
        
        return user_id
    
    async def _handle_generate_characters(self, websocketmessage):
        """Handle character generation request"""
        main_logger.info("Character generation request received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        
        try:
            from interview_configuration.service import InterviewConfigurationService
            from interview_configuration.models import CharacterGenerationRequest
            
            config_service = InterviewConfigurationService(self.providers['openai'])
            character_request = CharacterGenerationRequestFromClient(**message)
            character_input = CharacterGenerationRequest(**character_request.character_request)
            
            result = await config_service.generate_characters_only(character_input, user_id)
            
            websocket_response = WebSocketMessageToClient()
            websocket_response.message_type = WebSocketMessageTypeToClient.CHARACTERS_GENERATED
            websocket_response.message = result
            websocket_response.id = user_id
            
            await self.connection_manager.broadcast(websocket_response.model_dump_json())
            
        except Exception as e:
            main_logger.error(f"Character generation failed: {e}")
            await self._send_configuration_error(user_id, f"Character generation failed: {str(e)}")
        
        return user_id
    
    async def _handle_load_configuration(self, websocketmessage):
        """Handle configuration loading request"""
        main_logger.info("Configuration loading request received")
        user_id = websocketmessage.id.strip()
        message = websocketmessage.message
        
        try:
            load_request = ConfigurationLoadRequestFromClient(**message)
            configuration_id = load_request.configuration_id

            # Load configuration from database
            main_logger.info(f"Loading configuration: {configuration_id} for user: {user_id}")

            from interview_configuration.database_service import InterviewConfigurationDatabase
            db = InterviewConfigurationDatabase()
            configuration = await db.get_interview_configuration(configuration_id)

            if not configuration:
                main_logger.error(f"Configuration not found: {configuration_id}")
                await self._send_configuration_error(user_id, f"Configuration {configuration_id} not found")
                return user_id

            main_logger.info(f"Configuration loaded successfully: {configuration_id}")

            # Send configuration to frontend using ConfigurationGeneratedToClient
            config_response = ConfigurationGeneratedToClient(
                success=True,
                configuration_id=configuration_id,
                simulation_config=configuration.get('simulation_config'),
                generated_question=configuration.get('generated_question'),
                generated_characters=configuration.get('generated_characters'),
                candidate_profile=configuration.get('candidate_profile'),
                errors=[],
                warnings=[]
            )

            websocket_response = WebSocketMessageToClient()
            websocket_response.message_type = WebSocketMessageTypeToClient.CONFIGURATION_LOADED
            websocket_response.message = config_response.model_dump()
            websocket_response.id = user_id

            await self.connection_manager.broadcast(websocket_response.model_dump_json())
            
        except Exception as e:
            main_logger.error(f"Configuration loading failed: {e}")
            await self._send_configuration_error(user_id, f"Configuration loading failed: {str(e)}")
        
        return user_id
    
    async def _send_configuration_error(self, user_id, error_message):
        """Send configuration error to frontend"""
        websocket_response = WebSocketMessageToClient()
        websocket_response.message_type = WebSocketMessageTypeToClient.ERROR
        websocket_response.message = error_message
        websocket_response.id = user_id
        
        await self.connection_manager.broadcast(websocket_response.model_dump_json())