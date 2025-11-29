import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from interview_details_agent.base import (
    BaseInterviewConfiguration,
    InterviewRoundData,
    InterviewRoundDetails,
    InterviewTopicData,
)
from pydantic import BaseModel, Field

from core.memory.memory_graph import MemoryGraph
from core.resource.model_providers.schema import MasterChatMessage
from master_agent.base import InterviewRound, SubTopicData


class SubTopicNode(BaseModel):
    subtopic_data: SubTopicData
    status: bool = Field(default=False, description="Completion status")
    sections: defaultdict[str, bool] = Field(
        default_factory=dict, description="Section completion status"
    )

    def get_subtopic_name(self) -> str:
        return self.subtopic_data.name

    def get_subtopic_description(self) -> str:
        return self.subtopic_data.description

    def get_subtopic_status(self) -> bool:
        return self.status

    def get_section_status(self, section_name: str) -> bool:
        return self.sections.get(section_name, False)

    def get_section_names(self) -> list[str]:
        return list(self.sections.keys())


class TopicNode(BaseModel):
    topic_data: InterviewTopicData
    status: bool = False
    subtopic_nodes: dict[str, SubTopicNode] = {}

    def get_topic_name(self):
        return self.topic_data.name

    def get_topic_description(self):
        return self.topic_data.description

    def get_evaluation_criteria(self):
        return self.topic_data.evaluation_criteria

    def get_subtopic_node(self, subtopic_name):
        return self.subtopic_nodes.get(subtopic_name)

    def get_subtopics(self):
        return self.subtopic_nodes.keys()

    def get_topic_status(self):
        return self.status

    def get_subtopic_status(self, subtopic_name):
        return self.subtopic_nodes[subtopic_name].get_subtopic_status()

    def get_subtopic_description(self, subtopic_name):
        return self.subtopic_nodes[subtopic_name].get_subtopic_description()

    def add_subtopic_node(self, subtopic_name, subtopic_node):
        self.subtopic_nodes[subtopic_name] = subtopic_node

    def update_section_status(self, subtopic_name, section_name):
        self.subtopic_nodes[subtopic_name].sections[section_name] = True

    def update_subtopic_status(self, subtopic_name: str) -> bool:
        """Update subtopic status and return if changed"""
        subtopic_node = self.subtopic_nodes.get(subtopic_name)
        if not subtopic_node:
            return False

        old_status = subtopic_node.status
        subtopic_node.status = all(subtopic_node.sections.values())
        return old_status != subtopic_node.status

    def update_topic_status(self) -> bool:
        """Update topic status and return if changed"""
        old_status = self.status
        self.status = all(node.status for node in self.subtopic_nodes.values())
        return old_status != self.status


