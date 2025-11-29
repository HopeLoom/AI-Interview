from candidate_agent.personality_generator import generate_personality_info
from candidate_agent.background_generator import generate_background_info
from candidate_agent.base import Profile

class CandidateProfileGenerator():
        
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    async def generate_candidate_profile(self, resume_data):
        user_background = await generate_background_info(self.llm_provider, resume_data)
        personality = await generate_personality_info(self.llm_provider, user_background, resume_data)
        profile = Profile(background=user_background, personality=personality, character_id="Candidate")
        return profile