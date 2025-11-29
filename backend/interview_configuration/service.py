"""
Interview Configuration Service
Orchestrates configuration generation using existing components

This service uses the same character generation methods as data_uploader.py:
- _generate_panelist_profile: Uses panelist_factory.background_generator and personality_generator
- _generate_panelist_image: Uses core.image_generator.generator.TextToImageProvider
- Both methods follow the exact same logic and imports as data_uploader.py

Logging follows the same pattern as other routers in the codebase:
- Uses main_logger from globals
- main_logger.info() for informational messages
- main_logger.error() for error messages
- main_logger.warning() for warning messages
"""
import json
import uuid
import os
import asyncio

from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


from interview_details_agent.interview import Interview
from interview_details_agent.base import (
    BaseInterviewConfiguration, 
    JobDetails, 
    InterviewRoundDetails,
    CharacterDataOutput,
    ActivityDetailsOutputMessage,
    StarterCodeData,
    InterviewSettings
)
from candidate_agent.generate_candidate_profile import CandidateProfileGenerator
from utils.resume_file_reader import parse_resume
from master_agent.base import BaseMasterConfiguration
from core.database.db_manager import get_database
from core.resource.model_providers.schema import ChatModelProvider
from globals import main_logger


from .models import (
    FrontendConfigurationInput,
    ConfigurationGenerationResponse,
    ConfigurationValidationResult,
    FrontendJobDetails,

)
from .constants import AVAILABLE_JOB_TYPES, get_job_type_by_value, get_available_job_values

