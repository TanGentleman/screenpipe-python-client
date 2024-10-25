from datetime import datetime, timedelta

PREFER_24_HOUR_FORMAT = False

from utils.secrets import REPLACEMENT_TUPLES


def reformat_user_message(user_message: str, sanitized_results: str) -> str:
    """
    Reformats the user message by adding context and rules from ScreenPipe search results.

    Args:
        user_message (str): The original user message.

    Returns:
        str: A reformatted user message with added context and rules.
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

def remove_names(content: str) -> str:
    for old, new in REPLACEMENT_TUPLES[:10]:
        content = content.replace(old, new)
    return content

def convert_to_local_time(
        timestamp: str,
        use_24_hour_format=PREFER_24_HOUR_FORMAT):
    """
    Converts a given timestamp to the user's local time.

    Args:
    - timestamp (str): The timestamp to convert, in the format YYYY-MM-DDTHH:MM:SS.ssssssZ.
    - use_24_hour_format (bool): If True, the function will return the time in 24-hour format. Defaults to True.

    Returns:
    - str: The converted timestamp in the format MM/DD/YY HH:MM (24-hour) or MM/DD/YY HH:MM AM/PM (12-hour).
    """
    correct_timestamp_length = len("YYYY-MM-DDTHH:MM:SS.ssssssZ")
    alternate_timestamp_length = len("YYYY-MM-DDTHH:MM:SSZ")
    if len(timestamp) != correct_timestamp_length:
        if len(timestamp) == alternate_timestamp_length:
            timestamp = timestamp[:-1] + ".000000Z"
        else:
            return timestamp

    # Parse the UTC timestamp
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Convert to local timezone
    dt_local = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)

    # Format the date string
    if use_24_hour_format:
        return dt_local.strftime("%m/%d/%y %H:%M")
    else:
        return dt_local.strftime("%m/%d/%y %I:%M%p")


def get_current_time() -> str:
    """Get the current timestamp in UTC timezone.

    Returns the current timestamp in the format YYYY-MM-DDTHH:MM:SSZ.
    """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

def get_past_time(days: int = 0, weeks: int = 0, months: int = 0, hours: int = 0, minutes: int = 0) -> str:
    """
    Get the timestamp for a past time relative to the current time.

    Args:
    - days (int): Number of days in the past.
    - weeks (int): Number of weeks in the past.
    - months (int): Number of months in the past.
    - hours (int): Number of hours in the past.
    - minutes (int): Number of minutes in the past.

    Returns:
    - str: The timestamp in the format YYYY-MM-DDTHH:MM:SSZ.
    """
    assert days >= 0, "days must be non-negative"
    assert weeks >= 0, "weeks must be non-negative"
    assert months >= 0, "months must be non-negative"
    assert hours >= 0, "hours must be non-negative"
    assert minutes >= 0, "minutes must be non-negative"

    # Calculate the total timedelta
    total_days = days + weeks * 7 + months * 30  # Approximate months as 30 days
    delta = timedelta(days=total_days, hours=hours, minutes=minutes)

    return (datetime.now() - delta).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    print("Welcome! Current timestamp:")
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    print(current_timestamp)
    print("Converted to your local time:")
    print(convert_to_local_time(current_timestamp))
    while True:
        timestamp = input("Enter a timestamp (or 'q' to quit): ")
        if timestamp.lower() == 'q':
            break
        try:
            print(convert_to_local_time(timestamp))
        except ValueError:
            print("Invalid timestamp format. Please use YYYY-MM-DDTHH:MM:SS.ssssssZ")


if __name__ == "__main__":
    main()
