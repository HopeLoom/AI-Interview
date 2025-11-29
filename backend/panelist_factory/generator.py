from interview_details_agent.base import CharacterData

from panelist_agent.base import BasePanelistConfiguration, PanelistSettings, Profile


class PanelistGenerator:
    def __init__(
        self, llm_provider, character_data: CharacterData, data_dir, user_id, firebase_database
    ):
        self.llm_provider = llm_provider
        self.character_data = character_data
        self.data_dir = data_dir
        self.user_id = user_id
        self.firebase_database = firebase_database

    def configure_settings(self):
        settings = PanelistSettings()
        settings.big_brain = True
        return settings

    async def generate_info(self):
        settings = self.configure_settings()

        profile_json_data = self.firebase_database.get_panelist_profile_json_data(
            self.character_data.character_name
        )

        if profile_json_data:
            print("Loading panelist profile from database")
            profile = Profile(**profile_json_data)
        else:
            print("Generating panelist profile couldn't find in database")

        panelist_config = BasePanelistConfiguration(
            id=profile.character_id,
            profile=profile,
            settings=settings,
            name=self.character_data.character_name,
            description=self.character_data.character_name,
        )
        print("Panelist Configuration loaded:")
        return panelist_config
