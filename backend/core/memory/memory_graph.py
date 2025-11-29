from pydantic import BaseModel, Field
from collections import defaultdict
from typing import List, Dict, Any, Optional
from core.resource.model_providers.schema import ChatMessage, MasterChatMessage

# so we want to save conversation history of each topic which has further subtopics within it
# so we will have a memory graph where each node will be a topic and its children will be subtopics
# children will have conversation history and summary and topic will have summary of the children


class SubTopicMemory(BaseModel):
    subtopic_name: str = Field(default="", description="Name of the subtopic")
    conversation_memory: List[MasterChatMessage] = Field(default_factory=list)
    summary: Optional[List[str]] = Field(default=None, description="Summary of the subtopic")

    def add_to_memory(self, item: MasterChatMessage) -> None:
        """Add a message to conversation memory"""
        self.conversation_memory.append(item)

    def add_summary(self, item: List[str]) -> None:
        """Add summary items"""
        if self.summary is None:
            self.summary = []
        self.summary.extend(item)

    def clear(self) -> None:
        """Clear all memory"""
        self.conversation_memory.clear()
        if self.summary is not None:
            self.summary.clear()


class TopicMemory(BaseModel):
    topic_name: str = Field(default="", description="Name of the topic")
    summary: Optional[List[str]] = Field(default=None, description="Summary of the topic")
    subtopics: Dict[str, SubTopicMemory] = Field(default_factory=dict)

    def get_subtopic_memory_instance(self, subtopic_name: str) -> SubTopicMemory:
        """Get or create subtopic memory instance"""
        if subtopic_name not in self.subtopics:
            self.subtopics[subtopic_name] = SubTopicMemory(subtopic_name=subtopic_name)
        return self.subtopics[subtopic_name]
    
    def get_subtopic_summary(self, subtopic_name: str) -> List[str]:
        """Get subtopic summary safely"""
        subtopic = self.subtopics.get(subtopic_name)
        return subtopic.summary if subtopic and subtopic.summary else []
    
    def get_subtopic_conversation_memory(self, subtopic_name: str) -> Optional[List[MasterChatMessage]]:
        """Get subtopic conversation memory safely"""
        subtopic = self.subtopics.get(subtopic_name)
        return subtopic.conversation_memory if subtopic else None
    
    def add_subtopic(self, subtopic_name):
        """ Add subtopic """
        self.subtopics[subtopic_name] = SubTopicMemory(subtopic_name=subtopic_name)

    def add_subtopic_memory(self, subtopic_name, item: MasterChatMessage):
        """ Add subtopic memory """
        self.subtopics[subtopic_name].add_to_memory(item)

    def add_subtopic_summary(self, subtopic_name, item: List[str]):
        """ Add subtopic summary """
        self.subtopics[subtopic_name].add_summary(item)

    def clear_subtopic_memory(self, subtopic_name):
        """ Clear subtopic memory """
        self.subtopics[subtopic_name].clear()
    
    def clear_subtopic_summary(self, subtopic_name):
        """ Clear subtopic summary """
        if self.subtopics[subtopic_name].summary is not None:
            self.subtopics[subtopic_name].summary = []

    def clear_subtopic(self, subtopic_name):
        """ Clear subtopic """
        self.subtopics.pop(subtopic_name)

class TopicSubTopicGraph(BaseModel):
    """ Topic subtopic graph """
    topic_subtopic_graph: Dict[str, TopicMemory] = defaultdict(TopicMemory)

    def get_all_keys(self):
        """ Get all keys """
        return self.topic_subtopic_graph.keys()

    def create_new_topic(self, topic_name):
        """ Create a new topic """
        self.topic_subtopic_graph[topic_name] = TopicMemory(topic_name=topic_name)

    def create_new_subtopic(self, topic_name, subtopic_name):
        """ Create a new subtopic """
        self.topic_subtopic_graph[topic_name].add_subtopic(subtopic_name)

    def add_to_subtopic_memory(self, topic_name, subtopic_name, item: MasterChatMessage):
        """ Add subtopic memory to memory """
        self.topic_subtopic_graph[topic_name].add_subtopic_memory(subtopic_name, item)

    def add_to_subtopic_summary(self, topic_name, subtopic_name, item: List[str]):
        """ Add subtopic summary to memory """
        self.topic_subtopic_graph[topic_name].add_subtopic_summary(subtopic_name, item) 

    def add_to_topic_summary(self, topic_name, item: List[str]):
        """ Add topic summary to memory """
        self.topic_subtopic_graph[topic_name].summary = item

    def get_topic_summary(self, topic_name):
        """ Get topic summary """
        if self.topic_subtopic_graph[topic_name].summary is None:
            return []
        return self.topic_subtopic_graph[topic_name].summary
    
    def get_all_subtopics_conversation_memory(self, topic_name):
        """ Get all subtopics conversation memory """
        conversation_memory = []
        for subtopic_name in self.topic_subtopic_graph[topic_name].subtopics:
            conversation_history = self.topic_subtopic_graph[topic_name].get_subtopic_conversation_memory(subtopic_name)
            if conversation_history:
                conversation_memory.extend(conversation_history)
        return conversation_memory

    def get_subtopic_summary(self, topic_name, subtopic_name):
        """ Get subtopic summary """
        return self.topic_subtopic_graph[topic_name].get_subtopic_summary(subtopic_name)

    def get_subtopic_conversation_memory(self, topic_name, subtopic_name):
        """ Get subtopic conversation memory """
        return self.topic_subtopic_graph[topic_name].get_subtopic_conversation_memory(subtopic_name)

    def clear_subtopic_memory(self, topic_name, subtopic_name):
        """ Clear subtopic memory """
        self.topic_subtopic_graph[topic_name].clear_subtopic_memory(subtopic_name)

    def clear_subtopic_summary(self, topic_name, subtopic_name):
        """ Clear subtopic summary """
        self.topic_subtopic_graph[topic_name].clear_subtopic_summary(subtopic_name)

    def clear_subtopic(self, topic_name, subtopic_name):
        """ Clear subtopic data """
        self.topic_subtopic_graph[topic_name].clear_subtopic(subtopic_name)

    def clear_topic(self, topic_name):
        """ Clear topic memory """
        if self.topic_subtopic_graph[topic_name].summary is not None:
            self.topic_subtopic_graph[topic_name].summary = []
        self.topic_subtopic_graph[topic_name].subtopics.clear()


