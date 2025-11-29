from typing import List

from pydantic import BaseModel, Field


class Education(BaseModel):
    degree: str = ""
    major: str = ""
    university: str = ""
    year_graduated: float = 0


class Experience(BaseModel):
    company: str = ""
    position: str = ""
    duration_years: float = 0


class Skills(BaseModel):
    skill: str = ""
    level: int = 0


class Projects(BaseModel):
    project: str = ""
    description: str = ""
    duration_months: float = 0


class CurrentOccupation(BaseModel):
    occupation: str = ""
    duration_years: float = 0


# since npc is an interviewer, we need to know only relevant information
class Background(BaseModel):
    name: str = ""
    gender: str = ""
    age: int = 0
    bio: str = ""
    current_occupation: CurrentOccupation = CurrentOccupation()
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    skills: List[Skills] = Field(default_factory=list)
    projects: List[Projects] = Field(default_factory=list)

    @staticmethod
    def save():
        pass
