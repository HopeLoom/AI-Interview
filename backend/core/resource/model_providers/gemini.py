from google import genai
import enum
from core.resource.model_providers.schema import (
    ChatModelProvider, 
    ChatModelInfo,
    ModelInfo,
    ModelResponse,
    AssistantChatMessage,
    ModelProviderName,
    ModelProviderService,
    ModelProviderSettings,
    SystemSettings,
    ModelProviderBudget,
    ModelProviderConfiguration,
    ModelProviderCredentials,
    ModelProviderUsage,
    ChatMessage,
    ChatModelResponse,
    )
from core.prompting.schema import ChatPrompt

from typing import Optional, Callable
import tiktoken
import yaml

class GeminiModelName(str, enum.Enum):
    GEMINI_2_FLASH:str = "gemini-2.0-flash"
    GEMINI_1_5_PRO:str = "gemini-1.5-pro"

GEMINI_CHAT_MODELS = {
    info.name:info 
    for info in [
        ChatModelInfo(
            name=GeminiModelName.GEMINI_2_FLASH,
            service = ModelProviderService.CHAT,
            provider_name=ModelProviderName.GEMINI,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03/1000,
            prompt_token_cost=0.01/1000
        ),
        ChatModelInfo(
            name=GeminiModelName.GEMINI_1_5_PRO,
            service = ModelProviderService.CHAT,
            provider_name=ModelProviderName.GEMINI,
            max_tokens=50000,
            has_function_call_api=True,
            completion_token_cost=0.03/1000,
            prompt_token_cost=0.01/1000
        )
    ]
}

class GeminiConfiguration(ModelProviderConfiguration):
    fix_failed_tries:int = 3


class GeminiCredentials(ModelProviderCredentials):
    api_key:str = ""
    api_type:str = ""
    organization:str = ""

class GeminiSettings(SystemSettings):
    configuration: GeminiConfiguration
    credentials: Optional[GeminiCredentials]
    warning_token_threshold:float = 0.75
    #budget: ModelProviderBudget

import abc
import typing
from typing import Generic, TypeVar
S = TypeVar("S", bound=SystemSettings)

class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]

class GeminiProvider(Configurable[GeminiSettings], ChatModelProvider):

    default_settings = GeminiSettings(
        name = GeminiModelName.GEMINI_1_5_PRO,
        description = "Gemini model provider",
        configuration = GeminiConfiguration(
            retries_per_request=10, fix_failed_tries=3
        ),
        credentials=None    
    )
    '''
        budget = ModelProviderBudget(
            total_budget=10,
            total_cost=0,
            remaining_budget=10,
            usage = ModelProviderUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0
            )
           
        )
    '''
    #_budget: ModelProviderBudget
    _configuration: GeminiConfiguration
    _credentials: GeminiCredentials

    def __init__(
            self,
            settings
    ):
        if not settings:
            settings = self.default_settings
        
        self.settings = settings

        #self._budget = settings.budget
        self._configuration = settings.configuration
        self._credentials = settings.credentials
        
        # Check if credentials are provided and valid
        if not self._credentials or not self._credentials.api_key:
            raise ValueError("Missing Gemini API key! Please provide api_key in credentials.")
        
        #print ("Credentials: ", self._credentials.api_key)
        self._client = genai.Client(api_key=self._credentials.api_key)

    def get_token_limit(self, model_name):
        return GEMINI_CHAT_MODELS[model_name].max_tokens

    def get_tokenizer(self, model_name):
        return tiktoken.encoding_for_model(model_name)
    
    # use the same tokenizer as GPT for gemini?
    def count_tokens(self, text, model_name):
        if model_name.startswith("gemini-2.0"):
            encoding_model_name = "gpt-4"
        else:
            encoding_model_name = "gpt-3.5-turbo"
        encoder = self.get_tokenizer(encoding_model_name) 
        return len(encoder.encode(text))
    
    def count_message_tokens(self, messages, model_name):
        if isinstance(messages, ChatMessage):
            messages = [messages]

        if model_name.startswith("gemini-1.5"):
            tokens_per_message = 4 
            tokens_per_names = -1
            encoding_model = "gpt-3.5-turbo"
        elif model_name.startswith("gemini-2"):
            tokens_per_message = 3
            tokens_per_names = 1
            encoding_model = "gpt-4"

        else:
            raise ValueError(f"Unknown model name {model_name}")
        
        try:
            encoder = tiktoken.encoding_for_model(encoding_model)
        except KeyError:
            encoder = tiktoken.get_encoding("cl110k_base")
        
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message 
            content = message.content
            num_tokens += len(encoder.encode(content))
        num_tokens += 3 
        return num_tokens
    

    def _get_embedding_args(self, model_name, **kwargs):
        kwargs['model'] = model_name
        return kwargs
    
    _T = TypeVar("_T")

    async def create_chat_completion(
        self, 
        chat_messages: ChatPrompt,
        model_name: GeminiModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        is_json_mode: bool = True,
        **kwargs
    ):

        total_cost = 0 
        attempts = 0 
        kwargs = {
            "model": model_name
        }
        #print ("model_prompt: ", chatmessages)  

        gemini_messages = []
        for message in chat_messages.messages:
            role = message.role
            content = message.content

            gemini_messages.append(content)


        _response, _cost, t_input, t_output = await self._create_chat_completion(
           gemini_messages,kwargs
        )

        total_cost += _cost

        _assistant_msg = _response.text ## get output from response

        assistant_msg =  AssistantChatMessage(
            content = _assistant_msg,
            role = "assistant" 
        )
        if completion_parser is None:
            parsed_result = assistant_msg
        else:
            parsed_result = completion_parser(assistant_msg)

        return ChatModelResponse(
            response = AssistantChatMessage(
                content = assistant_msg.content
            ),
            parsed_response = parsed_result,
            model_info = GEMINI_CHAT_MODELS[model_name],
            prompt_tokens_used = t_input,
            completion_tokens_used = t_output
        )

    # This function calls the gemini chat completion API
    async def _create_chat_completion(self, messages, kwargs):
        print ("create_chat_completion")
            
        async def _create_chat_completion_with_retry(
                messages, kwargs
        ):
            print ("create_chat_completion_with_retry")
            
            string_message = ",".join(messages)

            return self._client.models.generate_content(
                string_message,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    #response_schema = 
                )
            )
        
        completion = await _create_chat_completion_with_retry(
            messages, kwargs
        )

        print ("Completion: ", completion)

        prompt_tokens_used = 0
        completion_tokens_used = 0

        # update cost
        cost = 0

        return completion, cost, prompt_tokens_used, completion_tokens_used
    