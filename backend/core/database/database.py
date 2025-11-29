import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

import firebase_admin
import requests
from firebase_admin import auth, credentials, firestore, storage
from firebase_admin.auth import UserNotFoundError

from activity_agent.base import (
    ActivityProgressAnalysisOutputMessage,
    ActivityProgressAnalysisSummaryForPanelistOutputMessage,
    ActivityProgressWithRespectToQuestionOutputMessage,
)
from evaluation_agent.base import (
    SubqueryDataExtractionOutputMessage,
    SubqueryGeneratorOutputMessage,
)
from master_agent.base import (
    CandidateEvaluationVisualisationReport,
    ConversationalAdviceOutputMessage,
    EvaluationMessageToFrontEnd,
    MasterChatMessage,
    QuestionSpecificEvaluationOutputMessage,
    SimulationIntroductionOutputMessage,
    SpeakerDeterminationOutputMessage,
    TopicSectionCompletionOutputMessage,
)
from panelist_agent.base import (
    DomainKnowledgeOutputMessage,
    EvaluationOutputMessage,
    ReasoningOutputMessage,
    ResponseOutputMessage,
    ResponseWithReasoningOutputMessage,
)


@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str
    company_name: str
    job_title: str
    location: str
    auth_code: str
    resume_url: Optional[str] = None
    starter_code_url: Optional[str] = None
    profile_json_url: Optional[str] = None
    simulation_config_json_url: Optional[str] = None
    panelist_profiles: Optional[List[str]] = None
    panelist_images: Optional[List[str]] = None
    created_at: Optional[str] = None
    role: Optional[str] = "candidate"  # candidate, company_admin, super_admin
    organization_id: Optional[str] = None


