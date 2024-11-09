# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {current_time}. When appropriate, create a short search_substring to narrow down the search results."""

JSON_SYSTEM_MESSAGE = """You are a helpful assistant. Create a screenpipe search conforming to the correct JSON schema to search captured data stored in ScreenPipe's local database.

Create a JSON object ONLY for the properties field of the search parameters:
{schema}

If the time range is not relevant, use None for the start_time and end_time fields. Otherwise, they must be in ISO format matching the current time: {current_time}.

Construct an optimal search filter for the query. When appropriate, create a search_substring to narrow down the search results. Set a limit based on the user's request, or default to 5.

Example search JSON objects:
{examples}

ONLY Output the search JSON object, nothing else.
"""

EXAMPLE_SEARCH_JSON = """\
{
    "limit": 2,
    "content_type": "audio",
    "start_time": null,
    "end_time": null
}
{
    "limit": 1,
    "content_type": "all",
    "start_time": "2024-03-20T00:00:00Z",
    "end_time": "2024-03-20T23:59:59Z"
}"""
