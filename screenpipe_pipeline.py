# Standard library imports
import json
import os
from datetime import datetime
from typing import Generator, Iterator, List, Literal, Optional, Union

# Third-party imports
import requests
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel

# Local imports
# from schemas import OpenAIChatMessage
from utils.screenpipe_client import search as sp_search
from utils.sp_utils import remove_names, convert_to_pst
def reformat_user_message(user_message: str, sanitized_results: str) -> str:
    """
    Reformats the user message by adding context and rules from ScreenPipe search results.

    Args:
        user_message (str): The original user message.

    Returns:
        str: A reformatted user message with added context and rules.
    """
    assert isinstance(sanitized_results, str), "Sanitized results must be a string"
    query = user_message
    context = sanitized_results
    
    reformatted_message = f"""You are given a user query, context from personal screen and microphone data, and rules, all inside xml tags. Answer the query based on the context while respecting the rules.
<context>
{context}
</context>

<rules>
- If the context is not relevant to the user query, just say so.
- If you are not sure, ask for clarification.
- If the answer is not in the context but you think you know the answer, explain that to the user then answer with your own knowledge.
- Answer directly and without using xml tags.
</rules>

<user_query>
{query}
</user_query>
"""
    return reformatted_message

def get_messages_with_screenpipe_data(messages: List[dict], results_as_string: str) -> List[dict]:
    """
    Combines the original messages with the sanitized ScreenPipe search results.

    This function takes the original conversation messages and appends the sanitized
    ScreenPipe search results as a new message. This allows the AI model to consider
    both the conversation context and the search results in its next response.

    Args:
        messages (List[dict]): The original list of conversation messages.
        sanitized_results (List[dict]): The sanitized results from the ScreenPipe search.

    Returns:
        List[dict]: A new list of messages that includes the original messages and
                    the ScreenPipe search results as a new message.
    """
    # Replace system message
    SYSTEM_MESSAGE = "You are a helpful assistant that parses screenpipe search results. Use the search results to answer the user's question as best as possible. If unclear, synthesize the context and provide an explanation."
    if messages[-1]["role"] != "user":
        raise ValueError("Last message must be from the user!")
    if len(messages) > 2:
        print("Warning! This LLM call uses only the search results and user message.")
    
    new_user_message = reformat_user_message(messages[-1]["content"], results_as_string)
    new_messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": new_user_message}
    ]
    return new_messages

def sanitize_results(results: dict) -> list[dict]:
    """
    Sanitizes the results from the screenpipe_search function.
    """
    assert isinstance(results, dict) and results.get("data"), "Result dictionary must match schema of screenpipe search results"
    results = results["data"]
    new_results = []
    for result in results:
        new_result = dict()
        if result["type"] == "OCR":
            new_result["type"] = "OCR"
            new_result["content"] = remove_names(result["content"]["text"])
            new_result["app_name"] = result["content"]["app_name"]
            new_result["window_name"] = result["content"]["window_name"]
        elif result["type"] == "Audio":
            new_result["type"] = "Audio"
            new_result["content"] = result["content"]["transcription"]
            new_result["device_name"] = result["content"]["device_name"]
            # NOTE: Not removing names from audio transcription
        else:
            raise ValueError(f"Unknown result type: {result['type']}")
        new_result["timestamp"] = convert_to_pst(result["content"]["timestamp"])
        new_results.append(new_result)
    return new_results

def screenpipe_search(
    search_substring: str = "",
    content_type: Literal["ocr", "audio", "all"] = "all",
    start_time: str = "2024-10-01T00:00:00Z",
    end_time: str = "2024-10-31T23:59:59Z",
    limit: int = 5,
    app_name: Optional[str] = None,
) -> dict:
    """Searches captured data stored in ScreenPipe's local database based on filters such as content type and timestamps.

    Args:
        search_substring: The search term. Defaults to "".
        content_type: The type of content to search. Must be one of "ocr", "audio", or "all". Defaults to "all".
        start_time: The start timestamp for the search range. Defaults to "2024-10-01T00:00:00Z".
        end_time: The end timestamp for the search range. Defaults to "2024-10-31T23:59:59Z".
        limit: The maximum number of results to return. Defaults to 5. Should be between 1 and 100.
        app_name: The name of the app to search in. Defaults to None.

    Returns:
        dict: A dictionary containing an error message or the search results.
    """
    if type(limit) == str:
        try:
            limit = int(limit)
        except ValueError:
            print(f"Limit must be an integer. Defaulting to 5")
            limit = 5
    assert 0 < limit <= 100, "Limit must be between 1 and 100"
    assert start_time < end_time, "Start time must be before end time"

    if limit > 50:
        print(f"Warning: Limit is set to {limit}. This may return a large number of results.")
        print("CHANGING LIMIT TO 20!")
        limit = 20
    # Make first letter of app_name uppercase
    if app_name:
        app_name = app_name.capitalize()
    results = sp_search(
        query=search_substring,
        content_type=content_type,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
        app_name=app_name,
    )
    if results is None:
        return {"error": "Screenpipe search failed"}
    if not results["data"]:
        return {"error": "No results found"}
    print(f"Found {len(results)} results")
    return results

