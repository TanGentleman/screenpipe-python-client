# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful assistant that can access external functions. When performing searches, consider the current date and time, which is {current_time} (ISO format). If specified, create a single-word search_substring."""

JSON_SYSTEM_MESSAGE = """You are a helpful assistant. Given a user request, construct search parameters for searching chunks (audio, ocr, etc.) in ScreenPipe's local database.

Use the properties field below to construct the search parameters:
{schema}

Ensure the following rules are met:
    - limit must be between 1 and 100. defaults to 5 if not specified.
    - content_type must be one of: "ocr", "audio", "all"
    - time values should be null unless the query specifies a time range
    - only include a search_substring if specified in the query

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

DEFAULT_QUERY = "Search the past 10 days for audio. Try your best to contextualize my conversations."
DEFAULT_STREAM = True

EXAMPLE_SEARCH_RESULTS = [
    {
        "content": "Hey Jason, can you help me with the project deadline?",
        "timestamp": "2024-03-20T14:30:00Z",
        "source": "Team Meeting - Zoom (audio)"
    },
    {
        "content": "Project Status: In Progress\nDeadline: March 25, 2024",
        "timestamp": "2024-03-20T14:31:00Z",
        "source": "Project Management Dashboard (ocr)"
    }
]
