import argparse
import json
from screenpipe_client import (
    search,
    list_audio_devices,
    add_tags_to_content,
    download_pipe,
    run_pipe,
    stop_pipe,
    health_check
)
from outputs import SearchOutput, HealthCheck

def main():
    """
    Entry point of the ScreenPipe API Client.

    This function parses command line arguments and executes the corresponding actions based on the provided command.

    Usage:
        python cli.py search [--query QUERY] [--content-type CONTENT_TYPE] [--limit LIMIT] [--offset OFFSET]
                             [--start-time START_TIME] [--end-time END_TIME] [--app-name APP_NAME]
                             [--window-name WINDOW_NAME] [--include-frames]

        python cli.py list-audio-devices

        python cli.py add-tags-to-content --content-type CONTENT_TYPE --id ID --tags TAGS [TAGS ...]

        python cli.py download-pipe --url URL

        python cli.py run-pipe --pipe-id PIPE_ID

        python cli.py stop-pipe --pipe-id PIPE_ID

        python cli.py health-check

    Command Line Arguments:
        search:
            --query: The search term
            --content-type: The type of content to search
            --limit: The maximum number of results per page
            --offset: The pagination offset
            --start-time: The start timestamp
            --end-time: The end timestamp
            --app-name: The application name
            --window-name: The window name
            --include-frames: If True, fetch frame data for OCR content

        list-audio-devices:
            No additional arguments required.

        add-tags-to-content:
            --content-type: The type of content
            --id: The ID of the content item
            --tags: A list of tags to add

        download-pipe:
            --url: The URL of the pipe

        run-pipe:
            --pipe-id: The ID of the pipe

        stop-pipe:
            --pipe-id: The ID of the pipe

        health-check:
            No additional arguments required.
    """
    # Rest of the code...
    parser = argparse.ArgumentParser(description="ScreenPipe API Client")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", help="The search term")
    search_parser.add_argument("--content-type", help="The type of content to search")
    search_parser.add_argument("--limit", type=int, help="The maximum number of results per page")
    search_parser.add_argument("--offset", type=int, help="The pagination offset")
    search_parser.add_argument("--start-time", help="The start timestamp")
    search_parser.add_argument("--end-time", help="The end timestamp")
    search_parser.add_argument("--app-name", help="The application name")
    search_parser.add_argument("--window-name", help="The window name")
    search_parser.add_argument("--include-frames", action="store_true", help="If True, fetch frame data for OCR content")

    list_audio_devices_parser = subparsers.add_parser("list-audio-devices")

    add_tags_to_content_parser = subparsers.add_parser("add-tags-to-content")
    add_tags_to_content_parser.add_argument("--content-type", help="The type of content")
    add_tags_to_content_parser.add_argument("--id", type=int, help="The ID of the content item")
    add_tags_to_content_parser.add_argument("--tags", nargs="+", help="A list of tags to add")

    download_pipe_parser = subparsers.add_parser("download-pipe")
    download_pipe_parser.add_argument("--url", help="The URL of the pipe")

    run_pipe_parser = subparsers.add_parser("run-pipe")
    run_pipe_parser.add_argument("--pipe-id", help="The ID of the pipe")

    stop_pipe_parser = subparsers.add_parser("stop-pipe")
    stop_pipe_parser.add_argument("--pipe-id", help="The ID of the pipe")

    health_check_parser = subparsers.add_parser("health-check")

    args = parser.parse_args()

    if args.command == "search":
        results = search(
            query=args.query,
            content_type=args.content_type,
            limit=args.limit,
            offset=args.offset,
            start_time=args.start_time,
            end_time=args.end_time,
            app_name=args.app_name,
            window_name=args.window_name,
            include_frames=args.include_frames
        )
        if results:
            try:
                results = SearchOutput(**results)
            except Exception as e:
                print(f"Error converting results: {e}")
            print(json.dumps(results.__dict__, indent=4))

    elif args.command == "list-audio-devices":
        devices = list_audio_devices()
        if devices:
            print(json.dumps(devices, indent=4))

    elif args.command == "add-tags-to-content":
        response = add_tags_to_content(args.content_type, args.id, args.tags)
        if response:
            print(json.dumps(response, indent=4))

    elif args.command == "download-pipe":
        response = download_pipe(args.url)
        if response:
            print(json.dumps(response, indent=4))

    elif args.command == "run-pipe":
        response = run_pipe(args.pipe_id)
        if response:
            print(json.dumps(response, indent=4))

    elif args.command == "stop-pipe":
        response = stop_pipe(args.pipe_id)
        if response:
            print(json.dumps(response, indent=4))

    elif args.command == "health-check":
        status = health_check()
        if status:
            try:
                status = HealthCheck(**status)
            except Exception as e:
                print(f"Error converting status: {e}")
            print(json.dumps(status.__dict__, indent=4))

if __name__ == "__main__":
    main()