class InterviewRoundDataGraph(BaseModel):
    interview_round_topic_data_graph: dict[str, list[TopicNode]] = {}
    _topic_name_index: dict[str, dict[str, TopicNode]] = {}  # Cache for topic lookups

    def __init__(self, **data):
        super().__init__(**data)
        self._topic_name_index = {}  # Cache for topic lookups

    def create_interview_round_node(self, interview_round):
        self.interview_round_topic_data_graph[interview_round] = []

    def add_topic_node(self, interview_round, topic_node):
        self.interview_round_topic_data_graph[interview_round].append(topic_node)
        # Update index
        if interview_round not in self._topic_name_index:
            self._topic_name_index[interview_round] = {}
        self._topic_name_index[interview_round][topic_node.get_topic_name()] = topic_node

    def get_topic_node_by_name(self, interview_round, topic_name):
        return self._topic_name_index.get(interview_round, {}).get(topic_name)

    def create_topic_node(self, topic_data: InterviewTopicData):
        subtopic_list = topic_data.subtopics
        subtopic_nodes = {}
        for subtopic in subtopic_list:
            subtopic_data: SubTopicData = subtopic
            subtopic_node = SubTopicNode(
                subtopic_data=subtopic_data,
                sections=dict.fromkeys(subtopic_data.sections, False),
            )
            subtopic_nodes[subtopic_data.name] = subtopic_node
        topic_node = TopicNode(topic_data=topic_data, subtopic_nodes=subtopic_nodes)
        return topic_node

    def get_next_topic_node(self, interview_round):
        for topic_node in self.interview_round_topic_data_graph[interview_round]:
            if not topic_node.status:
                return topic_node
        return None

    def get_next_subtopic_node(self, topic_node):
        for _subtopic_node_name, subtopic_node in topic_node.subtopic_nodes.items():
            if not subtopic_node.status:
                return subtopic_node
        return None

    def get_uncompleted_subtopics(self, interview_round, topic_name):
        for topic_node in self.interview_round_topic_data_graph[interview_round]:
            if topic_node.get_topic_name() == topic_name:
                subtopics = []
                for subtopic_name, subtopic_node in topic_node.subtopic_nodes.items():
                    if not subtopic_node.status:
                        subtopics.append(subtopic_name)
                return subtopics
        return None

    def get_next_section(self, subtopic_node):
        for section_name, section_status in subtopic_node.sections.items():
            if not section_status:
                return section_name
        return None

    def get_last_completed_topic_node(self, interview_round):
        last_topic_node = None
        for topic_node in self.interview_round_topic_data_graph[interview_round]:
            if not topic_node.status:
                break
            last_topic_node = topic_node
        return last_topic_node

    def get_last_completed_subtopic_node(self, interview_round, topic_name):
        last_subtopic_node = None
        for topic_node in self.interview_round_topic_data_graph[interview_round]:
            if topic_node.get_topic_name() == topic_name:
                for _subtopic_node_name, subtopic_node in topic_node.subtopic_nodes.items():
                    if not subtopic_node.status:
                        break
                    last_subtopic_node = subtopic_node
                break
        return last_subtopic_node

    def update_subtopic_status(self, interview_round, topic_name, subtopic_name, section_name):
        for topic_node in self.interview_round_topic_data_graph[interview_round]:
            if topic_node.get_topic_name() == topic_name:
                topic_node.update_section_status(subtopic_name, section_name)
                topic_node.update_subtopic_status(subtopic_name)
                topic_node.update_topic_status()
                break


