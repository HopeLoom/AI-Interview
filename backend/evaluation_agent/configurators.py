# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
from evaluation_agent.evaluation import Evaluation
from evaluation_agent.base import BaseEvaluation, BaseEvaluationConfiguration
from interview_details_agent.base import BaseInterviewConfiguration
import uuid 
from core.database.base import DatabaseInterface

def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"
   
async def create_evaluation_instance(
                llm_provider,
                gemini_provider,
                groq_provider,
                perplexity_provider,
                user_id,
                firebase_user_id,
                session_id,
                logger,
                database:DatabaseInterface):   
    
    activity_instance = _configure_evaluation(
                    user_id,
                    firebase_user_id,
                    session_id,
                    logger,
                    llm_provider,
                    gemini_provider, 
                    groq_provider,
                    perplexity_provider,
                    database)
    
    return activity_instance


def _configure_evaluation(
                user_id,
                firebase_user_id,
                session_id,
                logger,
                llm_provider,
                gemini_provider,
                groq_provider,
                perplexity_provider,
                firebase_database):
    
    return Evaluation(
                    user_id,
                    firebase_user_id,
                    session_id,
                    logger,
                    llm_provider, 
                    gemini_provider,
                    groq_provider,
                    perplexity_provider,
                    database)