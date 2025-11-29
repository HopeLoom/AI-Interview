# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
from panelist_agent.panelist import Panelist
import uuid 
from panelist_factory.generator import PanelistGenerator

def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"
   
async def create_panelist_instance(interview_config,
                                    llm_provider,
                                    gemini_provider,
                                    groq_provider, 
                                    grok_provider,
                                    deepseek_provider,
                                   character_data, 
                                   sending_message_queue, 
                                   receiving_message_queue, 
                                   data_dir, 
                                   user_id,
                                   firebase_user_id,
                                   session_id,
                                   server_address,
                                   firebase_database,
                                   logger):
    
    # do all checks before calling agent creation
    generator = PanelistGenerator(llm_provider, character_data, data_dir, user_id, firebase_database)
    config = await generator.generate_info()
    panelist_id = generate_id(user_id)
    config.id = panelist_id
    panelist = _configure_panelist(interview_config, 
                              config,
                              user_id,
                              firebase_user_id,
                              session_id,
                              llm_provider, 
                              gemini_provider,
                              groq_provider,
                              grok_provider,
                              deepseek_provider,
                              server_address,
                              firebase_database,
                              sending_message_queue, 
                              receiving_message_queue, 
                              logger)
    return panelist

def _configure_panelist(interview_config,
                        config,
                        user_id,
                        firebase_user_id,
                        session_id,
                        llm_provider,
                        gemini_provider,
                        groq_provider,
                        grok_provider,
                        deepseek_provider, 
                        server_address,
                        firebase_database,
                        sending_message_queue, 
                        receiving_message_queue,
                        logger):
    
    return Panelist(interview_config = interview_config, 
                    panelist_config = config, 
                    user_id = user_id,
                    firebase_user_id = firebase_user_id,
                    session_id = session_id,
                    llm_provider = llm_provider,
                    gemini_provider = gemini_provider,
                    groq_provider = groq_provider, 
                    grok_provider = grok_provider,
                    deepseek_provider = deepseek_provider,
                    server_address = server_address,
                    firebase_database = firebase_database,
                    receiving_message_queue = receiving_message_queue, 
                    sending_message_queue = sending_message_queue,
                    logger = logger)

