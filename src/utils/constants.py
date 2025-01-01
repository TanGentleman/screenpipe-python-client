# System Messages
TOOL_SYSTEM_MESSAGE = """You are a helpful search assistant. Use the supplied tools to search the database and assist the user. If the user requests recent results, default to the last 48 hours."""

FINAL_RESPONSE_SYSTEM_MESSAGE = """You are an AI assistant analyzing screen activity data from ScreenPipe. Your task is to:

1. Analyze the provided data (OCR text, audio transcriptions, and metadata)
2. Provide clear, actionable insights
3. Answer the user's query with the retrieved data

Input data is provided in XML tags (<user_query>, <search_parameters>, <context>). Focus on delivering practical insights that help users understand and improve their screen time patterns."""


DEFAULT_QUERY = "Search the past 10 days for audio and screen content. Try your best to contextualize my conversations with a limit of 2 results."
DEFAULT_STREAM = True

EXAMPLE_SEARCH_RESULTS = [
    {
        "content": "Hey Jason, can you help me with the project deadline?",
        "timestamp": "11/19/24 00:07",
        "type": "Audio",
        "device_name": "MacBook Pro Microphone ",
    },
    {
        "content": "Project Status: In Progress\nDeadline: March 25, 2024",
        "timestamp": "11/13/24 14:31",
        "type": "OCR",
        "app_name": "Project Management Dashboard"
    }
]
EXAMPLE_SEARCH_PARAMS = {
    "content_type": "AUDIO",
    "from_time": "2024-07-10T00:00:00Z",
    "to_time": "2024-12-01T23:59:59Z",
    "limit": 2,
    "search_substring": None,
    "application": None
}

FINAL_RESPONSE_USER_MESSAGE = """\
<user_query>
{query}
</user_query>

<search_parameters>
{search_params}
</search_parameters>

<context>
{context}
</context>"""
