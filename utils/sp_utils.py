from datetime import datetime

PREFER_24_HOUR_FORMAT = False

def convert_to_local_time(timestamp: str, use_24_hour_format=PREFER_24_HOUR_FORMAT):
    """
    Converts a given timestamp to the user's local time.

    Args:
    - timestamp (str): The timestamp to convert, in the format YYYY-MM-DDTHH:MM:SS.ssssssZ.
    - use_24_hour_format (bool): If True, the function will return the time in 24-hour format. Defaults to True.

    Returns:
    - str: The converted timestamp in the format MM/DD/YY HH:MM (24-hour) or MM/DD/YY HH:MM AM/PM (12-hour).
    """
    correct_timestamp_length = len("YYYY-MM-DDTHH:MM:SS.ssssssZ")
    alternate_timestamp_length = len("YYYY-MM-DDTHH:MM:SS")
    if len(timestamp) != correct_timestamp_length:
        if len(timestamp) == alternate_timestamp_length:
            timestamp += ".000000Z"
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
