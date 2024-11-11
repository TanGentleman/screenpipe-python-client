from datetime import datetime, timedelta, timezone
from typing import Optional, Union

PREFER_24_HOUR_FORMAT = False

def format_timestamp(
        timestamp: str,
        offset_hours: Optional[float] = None) -> str:
    """
    Formats an ISO UTC timestamp string to local time with an optional hour offset.

    Args:
        timestamp (str): ISO format UTC timestamp (YYYY-MM-DDTHH:MM:SS.ssssssZ or YYYY-MM-DDTHH:MM:SSZ)
        offset_hours (Optional[float]): Hours to offset from UTC. Default -7 (PDT).
                                      Example: -4 for EDT, 5.5 for IST, None for UTC.

    Returns:
        str: Formatted timestamp as "MM/DD/YY HH:MM" (24-hour format)

    Raises:
        ValueError: If timestamp format is invalid or not a string
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

def get_past_time(
        days: int = 0,
        weeks: int = 0,
        months: int = 0,
        hours: int = 0,
        minutes: int = 0) -> str:
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


def persistent_stamper():
    while True:
        timestamp = input("Enter a timestamp (or 'q' to quit): ")
        if timestamp.lower() == 'q':
            break
        try:
            print(format_timestamp(timestamp))
        except ValueError:
            print("Invalid timestamp format. Please use YYYY-MM-DDTHH:MM:SS.ssssssZ")


def main():
    print("Welcome! Current timestamp:")
    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    print(current_timestamp)
    print("Converted to your local time:")
    print(format_timestamp(current_timestamp))
    print("Converted to current timezone:")
    print(format_timestamp(current_timestamp, offset_hours=-7))


if __name__ == "__main__":
    main()
