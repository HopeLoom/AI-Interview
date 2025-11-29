"""
Database service for managing job postings, candidates, and interview configurations.
This service handles the multi-tenant structure where companies can have multiple job postings
and candidates can have multiple interviews.
"""

import firebase_admin
from firebase_admin import firestore
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from .models import (
    FrontendConfigurationInput, 
    ConfigurationGenerationResponse,
    ConfigurationTemplate,
    CandidateData,
    CompanyData,
    JobPostingData,
    CandidateApplicationData,
    CompanyDashboardData,
    JobPostingSummary,
    CandidateSummary
)
from interview_details_agent.base import JobDetails, InterviewRoundDetails

class InterviewConfigurationDatabase:
    """Database service for interview configuration management"""
    
    def __init__(self):
        self.db = firestore.client()
        
    def _generate_id(self) -> str:
        """Generate a unique ID for documents"""
        return str(uuid.uuid4())
    
    def _get_timestamp(self) -> datetime:
        """Get current timestamp"""
        return datetime.utcnow()
    
    # Company Management
    async def create_company(self, company_data: Dict[str, Any]) -> str:
        """Create a new company user"""
        company_id = self._generate_id()
        company_data.update({
            'id': company_id,
            'userType': 'company',
            'createdAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })
        
        doc_ref = self.db.collection('companies').document(company_id)
        doc_ref.set(company_data)
        return company_id
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company by ID"""
        doc_ref = self.db.collection('companies').document(company_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    async def get_company_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get company by contact email"""
        query = self.db.collection('companies').where('contact_email', '==', email).limit(1)
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None
    
    async def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """Update company information"""
        try:
            update_data['updatedAt'] = self._get_timestamp()
            doc_ref = self.db.collection('companies').document(company_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating company: {e}")
            return False
    
    async def get_company_dashboard_data(self, company_id: str) -> CompanyDashboardData:
        """Get company dashboard summary data"""
        try:
            # Get job postings count
            job_postings_query = self.db.collection('job_postings').where('companyId', '==', company_id)
            job_postings = list(job_postings_query.stream())
            
            active_jobs = [job for job in job_postings if job.to_dict().get('status') == 'active']
            
            # Get total candidates (unique candidates who applied to any job)
            candidate_ids = set()
            applications_query = self.db.collection('candidate_applications')
            
            for job in job_postings:
                job_applications = applications_query.where('jobPostingId', '==', job.id).stream()
                for app in job_applications:
                    candidate_ids.add(app.to_dict().get('candidateId'))
            
            # Get recent applications
            recent_applications = []
            for job in job_postings[:5]:  # Last 5 jobs
                job_apps = applications_query.where('jobPostingId', '==', job.id).limit(3).stream()
                for app in job_apps:
                    app_data = app.to_dict()
                    recent_applications.append({
                        'id': app.id,
                        'candidate_name': app_data.get('candidateName', 'Unknown'),
                        'job_title': job.to_dict().get('title', 'Unknown'),
                        'status': app_data.get('status', 'applied'),
                        'applied_date': app_data.get('appliedAt')
                    })
            
            # Get upcoming interviews
            upcoming_interviews = []
            interview_sessions_query = self.db.collection('interview_sessions')
            for job in job_postings:
                if job.to_dict().get('status') == 'active':
                    sessions = interview_sessions_query.where('jobPostingId', '==', job.id).where('status', '==', 'scheduled').stream()
                    for session in sessions:
                        session_data = session.to_dict()
                        upcoming_interviews.append({
                            'id': session.id,
                            'candidate_name': session_data.get('candidateName', 'Unknown'),
                            'job_title': job.to_dict().get('title', 'Unknown'),
                            'scheduled_time': session_data.get('scheduledAt'),
                            'round': session_data.get('currentRound', 'Unknown')
                        })
            
            return CompanyDashboardData(
                total_job_postings=len(job_postings),
                active_job_postings=len(active_jobs),
                total_candidates=len(candidate_ids),
                total_applications=len(recent_applications),
                recent_applications=recent_applications[:10],
                upcoming_interviews=upcoming_interviews[:10]
            )
            
        except Exception as e:
            print(f"Error getting company dashboard data: {e}")
            return CompanyDashboardData(
                total_job_postings=0,
                active_job_postings=0,
                total_candidates=0,
                total_applications=0,
                recent_applications=[],
                upcoming_interviews=[]
            )
    
    # Job Posting Management
    async def create_job_posting(self, company_id: str, job_data: Dict[str, Any]) -> str:
        """Create a new job posting for a company"""
        job_id = self._generate_id()
        job_data.update({
            'id': job_id,
            'companyId': company_id,
            'status': 'active',
            'createdAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })
        
        doc_ref = self.db.collection('job_postings').document(job_id)
        doc_ref.set(job_data)
        return job_id
    
    async def get_job_posting(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job posting by ID"""
        doc_ref = self.db.collection('job_postings').document(job_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    async def get_job_postings_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all job postings for a specific company"""
        query = self.db.collection('job_postings').where('companyId', '==', company_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def get_job_postings_summary_by_company(self, company_id: str) -> List[JobPostingSummary]:
        """Get job posting summaries for company dashboard"""
        try:
            job_postings = await self.get_job_postings_by_company(company_id)
            summaries = []
            
            for job in job_postings:
                # Get applications count
                applications_query = self.db.collection('candidate_applications').where('jobPostingId', '==', job['id'])
                applications_count = len(list(applications_query.stream()))
                
                # Get interviews scheduled count
                interviews_query = self.db.collection('interview_sessions').where('jobPostingId', '==', job['id']).where('status', '==', 'scheduled')
                interviews_scheduled = len(list(interviews_query.stream()))
                
                summary = JobPostingSummary(
                    id=job['id'],
                    title=job['title'],
                    status=job['status'],
                    location=job.get('location'),
                    applications_count=applications_count,
                    interviews_scheduled=interviews_scheduled,
                    created_date=job['createdAt'],
                    last_updated=job['updatedAt']
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            print(f"Error getting job postings summary: {e}")
            return []
    
    async def update_job_posting(self, job_id: str, update_data: Dict[str, Any]) -> bool:
        """Update job posting"""
        try:
            update_data['updatedAt'] = self._get_timestamp()
            doc_ref = self.db.collection('job_postings').document(job_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating job posting: {e}")
            return False
    
    async def delete_job_posting(self, job_id: str) -> bool:
        """Delete job posting (soft delete by setting status to closed)"""
        try:
            doc_ref = self.db.collection('job_postings').document(job_id)
            doc_ref.update({
                'status': 'closed',
                'updatedAt': self._get_timestamp()
            })
            return True
        except Exception as e:
            print(f"Error deleting job posting: {e}")
            return False
    
    async def search_job_postings(self, 
                                company_id: Optional[str] = None,
                                location: Optional[str] = None,
                                level: Optional[str] = None,
                                type: Optional[str] = None,
                                status: str = 'active') -> List[Dict[str, Any]]:
        """Search job postings with filters"""
        query = self.db.collection('job_postings').where('status', '==', status)
        
        if company_id:
            query = query.where('companyId', '==', company_id)
        if location:
            query = query.where('location', '==', location)
        if level:
            query = query.where('level', '==', level)
        if type:
            query = query.where('type', '==', type)
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    # Candidate Management
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create a new candidate user"""
        candidate_id = self._generate_id()
        candidate_data.update({
            'id': candidate_id,
            'userType': 'candidate',
            'createdAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })
        
        doc_ref = self.db.collection('candidates').document(candidate_id)
        doc_ref.set(candidate_data)
        return candidate_id
    
    async def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        doc_ref = self.db.collection('candidates').document(candidate_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

    async def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates"""
        docs = self.db.collection('candidates').stream()
        return [doc.to_dict() for doc in docs]
    
    async def get_candidate_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get candidate by email"""
        query = self.db.collection('candidates').where('email', '==', email).limit(1)
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None
    
    async def update_candidate(self, candidate_id: str, update_data: Dict[str, Any]) -> bool:
        """Update candidate information"""
        try:
            update_data['updatedAt'] = self._get_timestamp()
            doc_ref = self.db.collection('candidates').document(candidate_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating candidate: {e}")
            return False

    async def get_candidate_practice_sessions(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Get candidate practice sessions"""
        candidate = await self.get_candidate(candidate_id)
        if not candidate:
            return []
        sessions = candidate.get('practice_sessions', [])
        return sessions if isinstance(sessions, list) else []
    
    async def get_candidates_summary_by_company(self, company_id: str) -> List[CandidateSummary]:
        """Get candidate summaries for company dashboard"""
        try:
            # Get all job postings for the company
            job_postings = await self.get_job_postings_by_company(company_id)
            candidate_summaries = {}
            
            for job in job_postings:
                # Get applications for this job
                applications_query = self.db.collection('candidate_applications').where('jobPostingId', '==', job['id'])
                applications = list(applications_query.stream())
                
                for app in applications:
                    app_data = app.to_dict()
                    candidate_id = app_data.get('candidateId')
                    
                    if candidate_id not in candidate_summaries:
                        # Get candidate details
                        candidate = await self.get_candidate(candidate_id)
                        if candidate:
                            candidate_summaries[candidate_id] = CandidateSummary(
                                id=candidate_id,
                                name=candidate.get('name', 'Unknown'),
                                email=candidate.get('email', 'Unknown'),
                                applied_jobs=[job['id']],
                                total_applications=1,
                                interview_status=app_data.get('status'),
                                last_activity=app_data.get('appliedAt', self._get_timestamp())
                            )
                    else:
                        # Update existing candidate summary
                        summary = candidate_summaries[candidate_id]
                        summary.applied_jobs.append(job['id'])
                        summary.total_applications += 1
                        summary.last_activity = max(summary.last_activity, app_data.get('appliedAt', self._get_timestamp()))
            
            return list(candidate_summaries.values())
            
        except Exception as e:
            print(f"Error getting candidates summary: {e}")
            return []
    
    # Interview Session Management
    async def create_interview_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new interview session"""
        session_id = self._generate_id()
        session_data.update({
            'id': session_id,
            'status': 'scheduled',
            'currentStep': 0,
            'startedAt': self._get_timestamp(),
            'createdAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })
        
        doc_ref = self.db.collection('interview_sessions').document(session_id)
        doc_ref.set(session_data)
        return session_id
    
    async def get_interview_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get interview session by ID"""
        doc_ref = self.db.collection('interview_sessions').document(session_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    async def get_interview_sessions_by_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Get all interview sessions for a specific candidate"""
        query = self.db.collection('interview_sessions').where('candidateId', '==', candidate_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def get_interview_sessions_by_job(self, job_posting_id: str) -> List[Dict[str, Any]]:
        """Get all interview sessions for a specific job posting"""
        query = self.db.collection('interview_sessions').where('jobPostingId', '==', job_posting_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    async def get_interview_sessions_by_configuration(self, configuration_id: str) -> List[Dict[str, Any]]:
        """Get all interview sessions for a specific configuration"""
        sessions: Dict[str, Dict[str, Any]] = {}

        # Firestore field names may vary based on ingestion source
        field_candidates = ['configurationId', 'configuration_id']

        for field in field_candidates:
            try:
                query = self.db.collection('interview_sessions').where(field, '==', configuration_id)
                for doc in query.stream():
                    data = doc.to_dict() or {}
                    data.setdefault('id', doc.id)
                    sessions[doc.id] = data
            except Exception as exc:
                # Continue trying alternative field names if index missing
                print(f"Warning: failed to query interview_sessions where {field} == {configuration_id}: {exc}")

        # If we still have nothing, fall back to scanning all sessions (only for small data sets / dev)
        if not sessions:
            try:
                all_docs = self.db.collection('interview_sessions').stream()
                for doc in all_docs:
                    data = doc.to_dict() or {}
                    config_match = data.get('configurationId') == configuration_id or data.get('configuration_id') == configuration_id
                    if config_match:
                        data.setdefault('id', doc.id)
                        sessions[doc.id] = data
            except Exception as exc:
                print(f"Warning: fallback scan for configuration sessions failed: {exc}")

        return list(sessions.values())
    
    async def update_interview_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update interview session"""
        try:
            update_data['updatedAt'] = self._get_timestamp()
            doc_ref = self.db.collection('interview_sessions').document(session_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating interview session: {e}")
            return False

    async def get_session_evaluation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation document for a specific interview session"""
        try:
            session_doc = self.db.collection('interview_sessions').document(session_id).get()
            if not session_doc.exists:
                return None

            session_data = session_doc.to_dict() or {}

            # Attempt to resolve explicit evaluation reference
            evaluation_id = (
                session_data.get('evaluation_id')
                or session_data.get('evaluationId')
                or session_data.get('evaluation', {}).get('id')
            )

            if evaluation_id:
                evaluation_doc = self.db.collection('interview_evaluations').document(evaluation_id).get()
                if evaluation_doc.exists:
                    evaluation_data = evaluation_doc.to_dict() or {}
                    evaluation_data.setdefault('id', evaluation_doc.id)
                    return evaluation_data

            # Fallback: return evaluation data embedded in the session document if present
            evaluation_payload = session_data.get('evaluation') or session_data.get('evaluation_summary')
            if evaluation_payload:
                return evaluation_payload

            # Build a lightweight summary if no dedicated evaluation exists
            summary_fields = {
                "overall_score": session_data.get('score') or session_data.get('overall_score'),
                "technical_score": session_data.get('technical_score'),
                "communication_score": session_data.get('communication_score'),
                "feedback": session_data.get('feedback'),
                "strengths": session_data.get('strengths') or session_data.get('key_strengths'),
                "areas_for_improvement": session_data.get('areas_for_improvement'),
            }

            # Only return summary if there is at least one non-null value
            if any(value is not None for value in summary_fields.values()):
                summary_fields["id"] = evaluation_id or f"{session_id}-inline-evaluation"
                return summary_fields

            return None

        except Exception as exc:
            print(f"Error getting session evaluation {session_id}: {exc}")
            return None
    
    # Interview Configuration Management
    async def create_interview_configuration(self, config_data: Dict[str, Any]) -> str:
        """Create a new interview configuration"""
        # Use the config_id from config_data if provided, otherwise generate new one
        config_id = config_data.get('id') or config_data.get('configuration_id') or self._generate_id()

        config_data.update({
            'id': config_id,  # Ensure id field exists and matches
            'createdAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })

        doc_ref = self.db.collection('interview_configurations').document(config_id)
        doc_ref.set(config_data)
        return config_id
    
    async def get_interview_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get interview configuration by ID"""
        doc_ref = self.db.collection('interview_configurations').document(config_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    async def get_interview_configurations_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all interview configurations for a specific company"""
        query = self.db.collection('interview_configurations').where('companyId', '==', company_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def get_interview_configurations_by_job(self, job_posting_id: str) -> List[Dict[str, Any]]:
        """Get all interview configurations for a specific job posting"""
        query = self.db.collection('interview_configurations').where('jobPostingId', '==', job_posting_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def update_interview_configuration(self, config_id: str, update_data: Dict[str, Any]) -> bool:
        """Update interview configuration"""
        try:
            update_data['updatedAt'] = self._get_timestamp()
            doc_ref = self.db.collection('interview_configurations').document(config_id)
            doc_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating interview configuration: {e}")
            return False
    
    # Candidate Application Management
    async def create_candidate_application(self, application_data: Dict[str, Any]) -> str:
        """Create a new candidate application for a job"""
        application_id = self._generate_id()
        application_data.update({
            'id': application_id,
            'status': 'applied',
            'appliedAt': self._get_timestamp(),
            'updatedAt': self._get_timestamp()
        })
        
        doc_ref = self.db.collection('candidate_applications').document(application_id)
        doc_ref.set(application_data)
        return application_id
    
    async def get_candidate_applications_by_job(self, job_posting_id: str) -> List[Dict[str, Any]]:
        """Get all applications for a specific job posting"""
        query = self.db.collection('candidate_applications').where('jobPostingId', '==', job_posting_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def get_candidate_applications_by_candidate(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Get all applications by a specific candidate"""
        query = self.db.collection('candidate_applications').where('candidateId', '==', candidate_id)
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def update_application_status(self, application_id: str, new_status: str) -> bool:
        """Update candidate application status"""
        try:
            doc_ref = self.db.collection('candidate_applications').document(application_id)
            doc_ref.update({
                'status': new_status,
                'updatedAt': self._get_timestamp()
            })
            return True
        except Exception as e:
            print(f"Error updating application status: {e}")
            return False
    
    # Template Management
    async def get_public_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get public interview configuration templates"""
        query = self.db.collection('interview_configurations').where('isPublic', '==', True)
        if category:
            query = query.where('templateCategory', '==', category)
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]
    
    async def save_as_template(self, config_id: str, template_data: Dict[str, Any]) -> bool:
        """Save an interview configuration as a reusable template"""
        try:
            template_data.update({
                'isTemplate': True,
                'updatedAt': self._get_timestamp()
            })
            doc_ref = self.db.collection('interview_configurations').document(config_id)
            doc_ref.update(template_data)
            return True
        except Exception as e:
            print(f"Error saving as template: {e}")
            return False
    
    # Search and Filter Functions
    async def search_candidates(self,
                              skills: Optional[List[str]] = None,
                              location: Optional[str] = None,
                              experience_min: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search candidates with filters"""
        query = self.db.collection('candidates')

        if location:
            query = query.where('location', '==', location)
        if experience_min is not None:
            query = query.where('experience', '>=', experience_min)

        docs = query.stream()
        candidates = [doc.to_dict() for doc in docs]

        # Filter by skills if specified
        if skills:
            candidates = [
                candidate for candidate in candidates
                if any(skill.lower() in [s.lower() for s in candidate.get('skills', [])]
                      for skill in skills)
            ]

        return candidates

    # Join By Code Functions
    async def get_interview_configuration_by_invitation_code(self, invitation_code: str) -> Optional[Dict[str, Any]]:
        """Get interview configuration by invitation code"""
        try:
            # Query for configuration with matching invitation code
            query = self.db.collection('interview_configurations').where('invitation_code', '==', invitation_code.upper()).limit(1)
            docs = query.stream()

            for doc in docs:
                config_data = doc.to_dict()
                config_data['id'] = doc.id  # Ensure id is set
                return config_data

            return None
        except Exception as e:
            print(f"Error getting configuration by invitation code: {e}")
            return None

    async def validate_invitation_code(self, invitation_code: str) -> Optional[Dict[str, Any]]:
        """
        Validate invitation code and return configuration with company details
        Returns dict with: configuration, company, job_posting (if exists)
        """
        try:
            # Get configuration by invitation code
            config = await self.get_interview_configuration_by_invitation_code(invitation_code)

            if not config:
                return None

            # Get company details
            company_id = config.get('companyId') or config.get('company_id')
            company = None
            if company_id:
                company = await self.get_company(company_id)

            # Get job posting details if exists
            job_posting_id = config.get('jobPostingId') or config.get('job_posting_id')
            job_posting = None
            if job_posting_id:
                job_posting = await self.get_job_posting(job_posting_id)

            return {
                'configuration': config,
                'company': company,
                'job_posting': job_posting
            }
        except Exception as e:
            print(f"Error validating invitation code: {e}")
            return None

    async def create_interview_session_from_code(self,
                                                  invitation_code: str,
                                                  candidate_id: str,
                                                  candidate_email: str) -> Optional[Dict[str, Any]]:
        """
        Create an interview session for a candidate using invitation code
        Returns session data with configuration and company details
        """
        try:
            # Validate invitation code and get details
            validation_result = await self.validate_invitation_code(invitation_code)

            if not validation_result:
                return None

            config = validation_result['configuration']
            company = validation_result['company']
            job_posting = validation_result['job_posting']

            # Get or create candidate
            candidate = await self.get_candidate(candidate_id)
            if not candidate:
                # Auto-create candidate with email
                candidate_id = await self.create_candidate({
                    'email': candidate_email,
                    'name': candidate_email.split('@')[0],  # Use email prefix as name
                    'skills': []
                })
                candidate = await self.get_candidate(candidate_id)

            # Create interview session
            session_data = {
                'candidateId': candidate_id,
                'candidateName': candidate.get('name'),
                'candidateEmail': candidate.get('email'),
                'configurationId': config.get('id'),
                'companyId': company.get('id') if company else None,
                'jobPostingId': job_posting.get('id') if job_posting else None,
                'status': 'scheduled',
                'invitationCode': invitation_code.upper()
            }

            session_id = await self.create_interview_session(session_data)

            return {
                'success': True,
                'session_id': session_id,
                'configuration': config,
                'company': company,
                'job_posting': job_posting,
                'candidate': candidate
            }
        except Exception as e:
            print(f"Error creating interview session from code: {e}")
            return None
