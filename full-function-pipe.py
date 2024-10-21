"""
title: Screenpipe Pipeline
author: TanGentleman
author_url: https://github.com/TanGentleman
version: 0.1
"""
# NOTE: This is a full-function pipe. It can be added using OpenWebUI > Workspace > Functions > Add Function

# Standard library imports
import json
from datetime import datetime
from typing import Generator, Iterator, List, Literal, Optional, Union
from zoneinfo import ZoneInfo

# Third-party imports
import requests
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel

SCREENPIPE_PORT = 3030
SCREENPIPE_BASE_URL = f"http://host.docker.internal:{SCREENPIPE_PORT}"

# NOTE: The following must be set correctly!

### IMPORTANT CONFIG ###
LLM_API_BASE_URL = "http://host.docker.internal:4000/v1"
LLM_API_KEY = "API-KEY"
TOOL_MODEL = "Llama-3.1-70B"
FINAL_MODEL = "Qwen2.5-72B"
# The model names must be valid for the endpoint LLM_API_BASE_URL/v1/chat/completions

# NOTE: The following can be used to remove/replace sensitive keywords
SENSITIVE_WORD_1, SENSITIVE_REPLACEMENT_1 = "LASTNAME", ""
SENSITIVE_WORD_2, SENSITIVE_REPLACEMENT_2 = "FIRSTNAME", "NICKNAME"

def remove_names(content: str) -> str:
    return content.replace(SENSITIVE_WORD_1, SENSITIVE_REPLACEMENT_1).replace(SENSITIVE_WORD_2, SENSITIVE_REPLACEMENT_2)

def convert_to_pst(timestamp, safety=True):
    """
    Converts a given timestamp to Pacific Standard Time (PST).

    Args:
    - timestamp (str): The timestamp to convert, in the format YYYY-MM-DDTHH:MM:SS.ssssssZ.
    - safety (bool): If True, the function will return the original timestamp if it does not end with 'Z'. Defaults to True.

    Returns:
    - str: The converted timestamp in the format MM/DD/YY HH:MM AM/PM.
    """
    if safety:
        if not timestamp.endswith('Z'):
            # NOTE: Should I have a warning message?
            return timestamp
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    dt_pst = dt.replace(
        tzinfo=ZoneInfo('UTC')).astimezone(
        ZoneInfo('America/Los_Angeles'))
    return dt_pst.strftime("%m/%d/%y %I:%M%p")

def sp_search(
    limit: int = 5,
    query: Optional[str] = None,
    content_type: Optional[str] = None,
    offset: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    app_name: Optional[str] = None,
    window_name: Optional[str] = None,
    include_frames: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> dict:
    """
    Searches captured data (OCR, audio transcriptions, etc.) stored in ScreenPipe's local database based on filters such as content type, timestamps, app name, and window name.

    Args:
    query (str): The search term.
    content_type (str): The type of content to search (ocr, audio, fts, all.).
    limit (int): The maximum number of results per page.
    offset (int): The pagination offset.
    start_time (str): The start timestamp.
    end_time (str): The end timestamp.
    app_name (str): The application name.
    window_name (str): The window name.
    include_frames (bool): If True, fetch frame data for OCR content.
    min_length (int): Minimum length of the content.
    max_length (int): Maximum length of the content.

    Returns:
    dict: The search results.
    """
    if not query:
        query = ""

    if content_type is None:
        content_type = "all"
    assert content_type in ["ocr", "audio", "fts", "all"], "Invalid content type. Must be 'ocr', 'audio', 'fts', or 'all'."
    print(f"Searching for: {content_type}")
    params = {
        "q": query,
        "content_type": content_type,
        "limit": limit,
        "offset": offset,
        "start_time": start_time,
        "end_time": end_time,
        "app_name": app_name,
        "window_name": window_name,
        "include_frames": "true" if include_frames is True else None,
        "min_length": min_length,
        "max_length": max_length
    }

    # Remove None values from params dictionary
    params = {key: value for key, value in params.items() if value is not None}
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/search", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching for content: {e}")
        return None


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
    Combines the last user message with the sanitized ScreenPipe search results.

    This function takes the original conversation messages, extracts the last user message,
    and combines it with the sanitized ScreenPipe search results. This allows the AI model
    to consider both the user's query and the search results in its next response.

    Args:
        messages (List[dict]): The original list of conversation messages.
        results_as_string (str): The sanitized results from the ScreenPipe search as a string.

    Returns:
        List[dict]: A new list of messages that includes a system message and a reformatted user message
                    containing the original query and ScreenPipe search results.
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
        print("CHANGING LIMIT TO 40!")
        limit = 40
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

class Pipe:
    class Valves(BaseModel):
        LLM_API_BASE_URL: str = ""
        LLM_API_KEY: str = ""
        TOOL_MODEL: str = ""
        FINAL_MODEL: str = ""

    def __init__(self):
        self.name = "Screenpipe Pipeline"
        self.valves = self.Valves(
            **{
                "LLM_API_BASE_URL": LLM_API_BASE_URL,
                "LLM_API_KEY": LLM_API_KEY,
                "TOOL_MODEL": TOOL_MODEL,
                "FINAL_MODEL": FINAL_MODEL
            }
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
        self, body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")
        messages = body["messages"]
        print("Now piping body:", body)
        self.client = OpenAI(
            base_url=self.valves.LLM_API_BASE_URL,
            api_key=self.valves.LLM_API_KEY
        )
        
        messages = body["messages"]
        if messages[0]["role"] == "system":
            print("System message is being replaced!")
            messages = messages[1:]

        SYSTEM_MESSAGE = f"You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {self.get_current_time()}. When appropriate, create a short search_substring to narrow down the search results."
        messages.insert(0, {
            "role": "system",
            "content": SYSTEM_MESSAGE
        })

        response = self.client.chat.completions.create(
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
        results_as_string = json.dumps(sanitized_results)
        messages_with_screenpipe_data = get_messages_with_screenpipe_data(messages, results_as_string)
        if body["stream"]:
            return self.client.chat.completions.create(
                model=self.valves.FINAL_MODEL,
                messages=messages_with_screenpipe_data,
                stream=True
            )
        else:
            final_response = self.client.chat.completions.create(
                model=self.valves.FINAL_MODEL,
                messages=messages_with_screenpipe_data,
            )
            return final_response.choices[0].message.content
