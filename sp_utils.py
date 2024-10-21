from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

# NOTE: This has Sensitive information

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


def sanitize_results(results: dict) -> list[dict]:
    """
    Sanitizes the results from the screenpipe_search function.
    """
    assert results.get("data"), "No data found in results"
    results = results["data"]
    new_results = []
    for result in results:
        new_result = {}
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

def reformat_user_message(user_message: str, sanitized_results: List[dict]) -> str:
    """
    Reformats the user message by adding context and rules from ScreenPipe search results.

    Args:
        user_message (str): The original user message.

    Returns:
        str: A reformatted user message with added context and rules.
    """
    context = "\n".join([f"{result['type']} - {result['content']}" for result in sanitized_results])
    
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
{user_message}
</user_query>
"""
    return reformatted_message

def get_messages_with_screenpipe_data(messages: List[dict], sanitized_results: List[dict]) -> List[dict]:
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
    
    new_user_message = reformat_user_message(messages[-1]["content"], sanitized_results)
    new_messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": new_user_message}
    ]
    return new_messages


def main():
    while True:
        timestamp = input("Enter a timestamp (or 'q' to quit): ")
        if timestamp.lower() == 'q':
            break
        try:
            print(convert_to_pst(timestamp))
        except ValueError:
            print("Invalid timestamp format. Please use YYYY-MM-DDTHH:MM:SS.ssssssZ")


if __name__ == "__main__":
    main()
