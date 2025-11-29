# This file contains the agent creation logic. It is responsible for creating the agent object and its settings.
from master_agent.master import Master
from master_agent.base import BaseMasterConfiguration
import uuid 

def generate_id(agent_name):
    unique_id = str(uuid.uuid4())[:8]
    return f"{agent_name}_{unique_id}"
   
async def create_master_instance(
                llm_provider,
                gemini_provider,
                groq_provider,
                grok_provider,
                deepseek_provider,
                config:BaseMasterConfiguration, 
                candidate_name,
                user_id,
                firebase_user_id,
                session_id,
                database,
                logger,
                data_dir):
    # do all checks before calling agent creation
    master_id = generate_id(config.name)
    config.id = master_id
    master_instance = _configure_master(
                    config,
                    candidate_name,
                    llm_provider,
                    gemini_provider,
                    groq_provider,
                    grok_provider,
                    deepseek_provider,
                    user_id,
                    firebase_user_id,
                    session_id,
                    database,
                    logger,
                    data_dir)
    return master_instance

def _configure_master(config,
                 candidate_name,
                 llm_provider,
                 gemini_provider,
                 groq_provider,
                 grok_provider,
                 deepseek_provider,
                 user_id,
                 firebase_user_id,
                 session_id,
                 database,
                 logger,
                 data_dir):
    
    return Master(user_id,
                  firebase_user_id,
                  session_id, 
                  config, 
                  candidate_name,
                  llm_provider,
                  gemini_provider,
                  groq_provider,
                  grok_provider, 
                  deepseek_provider,
                  database,
                  logger,
                  data_dir)