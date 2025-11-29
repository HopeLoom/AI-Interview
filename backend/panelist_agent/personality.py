from pydantic import BaseModel, Field


class Personality(BaseModel):
    openness: dict = Field(default_factory=dict)
    conscientiousness: dict = Field(default_factory=dict)
    extraversion: dict = Field(default_factory=dict)
    agreeableness: dict = Field(default_factory=dict)
    neuroticism: dict = Field(default_factory=dict)

    @staticmethod
    def save():
        pass

    @staticmethod
    def get_prompt():
        return "You are a person with a lot of emotions and traits. "
