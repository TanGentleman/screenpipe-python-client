from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo
import json

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
