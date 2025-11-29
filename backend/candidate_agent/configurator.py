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
    resume_data = kwargs.get("resume_data")
    receiving_message_queue = kwargs.get("receiving_message_queue")
    sending_message_queue = kwargs.get("sending_message_queue")
    data_dir = kwargs.get("data_dir")
    user_id = kwargs.get("user_id")
    firebase_database = kwargs.get("firebase_database")

    profile_json_data = firebase_database.get_profile_json_data()
    if profile_json_data:
        print("Loading user profile from database")
        candidate_profile = Profile(**profile_json_data)
    # check if data_dir is provided and load user profile
    # if os.path.exists(data_dir + user_id + ".json"):
    #     print ("Loading user profile from file")
    #     candidate_profile_file = open(data_dir + user_id + ".json", "r")
    #     candidate_profile = Profile(**json.loads(candidate_profile_file.read()))
    else:
        print("Generating user profile as cannot find in database")
        # candidate_profile = await CandidateProfileGenerator(llm_provider).generate_candidate_profile(resume_data)
        # # save the profile
        # with open(data_dir + user_id + ".json", "w") as f:
        #     json.dump(candidate_profile.model_dump(), f, indent=4)

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
