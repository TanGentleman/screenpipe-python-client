from datetime import datetime

def convert_to_local_time(timestamp, safety=True):
    """
    Converts a given timestamp to the user's local time.

    Args:
    - timestamp (str): The timestamp to convert, in the format YYYY-MM-DDTHH:MM:SS.ssssssZ.
    - safety (bool): If True, the function will return the original timestamp if it does not end with 'Z'. Defaults to True.

    Returns:
    - str: The converted timestamp in the format MM/DD/YY HH:MM AM/PM.
    """
    if safety and not timestamp.endswith('Z'):
        return timestamp
    
    # Parse the UTC timestamp
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Convert to local timezone
    dt_local = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    
    # Format the date string
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