class InterviewConfigurationService:
    """Main service for handling interview configuration generation"""
    
    def __init__(self, llm_provider: ChatModelProvider):
        self.llm_provider = llm_provider
        # Database will be initialized when needed
        self.database = None
        
    async def _get_database(self):
        """Get database instance using the database manager"""
        if self.database is None:
            self.database = await get_database()
        return self.database
    
    def get_available_job_types(self) -> List[Dict[str, str]]:
        """
        Get list of available job types for frontend dropdown
        """
        return AVAILABLE_JOB_TYPES


    def get_example_job_details(self, examples:List[BaseInterviewConfiguration]) -> List[JobDetails]:
        """
        Get example job details for a given job type
        """
        job_details = []
        for example in examples:
            print (f"Example job details: {example.job_details}")
            job_details.append(example.job_details)
        return job_details
        
    def get_example_activity_details(self, examples:List[BaseInterviewConfiguration]) -> List[ActivityDetailsOutputMessage]:
        """
        Get example activity details for a given job type
        """
        activity_details = []
        for example in examples:
            activity_details.append(example.activity_details)
        return activity_details


    def get_example_starter_code(self, examples:List[BaseInterviewConfiguration], job_type:str) -> List[StarterCodeData]:
        """
        Get example starter code for a given job type
        """
        starter_code = []
        for example in examples:
            # we need to define the path relative to the root of the project
            root_path = Path(__file__).parent.parent.parent
            code_path = root_path / "onboarding_data" / "examples" / job_type / example.activity_code_path
            with open(code_path, 'r') as f:
                code = f.read()
            starter_code.append(StarterCodeData(code=code, description=example.activity_details.scenario))
        return starter_code


    def get_example_character_information(self, examples:List[BaseInterviewConfiguration]) -> List[CharacterDataOutput]:
        """
        Get example character information for a given job type
        """
        character_information = []
        for example in examples:
            character_information.append(example.character_data)
        return character_information

    async def generate_full_configuration(
        self, 
        config_input: FrontendConfigurationInput,
        company_id: str,
        job_type: str
    ) -> ConfigurationGenerationResponse:
        """
        Generate complete interview configuration from frontend input
        """
        try:
            main_logger.info(f"Starting full configuration generation for company: {company_id}, job: {job_type}")
            
            response = ConfigurationGenerationResponse(success=True)
            config_id = self._generate_config_id()
            invitation_code = self._generate_invitation_code()
            response.configuration_id = config_id
            response.invitation_code = invitation_code

            # 1. Validate input
            main_logger.info("Step 1: Validating configuration input...")
            validation = self._validate_configuration_input(config_input)
            if not validation.is_valid:
                response.success = False
                response.errors = validation.errorsx
                main_logger.error(f"Configuration validation failed: {response.errors}")
                return response
            
            # 2. Build base interview configuration
            main_logger.info("Step 2: Loading template configuration...")
            # job type is one of the values in AVAILABLE_JOB_TYPES
            interview_config = await self._load_template_config(job_type)
            # load the examples for the job_type
            example_data = await self._load_examples(job_type)  

            example_job_details = self.get_example_job_details(example_data)
            example_activity_details = self.get_example_activity_details(example_data)
            example_starter_code = self.get_example_starter_code(example_data, job_type)
            example_character_data = self.get_example_character_information(example_data)

            # 3. Generate job details
            main_logger.info("Step 3: Generating job details...")
            job_details:JobDetails | None = await self._generate_job_details(config_input, company_id, job_type)
            if job_details is None:
                response.success = False
                response.errors = ["Failed to generate job details"]
                main_logger.error("Job details generation failed")
                return response
                
            # 4. Update interview configuration with generated job details
            main_logger.info("Step 4: Updating interview configuration...")
            interview_config.job_details = job_details
            
            # 5. Create Interview agent instance and generate activity details
            main_logger.info("Step 5: Creating interview agent and generating activity details...")
            interview_agent = Interview(config_id, interview_config, self.llm_provider)

            # we need to pass the examples data to the run_activity_details and run_starter_code functions
            activity_details = await interview_agent.generate_activity_details(
                example_job_details,
                example_activity_details
            )
            # generate the starter code based on the activity details and starter code examples
            generated_starter_code:StarterCodeData = await interview_agent.generate_starter_code(
                example_activity_details,
                example_starter_code,
                activity_details
            )
            # update the interview configuration with the generated activity details and starter code
            interview_config.activity_details = activity_details

            # 6. Generate characters
            main_logger.info("Step 6: Generating characters...")


            # generate character information
            character_data_output = await interview_agent.generate_character_information(example_character_data)
            
            # Generate characters using the same methods as data_uploader.py
            # This follows the exact same logic as the character generation loop in data_uploader.py
            character_data_output = interview_config.character_data
            character_data_list = character_data_output.data
            
            main_logger.info(f"Generating profiles for {len(character_data_list)} characters...")
            
            panelist_profiles_urls = []
            panelist_images_urls = []
            
            for character_data in character_data_list:
                main_logger.info(f"Processing character: {character_data.character_name}")
                
                # Generate panelist profile using the same method as data_uploader.py
                # This replicates the character processing loop from data_uploader.py lines 250-280
                panelist_profile = await self._generate_panelist_profile(character_data)
                
                if panelist_profile:
                    # Upload panelist profile to storage
                    profile_url = await self._upload_json_to_storage(
                        panelist_profile,
                        company_id,
                        f"{character_data.character_name}_profile.json"
                    )
                    panelist_profiles_urls.append(profile_url)
                    main_logger.info(f"Uploaded panelist profile for {character_data.character_name} to: {profile_url}")
                    
                    # Generate and upload panelist image using the same method as data_uploader.py
                    # This replicates the image generation logic from data_uploader.py lines 270-280
                    try:
                        image_url = await self._generate_panelist_image(character_data, panelist_profile)
                        if image_url:
                            panelist_images_urls.append(image_url)
                            main_logger.info(f"Generated and uploaded image for {character_data.character_name} to: {image_url}")
                    except Exception as e:
                        main_logger.warning(f"Failed to generate image for {character_data.character_name}: {e}")
                else:
                    main_logger.warning(f"Failed to generate profile for character {character_data.character_name}")
            
            # Store panelist information in the interview config
            interview_config.panelist_profiles = panelist_profiles_urls
            interview_config.panelist_images = panelist_images_urls
            
            main_logger.info(f"Successfully generated {len(panelist_profiles_urls)} panelist profiles and {len(panelist_images_urls)} images")

            # Assemble master config after all data is ready
            master_config = self._assemble_master_config(
                interview_config,
                character_data_output,
                activity_details,
                generated_starter_code,
                None  # candidate_profile will be set later
            )
            
            # Store configuration in database
            await self._store_configuration(config_id, invitation_code, master_config, company_id, config_input)
            
            response.simulation_config = interview_config.model_dump()
            main_logger.info("Step 6 completed: Characters generated and simulation config prepared")

            # 7. Process resume files and generate candidate profiles
            main_logger.info("Step 7: Processing resume files and generating candidate profiles...")
            if not config_input.resume_data or not config_input.resume_data.resume_file_ids:
                response.success = False
                response.errors = ["No resume files provided"]
                main_logger.error("No resume files provided")
                return response
            
            resume_file_ids = config_input.resume_data.resume_file_ids
            main_logger.info(f"Processing {len(resume_file_ids)} resume files for company {company_id}, job {job_type}")
            
            # Upload simulation config to Firebase Storage
            main_logger.info("Uploading simulation config to Firebase Storage...")
            simulation_config_url = await self._upload_json_to_storage(
                interview_config.model_dump(), 
                company_id, 
                f"{job_type}_simulation_config.json"
            )
            main_logger.info(f"Uploaded simulation config to: {simulation_config_url}")
            
            # Upload starter code to Firebase Storage
            main_logger.info("Uploading starter code to Firebase Storage...")
            
            try:
                # lets save the starter code to a file on a temp basis
                with open("starter_code.txt", "w") as f:
                    f.write(generated_starter_code.code)
                starter_code_url = await self._upload_file_to_storage(
                    "starter_code.txt",
                    company_id,
                    "starter_code.txt"
                )
                os.remove("starter_code.txt")
                main_logger.info(f"Uploaded starter code to: {starter_code_url}")
            except Exception as e:
                main_logger.warning(f"Failed to upload starter code to Firebase: {e}")
            
            # Process each resume file
            processed_candidates = 0
            failed_candidates = 0
            
            for resume_file_id in resume_file_ids:
                try:
                    resume_file_path = os.path.join(f"static/{company_id}/{job_type}/resume", resume_file_id)
                    main_logger.info(f"Processing resume file: {resume_file_id}")
                    
                    # Check if file exists
                    if not os.path.exists(resume_file_path):
                        main_logger.warning(f"Resume file not found: {resume_file_path}")
                        failed_candidates += 1
                        continue
                    
                    # Parse resume content
                    resume_file_content = self._parse_resume_file(resume_file_path)
                    if resume_file_content is None:
                        main_logger.warning(f"Failed to parse resume file: {resume_file_id}")
                        failed_candidates += 1
                        continue
                    
                    # Generate candidate profile
                    candidate_profile = await self._generate_candidate_profile(resume_file_content)
                    if candidate_profile is None:
                        main_logger.warning(f"Failed to generate candidate profile for: {resume_file_id}")
                        failed_candidates += 1
                        continue
                    
                    # Extract candidate information safely
                    candidate_name = getattr(candidate_profile, 'name', None) or "Candidate"
                    candidate_email = getattr(candidate_profile, 'email', None) or f"candidate_{uuid.uuid4().hex[:8]}@example.com"
                    
                    # Create Firebase user
                    user_id = await self._create_firebase_user(candidate_name, candidate_email)
                    
                    # Generate authentication code
                    auth_code = self._generate_authentication_code()
                    
                    # Upload resume to Firebase Storage
                    try:
                        resume_url = await self._upload_file_to_storage(resume_file_path, user_id, "resume.pdf")
                        main_logger.info(f"Uploaded resume for {candidate_name} to: {resume_url}")
                    except Exception as e:
                        main_logger.warning(f"Failed to upload resume for {candidate_name}: {e}")
                    
                    # Upload candidate profile to Firebase Storage
                    candidate_profile_data = candidate_profile.model_dump() if hasattr(candidate_profile, 'model_dump') else candidate_profile
                    try:
                        candidate_profile_url = await self._upload_json_to_storage(
                            candidate_profile_data,
                            user_id,
                            "candidate_profile.json"
                        )
                        main_logger.info(f"Uploaded candidate profile for {candidate_name} to: {candidate_profile_url}")
                    except Exception as e:
                        main_logger.warning(f"Failed to upload candidate profile for {candidate_name}: {e}")
                    
                    # Store candidate data in Firestore
                    try:
                        await self._store_candidate_data(
                            user_id=user_id,
                            candidate_info={
                                "name": candidate_name,
                                "email": candidate_email
                            },
                            company_id=company_id,
                            job_name=job_type,
                            resume_url=resume_url,
                            candidate_profile_url=candidate_profile_url,
                            auth_code=auth_code,
                            simulation_config_url=simulation_config_url,
                            starter_code_url=starter_code_url
                        )
                        
                        main_logger.info(f"Successfully processed candidate: {candidate_name} ({candidate_email})")
                        processed_candidates += 1
                    except Exception as e:
                        main_logger.warning(f"Failed to store candidate data in Firestore for {candidate_name}: {e}")
                        # Still count as processed since we got this far
                        processed_candidates += 1
                        
                except Exception as e:
                    main_logger.error(f"Error processing candidate {resume_file_id}: {e}")
                    failed_candidates += 1
                    continue
            
            main_logger.info(f"Configuration generation completed. Processed: {processed_candidates}, Failed: {failed_candidates}")
            
            if processed_candidates > 0:
                main_logger.info(f"Successfully generated configuration for {processed_candidates} candidates")
                response.success = True
            else:
                main_logger.warning("No candidates were successfully processed")
                response.success = False
                response.errors.append("No candidates were successfully processed")
            
            return response
            
        except Exception as e:
            main_logger.error(f"Error generating full configuration: {e}")
            import traceback
            traceback.print_exc()
            response = ConfigurationGenerationResponse(success=False)
            response.errors = [str(e)]
            return response

    def _validate_configuration_input(self, config_input: FrontendConfigurationInput) -> ConfigurationValidationResult:
        """Validate the configuration input"""
        result = ConfigurationValidationResult()
        
        main_logger.info(f"Validating configuration input for user mode: {config_input.userMode}")
        
        # Validate job details
        if not config_input.job_details.job_description and config_input.job_details.input_type == 'text':
            result.errors.append("Job description is required when input type is text")
        
        if config_input.job_details.input_type == 'pdf' and not config_input.job_details.job_file_id:
            result.errors.append("Job file ID is required when input type is PDF")
        
        # Validate resume data
        if not config_input.resume_data or not config_input.resume_data.resume_file_ids:
            result.errors.append("At least one resume file is required")
        
        # Validate character request if provided
        if hasattr(config_input, 'character_request') and config_input.character_request:
            if hasattr(config_input.character_request, 'character_count') and config_input.character_request.character_count <= 0:
                result.errors.append("Character count must be greater than 0")
            if hasattr(config_input.character_request, 'roles') and not config_input.character_request.roles:
                result.errors.append("At least one role must be specified for characters")
        
        result.is_valid = len(result.errors) == 0
        
        if result.is_valid:
            main_logger.info("Configuration input validation passed")
        else:
            main_logger.error(f"Configuration input validation failed with {len(result.errors)} errors: {result.errors}")
        
        return result

    async def _generate_job_details(
        self,
        config_input: FrontendConfigurationInput,
        company_id: str,
        job_name: str
    ) -> JobDetails | None:

        frontend_job_info:FrontendJobDetails = config_input.job_details
        upload_dir = f"static/{company_id}/{job_name}/job_description"
        job_description = ""
        
        # Check the file type and read content accordingly
        if frontend_job_info.file_type == "pdf":
            file_name = frontend_job_info.job_file_id
            file_path = os.path.join(upload_dir, file_name)
            job_description = self._read_pdf_file(file_path)
        elif frontend_job_info.file_type == "text":
            job_description = frontend_job_info.job_description

        if not job_description:
            main_logger.warning("No job description content available")
            return None

        """
        Generate structured job details using LLM
        """
        try:
            main_logger.info(f"Generating job details from content length: {len(job_description)}")
            
            # Check if job_title is provided from frontend
            frontend_job_title = frontend_job_info.job_title if frontend_job_info.job_title else None
            job_title_instruction = f"Use the job title: '{frontend_job_title}'" if frontend_job_title else "Extract the job title from the description"
            
            prompt = f"""
            You are provided with the job description. 
            Your goal is to generate structured job details in JSON format.
            
            The job description is the following:
            {job_description}
            
            {job_title_instruction}
            
            Generate a comprehensive job details structure with:
            - job_title: {f"'{frontend_job_title}'" if frontend_job_title else "The job title extracted from the description"}
            - job_description: A detailed, professional job description
            - job_requirements: List of key requirements and responsibilities
            - job_qualifications: List of required qualifications and experience
            - company_name: Company name
            - company_description: A professional company description
            
            Return only valid JSON without markdown formatting.
            """
            
            # Use LLM to generate job details
            from core.prompting.schema import ChatPrompt, ChatMessage
            
            chat_prompt = ChatPrompt(messages=[
                ChatMessage(role="user", content=prompt)
            ])
            
            response = await self.llm_provider.create_chat_completion(
                chat_messages=chat_prompt,
                model_name="gpt-4o",
                temperature=0.7,
                is_json_mode=True
            )
            
            # Parse response and create JobDetails object
            try:
                job_data = json.loads(response.response.content)
                job_details = JobDetails(**job_data)
                main_logger.info(f"Successfully generated job details for: {job_details.job_title if hasattr(job_details, 'job_title') else 'Unknown'}")
                return job_details
            except Exception as parse_error:
                main_logger.error(f"Error parsing LLM response: {parse_error}")
                main_logger.error(f"Raw response content: {response.response.content[:200]}...")
                return None
                
        except Exception as e:
            main_logger.error(f"Error generating job details: {e}")
            return None

    async def _generate_panelist_profile(self, character_data) -> Optional[Dict[str, Any]]:
        """
        Generate panelist profile using the same method as data_uploader.py
        
        This method replicates the get_panelist_profile function from data_uploader.py:
        - Uses panelist_factory.background_generator.generate_background_info()
        - Uses panelist_factory.personality_generator.generate_personality_info()
        - Creates Profile object with the same structure
        - Returns profile as dictionary (same as data_uploader.py)
        """
        try:
            # Import the panelist generation modules (same as data_uploader)
            from panelist_factory import background_generator, personality_generator
            from panelist_agent.base import Profile
            
            main_logger.info(f"Generating panelist profile for {character_data.character_name}")
            
            # Generate background and personality using the same methods as data_uploader
            background = await background_generator.generate_background_info(self.llm_provider, character_data)
            personality = await personality_generator.generate_personality_info(self.llm_provider, background, character_data)
            
            # Create profile object
            profile = Profile(background=background, personality=personality)
            profile.interview_round_part_of = character_data.interview_round_part_of
            profile.character_id = character_data.character_id
            
            # Convert to dictionary format
            profile_dict = profile.model_dump()
            main_logger.info(f"Successfully generated profile for {character_data.character_name}")
            
            return profile_dict
            
        except Exception as e:
            main_logger.error(f"Error generating panelist profile for {character_data.character_name}: {e}")
            return None

    async def _generate_panelist_image(self, character_data, panelist_profile: Dict[str, Any]) -> Optional[str]:
        """
        Generate panelist image using the same method as data_uploader.py
        
        This method replicates the image generation logic from data_uploader.py:
        - Uses the same text prompt format for image generation
        - Uses core.image_generator.generator.TextToImageProvider
        - Configures image generation with the same parameters
        - Generates and uploads images following the same workflow
        """
        try:
            # Import the image generation modules (same as data_uploader)
            from core.image_generator.generator import TextToImageProvider, Text2ImageConfig
            
            main_logger.info(f"Generating image for {character_data.character_name}")
            
            # Extract profile information for image generation
            background = panelist_profile.get('background', {})
            age = background.get('age', '30')
            gender = background.get('gender', 'unknown')
            bio = background.get('bio', '')
            name = background.get('name', character_data.character_name)
            
            # Create text prompt for image generation (same as data_uploader)
            text_prompt = f"Generate professional profile image for a person with age: {age}, gender: {gender} and bio {bio}. Ensure its a formal headshot of the person. Only generate face of the person with no other objects. Ensure the facial details are maintained"
            
            # Configure image generation provider
            image_config = Text2ImageConfig()
            image_config.provider = "openai"  # Default to OpenAI
            
            # Get the LLM provider's API key if available
            if hasattr(self.llm_provider, 'api_key'):
                image_config.api_key = self.llm_provider.api_key
            
            # Create temporary directory for image generation
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                image_config.data_dir = temp_dir
                
                # Create image provider and generate image
                image_provider = TextToImageProvider(image_config)
                filename = f"{name}.png"
                
                # Generate the image
                image_path = await image_provider.generate_image(text_prompt, filename)
                
                if image_path and os.path.exists(image_path):
                    # Upload the generated image to storage
                    image_url = await self._upload_file_to_storage(image_path, "temp_user", filename)
                    main_logger.info(f"Successfully generated and uploaded image for {character_data.character_name}")
                    return image_url
                else:
                    main_logger.warning(f"Failed to generate image for {character_data.character_name}")
                    return None
                    
        except Exception as e:
            main_logger.error(f"Error generating panelist image for {character_data.character_name}: {e}")
            return None

    async def _create_firebase_user(self, name: str, email: str) -> str:
        """
        Create Firebase user and return user ID
        """
        try:
            # Validate email format
            if not email or '@' not in email:
                raise ValueError(f"Invalid email format: {email}")
            
            # For now, we'll generate a user ID since Firebase Auth creation requires admin SDK
            # In a production environment, this would be handled by the frontend/auth system
            user_id = f"user_{int(datetime.now().timestamp())}_{hash(email) % 10000}"
            main_logger.info(f"Generated user ID for {name} ({email}): {user_id}")
            return user_id
            
        except Exception as e:
            main_logger.error(f"Error creating user for {email}: {e}")
            # Fallback to generating a mock user ID
            user_id = f"user_{int(datetime.now().timestamp())}_{hash(email) % 10000}"
            main_logger.warning(f"Using fallback user ID: {user_id}")
            return user_id

    def _generate_authentication_code(self) -> str:
        """
        Generate 6-digit numeric authentication code
        """
        import random
        auth_code = f"{random.randint(100000, 999999)}"
        main_logger.info(f"Generated authentication code: {auth_code}")
        return auth_code

    async def _upload_json_to_storage(self, data: Any, user_id: str, file_name: str) -> str | None:
        """
        Upload JSON data to Firebase Storage using database manager
        """
        try:
            if data is None:
                data = {}
            
            database = await self._get_database()
            # Use the database manager's upload_json method
            url = database.upload_json(user_id, data, file_name)
            main_logger.info(f"Successfully uploaded JSON data to: {url}")
            return url
        except Exception as e:
            main_logger.error(f"Error uploading JSON data to storage: {e}")
            return None

    async def _upload_file_to_storage(self, file_path: str, user_id: str, file_name: str) -> str | None:
        """
        Upload file data to Firebase Storage using database manager
        """
        try:
            # Ensure file path is a string
            file_path = str(file_path)
            # since the database manager doesn't have a direct file upload method
            database = await self._get_database()
            url = database.upload_file(file_path, user_id, file_name)
            main_logger.info(f"Successfully uploaded file data to: {url}")
            return url
        except Exception as e:
            main_logger.error(f"Error uploading file data to storage: {e}")
            return None

    async def _store_candidate_data(
        self,
        user_id: str,
        candidate_info: Dict[str, str],
        company_id: str,
        job_name: str,
        resume_url: str,
        candidate_profile_url: Any,
        auth_code: str,
        simulation_config_url: str,
        starter_code_url: str
    ):
        """
        Store candidate data using database manager
        """
        try:
            # Prepare candidate profile data safel
            
            # Create user profile using the database manager
            from core.database.base import UserProfile
            
            user_profile = UserProfile(
                user_id=user_id,
                name=candidate_info["name"],
                email=candidate_info["email"],
                company_name=company_id,  # Using company_id as company_name for now
                job_title=job_name,
                location="Unknown",  # Default location
                resume_url=resume_url,
                starter_code_url=starter_code_url,
                profile_json_url=candidate_profile_url, 
                simulation_config_json_url=simulation_config_url,
                panelist_profiles=None,
                panelist_images=None,
                created_at=datetime.now().isoformat(),
                auth_code=auth_code
            )
            
            # Store using database manager
            database = await self._get_database()
            success = await database.create_user(user_profile)
            
            if success:
                main_logger.info(f"Successfully stored candidate data for {candidate_info['name']}")
            else:
                main_logger.error(f"Failed to store candidate data for {candidate_info['name']}")
                raise Exception("Failed to create user in database")
                
        except Exception as e:
            main_logger.error(f"Error storing candidate data for {candidate_info.get('name', 'Unknown')}: {e}")
            raise  # Re-raise to be handled by the caller

    async def _load_template_config(self, job_type: str) -> Optional[BaseInterviewConfiguration]:
        """
        Load template configuration based on job type
        """
        try:
            # Look for template in onboarding_data folder using the validated job type
            # we need to define the path relative to the root of the project
            root_path = Path(__file__).parent.parent.parent
            template_path = root_path / "onboarding_data" / "templates" / job_type / "simulation_config.json"
            
            if os.path.exists(template_path):
                main_logger.info(f"Loading template from: {template_path}")
                with open(template_path, 'r') as f:
                    template_data = json.load(f)
                    return BaseInterviewConfiguration(**template_data)
            else:
                main_logger.warning(f"Template not found at: {template_path}")
            
            return None
            
        except Exception as e:
            main_logger.error(f"Error loading template config for job type '{job_type}': {e}")
            return None


    async def _load_examples(self, job_type:str) -> Optional[List[BaseInterviewConfiguration]]:
        """
        Load example configuration based on job type
        """
        try:
            # we need to define the path relative to the root of the project
            root_path = Path(__file__).parent.parent
            examples_path = root_path / "onboarding_data" / "examples" / job_type 
            # add a slash to the end of the path
            examples_path_str = str(examples_path) + os.sep
            print (f"Examples path: {examples_path_str}")
            examples = []
            for example in os.listdir(examples_path_str):
                print (f"Example: {example}")
                example_path = os.path.join(examples_path_str, example)
                print (f"Example path: {example_path}")
                if os.path.isdir(example_path):
                    with open(example_path, 'r') as f:
                        example_data = json.load(f)
                        print (f"Example data: {example_data}")
                        examples.append(BaseInterviewConfiguration(**example_data))
                else:
                    print (f"Example path is not a directory: {example_path}")

            return examples
        except Exception as e:
            main_logger.error(f"Error loading examples for job type '{job_type}': {e}")
            return None

    
    async def _generate_candidate_profile(self, resume_content: str):
        """Generate candidate profile from resume content"""
        try:
            if not resume_content or not resume_content.strip():
                main_logger.warning("Empty resume content provided")
                return None
            
            candidate_generator = CandidateProfileGenerator(self.llm_provider)
            # For now, we'll pass the raw content. In a real implementation,
            # you might want to parse this into a structured format first
            profile = await candidate_generator.generate_candidate_profile(resume_content)
            
            if profile is None:
                main_logger.warning("Candidate profile generator returned None")
                return None
            
            main_logger.info(f"Successfully generated candidate profile")
            return profile
        except Exception as e:
            main_logger.error(f"Error generating candidate profile: {e}")
            return None
    
    async def _generate_characters(
        self, 
        interview_agent: Interview, 
        request: CharacterGenerationRequest,
        job_details: JobDetails
    ) -> Optional[CharacterDataOutput]:
        """Generate interview panel characters using existing Interview agent"""
        try:
            # Create example character data for the prompt
            example_character_data = CharacterDataOutput()
            # You might want to load this from existing templates or create a basic example
            
            characters = await interview_agent.get_character_information(example_character_data)
            return characters
        except Exception as e:
            print(f"Error generating characters: {e}")
            return None
    
    async def _generate_question_and_code(
        self,
        interview_agent: Interview,
        request: QuestionGenerationRequest,
        job_details: JobDetails
    ) -> tuple[Optional[ActivityDetailsOutputMessage], Optional[StarterCodeData]]:
        """Generate coding question and starter code using existing Interview agent"""
        try:
            # Create example data for prompts
            example_job_details = job_details
            example_activity_output = ActivityDetailsOutputMessage()
            example_activity_output.scenario = f"Create a {request.programming_language} solution for a {request.difficulty_level} level problem"
            example_activity_output.task_for_the_candidate = request.requirements
            
            # Generate activity details
            activity_details = await interview_agent.run_activity_details(
                example_job_details, 
                example_activity_output
            )
            
            # Generate starter code
            example_starter_code = StarterCodeData()
            example_starter_code.description = f"Starter code for {request.programming_language} problem"
            
            starter_code = await interview_agent.run_starter_code(
                example_activity_output,
                example_starter_code,
                activity_details
            )
            
            return activity_details, starter_code
            
        except Exception as e:
            print(f"Error generating question and code: {e}")
            return None, None
    
    def _assemble_master_config(
        self,
        interview_config: BaseInterviewConfiguration,
        characters: Optional[CharacterDataOutput],
        activity_details: Optional[ActivityDetailsOutputMessage],
        starter_code: Optional[StarterCodeData],
        candidate_profile: Optional[Any]
    ) -> BaseMasterConfiguration:
        """Assemble final BaseMasterConfiguration"""
        master_config = BaseMasterConfiguration()
        master_config.simulation_id = self._generate_config_id()
        master_config.simulation_name = f"interview_{interview_config.job_details.job_title.lower().replace(' ', '_')}"
        master_config.interview_data = interview_config
        
        # Set generated data
        if characters:
            master_config.interview_data.character_data = characters
        
        if activity_details:
            master_config.interview_data.activity_details = activity_details
        
        return master_config
    
    async def _store_configuration(
        self,
        config_id: str,
        invitation_code: str,
        master_config: BaseMasterConfiguration,
        user_id: str,
        config_input: FrontendConfigurationInput
    ):
        """Store configuration in database"""
        try:
            from interview_configuration.database_service import InterviewConfigurationDatabase
            from datetime import datetime

            db = InterviewConfigurationDatabase()

            # Build configuration data for storage
            config_data = {
                "id": config_id,
                "configuration_id": config_id,
                "invitation_code": invitation_code,
                "user_id": user_id,
                "company_id": user_id if config_input.user_mode == "company" else None,
                "simulation_config": master_config.model_dump(),
                "template_name": config_input.template_name,
                "is_template": config_input.save_as_template,
                "user_mode": config_input.user_mode,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store in database
            await db.create_interview_configuration(config_data)
            print(f"Configuration {config_id} with invitation code {invitation_code} stored for user {user_id}")

        except Exception as e:
            print(f"Error storing configuration: {e}")
            raise
    
    def _generate_config_id(self) -> str:
        """Generate unique configuration ID"""
        timestamp = int(datetime.now().timestamp())
        unique_id = uuid.uuid4().hex[:8]
        config_id = f"config_{timestamp}_{unique_id}"
        main_logger.info(f"Generated configuration ID: {config_id}")
        return config_id

    def _generate_invitation_code(self) -> str:
        """
        Generate a short, memorable invitation code
        Format: ABC123 (3 uppercase letters + 3 digits)
        """
        import random
        import string

        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        digits = ''.join(random.choices(string.digits, k=3))
        return f"{letters}{digits}"

    def _read_pdf_file(self, file_path: str) -> Optional[str]:
        """Read PDF file content"""
        try:
            # Try to use PyPDF2 first
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            except ImportError:
                # Fallback to pdfplumber
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                        return text
                except ImportError:
                    # If neither library is available, return a placeholder
                    main_logger.warning(f"PDF reading libraries not available. Install PyPDF2 or pdfplumber")
                    return "PDF content placeholder - install PyPDF2 or pdfplumber for actual PDF reading"
        except Exception as e:
            main_logger.error(f"Error reading PDF file {file_path}: {e}")
            return None


    def _parse_resume_file(self, file_path: str) -> Optional[str]:
        """Parse resume file content"""
        try:
            # Use the existing resume parser from utils
            resume_data = parse_resume(file_path)
            if not resume_data:
                main_logger.warning(f"Resume parser returned empty data for {file_path}")
                return None
            return resume_data
        except Exception as e:
            main_logger.error(f"Error parsing resume file {file_path}: {e}")
            return None
