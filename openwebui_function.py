"""
title: Screenpipe Pipeline
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.8
"""
# NOTE: Add pipeline using OpenWebUI > Workspace > Functions > Add Function

# Standard library imports
import json
from datetime import datetime, timedelta, timezone
from typing import Generator, Iterator, List, Literal, Optional, Union

# Third-party imports
import requests
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
from pydantic import BaseModel, ValidationError

# NOTE: Sensitive - Sanitize before sharing
SENSITIVE_KEY = "api-key"
REPLACEMENT_TUPLES = [
    # ("LASTNAME", ""),
    # ("FIRSTNAME", "NICKNAME")
]
# Mode configuration for base URL
SCRIPT_ORIGIN = "docker"
SCREENPIPE_PORT = 3030
assert SCRIPT_ORIGIN in ["docker", "localhost"]

URL_BASE = f"http://localhost" if SCRIPT_ORIGIN == "localhost" else f"http://host.docker.internal"
DEFAULT_SCREENPIPE_BASE_URL = f"{URL_BASE}:{SCREENPIPE_PORT}"


# NOTE: The above are used to remove/replace sensitive keywords

### IMPORTANT CONFIG ###
# Change this to any openai compatible endpoint
DEFAULT_LLM_API_BASE_URL = f"{URL_BASE}:4000/v1"
DEFAULT_LLM_API_KEY = SENSITIVE_KEY
DEFAULT_USE_GRAMMAR = False
# If USE_GRAMMAR is True, grammar model is used instead of the tool model

# MODELS
# This model should support native tool use
DEFAULT_TOOL_MODEL = "Llama-3.1-70B"
# This model receives private screenpipe data
DEFAULT_FINAL_MODEL = "lmstudio-Llama-3.2-3B-4bit-MLX"
DEFAULT_LOCAL_GRAMMAR_MODEL = "lmstudio-Llama-3.2-3B-4bit-MLX"

# NOTE: Model name must be valid for the endpoint:
# {DEFAULT_LLM_API_BASE_URL}/v1/chat/completions

MAX_TOOL_CALLS = 1
PREFER_24_HOUR_FORMAT = True
DEFAULT_UTC_OFFSET = -7  # PDT
### HELPER FUNCTIONS ###


class SearchSchema(BaseModel):
    limit: int = 5
    content_type: Literal["ocr", "audio", "all"] = "all"
    search_substring: Optional[str] = ""
    start_time: Optional[str] = "2024-10-01T00:00:00Z"
    end_time: Optional[str] = "2024-10-31T23:59:59Z"
    app_name: Optional[str] = None


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
    if isinstance(limit, str):
        try:
            limit = int(limit)
        except ValueError:
            print(f"Limit must be an integer. Defaulting to 5")
            limit = 5
    assert 0 < limit <= 100, "Limit must be between 1 and 100"
    assert start_time < end_time, "Start time must be before end time"

    if limit > 50:
        print(
            f"Warning: Limit is set to {limit}. This may return a large number of results.")
        print("CHANGING LIMIT TO 40!")
        limit = 40
    # Make first letter of app_name uppercase
    if app_name:
        app_name = app_name.capitalize()
    params = {
        "q": search_substring,
        "content_type": content_type,
        "limit": limit,
        "start_time": start_time,
        "end_time": end_time,
        "app_name": app_name
    }
    # Remove None values from params dictionary
    params = {key: value for key, value in params.items() if value is not None}
    try:
        response = requests.get(
            f"{DEFAULT_SCREENPIPE_BASE_URL}/search",
            params=params)
        response.raise_for_status()
        results = response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Screenpipe search failed: {e}"}
    if results is None:
        return {"error": "Screenpipe request failed"}
    if not results["data"]:
        return {"error": "No results found"}
    print(f"Found {len(results['data'])} results")
    return results


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


