# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
from discussion.discussion import Discussion
from discussion.base import BaseDiscussionConfiguration
import uuid 

def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"

def create_discussion_instance(interview_name, 
                config,
                llm_provider, character_data):
    # do all checks before calling agent creation
    interview_id = generate_id(interview_name)
    agent = _configure_discussion(interview_id,
                     config,
                    llm_provider, 
                    character_data)
    return agent

def _configure_discussion(interview_id, 
                 config,
                 llm_provider, character_data):
    
    return Discussion(interview_id, config, llm_provider, character_data)