class Pipeline:
    class Valves(BaseModel):
        LITELLM_API_KEY: str = ""
        TOOL_MODEL: str = ""
        FINAL_MODEL: str = ""

    def __init__(self):
        self.name = "Screenpipe Pipeline"
        self.valves = self.Valves(
            **{
                "LITELLM_API_KEY": os.getenv("LITELLM_API_KEY", ""),
                "TOOL_MODEL": "Llama-3.1-70B",
                "FINAL_MODEL": "Qwen2.5-72B"
            }
        )
        # self.client = OpenAI(
        #     base_url="https://api.together.xyz/v1",
        #     api_key=self.valves.TOGETHER_API_KEY
        # )
        self.liteLLM_client = OpenAI(
            base_url="http://localhost:4000/v1",
            api_key=self.valves.LITELLM_API_KEY
        )

        self.tools = [convert_to_openai_tool(screenpipe_search)]

    # ... existing methods ...
    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def get_current_time(self) -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")
        print(messages)
        print(user_message)
        print("Now piping body:", body)
        messages = body["messages"]
        if messages[0]["role"] == "system":
            print("System message is being replaced!")
            messages = messages[1:]

        SYSTEM_MESSAGE = f"You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {self.get_current_time()}. When appropriate, create a short search_substring to narrow down the search results."
        messages.insert(0, {
            "role": "system",
            "content": SYSTEM_MESSAGE
        })

        response = self.liteLLM_client.chat.completions.create(
            model=self.valves.TOOL_MODEL,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
        )

        tool_calls = response.choices[0].message.model_dump().get('tool_calls', [])
        if not tool_calls:
            return response.choices[0].message.content

        max_tool_calls = 1
        if len(tool_calls) > max_tool_calls:
            print(f"Warning: More than {max_tool_calls} tool calls found. Only the first {max_tool_calls} tool calls will be processed.")
            tool_calls = tool_calls[:max_tool_calls]
        
        for tool_call in tool_calls:
            if tool_call['function']['name'] == 'screenpipe_search':
                function_args = json.loads(tool_call['function']['arguments'])
                search_results = screenpipe_search(**function_args)
                assert isinstance(search_results, dict), "Search results must be a dictionary"
                if not search_results:
                    return "No results found"
                if "error" in search_results:
                    # NOTE: Returning the error message from screenpipe_search
                    return search_results["error"]
                
                sanitized_results = sanitize_results(search_results)
                # print("First sanitized result:")
                # print(json.dumps(sanitized_results[0], indent=2))
                ### Legacy code ###
                # messages.append({
                #     "role": "function",
                #     "name": "screenpipe_search",
                #     "content": json.dumps(sanitized_results)
                # })
        results_as_string = json.dumps(sanitized_results)
        messages_with_screenpipe_data = get_messages_with_screenpipe_data(messages, results_as_string)
        if body["stream"]:
            return self.liteLLM_client.chat.completions.create(
                model=self.valves.FINAL_MODEL,
                messages=messages_with_screenpipe_data,
                stream=True
            )
        else:
            final_response = self.liteLLM_client.chat.completions.create(
                model=self.valves.FINAL_MODEL,
                messages=messages_with_screenpipe_data,
            )
            return final_response.choices[0].message.content


### TOOL DEFINITION ###
# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "screenpipe_search",
#             "description": "Searches captured data stored in ScreenPipe's local database based on filters such as content type and timestamps.",
#             "parameters": {
#                 "properties": {
#                     "search_substring": {
#                         "default": "",
#                         "type": "string"
#                     },
#                     "content_type": {
#                         "default": "all",
#                         "enum": [
#                             "ocr",
#                             "audio",
#                             "all"
#                         ],
#                         "type": "string"
#                     },
#                     "start_time": {
#                         "default": "2024-10-01T00:00:00Z",
#                         "type": "string"
#                     },
#                     "end_time": {
#                         "default": "2024-10-31T23:59:59Z",
#                         "type": "string"
#                     },
#                     "limit": {
#                         "default": 5,
#                         "type": "integer"
#                     },
#                     "app_name": {
#                         "anyOf": [
#                             {
#                                 "type": "string"
#                             },
#                             {
#                                 "type": "null"
#                             }
#                         ],
#                         "default": None
#                     }
#                 },
#                 "type": "object"
#             }
#         }
#     }
# ]