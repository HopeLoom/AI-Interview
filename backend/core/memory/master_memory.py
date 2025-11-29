from interview_details_agent.base import (
    BaseInterviewConfiguration,
    InterviewRoundData,
    InterviewTopicData,
)
from pydantic import BaseModel

from core.resource.model_providers.schema import MasterChatMessage


# we should further split the conversation history into topic wise conversation history
class SimpleMemory(BaseModel):
    interview_round_one_topic_memory: dict[str, list[MasterChatMessage]] = {}
    interview_round_two_topic_memory: dict[str, list[MasterChatMessage]] = {}
    interview_round_one_topic_summary: dict[str, list[str]] = {}
    interview_round_two_topic_summary: dict[str, list[str]] = {}

    def set_interview_config(self, interview_config: BaseInterviewConfiguration):
        self.interview_config: BaseInterviewConfiguration = interview_config
        round_details = self.interview_config.interview_round_details
        interview_round_one: InterviewRoundData = round_details.rounds["interview_round_1"]

        topic_list_round_one: list[InterviewTopicData] = interview_round_one.topic_info
        for topic in topic_list_round_one:
            self.interview_round_one_topic_summary[topic.name] = []
            self.interview_round_one_topic_memory[topic.name] = []

        interview_round_two: InterviewRoundData = round_details.rounds["interview_round_2"]
        topic_list_round_two: list[InterviewTopicData] = interview_round_two.topic_info
        for topic in topic_list_round_two:
            self.interview_round_two_topic_summary[topic.name] = []
            self.interview_round_two_topic_memory[topic.name] = []

    def remember_interview_round1_conversation(self, topic, item: MasterChatMessage):
        self.interview_round_one_topic_memory[topic].append(item)

    def remember_interview_round2_conversation(self, topic, item: MasterChatMessage):
        self.interview_round_two_topic_memory[topic].append(item)

    def remember_interview_round1_summary(self, topic, item: list[str]):
        self.interview_round_one_topic_summary[topic].extend(item)

    def remember_interview_round2_summary(self, topic, item: list[str]):
        self.interview_round_two_topic_summary[topic].extend(item)

    def recall_interview_round1_conversation(self, topic):
        if self.interview_round_one_topic_memory[topic]:
            return self.interview_round_one_topic_memory[topic]
        else:
            return None

    def recall_interview_round2_conversation(self, topic):
        if self.interview_round_two_topic_memory[topic]:
            return self.interview_round_two_topic_memory[topic]
        else:
            return None

    def recall_interview_round1_summary(self, topic):
        if self.interview_round_one_topic_summary[topic]:
            return self.interview_round_one_topic_summary[topic]
        else:
            return None

    def recall_interview_round2_summary(self, topic):
        if self.interview_round_two_topic_summary[topic]:
            return self.interview_round_two_topic_summary[topic]
        else:
            return None

    def interview_round1_conversation_clear(self):
        for topic in self.interview_round_one_topic_memory:
            self.interview_round_one_topic_memory[topic] = []

    def interview_round2_conversation_clear(self):
        for topic in self.interview_round_two_topic_memory:
            self.interview_round_two_topic_memory[topic] = []

    def interview_round1_summary_clear(self):
        for topic in self.interview_round_one_topic_summary:
            self.interview_round_one_topic_summary[topic] = []

    def interview_round2_summary_clear(self):
        for topic in self.interview_round_two_topic_summary:
            self.interview_round_two_topic_summary[topic] = []

    def clear_memory(self):
        self.interview_round1_conversation_clear()
        self.interview_round2_conversation_clear()
        self.interview_round1_summary_clear()
        self.interview_round2_summary_clear()

    def recall_interview_round1_last_exchange(self, topic):
        if self.interview_round_one_topic_memory[topic]:
            return self.interview_round_one_topic_memory[topic][-1]
        else:
            return None

    def recall_interview_round2_last_exchange(self, topic):
        if self.interview_round_two_topic_memory[topic]:
            return self.interview_round_two_topic_memory[topic][-1]
        else:
            return None