class InterviewTopicTracker(BaseModel):
    interview_data: BaseInterviewConfiguration = BaseInterviewConfiguration()
    interview_round_data_graph: InterviewRoundDataGraph = InterviewRoundDataGraph()
    memory_graph: MemoryGraph = MemoryGraph()
    interview_round1_metrics_covered: list[str] = []
    interview_round2_metrics_covered: list[str] = []

    # mainly loading the interview details which contains the different interview rounds, topics and subtopics
    def load_interview_configuration(self, logger):
        # load the interview configuration
        interview_round_details: InterviewRoundDetails = self.interview_data.interview_round_details
        rounds_data = interview_round_details.rounds
        interview_round1_data: InterviewRoundData = rounds_data["interview_round_1"]
        interview_round2_data: InterviewRoundData = rounds_data["interview_round_2"]
        self.interview_round1_metrics_covered = interview_round1_data.metrics_covered
        self.interview_round2_metrics_covered = interview_round2_data.metrics_covered

        # creates nodes for the interview round data inside the interview round data graph
        self.interview_round_data_graph.create_interview_round_node(InterviewRound.ROUND_ONE)
        self.interview_round_data_graph.create_interview_round_node(InterviewRound.ROUND_TWO)

        # create node for the interview round inside the memory graph
        self.memory_graph.create_interview_round_node(InterviewRound.ROUND_ONE)
        self.memory_graph.create_interview_round_node(InterviewRound.ROUND_TWO)

        topic_list_round_1: list[InterviewTopicData] = interview_round1_data.topic_info
        # fill the round 1 topic tracker with the topic and subtopics
        for topic in topic_list_round_1:
            topic_node = self.interview_round_data_graph.create_topic_node(topic)
            self.interview_round_data_graph.add_topic_node(InterviewRound.ROUND_ONE, topic_node)
            sub_topic_names = [subtopic.name for subtopic in topic.subtopics]
            topic_memory_node = self.memory_graph.create_topic_node(topic.name, sub_topic_names)
            self.memory_graph.add_topic_node(InterviewRound.ROUND_ONE, topic_memory_node)

        topic_list_round_2: list[InterviewTopicData] = interview_round2_data.topic_info
        # fill the round 2 topic tracker with the topic and subtopics
        for topic in topic_list_round_2:
            logger.info(f"topic name:{topic.name}")
            logger.info(f"topic description:{topic.description}")
            topic_node = self.interview_round_data_graph.create_topic_node(topic)
            self.interview_round_data_graph.add_topic_node(InterviewRound.ROUND_TWO, topic_node)
            sub_topic_names = [subtopic.name for subtopic in topic.subtopics]
            topic_memory_node = self.memory_graph.create_topic_node(topic.name, sub_topic_names)
            self.memory_graph.add_topic_node(InterviewRound.ROUND_TWO, topic_memory_node)

    def load_data_into_memory_graph(self, memory_graph_json_path: str) -> None:
        """Load memory graph with error handling"""
        try:
            file_path = Path(memory_graph_json_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Memory graph file not found: {memory_graph_json_path}")

            with open(file_path) as f:
                memory_graph_data = json.load(f)
                self.memory_graph = MemoryGraph(**memory_graph_data)
        except Exception as e:
            # Log error or handle gracefully
            raise RuntimeError(f"Failed to load memory graph: {e}")

    # this function is used to get the topic and subtopic for the current interview round
    def get_topic_subtopic_for_discussion(
        self, interview_round: InterviewRound
    ) -> tuple[Optional[InterviewTopicData], Optional[SubTopicData], Optional[str], bool]:
        """Get topic and subtopic for discussion with error handling"""
        try:
            is_interview_round_changed = False
            subtopic_data = None
            topic_data = None
            section = None

            if interview_round == InterviewRound.ROUND_ONE:
                topic_node = self.interview_round_data_graph.get_next_topic_node(
                    InterviewRound.ROUND_ONE
                )
                if topic_node is None:
                    interview_round = InterviewRound.ROUND_TWO
                    is_interview_round_changed = True
                else:
                    topic_data = topic_node.topic_data
                    subtopic_node = self.interview_round_data_graph.get_next_subtopic_node(
                        topic_node
                    )
                    if subtopic_node:
                        section = self.interview_round_data_graph.get_next_section(subtopic_node)
                        subtopic_data = subtopic_node.subtopic_data
                    else:
                        topic_node.status = True

            if interview_round == InterviewRound.ROUND_TWO:
                next_topic_node = self.interview_round_data_graph.get_next_topic_node(
                    InterviewRound.ROUND_TWO
                )
                if next_topic_node:
                    topic_data = next_topic_node.topic_data
                    next_subtopic_node = self.interview_round_data_graph.get_next_subtopic_node(
                        next_topic_node
                    )
                    if next_subtopic_node:
                        section = self.interview_round_data_graph.get_next_section(
                            next_subtopic_node
                        )
                        subtopic_data = next_subtopic_node.subtopic_data
                    else:
                        next_topic_node.status = True

            return topic_data, subtopic_data, section, is_interview_round_changed

        except Exception:
            # Log error or handle gracefully
            return None, None, None, False

    # get the last completed topic for the current interview round
    def get_last_completed_topic_name(self, interview_round):
        last_topic_node = self.interview_round_data_graph.get_last_completed_topic_node(
            interview_round
        )
        if last_topic_node is None:
            return None
        return last_topic_node.topic_data.name

    # get the topic node based on the topic name
    def get_topic_data_based_on_name(self, interview_round, topic_name):
        topic_node = self.interview_round_data_graph.get_topic_node_by_name(
            interview_round, topic_name
        )
        return topic_node.topic_data if topic_node else None

    def get_subtopic_data_based_on_name(self, interview_round, topic_name, subtopic_name):
        topic_node = self.interview_round_data_graph.get_topic_node_by_name(
            interview_round, topic_name
        )
        if topic_node:
            subtopic_node = topic_node.subtopic_nodes.get(subtopic_name)
            return subtopic_node.subtopic_data if subtopic_node else None
        return None

    # get the last completed subtopic for the current interview round
    def get_last_completed_subtopic_name(self, interview_round, topic_name):
        last_subtopic_node = self.interview_round_data_graph.get_last_completed_subtopic_node(
            interview_round, topic_name
        )
        if last_subtopic_node is None:
            return None
        return last_subtopic_node.subtopic_data.name

    def get_subtopic_nodes(self, interview_round, topic_name):
        for topic_node in self.interview_round_data_graph.interview_round_topic_data_graph[
            interview_round
        ]:
            if topic_node.get_topic_name() == topic_name:
                return topic_node.subtopic_nodes
        return None

    def update_topic_completion_status(
        self, interview_round, topic_name, subtopic_name, section_name
    ):
        self.interview_round_data_graph.update_subtopic_status(
            interview_round, topic_name, subtopic_name, section_name
        )

    def update_all_subtopics_within_topic_status(self, interview_round, topic_name):
        for topic_node in self.interview_round_data_graph.interview_round_topic_data_graph[
            interview_round
        ]:
            if topic_node.get_topic_name() == topic_name:
                for subtopic_node_name, _subtopic_node in topic_node.subtopic_nodes.items():
                    topic_node.update_subtopic_status(subtopic_node_name)

                topic_node.status = True
                break

    def is_topic_completed(self, interview_round, topic_name):
        for topic_node in self.interview_round_data_graph.interview_round_topic_data_graph[
            interview_round
        ]:
            if topic_node.get_topic_name() == topic_name:
                return topic_node.get_topic_status()

    def is_subtopic_completed(self, interview_round, topic_name, subtopic_name):
        for topic_node in self.interview_round_data_graph.interview_round_topic_data_graph[
            interview_round
        ]:
            if topic_node.get_topic_name() == topic_name:
                subtopic_node = topic_node.get_subtopic_node(subtopic_name)
                return subtopic_node.get_subtopic_status()
        return False

    def get_all_uncompleted_subtopics(self, interview_round, topic_name):
        return self.interview_round_data_graph.get_uncompleted_subtopics(
            interview_round, topic_name
        )

    def get_metrics_covered_for_current_interview_round(self, current_interview_round) -> list[str]:
        if current_interview_round == InterviewRound.ROUND_ONE:
            return self.interview_round1_metrics_covered
        elif current_interview_round == InterviewRound.ROUND_TWO:
            return self.interview_round2_metrics_covered
        return []

    # we have four get functions for memory graph
    def get_conversation_history_for_subtopic(
        self, current_interview_round, topic_name, subtopic_name
    ):
        return self.memory_graph.get_subtopic_conversation_memory(
            current_interview_round, topic_name, subtopic_name
        )

    def get_conversation_history_for_topic(self, current_interview_round, topic_name):
        return self.memory_graph.get_topic_conversation_memory(current_interview_round, topic_name)

    def get_conversation_history_for_all_topics(self, current_interview_round):
        # Get all topic names first
        topic_names = [
            node.get_topic_name()
            for node in self.interview_round_data_graph.interview_round_topic_data_graph[
                current_interview_round
            ]
        ]

        # Batch fetch from memory graph
        conversation_history = []
        for topic_name in topic_names:
            history = self.memory_graph.get_topic_conversation_memory(
                current_interview_round, topic_name
            )
            if history:
                conversation_history.extend(history)
        return conversation_history

    def get_topic_summary_of_all_completed_topics(self, current_interview_round):
        # check which topics have been completed
        completed_topics = []
        for topic_node in self.interview_round_data_graph.interview_round_topic_data_graph[
            current_interview_round
        ]:
            if topic_node.get_topic_status():
                completed_topics.append(topic_node.get_topic_name())

        # get the summary of all the completed topics
        topic_summary = []
        for topic_name in completed_topics:
            topic_summary.extend(
                self.memory_graph.get_topic_summary(current_interview_round, topic_name)
            )

        return topic_summary

    def get_topic_summary(self, current_interview_round, topic_name):
        return self.memory_graph.get_topic_summary(current_interview_round, topic_name)

    def get_subtopic_summary(self, current_interview_round, topic_name, subtopic_name):
        return self.memory_graph.get_subtopic_summary(
            current_interview_round, topic_name, subtopic_name
        )

    def get_all_conversation_summary_for_topic(self, current_interview_round, topic_name):
        return self.memory_graph.get_all_subtopics_conversation_summary(
            current_interview_round, topic_name
        )

    # we have three add functions for memory graph
    def add_dialog_to_memory(
        self, current_interview_round, topic_name, subtopic_name, item: MasterChatMessage
    ) -> bool:
        return self.memory_graph.add_dialog_to_memory(
            current_interview_round, topic_name, subtopic_name, item
        )

    def add_subtopic_summary_to_memory(
        self, current_interview_round, topic_name, subtopic_name, item: list[str]
    ):
        self.memory_graph.add_subtopic_summary_to_memory(
            current_interview_round, topic_name, subtopic_name, item
        )

    def add_topic_summary_to_memory(self, current_interview_round, topic_name, item: list[str]):
        self.memory_graph.add_topic_summary_to_memory(current_interview_round, topic_name, item)

    def update_multiple_sections(
        self,
        interview_round: InterviewRound,
        topic_name: str,
        subtopic_name: str,
        section_names: list[str],
    ) -> None:
        """Update multiple sections at once"""
        topic_node = self.interview_round_data_graph.get_topic_node_by_name(
            interview_round, topic_name
        )
        if not topic_node:
            return

        subtopic_node = topic_node.subtopic_nodes.get(subtopic_name)
        if not subtopic_node:
            return

        # Update all sections
        for section_name in section_names:
            subtopic_node.sections[section_name] = True

        # Update statuses
        topic_node.update_subtopic_status(subtopic_name)
        topic_node.update_topic_status()

    def get_completion_statistics(self, interview_round: InterviewRound) -> dict[str, Any]:
        """Get completion statistics for an interview round"""
        topics = self.interview_round_data_graph.interview_round_topic_data_graph.get(
            interview_round, []
        )

        stats = {
            "total_topics": len(topics),
            "completed_topics": sum(1 for topic in topics if topic.status),
            "total_subtopics": sum(len(topic.subtopic_nodes) for topic in topics),
            "completed_subtopics": sum(
                sum(1 for subtopic in topic.subtopic_nodes.values() if subtopic.status)
                for topic in topics
            ),
        }

        if stats["total_topics"] > 0:
            stats["topic_completion_percentage"] = int(
                (stats["completed_topics"] / stats["total_topics"]) * 100
            )
        if stats["total_subtopics"] > 0:
            stats["subtopic_completion_percentage"] = int(
                (stats["completed_subtopics"] / stats["total_subtopics"]) * 100
            )

        return stats

    def save_memory_graph(self, path: str) -> None:
        """Save memory graph with error handling"""
        try:
            file_path = Path(path) / "memory_graph.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(self.memory_graph.model_dump(), f, indent=4)
        except Exception as e:
            # Log error or handle gracefully
            raise RuntimeError(f"Failed to save memory graph: {e}")