class MemoryGraph(BaseModel):
    interview_round_topic_memory: Dict[str, List[TopicSubTopicGraph]] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
    
    def get_topic_node_from_name(self, interview_round: str, topic_name: str) -> Optional[TopicSubTopicGraph]:
        """Get topic node with optimized search"""
        topic_nodes = self.interview_round_topic_memory.get(interview_round, [])
        # Use list comprehension for better performance
        matching_nodes = [node for node in topic_nodes if topic_name in node.topic_subtopic_graph.keys()]
        return matching_nodes[0] if matching_nodes else None

    def create_interview_round_node(self, interview_round):
        """ Create a new interview round node """
        self.interview_round_topic_memory[interview_round] = []

    def add_topic_node(self, interview_round, topic_node):
        """ Add a topic node to the interview round """
        self.interview_round_topic_memory[interview_round].append(topic_node)

    def create_topic_node(self, topic_name, subtopic_names):
        """ Create a new topic node """
        topic_node = TopicSubTopicGraph()
        topic_node.create_new_topic(topic_name)
        for subtopic_name in subtopic_names:
            topic_node.create_new_subtopic(topic_name, subtopic_name)
        return topic_node
    
    def add_dialog_to_memory(self, interview_round: str, topic_name: str, 
                            subtopic_name: str, item: MasterChatMessage) -> bool:
        """Add dialog to memory with error handling"""
        try:
            topic_node = self.get_topic_node_from_name(interview_round, topic_name)
            if topic_node and topic_name in topic_node.topic_subtopic_graph:
                topic_node.topic_subtopic_graph[topic_name].subtopics[subtopic_name].add_to_memory(item)
                return True
            return False
        except Exception as e:
            # Log error or handle gracefully
            return False
   
    def add_subtopic_summary_to_memory(self, interview_round, topic_name, subtopic_name, item:List[str]):
        topic_node = self.get_topic_node_from_name(interview_round, topic_name) 
        if topic_node is None:
            return
        topic_node.add_to_subtopic_summary(topic_name, subtopic_name, item)

    def add_topic_summary_to_memory(self, interview_round, topic_name, item:List[str]):
        """ Add topic summary to memory """
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return
        topic_node.add_to_topic_summary(topic_name, item)

    def get_topic_summary(self, interview_round, topic_name):
        """ Get topic summary """
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return []
        return topic_node.get_topic_summary(topic_name)

    
    def get_subtopic_summary(self, interview_round, topic_name, subtopic_name):
        """ Get subtopic summary """
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return []
        return topic_node.get_subtopic_summary(topic_name, subtopic_name)
    
    def get_subtopic_conversation_memory(self, interview_round, topic_name, subtopic_name):
        """ Get subtopic conversation memory """
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return []
        return topic_node.get_subtopic_conversation_memory(topic_name, subtopic_name)
    
    def get_topic_conversation_memory(self, interview_round, topic_name):
        """Get all subtopics conversation memory"""
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return []
        return topic_node.get_all_subtopics_conversation_memory(topic_name)
    
    def get_all_subtopics_conversation_summary(self, interview_round, topic_name):
        """Get all subtopics conversation summary"""
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node is None:
            return []
        
        summary = []
        topic_memory = topic_node.topic_subtopic_graph.get(topic_name)
        if topic_memory:
            for subtopic_memory in topic_memory.subtopics.values():
                if subtopic_memory.summary:
                    summary.extend(subtopic_memory.summary)
        return summary
    
    def add_multiple_dialogs_to_memory(self, interview_round: str, topic_name: str, 
                                      subtopic_name: str, items: List[MasterChatMessage]) -> None:
        """Add multiple dialogs at once"""
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if topic_node and topic_name in topic_node.topic_subtopic_graph:
            subtopic_memory = topic_node.topic_subtopic_graph[topic_name].subtopics.get(subtopic_name)
            if subtopic_memory:
                subtopic_memory.conversation_memory.extend(items)
    
    def get_topic_statistics(self, interview_round: str, topic_name: str) -> Dict[str, Any]:
        """Get statistics for a topic"""
        topic_node = self.get_topic_node_from_name(interview_round, topic_name)
        if not topic_node:
            return {}
        
        topic_memory = topic_node.topic_subtopic_graph.get(topic_name)
        if not topic_memory:
            return {}
        
        stats = {
            'subtopic_count': len(topic_memory.subtopics),
            'total_messages': sum(len(sub.conversation_memory) for sub in topic_memory.subtopics.values()),
            'subtopics_with_summaries': sum(1 for sub in topic_memory.subtopics.values() if sub.summary)
        }
        return stats
    
    
