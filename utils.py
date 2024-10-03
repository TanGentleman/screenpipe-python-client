from datetime import datetime
from re import L
import pytz

def convert_to_pst(timestamp, safety=True):
    if safety:
        if not timestamp.endswith('Z'):
            return timestamp
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    dt_pst = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
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