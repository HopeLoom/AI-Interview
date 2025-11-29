# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
import uuid

from interview_details_agent.interview import Interview


def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"


def create_interview_instance(interview_name, config, llm_provider):
    # do all checks before calling agent creation
    interview_id = generate_id(interview_name)
    agent = _configure_interview(interview_id, config, llm_provider)
    return agent


def _configure_interview(interview_id, config, llm_provider):
    return Interview(interview_id, config, llm_provider)