class Pipe:
    class Valves(BaseModel):
        SCREENPIPE_BASE_URL: str = ""
        LLM_API_BASE_URL: str = ""
        LLM_API_KEY: str = ""
        TOOL_MODEL: str = ""
        FINAL_MODEL: str = ""
        LOCAL_GRAMMAR_MODEL: str = ""
        USE_GRAMMAR: bool = False

    def __init__(self):
        self.type = "pipe"
        self.name = "screenpipe_pipeline"
        self.valves = self.Valves(
            **{
                "SCREENPIPE_BASE_URL": DEFAULT_SCREENPIPE_BASE_URL,
                "LLM_API_BASE_URL": DEFAULT_LLM_API_BASE_URL,
                "LLM_API_KEY": DEFAULT_LLM_API_KEY,
                "TOOL_MODEL": DEFAULT_TOOL_MODEL,
                "FINAL_MODEL": DEFAULT_FINAL_MODEL,
                "LOCAL_GRAMMAR_MODEL": DEFAULT_LOCAL_GRAMMAR_MODEL,
                "USE_GRAMMAR": DEFAULT_USE_GRAMMAR
            }
        )
        self.tools = [convert_to_openai_tool(screenpipe_search)]

    def initialize_settings(self):
        base_url = self.valves.LLM_API_BASE_URL or DEFAULT_LLM_API_BASE_URL
        api_key = self.valves.LLM_API_KEY or DEFAULT_LLM_API_KEY
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.tool_model = self.valves.TOOL_MODEL or DEFAULT_TOOL_MODEL
        self.final_model = self.valves.FINAL_MODEL or DEFAULT_FINAL_MODEL
        self.local_grammar_model = self.valves.LOCAL_GRAMMAR_MODEL or DEFAULT_LOCAL_GRAMMAR_MODEL
        self.use_grammar = self.valves.USE_GRAMMAR or DEFAULT_USE_GRAMMAR
        self.screenpipe_base_url = self.valves.SCREENPIPE_BASE_URL or DEFAULT_SCREENPIPE_BASE_URL
        pass

    def sanitize_results(self, results: dict) -> list[dict]:
        """
        Sanitizes the results from the screenpipe_search function.
        """
        assert isinstance(results, dict) and results.get(
            "data"), "Result dictionary must match schema of screenpipe search results"
        results = results["data"]
        new_results = []
        for result in results:
            new_result = dict()
            if result["type"] == "OCR":
                new_result["type"] = "OCR"
                new_result["content"] = self.remove_names(
                    result["content"]["text"])
                new_result["app_name"] = result["content"]["app_name"]
                new_result["window_name"] = result["content"]["window_name"]
            elif result["type"] == "Audio":
                new_result["type"] = "Audio"
                new_result["content"] = result["content"]["transcription"]
                new_result["device_name"] = result["content"]["device_name"]
                # NOTE: Not removing names from audio transcription
            else:
                raise ValueError(f"Unknown result type: {result['type']}")
            new_result["timestamp"] = self.format_timestamp(
                result["content"]["timestamp"])
            new_results.append(new_result)
        return new_results

    def parse_tool_or_response_string(self, response_text: str) -> str | dict:
        tool_start_string = "<function=screenpipe_search>"

        def is_tool_condition(text):
            return text.startswith(tool_start_string)
        if is_tool_condition(response_text):
            try:
                end_index = response_text.rfind("}")
                if end_index == -1:
                    print("Closing bracket not found in response text")
                    return response_text

                function_args_str = response_text[len(
                    tool_start_string):end_index + 1]

                # Validate JSON structure
                # This will raise JSONDecodeError if invalid
                json.loads(function_args_str)
                # TODO: Avoid duplicate json.loads call
                # by storing the object and skipping json.loads if isinstance(arguments, dict)
                # Append new tool call for screenpipe_search
                new_tool_call = {
                    "id": f"call_{len(function_args_str)}",
                    "type": "function",
                    "function": {
                        "name": "screenpipe_search",
                        "arguments": function_args_str
                    }
                }
                return new_tool_call
            except json.JSONDecodeError:
                print("Error: Invalid JSON in function arguments")
                return response_text
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                return "An unexpected error occurred while processing the function call"
        else:
            return response_text

    def _tool_response_as_results_or_str(self, messages: list) -> str | dict:
        try:
            response = self._make_tool_api_call(messages)
        except Exception:
            return "Failed tool api call."

        tool_calls = self._extract_tool_calls(response)

        if not tool_calls:
            response_text = response.choices[0].message.content
            parsed_response = self.parse_tool_or_response_string(response_text)
            if isinstance(parsed_response, str):
                return parsed_response
            parsed_tool_call = parsed_response
            assert isinstance(
                parsed_tool_call, dict), "Parsed tool must be dict"
            # RESPONSE is a tool
            tool_calls = [parsed_tool_call]

        tool_calls = self._limit_tool_calls(tool_calls)
        search_results = self._process_tool_calls(tool_calls)
        return search_results

    def _parse_schema_from_response(
            self,
            response_text: str,
            target_schema=SearchSchema) -> SearchSchema | str:
        """
        Parses the response text into a dictionary using the provided Pydantic schema.

        Args:
            response_text (str): The response text to parse.
            schema (BaseModel): The Pydantic schema to validate the parsed data against.

        Returns:
            dict: The parsed and validated data as a dictionary. If parsing fails, returns an empty dictionary.
        """
        assert issubclass(
            target_schema, BaseModel), "Schema must be a Pydantic BaseModel"
        try:
            response_object = json.loads(response_text)
            pydantic_object = target_schema(**response_object)
            return pydantic_object
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error: {e}")
            return response_text

    def _get_response_format(self) -> dict:
        json_schema = SearchSchema.model_json_schema()
        allow_condition = "lmstudio" in self.local_grammar_model
        if allow_condition:
            return {
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "schema": json_schema
                }
            }
        # OpenAI format, but doesn't allow a forced schema
        else:
            return {
                "type": "json_object",
            }

    def _grammar_response_as_results_or_str(
            self, messages: list) -> str | dict:
        # Replace system message
        assert messages[0]["role"] == "system", "There should be a system message here!"
        # NOTE: Response format varies by provider
        try:
            response = self.client.chat.completions.create(
                model=self.local_grammar_model,
                messages=messages,
                response_format=self._get_response_format(),
            )
            response_text = response.choices[0].message.content
            parsed_search_schema = self._parse_schema_from_response(
                response_text)
            if isinstance(parsed_search_schema, str):
                return response_text

            function_args = parsed_search_schema.model_dump()
            print("Constructed search params:", function_args)
            search_results = screenpipe_search(**function_args)
            if not search_results:
                return "No results found"
            if "error" in search_results:
                return search_results["error"]
            return search_results
        except Exception:
            return "Failed grammar api call."

    def _prologue_from_search_results(self, search_results: dict) -> str:
        return f"Found {len(search_results)} results"

    def pipe(
        self, body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")
        print("Now piping body:", body)
        assert "messages" in body and "stream" in body, "Body must have keys 'messages' and 'stream'"

        print("Valves:", self.valves)
        self.initialize_settings()
        messages = self._prepare_messages(body["messages"])

        if self.use_grammar:
            parsed_results = self._grammar_response_as_results_or_str(messages)
        else:
            parsed_results = self._tool_response_as_results_or_str(messages)
        if isinstance(parsed_results, str):
            return parsed_results
        search_results = parsed_results
        # Get Final Response Prologue
        final_response_prologue = self._prologue_from_search_results(
            search_results)
        # Sanitize results
        sanitized_results = self.sanitize_results(search_results)
        results_as_string = json.dumps(sanitized_results)
        print("Results as string:", results_as_string)
        messages_with_screenpipe_data = self.get_messages_with_screenpipe_data(
            messages,
            results_as_string
        )

        return self._generate_final_response(
            body, messages_with_screenpipe_data)

    def _prepare_messages(self, messages):
        assert messages[-1]["role"] == "user", "Last message must be from the user!"
        if messages[0]["role"] == "system":
            print("System message is being replaced!")
        if len(messages) > 2:
            print("Warning! This LLM call does not use past chat history!")

        CURRENT_TIME = get_current_time()
        # NOTE: This overrides valve settings if self.use_grammar is True!!!
        if self.use_grammar:
            system_message = f"""You are a helpful assistant. Create a screenpipe search conforming to the correct schema to search captured data stored in ScreenPipe's local database.
Fields:
limit (int): The maximum number of results to return. Should be between 1 and 100. Default to 10.
content_type (Literal["ocr", "audio", "all"]): The type of content to search. Default to "all".
search_substring (Optional[str]): The optional search term.
start_time (Optional[str]): The start timestamp for the search range. Defaults to "2024-10-01T00:00:00Z".
end_time (Optional[str]): The end timestamp for the search range. Defaults to "2024-10-31T23:59:59Z".
app_name (Optional[str]): The name of the app to search in. Defaults to None.

The start_time and end_time fields must be in the same format as the current time.
Current time: {CURRENT_TIME}.

Construct an optimal search filter for the query. When appropriate, create a search_substring to narrow down the search results. Do not include unnecessary fields.
"""
        else:
            system_message = f"You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {CURRENT_TIME}. When appropriate, create a short search_substring to narrow down the search results."
        new_messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": messages[-1]["content"]}
        ]
        return new_messages

    def _make_tool_api_call(self, messages):
        tool_model = self.tool_model
        print("Using tool model:", tool_model)
        return self.client.chat.completions.create(
            model=tool_model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=False
        )

    def _extract_tool_calls(self, response):
        return response.choices[0].message.model_dump().get('tool_calls', [])

    def _limit_tool_calls(self, tool_calls):
        if not tool_calls:
            raise ValueError("No tool calls found")
        if len(tool_calls) > MAX_TOOL_CALLS:
            print(
                f"Warning: More than {MAX_TOOL_CALLS} tool calls found. Only the first {MAX_TOOL_CALLS} tool calls will be processed.")
            return tool_calls[:MAX_TOOL_CALLS]
        return tool_calls

    def _process_tool_calls(self, tool_calls) -> dict | str:
        for tool_call in tool_calls:
            if tool_call['function']['name'] == 'screenpipe_search':
                function_args = json.loads(tool_call['function']['arguments'])
                search_results = screenpipe_search(**function_args)
                if not search_results:
                    return "No results found"
                if "error" in search_results:
                    return search_results["error"]
                return search_results
        raise ValueError("No valid tool call found")

    def _generate_final_response(self, body, messages_with_screenpipe_data):
        if body["stream"]:
            return self.client.chat.completions.create(
                model=self.final_model,
                messages=messages_with_screenpipe_data,
                stream=True
            )
        else:
            final_response = self.client.chat.completions.create(
                model=self.final_model,
                messages=messages_with_screenpipe_data,
            )
            return final_response.choices[0].message.content

    def get_messages_with_screenpipe_data(
            self,
            messages: List[dict],
            results_as_string: str) -> List[dict]:
        """
        Combines the last user message with sanitized ScreenPipe search results.
        """
        SYSTEM_MESSAGE = "You are a helpful assistant that parses screenpipe search results. Use the search results to answer the user's question as best as possible. If unclear, synthesize the context and provide an explanation."
        if messages[-1]["role"] != "user":
            raise ValueError("Last message must be from the user!")
        if len(messages) > 2:
            print("Warning! This LLM call does not use past chat history!")

        new_user_message = self.reformat_user_message(
            messages[-1]["content"], results_as_string)
        new_messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": new_user_message}
        ]
        return new_messages

    @staticmethod
    def remove_names(content: str) -> str:
        for sensitive_word, replacement in REPLACEMENT_TUPLES:
            content = content.replace(sensitive_word, replacement)
        return content

    @staticmethod
    def format_timestamp(
            timestamp: str,
            offset_hours: Optional[float] = DEFAULT_UTC_OFFSET) -> str:
        """
        Formats an ISO UTC timestamp string to local time with an optional hour offset.

        Args:
            timestamp (str): ISO format UTC timestamp (YYYY-MM-DDTHH:MM:SS.ssssssZ or YYYY-MM-DDTHH:MM:SSZ)
            offset_hours (Optional[float]): Hours to offset from UTC. Default -7 (PDT).
                                        Example: -4 for EDT, 5.5 for IST, None for UTC.

        Returns:
            str: Formatted timestamp as "MM/DD/YY HH:MM" (24-hour format)
        """
        if not isinstance(timestamp, str):
            raise ValueError("Timestamp must be a string")

        try:
            # Force UTC interpretation by using timezone.utc
            dt = datetime.strptime(
                timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                dt = datetime.strptime(
                    timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {timestamp}")

        if offset_hours is not None:
            dt = dt + timedelta(hours=offset_hours)

        return dt.strftime("%m/%d/%y %H:%M")

    @staticmethod
    def reformat_user_message(
            user_message: str,
            sanitized_results: str) -> str:
        """
        Reformats the user message by adding context and rules from ScreenPipe search results.
        """
        assert isinstance(
            sanitized_results, str), "Sanitized results must be a string"
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

    @staticmethod
    def get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