class FireBaseDataBase:
    def __init__(
        self,
        logger=None,
        credentials_path: Optional[str] = None,
        storage_bucket: Optional[str] = None,
    ):
        self.user_data: UserProfile = UserProfile(
            user_id="", name="", email="", company_name="", job_title="", location="", auth_code=""
        )
        self.logger = logger
        self.pending_batch_operations = []
        self.batch_size_limit = 5

        # Initialize Firebase if not already done
        self._initialize_firebase(credentials_path, storage_bucket)

        # Set up clients
        self.db = firestore.client()
        self.bucket = storage.bucket()

        if self.logger is not None:
            self.logger.info("Firebase initialized successfully.")

    def _initialize_firebase(
        self, credentials_path: Optional[str] = None, storage_bucket: Optional[str] = None
    ):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                if self.logger is not None:
                    self.logger.info("Firebase already initialized, skipping initialization.")
                return

            # Determine credentials path
            if credentials_path:
                cred_path = credentials_path
            else:
                # Fallback to environment variable or default path
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
                if not cred_path:
                    # Default fallback path
                    root_path = Path(__file__).parent.parent.parent.parent
                    cred_path = str(root_path / "backend" / "interview-simulation-firebase.json")

            # Determine storage bucket
            if not storage_bucket:
                storage_bucket = os.getenv(
                    "FIREBASE_STORAGE_BUCKET", "interview-simulation-c96c7.firebasestorage.app"
                )

            # Initialize Firebase
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
                if self.logger is not None:
                    self.logger.info(f"Firebase initialized with credentials from: {cred_path}")
            else:
                if self.logger is not None:
                    self.logger.warning(f"Firebase credentials file not found at: {cred_path}")
                # Try to initialize with default credentials
                firebase_admin.initialize_app()

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Failed to initialize Firebase: {e}")
            raise

    # TODO: We cannot directly add data to the database since every data is being converted into a specific format first. Lets fix this later.
    def add_to_batch(self, user_id, session_id, operation_type, data, collection_path):
        """Adds an operation to the batch queue"""
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
            self.commit_batch()

    def commit_batch(self):
        """Commits the batch to Firestore"""
        if not self.pending_batch_operations:
            return
        try:
            batch = self.db.batch()
            for operation in self.pending_batch_operations:
                doc_ref = (
                    self.db.collection("users")
                    .document(operation["user_id"])
                    .collection("sessions")
                    .document(operation["session_id"])
                    .collection(operation["collection_path"])
                    .document()
                )
                batch.set(doc_ref, operation["data"])
            batch.commit()
            self.pending_batch_operations = []

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error committing batch: {e}")
            self.fallback_individual_writes()

    def fallback_individual_writes(self):
        for operation in self.pending_batch_operations:
            try:
                doc_ref = (
                    self.db.collection("users")
                    .document(operation["user_id"])
                    .collection("sessions")
                    .document(operation["session_id"])
                    .collection(operation["collection_path"])
                    .document()
                )
                doc_ref.set(operation["data"])
            except Exception as e:
                if self.logger is not None:
                    self.logger.error(f"Error writing individual document: {e}")
        self.pending_batch_operations = []

    def set_logger(self, logger):
        """Set the logger for the class"""
        self.logger = logger
        if self.logger is not None:
            self.logger.info("Logger set successfully.")

    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Fetches user_id from Firebase Auth using email.
        Returns the user ID if the user exists and email is valid.
        Returns None if the user doesn't exist or the email is invalid.
        """
        try:
            user = auth.get_user_by_email(email)
            return user.uid

        except UserNotFoundError:
            if self.logger is not None:
                self.logger.error(f"User with email {email} not found.")
            return None
        except ValueError as ve:
            if self.logger is not None:
                self.logger.error(f"Invalid email format: {email}. Error: {ve}")
            return None
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"An error occurred while fetching user ID: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Fetch user details and return a structured UserProfile object"""
        doc_ref = self.db.collection("users").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return UserProfile(**doc.to_dict())
        return None

    def load_user_data(self, user_id) -> bool:
        """Fetch user details and return a structured UserProfile object"""

        doc_ref = self.db.collection("users").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            user_data = doc.to_dict()
            self.user_data = UserProfile(**user_data)  # Convert dict to dataclass
            return True

        return False

    def create_new_session(self, user_id):
        """Creates a new session for a user when they log in"""
        session_id = datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )  # Generate a session ID (timestamp-based)

        session_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
        )

        # Call `.set()` to create a session document
        session_ref.set({"start_time": datetime.now().isoformat(), "status": "active"})

        if self.logger is not None:
            self.logger.info(f"New session created with ID: {session_id} for user: {user_id}")
        self.session_id = session_id
        return session_id

    def add_activity_progress_analysis_output_to_database(
        self, user_id, session_id, output: ActivityProgressAnalysisOutputMessage
    ):
        """Add activity progress analysis output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("activity_progress_analysis_output")
        )

        output_data = {
            "activity_progress": output.model_dump_json(),
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Activity progress analysis output added successfully.")

    def add_activity_progress_analysis_summary_for_panelist_output_to_database(
        self, user_id, session_id, output: ActivityProgressAnalysisSummaryForPanelistOutputMessage
    ):
        """Add activity progress analysis summary for panelist output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("activity_progress_analysis_summary_for_panelist_output")
        )

        output_data = {
            "activity_progress_summary_for_panelist": output.model_dump_json(),
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info(
                "Activity progress analysis summary for panelist output added successfully."
            )

    def get_activity_progress_analysis_output_from_database(
        self, user_id, session_id
    ) -> Optional[Dict[str, Any]]:
        """Get activity progress analysis output from Firestore"""
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("activity_progress_analysis_summary_for_panelist_output")
        )
        query = output_ref.order_by("__name__", direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        for doc in results:
            if self.logger is not None:
                self.logger.info(f"Most recent activity progress analysis output: {doc.to_dict()}")
            return doc.to_dict()
        if self.logger is not None:
            self.logger.warning("No activity progress analysis output found.")
        return None

    def add_activity_code_to_database(self, user_id, session_id, activity_code):
        """Add activity code to Firestore"""
        activity_code_id = datetime.now().isoformat()

        activity_code_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("activity_code")
        )

        activity_code_data = {"activity_code": activity_code}

        activity_code_ref.document(activity_code_id).set(activity_code_data)

        if self.logger is not None:
            self.logger.info("Activity code added successfully.")

    def add_activity_progress_with_respect_to_question_output_to_database(
        self, user_id, session_id, output: ActivityProgressWithRespectToQuestionOutputMessage
    ):
        """Add activity progress with respect to question output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("activity_progress_with_respect_to_question_output")
        )

        output_data = {
            "activity_progress_with_respect_to_question": output.model_dump_json(),
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info(
                "Activity progress with respect to question output added successfully."
            )

    def add_subtopic_summary_to_database(
        self, user_id, session_id, current_interview_round, topic_name, subtopic_name, summary
    ):
        """Add subtopic summary to Firestore"""
        summary_id = datetime.now().isoformat()

        summary_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("subtopic_summary")
        )

        summary_data = {
            "interview_round": current_interview_round,
            "topic": topic_name,
            "subtopic": subtopic_name,
            "summary": summary,
        }

        summary_ref.document(summary_id).set(summary_data)

        if self.logger is not None:
            self.logger.info("Subtopic summary added successfully.")

    def add_panelist_evaluation_to_database(
        self, user_id, session_id, panelist_name, evaluation_output: EvaluationOutputMessage
    ):
        """Add panelist evaluation output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("panelist_evaluation")
        )

        output_data = {"panelist": panelist_name, "evaluation": evaluation_output.model_dump_json()}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Panelist evaluation output added successfully.")

    def add_topic_summary_to_database(
        self, user_id, session_id, current_interview_round, topic_name, summary_data
    ):
        """Add topic summary to Firestore"""
        summary_id = datetime.now().isoformat()

        summary_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("topic_summary")
        )

        summary_data = {"interview_round": current_interview_round, "topic": topic_name}

        summary_ref.document(summary_id).set(summary_data)

        if self.logger is not None:
            self.logger.info("Topic summary added successfully.")

    def add_panelist_reasoning_to_database(
        self, user_id, session_id, panelist_name, reasoning_output: ReasoningOutputMessage
    ):
        """Add panelist reasoning output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("panelist_reasoning")
        )

        output_data = {"panelist": panelist_name, "reasoning": reasoning_output.model_dump_json()}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Panelist reasoning output added successfully.")

    def add_panelist_domain_knowledge_to_database(
        self,
        user_id,
        session_id,
        panelist_name,
        domain_knowledge_output: DomainKnowledgeOutputMessage,
    ):
        """Add panelist domain knowledge output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("panelist_domain_knowledge")
        )

        output_data = {
            "panelist": panelist_name,
            "domain_knowledge": domain_knowledge_output.model_dump_json(),
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Panelist domain knowledge output added successfully.")

    def add_panelist_response_to_database(
        self, user_id, session_id, panelist_name, response_output: ResponseOutputMessage
    ):
        """Add panelist response output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("panelist_response")
        )

        output_data = {"panelist": panelist_name, "response": response_output.model_dump_json()}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Panelist response output added successfully.")

    def add_panelist_response_with_reasoning_to_database(
        self, user_id, session_id, panelist_name, output: ResponseWithReasoningOutputMessage
    ):
        """Add panelist response with reasoning output to Firestore"""
        output_id = datetime.now().isoformat()
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("panelist_response_with_reasoning")
        )
        output_data = {
            "panelist": panelist_name,
            "response_with_reasoning": output.model_dump_json(),
        }
        output_ref.document(output_id).set(output_data)
        if self.logger is not None:
            self.logger.info("Panelist response with reasoning output added successfully.")

    def add_introduction_output_to_database(
        self, user_id, session_id, output: SimulationIntroductionOutputMessage
    ):
        """Add simulation introduction output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("simulation_introduction_output")
        )

        panelist_json_data = [panelist.model_dump_json() for panelist in output.panelists]
        output_data = {"introduction": output.introduction, "panelists": panelist_json_data}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Simulation introduction output added successfully.")

    def add_dialog_to_database(self, user_id, session_id, message: MasterChatMessage):
        """Check if the conversation exists; if not, create it. Then, append a message."""
        message_id = datetime.now().isoformat()  # Unique message ID based on timestamp

        conversation_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("interview_transcript")
        )

        message_data = {"speaker": message.speaker, "dialog": message.content}

        conversation_ref.document(message_id).set(message_data)

        if self.logger is not None:
            self.logger.info(
                f"Message added to conversation: {message.speaker} - {message.content}"
            )

    def add_speaker_determination_output_to_database(
        self, user_id, session_id, output: SpeakerDeterminationOutputMessage
    ):
        """Add speaker determination output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("speaker_determination_output")
        )

        output_data = {
            "next_speaker": output.next_speaker,
            "reason": output.reason_for_selecting_next_speaker,
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Speaker determination output added successfully.")

    def add_conversational_advice_output_to_database(
        self, user_id, session_id, output: ConversationalAdviceOutputMessage
    ):
        """Add conversational advice output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("conversational_advice_output")
        )

        output_data = {
            "advice_for_speaker": output.advice_for_speaker,
            "should_wrap_up_current_topic": output.should_wrap_up_current_topic,
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Conversational advice output added successfully.")

    def add_topic_section_completion_output_to_database(
        self, user_id, session_id, topic_name, output: TopicSectionCompletionOutputMessage
    ):
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("topic_section_completion_output")
        )

        output_data = {"topic": topic_name, "decision": output.decision, "reason": output.reason}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Topic section completion output added successfully.")

    def add_evaluation_output_to_database(
        self, user_id, session_id, output: QuestionSpecificEvaluationOutputMessage
    ):
        """Add evaluation output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("evaluation_output")
        )

        question_criteria_specific_scoring_json_list = (
            [
                criteria_scoring.model_dump_json()
                for criteria_scoring in output.question_criteria_specific_scoring
            ]
            if output.question_criteria_specific_scoring is not None
            else []
        )

        output_data = {
            "question_criteria_specific_scoring": question_criteria_specific_scoring_json_list
        }

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Evaluation output added successfully.")

    def add_subquery_data_to_database(
        self, user_id, session_id, output: SubqueryGeneratorOutputMessage
    ):
        """Add subquery data to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("subquery_data")
        )

        output_data = {"subquery_data": output.model_dump_json()}
        output_ref.document(output_id).set(output_data)
        if self.logger is not None:
            self.logger.info("Subquery data added successfully.")

    def add_subquery_data_extraction_output_to_database(
        self, user_id, session_id, output: SubqueryDataExtractionOutputMessage
    ):
        """Add subquery data extraction output to Firestore"""
        output_id = datetime.now().isoformat()

        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("subquery_data_extraction_output")
        )

        output_data = {"subquery_data_extraction": output.model_dump_json()}

        output_ref.document(output_id).set(output_data)

        if self.logger is not None:
            self.logger.info("Subquery data extraction output added successfully.")

    def add_metadata_to_database(self, user_id, session_id, is_interview_completed):
        """Add metadata to Firestore"""
        # we should keep replacing the metadata document with the same id
        metadata_id = "metadata"  # Use a fixed ID for metadata document
        # This will replace the document if it already exists
        # If you want to keep multiple metadata documents, you can use a timestamp or unique ID
        # metadata_id = datetime.now().isoformat()

        metadata_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("metadata")
        )

        metadata_data = {"is_interview_completed": is_interview_completed}

        metadata_ref.document(metadata_id).set(metadata_data)

        if self.logger is not None:
            self.logger.info("Metadata added successfully.")

    def get_metadata_from_database(self, user_id, session_id):
        """Get metadata from Firestore"""
        metadata_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("metadata")
        )

        docs = metadata_ref.stream()
        for doc in docs:
            return doc.to_dict()

        if self.logger is not None:
            self.logger.warning("No metadata found.")
        return None

    def add_final_evaluation_output_to_database(
        self, user_id, session_id, output: EvaluationMessageToFrontEnd
    ):
        """Add final evaluation output to Firestore"""
        output_id = datetime.now().isoformat()
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("final_evaluation_output")
        )
        output_data = {"final_evaluation": output.model_dump_json()}
        output_ref.document(output_id).set(output_data)
        if self.logger is not None:
            self.logger.info("Final evaluation output added successfully.")

    def add_final_visualisation_report_to_database(
        self, user_id, session_id, output: CandidateEvaluationVisualisationReport
    ):
        """Add final visualisation report to Firestore"""
        output_id = datetime.now().isoformat()
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("final_visualisation_report")
        )
        output_data = {"visualisation_report": output.model_dump_json()}
        output_ref.document(output_id).set(output_data)
        if self.logger is not None:
            self.logger.info("Final visualisation report added successfully.")

    def get_final_visualisation_report_from_database(self, user_id, session_id):
        # get the most recent final visualisation report
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("final_visualisation_report")
        )
        query = output_ref.order_by("__name__", direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        for doc in results:
            if self.logger is not None:
                self.logger.info(f"Most recent final visualisation report: {doc.to_dict()}")
            return doc.to_dict()
        if self.logger is not None:
            self.logger.warning("No final visualisation report found.")
        return None

    def get_final_evaluation_output_from_database(self, user_id, session_id):
        # get the most recent final evaluation output
        output_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection("final_evaluation_output")
        )
        query = output_ref.order_by("__name__", direction=firestore.Query.DESCENDING).limit(1)
        results = query.stream()
        for doc in results:
            if self.logger is not None:
                self.logger.info(f"Most recent final evaluation output: {doc.to_dict()}")
            return doc.to_dict()
        if self.logger is not None:
            self.logger.warning("No final evaluation output found.")
        return None

    def add_json_data_output_to_database(self, user_id, session_id, name, json_data):
        """Add JSON data output to Firestore"""
        output_id = datetime.now().isoformat()
        json_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection(name)
        )
        json_val = {"json_data": json_data}
        json_ref.document(output_id).set(json_val)
        if self.logger is not None:
            self.logger.info("JSON data output added successfully.")

    def get_json_data_output_from_database(self, name, user_id, session_id):
        """Get JSON data output from Firestore"""
        json_ref = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(session_id)
            .collection(name)
        )
        docs = json_ref.stream()
        for doc in docs:
            return doc.to_dict()
        if self.logger is not None:
            self.logger.warning(f"No JSON data found in {name}.")
        return None

    def get_profile_json_url(self):
        """Fetch URL of the user's profile JSON file from Firestore"""
        return self.user_data.profile_json_url

    def get_profile_json_data(self):
        """Fetch user profile JSON data from Firestore"""
        json_url = self.get_profile_json_url()
        return self.fetch_json_from_url(json_url)

    def get_panelists_json_urls(self):
        """Fetch URLs of the panelists' profile JSON files from Firestore"""
        return self.user_data.panelist_profiles

    def get_panelist_profile_json_data(self, panelist_name):
        """Fetch panelist profile JSON data from Firestore"""
        panelist_profiles = self.get_panelists_json_urls()
        if panelist_profiles is None:
            if self.logger is not None:
                self.logger.warning("No panelist profiles found.")
            return None

        for profile_url in panelist_profiles:
            filename = self.get_file_name_from_url(profile_url)
            if panelist_name in filename:
                return self.fetch_json_from_url(profile_url)
        return None

    def fetch_json_from_url(self, json_url):
        """Fetch JSON data from a public Firebase Storage URL and bust cache."""
        # Append a timestamp or version to bust cache
        version = int(time.time())  # Current timestamp
        updated_url = f"{json_url}?v={version}"  # Cache-busting URL
        response = requests.get(updated_url)
        if response.status_code == 200:
            return response.json()  # Convert response to Python dictionary
        else:
            if self.logger is not None:
                self.logger.error(f"Failed to fetch JSON data. Status Code: {response.status_code}")
            return None

    def get_simulation_config_json_url(self):
        """Fetch URL of the simulation configuration JSON file from Firestore"""
        return self.user_data.simulation_config_json_url

    def get_simulation_config_json_data(self):
        """Fetch simulation configuration JSON data from Firestore"""
        json_url = self.get_simulation_config_json_url()
        return self.fetch_json_from_url(json_url)

    def get_starter_code_url(self):
        """Fetch URL of the starter code from Firestore"""
        return self.user_data.starter_code_url

    def fetch_starter_code_from_url(self) -> Optional[str]:
        """Fetch starter code from a public Firebase Storage URL and bust cache."""
        # Append a timestamp or version to bust cache
        version = int(time.time())
        updated_url = f"{self.user_data.starter_code_url}?v={version}"  # Cache-busting URL
        response = requests.get(updated_url)
        if response.status_code == 200:
            return (
                response.content.decode("utf-8")
                if isinstance(response.content, bytes)
                else response.content
            )
        else:
            if self.logger is not None:
                self.logger.error(
                    f"Failed to fetch starter code. Status Code: {response.status_code}"
                )
            return None

    def get_resume_url(self):
        """Fetch URL of the user's resume from Firestore"""
        return self.user_data.resume_url

    def get_panelist_images_urls(self):
        """Fetch URLs of the panelists' images from Firestore"""
        return self.user_data.panelist_images

    def get_file_name_from_url(self, json_url):
        """Extract file name from Firebase Storage URL"""
        parsed_url = urlparse(json_url)
        path = unquote(parsed_url.path)  # Decode URL-encoded characters
        return path.split("/")[-1]  # Extract the last segment as file name

    def get_image_url_from_name(self, image_name):
        panelist_images_url = self.get_panelist_images_urls()
        if self.logger is not None:
            self.logger.info(f"Panelist images URLs: {panelist_images_url}")

        if panelist_images_url is None:
            if self.logger is not None:
                self.logger.warning("No panelist images URLs found.")
            return None

        for image_url in panelist_images_url:
            filename = self.get_file_name_from_url(image_url)
            if self.logger is not None:
                self.logger.info(f"Image URL: {image_url}, File Name: {filename}")
            if filename == image_name:
                if self.logger is not None:
                    self.logger.info(f"Found image URL: {image_url} for image name: {image_name}")
                return image_url
        return None

    def get_image_url(self, user_id, file_name, cache_bust: bool = True):
        """
        Fetch the public URL of a user's image from Firebase Storage.
        Adds a cache-busting query parameter to force updated image retrieval if enabled.
        """
        blob = self.bucket.blob(f"users/{user_id}/{file_name}")
        if blob.exists():
            url = blob.public_url
            if cache_bust:
                url += f"?cacheBust={int(time.time())}"
            return url
        else:
            if self.logger is not None:
                self.logger.error(f"Image not found: {file_name}")
            return None

    def upload_image(self, image_path, user_id, file_name):
        """Uploads an image to Firebase Storage inside the user's folder"""
        blob = self.bucket.blob(
            f"users/{user_id}/{file_name}"
        )  # Example: users/{user_id}/profile_pic.jpg
        blob.upload_from_filename(
            image_path, content_type="image/jpeg"
        )  # Change content_type based on format
        blob.make_public()  # Optional: Make public or use signed URLs for security
        return blob.public_url  # Return URL of the uploaded image

    def upload_video(self, user_id, session_id, filename, content, content_type):
        """Uploads a video to Firebase Storage inside the user's folder"""
        # Step 2: Upload to Firebase
        blob = self.bucket.blob(f"recordings/{user_id}/{session_id}/{filename}")
        blob.upload_from_string(content, content_type=content_type)
        blob.make_public()  # Optional: Make public or use signed URLs for security
        return blob.public_url  # Return URL of the uploaded video

    def get_all_video_urls(self, user_id: str, session_id: str) -> list:
        """Returns a list of public URLs for all video chunks under a given session."""
        prefix = f"recordings/{user_id}/{session_id}/"
        blobs = self.bucket.list_blobs(prefix=prefix)

        urls = []
        for blob in blobs:
            if blob.name.endswith(".webm"):  # filter only video chunks
                urls.append(blob.public_url)

        if not urls:
            if self.logger is not None:
                self.logger.warning(f"No video chunks found for session: {session_id}")

        return urls

    def upload_file(self, file_path, user_id, file_name):
        """Uploads a file (PDF, JSON) to Firebase Storage inside the user's folder"""
        blob = self.bucket.blob(
            f"users/{user_id}/{file_name}"
        )  # Folder structure: users/{user_id}/
        blob.upload_from_filename(file_path)
        blob.cache_control = "no-cache, max-age=0"
        blob.patch()
        blob.make_public()

        return blob.public_url  # Return the URL of the uploaded file

    def upload_json(self, user_id, json_data, filename):
        """Uploads a JSON file to Firebase Storage"""
        blob = self.bucket.blob(f"users/{user_id}/{filename}.json")
        blob.upload_from_string(json.dumps(json_data), content_type="application/json")
        blob.make_public()
        return blob.public_url

    def get_most_recent_session_id_by_user_id(self, user_id: str) -> Optional[str]:
        """Fetches the most recent session ID for a specific user_id based on timestamp-named documents"""
        try:
            sessions_ref = self.db.collection("users").document(user_id).collection("sessions")
            query = sessions_ref.order_by("__name__", direction=firestore.Query.DESCENDING).limit(1)
            results = query.stream()

            for doc in results:
                if self.logger is not None:
                    self.logger.info(f"Most recent session ID for user {user_id}: {doc.id}")
                return doc.id

            if self.logger is not None:
                self.logger.warning(f"No sessions found for user: {user_id}")
            return None

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error while fetching recent session ID for user {user_id}: {e}")
            return None

    def get_all_users_data(self) -> List[UserProfile]:
        """Fetches all user data from Firestore and returns a list of UserProfile objects"""
        try:
            users_ref = self.db.collection("users")
            users = users_ref.stream()
            user_profiles = []

            for user in users:
                user_data = user.to_dict()
                user_profile = UserProfile(**user_data)  # Convert dict to dataclass
                user_profiles.append(user_profile)

            if self.logger is not None:
                self.logger.info(f"Fetched all user profiles: {user_profiles}")
            return user_profiles

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error while fetching all users data: {e}")
            return []

    def get_all_users(self) -> List[str]:
        """Fetches all user IDs from Firebase Auth"""
        try:
            users = auth.list_users().users
            user_ids = [user.uid for user in users]
            if self.logger is not None:
                self.logger.info(f"Fetched all user IDs: {user_ids}")
            return user_ids

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error while fetching all users: {e}")
            return []

    def get_all_session_data(self, user_id, session_id=None) -> dict:
        """
        Fetches all data from all subcollections under a specific session.
        If no session_id is passed, uses self.session_id.
        Returns a nested dictionary: {subcollection_name: {document_id: document_data, ...}, ...}
        """
        session_id = session_id or self.session_id
        result = {}

        try:
            session_doc_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
            )
            subcollections = session_doc_ref.list_collections()

            for subcol in subcollections:
                subcol_name = subcol.id
                docs = subcol.stream()
                result[subcol_name] = {}

                for doc in docs:
                    result[subcol_name][doc.id] = doc.to_dict()

            if self.logger is not None:
                self.logger.info(f"Fetched all data for session: {session_id}")
            return result

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Failed to fetch all session data: {e}")
            return {}

    def get_recent_code_data(self, user_id):
        """Fetches the most recent code data from Firestore"""
        try:
            session_id = self.get_most_recent_session_id_by_user_id(user_id)
            if not session_id:
                if self.logger is not None:
                    self.logger.warning("No recent session found.")
                return None

            code_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
                .collection("activity_code")
            )
            query = code_ref.order_by("__name__", direction=firestore.Query.DESCENDING).limit(1)
            results = query.stream()

            for doc in results:
                if self.logger is not None:
                    self.logger.info(f"Most recent code data: {doc.to_dict()}")
                return doc.to_dict()

            if self.logger is not None:
                self.logger.warning("No code data found.")
            return None

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error while fetching recent code data: {e}")
            return None

    # Company Management Methods
    def create_company(self, company_data):
        """Create a new company in Firestore"""
        try:
            doc_ref = self.db.collection("companies").document(company_data["company_id"])
            doc_ref.set(company_data)

            if self.logger is not None:
                self.logger.info(f"Company created successfully: {company_data['company_id']}")
            return True
        except Exception as e:
            if self.logger is not None:
                self.logger.error(
                    f"Error creating company {company_data.get('company_id', 'unknown')}: {e}"
                )
            return False

    def get_company_by_id(self, company_id):
        """Get company by ID from Firestore"""
        try:
            doc_ref = self.db.collection("companies").document(company_id)
            doc = doc_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting company {company_id}: {e}")
            return None

    def get_company_by_email(self, email):
        """Get company by email from Firestore"""
        try:
            companies_ref = self.db.collection("companies")
            query = companies_ref.where("email", "==", email).limit(1)
            results = query.stream()

            for doc in results:
                return doc.to_dict()
            return None
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting company by email {email}: {e}")
            return None

    def update_company(self, company_id, updates):
        """Update company in Firestore"""
        try:
            if not updates:
                return True

            # Add updated_at timestamp
            updates["updated_at"] = datetime.now().isoformat()

            doc_ref = self.db.collection("companies").document(company_id)
            doc_ref.update(updates)

            if self.logger is not None:
                self.logger.info(f"Company updated successfully: {company_id}")
            return True
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error updating company {company_id}: {e}")
            return False

    def delete_company(self, company_id):
        """Delete company from Firestore"""
        try:
            doc_ref = self.db.collection("companies").document(company_id)
            doc_ref.delete()

            if self.logger is not None:
                self.logger.info(f"Company deleted successfully: {company_id}")
            return True
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error deleting company {company_id}: {e}")
            return False

    def search_companies_by_name(self, name):
        """Search companies by name in Firestore"""
        try:
            companies_ref = self.db.collection("companies")
            # Case-insensitive search (Firestore doesn't support case-insensitive queries natively)
            # This is a simple implementation - for production, consider using Algolia or similar
            query = companies_ref.where("name", ">=", name.lower()).where(
                "name", "<=", name.lower() + "\uf8ff"
            )
            results = query.stream()

            companies = []
            for doc in results:
                companies.append(doc.to_dict())

            return companies
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error searching companies by name {name}: {e}")
            return []

    def check_company_email_availability(self, email):
        """Check if company email is available"""
        try:
            company = self.get_company_by_email(email)
            return company is None
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error checking email availability {email}: {e}")
            return False

    def get_all_companies(self):
        """Get all companies from Firestore"""
        try:
            companies_ref = self.db.collection("companies")
            results = companies_ref.stream()

            companies = []
            for doc in results:
                companies.append(doc.to_dict())

            return companies
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting all companies: {e}")
            return []

    def validate_company_session(self, token):
        """Validate company session token"""
        try:
            # For now, we'll use a simple token validation
            # In production, this should validate JWT tokens or check session storage
            if token.startswith("mock_token_") or token.startswith("token_"):
                return True

            # TODO: Implement proper token validation
            # This could check Firebase Auth tokens or custom session storage
            return False
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error validating company session: {e}")
            return False

    # Dashboard and Candidate Management Methods
    def get_candidates_by_company_name(self, company_name):
        """Get all candidates for a specific company by company name"""
        try:
            users_ref = self.db.collection("users")
            query = users_ref.where("company_name", "==", company_name)
            results = query.stream()

            candidates = []
            for doc in results:
                user_data = doc.to_dict()
                candidates.append(user_data)

            if self.logger is not None:
                self.logger.info(f"Found {len(candidates)} candidates for company: {company_name}")
            return candidates
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting candidates by company name {company_name}: {e}")
            return []

    def get_candidates_by_company_id(self, company_id):
        """Get all candidates for a specific company by company ID"""
        try:
            # First get the company name from company_id
            company = self.get_company_by_id(company_id)
            if not company:
                if self.logger is not None:
                    self.logger.warning(f"Company not found: {company_id}")
                return []

            # Then get candidates by company name
            return self.get_candidates_by_company_name(company.get("name", ""))
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting candidates by company ID {company_id}: {e}")
            return []

    def get_candidate_evaluation_data(self, user_id, session_id=None):
        """Get evaluation data for a specific candidate"""
        try:
            if session_id:
                # Get evaluation for specific session
                evaluation_data = self.get_final_evaluation_output_from_database(
                    user_id, session_id
                )
                return evaluation_data
            else:
                # Get most recent session and its evaluation
                recent_session_id = self.get_most_recent_session_id_by_user_id(user_id)
                if recent_session_id:
                    evaluation_data = self.get_final_evaluation_output_from_database(
                        user_id, recent_session_id
                    )
                    return evaluation_data
            return None
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting evaluation data for candidate {user_id}: {e}")
            return None

    def get_candidate_interview_sessions(self, user_id):
        """Get all interview sessions for a candidate"""
        try:
            sessions_ref = self.db.collection("users").document(user_id).collection("sessions")
            results = sessions_ref.stream()

            sessions = []
            for doc in results:
                session_data = doc.to_dict()
                session_data["session_id"] = doc.id
                session_data["user_id"] = user_id
                sessions.append(session_data)

            # Sort by start_time descending (most recent first)
            sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

            if self.logger is not None:
                self.logger.info(f"Found {len(sessions)} sessions for candidate: {user_id}")
            return sessions
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting interview sessions for candidate {user_id}: {e}")
            return []

    def get_company_dashboard_data(self, company_id):
        """Get comprehensive dashboard data for a company"""
        try:
            # Get company info
            company = self.get_company_by_id(company_id)
            if not company:
                if self.logger is not None:
                    self.logger.warning(f"Company not found: {company_id}")
                return {}

            # Get all candidates for this company
            candidates = self.get_candidates_by_company_id(company_id)

            # Process candidate data
            total_candidates = len(candidates)
            completed_interviews = 0
            pending_interviews = 0
            total_score = 0
            scored_interviews = 0
            recent_interviews = []

            for candidate in candidates:
                user_id = candidate.get("user_id")
                if not user_id:
                    continue

                # Get candidate's sessions
                sessions = self.get_candidate_interview_sessions(user_id)

                if sessions:
                    # Check if any session is completed
                    has_completed = any(
                        session.get("status") == "completed" for session in sessions
                    )
                    if has_completed:
                        completed_interviews += 1

                        # Get evaluation data for most recent completed session
                        for session in sessions:
                            if session.get("status") == "completed":
                                evaluation = self.get_candidate_evaluation_data(
                                    user_id, session["session_id"]
                                )
                                if evaluation and "final_evaluation" in evaluation:
                                    try:
                                        eval_data = json.loads(evaluation["final_evaluation"])
                                        if "overall_score" in eval_data:
                                            total_score += eval_data["overall_score"]
                                            scored_interviews += 1

                                            # Add to recent interviews
                                            recent_interviews.append(
                                                {
                                                    "candidate_id": user_id,
                                                    "candidate_name": candidate.get(
                                                        "name", "Unknown"
                                                    ),
                                                    "email": candidate.get("email", ""),
                                                    "position": eval_data.get(
                                                        "position", "Unknown"
                                                    ),
                                                    "interview_date": session.get("start_time", ""),
                                                    "overall_score": eval_data["overall_score"],
                                                    "evaluation_id": session["session_id"],
                                                }
                                            )
                                    except (json.JSONDecodeError, KeyError) as e:
                                        if self.logger is not None:
                                            self.logger.warning(
                                                f"Error parsing evaluation data: {e}"
                                            )
                                break
                    else:
                        pending_interviews += 1
                else:
                    pending_interviews += 1

            # Calculate average score
            average_score = (
                round(total_score / scored_interviews, 2) if scored_interviews > 0 else 0
            )

            # Sort recent interviews by date and take top 5
            recent_interviews.sort(key=lambda x: x.get("interview_date", ""), reverse=True)
            recent_interviews = recent_interviews[:5]

            dashboard_data = {
                "company_info": {
                    "company_id": company_id,
                    "name": company.get("name", ""),
                    "industry": company.get("industry", ""),
                    "size": company.get("size", ""),
                    "location": company.get("location", ""),
                },
                "total_candidates": total_candidates,
                "completed_interviews": completed_interviews,
                "pending_interviews": pending_interviews,
                "average_score": average_score,
                "recent_interviews": recent_interviews,
            }

            if self.logger is not None:
                self.logger.info(
                    f"Generated dashboard data for company {company_id}: {total_candidates} candidates, {completed_interviews} completed"
                )

            return dashboard_data
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting dashboard data for company {company_id}: {e}")
            return {}

    def get_candidates_with_evaluations(self, company_id):
        """Get candidates with their evaluation data for a company"""
        try:
            # Get all candidates for this company
            candidates = self.get_candidates_by_company_id(company_id)

            candidates_with_evaluations = []
            for candidate in candidates:
                user_id = candidate.get("user_id")
                if not user_id:
                    continue

                # Get candidate's sessions
                sessions = self.get_candidate_interview_sessions(user_id)

                candidate_data = {
                    "candidate_id": user_id,
                    "name": candidate.get("name", "Unknown"),
                    "email": candidate.get("email", ""),
                    "company_name": candidate.get("company_name", ""),
                    "location": candidate.get("location", ""),
                    "status": "pending",
                    "interview_date": None,
                    "overall_score": None,
                    "evaluation_id": None,
                    "position": "Unknown",
                    "sessions": [],
                }

                if sessions:
                    # Check if any session is completed
                    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
                    if completed_sessions:
                        candidate_data["status"] = "completed"
                        # Get the most recent completed session
                        recent_session = completed_sessions[0]
                        candidate_data["interview_date"] = recent_session.get("start_time")
                        candidate_data["evaluation_id"] = recent_session.get("session_id")

                        # Get evaluation data
                        evaluation = self.get_candidate_evaluation_data(
                            user_id, recent_session.get("session_id")
                        )
                        if evaluation and "final_evaluation" in evaluation:
                            try:
                                eval_data = json.loads(evaluation["final_evaluation"])
                                candidate_data["overall_score"] = eval_data.get("overall_score")
                                candidate_data["position"] = eval_data.get("position", "Unknown")
                            except (json.JSONDecodeError, KeyError):
                                pass

                    # Add session data
                    for session in sessions:
                        session_data = {
                            "session_id": session.get("session_id"),
                            "start_time": session.get("start_time"),
                            "status": session.get("status"),
                            "end_time": session.get("end_time"),
                        }
                        candidate_data["sessions"].append(session_data)

                candidates_with_evaluations.append(candidate_data)

            if self.logger is not None:
                self.logger.info(
                    f"Retrieved {len(candidates_with_evaluations)} candidates with evaluations for company {company_id}"
                )

            return candidates_with_evaluations
        except Exception as e:
            if self.logger is not None:
                self.logger.error(
                    f"Error getting candidates with evaluations for company {company_id}: {e}"
                )
            return []

    def get_company_interviews(self, company_id):
        """Get all interviews/job postings for a company"""
        try:
            # First get the company name from company_id
            company = self.get_company_by_id(company_id)
            if not company:
                if self.logger is not None:
                    self.logger.warning(f"Company not found: {company_id}")
                return []

            company_name = company.get("name", "")

            # Get all candidates for this company to calculate statistics
            candidates = self.get_candidates_by_company_name(company_name)

            # Group candidates by job_title to create interview entries
            job_interviews = {}
            for candidate in candidates:
                job_title = candidate.get("job_title", "Unknown Position")

                if job_title not in job_interviews:
                    job_interviews[job_title] = {
                        "candidates": [],
                        "total_candidates": 0,
                        "completed_candidates": 0,
                        "scores": [],
                    }

                job_interviews[job_title]["candidates"].append(candidate)
                job_interviews[job_title]["total_candidates"] += 1

                # Check if candidate has completed interview
                user_id = candidate.get("user_id")
                if user_id:
                    sessions = self.get_candidate_interview_sessions(user_id)
                    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
                    if completed_sessions:
                        job_interviews[job_title]["completed_candidates"] += 1

                        # Get evaluation score
                        for session in completed_sessions:
                            evaluation = self.get_candidate_evaluation_data(
                                user_id, session.get("session_id")
                            )
                            if evaluation and "final_evaluation" in evaluation:
                                try:
                                    import json

                                    eval_data = json.loads(evaluation["final_evaluation"])
                                    if "overall_score" in eval_data:
                                        job_interviews[job_title]["scores"].append(
                                            eval_data["overall_score"]
                                        )
                                except (json.JSONDecodeError, KeyError):
                                    pass
                                break

            # Convert to interview list format
            interviews = []
            for job_title, data in job_interviews.items():
                # Calculate average score
                avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0

                # Create interview entry
                interview = {
                    "id": f"interview_{hash(f'{company_id}_{job_title}') % 10000}",
                    "name": f"{job_title} Interview",
                    "job_title": job_title,
                    "department": self._get_department_from_title(job_title),
                    "total_candidates": data["total_candidates"],
                    "completed_candidates": data["completed_candidates"],
                    "average_score": round(avg_score, 2),
                    "status": "active",
                    "created_date": min(
                        [c.get("created_at", "") for c in data["candidates"]]
                        + [datetime.now().isoformat()]
                    ),
                    "last_activity": max(
                        [c.get("created_at", "") for c in data["candidates"]]
                        + [datetime.now().isoformat()]
                    ),
                    "job_description": f"{job_title} position at {company_name}",
                    "requirements": self._get_requirements_from_title(job_title),
                }
                interviews.append(interview)

            # Sort by created_date descending
            interviews.sort(key=lambda x: x.get("created_date", ""), reverse=True)

            if self.logger is not None:
                self.logger.info(f"Found {len(interviews)} interviews for company: {company_id}")
            return interviews

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting interviews for company {company_id}: {e}")
            return []

    def _get_department_from_title(self, job_title):
        """Helper to determine department from job title"""
        title_lower = job_title.lower()
        if any(
            tech in title_lower
            for tech in ["engineer", "developer", "software", "frontend", "backend", "fullstack"]
        ):
            return "Engineering"
        elif any(ml in title_lower for ml in ["ml", "machine learning", "data scientist", "ai"]):
            return "AI/ML"
        elif any(design in title_lower for design in ["design", "ui", "ux"]):
            return "Design"
        elif any(product in title_lower for product in ["product", "pm"]):
            return "Product"
        elif any(marketing in title_lower for marketing in ["marketing", "growth"]):
            return "Marketing"
        else:
            return "Other"

    def _get_requirements_from_title(self, job_title):
        """Helper to determine requirements from job title"""
        title_lower = job_title.lower()
        if "frontend" in title_lower:
            return ["React", "TypeScript", "CSS", "JavaScript"]
        elif "backend" in title_lower:
            return ["Python", "FastAPI", "Database", "API Design"]
        elif "fullstack" in title_lower or "full stack" in title_lower:
            return ["React", "Python", "Database", "API Design"]
        elif any(ml in title_lower for ml in ["ml", "machine learning", "data scientist"]):
            return ["Python", "TensorFlow", "Machine Learning", "Data Analysis"]
        elif "engineer" in title_lower:
            return ["Programming", "Problem Solving", "System Design"]
        else:
            return ["Communication", "Problem Solving", "Domain Knowledge"]

    def get_interview_candidates(self, company_id, interview_id):
        """Get candidates for a specific interview/job posting"""
        try:
            # First get the company name from company_id
            company = self.get_company_by_id(company_id)
            if not company:
                if self.logger is not None:
                    self.logger.warning(f"Company not found: {company_id}")
                return []

            company_name = company.get("name", "")

            # Get all candidates for this company
            all_candidates = self.get_candidates_by_company_name(company_name)

            # Get all interviews to find the job_title for this interview_id
            interviews = self.get_company_interviews(company_id)
            target_interview = None
            for interview in interviews:
                if interview["id"] == interview_id:
                    target_interview = interview
                    break

            if not target_interview:
                if self.logger is not None:
                    self.logger.warning(f"Interview not found: {interview_id}")
                return []

            # Filter candidates by job_title
            job_title = target_interview["job_title"]
            filtered_candidates = [c for c in all_candidates if c.get("job_title") == job_title]

            # Convert to frontend format with evaluation data
            candidates = []
            for candidate in filtered_candidates:
                user_id = candidate.get("user_id")

                # Initialize candidate data
                candidate_data = {
                    "id": user_id,
                    "name": candidate.get("name", "Unknown"),
                    "email": candidate.get("email", ""),
                    "position": job_title,
                    "status": "pending",
                    "interview_date": None,
                    "overall_score": None,
                    "evaluation_id": None,
                    "resume_url": candidate.get("resume_url"),
                    "applied_date": candidate.get("created_at"),
                }

                # Get candidate's sessions to determine status and score
                if user_id:
                    sessions = self.get_candidate_interview_sessions(user_id)
                    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
                    if completed_sessions:
                        candidate_data["status"] = "completed"
                        # Get the most recent completed session
                        recent_session = completed_sessions[0]
                        candidate_data["interview_date"] = recent_session.get("start_time")
                        candidate_data["evaluation_id"] = recent_session.get("session_id")

                        # Get evaluation data
                        evaluation = self.get_candidate_evaluation_data(
                            user_id, recent_session.get("session_id")
                        )
                        if evaluation and "final_evaluation" in evaluation:
                            try:
                                import json

                                eval_data = json.loads(evaluation["final_evaluation"])
                                candidate_data["overall_score"] = eval_data.get("overall_score")
                            except (json.JSONDecodeError, KeyError):
                                pass

                candidates.append(candidate_data)

            # Sort by applied_date descending
            candidates.sort(key=lambda x: x.get("applied_date", ""), reverse=True)

            if self.logger is not None:
                self.logger.info(f"Found {len(candidates)} candidates for interview {interview_id}")
            return candidates

        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error getting candidates for interview {interview_id}: {e}")
            return []
