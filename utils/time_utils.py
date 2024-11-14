from datetime import datetime, timedelta, timezone
from typing import Optional, Union

PREFER_24_HOUR_FORMAT = False


def format_timestamp(
        timestamp: str,
        offset_hours: Optional[float] = None) -> str:
    """Formats ISO UTC timestamp to UTC time with optional hour offset.
    Args:
        timestamp (str): ISO UTC timestamp (YYYY-MM-DDTHH:MM:SS[.ssssss]Z)
        offset_hours (Optional[float]): Hours offset from UTC. None for UTC.
    Returns:
        str: Formatted as "MM/DD/YY HH:MM" (24-hour)
    Raises:
        ValueError: If invalid timestamp format
    """
    if not isinstance(timestamp, str):
        raise ValueError("Timestamp must be a string")

    try:
        dt = datetime.strptime(timestamp.split(
            '.')[0] + 'Z', "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    if offset_hours is not None:
        dt = dt + timedelta(hours=offset_hours)

    return dt.strftime("%m/%d/%y %H:%M")


def get_past_time(days: int = 0, weeks: int = 0, months: int = 0,
                  hours: int = 0, minutes: int = 0) -> str:
    """Get timestamp for a past time relative to now.
    Args: days/weeks/months/hours/minutes in the past (all >= 0)
    Returns: Timestamp as YYYY-MM-DDTHH:MM:SSZ
    """
    delta = timedelta(days=days + weeks * 7 + months * 30,
                      hours=hours, minutes=minutes)
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
