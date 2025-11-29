# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
from activity_agent.activity import Activity
from activity_agent.base import BaseActivity, BaseActivityConfiguration
from interview_details_agent.base import BaseInterviewConfiguration
import asyncio
import uuid 
from core.database.base import DatabaseInterface

def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"
   
async def create_activity_instance(
                llm_provider,
                gemini_provider,
                groq_provider,
                user_id,
                firebase_user_id,
                session_id,
                config:BaseActivityConfiguration,
                interview_config:BaseInterviewConfiguration,
                database:DatabaseInterface,
                receiving_message_queue:asyncio.Queue,
                sending_message_queue:asyncio.Queue,
                logger,
                is_evaluating:bool = False):
    # do all checks before calling agent creation
    activity_id = generate_id(config.activity_name)
    config.activity_name = activity_id
    
    activity_instance = _configure_activity(
                    config,
                    user_id,
                    firebase_user_id,
                    session_id,
                    llm_provider,
                    gemini_provider, 
                    groq_provider,
                    interview_config,
                    database,
                    receiving_message_queue,
                    sending_message_queue,
                    logger,
                    is_evaluating)
    
    return activity_instance


def _configure_activity(config,
                user_id,
                firebase_user_id,
                session_id,
                llm_provider,
                gemini_provider,
                groq_provider,
                interview_config,
                database, 
                receiving_message_queue, 
                sending_message_queue,
                logger,
                is_evaluating):
    
    return Activity(config, 
                    user_id,
                    firebase_user_id,
                    session_id,
                    interview_config, 
                    llm_provider, 
                    gemini_provider,
                    groq_provider,
                    database,
                    receiving_message_queue, 
                    sending_message_queue,
                    logger,
                    is_evaluating)