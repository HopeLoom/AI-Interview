# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.

from candidate_agent.base import BaseCandidateConfiguration, CandidateSettings
from candidate_agent.candidate import Candidate, Profile


def configure_settings():
    settings = CandidateSettings()
    settings.big_brain = False
    settings.fast_llm = "gpt-4o-mini"
    settings.slow_llm = "gpt-4o"
    return settings


async def create_candidate_instance(**kwargs):
    # do all checks before calling agent creation
    settings = configure_settings()
    llm_provider = kwargs.get("llm_provider")
    kwargs.get("resume_data")
    receiving_message_queue = kwargs.get("receiving_message_queue")
    sending_message_queue = kwargs.get("sending_message_queue")
    kwargs.get("data_dir")
    user_id = kwargs.get("user_id")
    firebase_database = kwargs.get("firebase_database")

    profile_json_data = firebase_database.get_profile_json_data()
    if profile_json_data:
        print("Loading user profile from database")
        candidate_profile = Profile(**profile_json_data)
    else:
        print("Generating user profile as cannot find in database")

    config = BaseCandidateConfiguration()
    config.settings = settings
    config.profile = candidate_profile
    config.candidate_id = user_id
    candidate_instance = _configure_candidate(
        config, llm_provider, receiving_message_queue, sending_message_queue
    )

    return candidate_instance


def _configure_candidate(config, llm_provider, receiving_message_queue, sending_message_queue):
    return Candidate(config, llm_provider, receiving_message_queue, sending_message_queue)
