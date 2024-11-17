# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {current_time} (ISO format). If specified, create a single-word search_substring."""

JSON_SYSTEM_MESSAGE = """You are a helpful assistant. Given a user request, construct search parameters for searching chunks (audio, ocr, etc.) in ScreenPipe's local database.

Use the properties field below to construct the search parameters:
{schema}

Ensure the following rules are met:
    - limit must be between 1 and 100. defaults to 5 if not specified.
    - content_type must be one of: "ocr", "audio", "all"
    - if provided, time values should be in ISO format relative to the current timestamp: {current_time}
    - when appropriate, create a short search_substring to narrow down the search results

Example search JSON objects:
{examples}

ONLY Output the search JSON object, nothing else.
"""

EXAMPLE_SEARCH_JSON = """\
{
    "limit": 10,
    "content_type": "audio",
    "search_substring": "jason",
    "start_time": null,
    "end_time": null
}
{
    "limit": 1,
    "content_type": "all",
    "start_time": "2024-03-20T00:00:00Z",
    "end_time": "2024-03-20T23:59:59Z"
}"""
