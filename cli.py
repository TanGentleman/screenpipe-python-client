import requests
import logging
import argparse
import json
from utils.screenpipe_client import (
    search,
    list_audio_devices,
    add_tags_to_content,
    remove_tags_from_content,
    download_pipe,
    run_pipe,
    stop_pipe,
    health_check,
    list_monitors,
    list_pipes,
    get_pipe_info
)
from utils.outputs import SearchOutput, HealthCheck


def main():
    """
    Entry point of the ScreenPipe API Client.

    This function parses command line arguments and executes the corresponding actions based on the provided command.

    Usage:
        python cli.py search [--query QUERY] [--content-type CONTENT_TYPE] [--limit LIMIT] [--offset OFFSET]
                             [--start-time START_TIME] [--end-time END_TIME] [--app-name APP_NAME]
                             [--window-name WINDOW_NAME] [--include-frames] [--min-length MIN_LENGTH]
                             [--max-length MAX_LENGTH]

        python cli.py list-audio-devices

        python cli.py add-tags-to-content --content-type CONTENT_TYPE --id ID --tags TAGS [TAGS ...]

        python cli.py download-pipe --url URL

        python cli.py run-pipe --pipe-id PIPE_ID

        python cli.py stop-pipe --pipe-id PIPE_ID

        python cli.py health-check

        python cli.py list-monitors

        python cli.py list-pipes

        python cli.py get-pipe-info --pipe-id PIPE_ID

        python cli.py remove-tags-from-content --content-type CONTENT_TYPE --id ID --tags TAGS [TAGS ...]

    Command Line Arguments:
        search:
            --query: The search term
            --content-type: The type of content to search (ocr, audio, all)
            --limit: The maximum number of results per page
            --offset: The pagination offset
            --start-time: The start timestamp
            --end-time: The end timestamp
            --app-name: The application name
            --window-name: The window name
            --include-frames: If True, fetch frame data for OCR content
            --min-length: Minimum length of the content
            --max-length: Maximum length of the content

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

        list-monitors:
            No additional arguments required.

        list-pipes:
            No additional arguments required.

        get-pipe-info:
            --pipe-id: The ID of the pipe

        remove-tags-from-content:
            --content-type: The type of content
            --id: The ID of the content item
            --tags: A list of tags to remove
    """
    parser = argparse.ArgumentParser(description="ScreenPipe API Client")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", help="The search term")
    search_parser.add_argument(
        "--content-type",
        help="The type of content to search (ocr, audio, all)")
    search_parser.add_argument(
        "--limit",
        type=int,
        help="The maximum number of results per page")
    search_parser.add_argument(
        "--offset",
        type=int,
        help="The pagination offset")
    search_parser.add_argument("--start-time", help="The start timestamp")
    search_parser.add_argument("--end-time", help="The end timestamp")
    search_parser.add_argument("--app-name", help="The application name")
    search_parser.add_argument("--window-name", help="The window name")
    search_parser.add_argument(
        "--include-frames",
        action="store_true",
        help="If True, fetch frame data for OCR content")
    search_parser.add_argument(
        "--min-length",
        type=int,
        help="Minimum length of the content")
    search_parser.add_argument(
        "--max-length",
        type=int,
        help="Maximum length of the content")

    list_audio_devices_parser = subparsers.add_parser(
        "list-audio-devices")  # No args

    add_tags_to_content_parser = subparsers.add_parser("add-tags-to-content")
    add_tags_to_content_parser.add_argument(
        "--content-type", help="The type of content")
    add_tags_to_content_parser.add_argument(
        "--id", type=int, help="The ID of the content item")
    add_tags_to_content_parser.add_argument(
        "--tags", nargs="+", help="A list of tags to add")

    download_pipe_parser = subparsers.add_parser("download-pipe")
    download_pipe_parser.add_argument("--url", help="The URL of the pipe")

    run_pipe_parser = subparsers.add_parser("run-pipe")
    run_pipe_parser.add_argument("--pipe-id", help="The ID of the pipe")

    stop_pipe_parser = subparsers.add_parser("stop-pipe")
    stop_pipe_parser.add_argument("--pipe-id", help="The ID of the pipe")

    health_check_parser = subparsers.add_parser("health-check")  # No args

    list_monitors_parser = subparsers.add_parser("list-monitors")

    list_pipes_parser = subparsers.add_parser("list-pipes")

    get_pipe_info_parser = subparsers.add_parser("get-pipe-info")
    get_pipe_info_parser.add_argument("--pipe-id", help="The ID of the pipe")

    remove_tags_from_content_parser = subparsers.add_parser(
        "remove-tags-from-content")
    remove_tags_from_content_parser.add_argument(
        "--content-type", help="The type of content")
    remove_tags_from_content_parser.add_argument(
        "--id", type=int, help="The ID of the content item")
    remove_tags_from_content_parser.add_argument(
        "--tags", nargs="+", help="A list of tags to remove")

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
            include_frames=args.include_frames,
            min_length=args.min_length,
            max_length=args.max_length
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
                print(json.dumps(status.to_dict(), indent=4))
            except Exception as e:
                print(f"Error converting status!")
                print(json.dumps(status, indent=4))

    elif args.command == "list-monitors":
        monitors = list_monitors()
        if monitors:
            print(json.dumps(monitors, indent=4))

    elif args.command == "list-pipes":
        pipes = list_pipes()
        if pipes:
            print(json.dumps(pipes, indent=4))

    elif args.command == "get-pipe-info":
        info = get_pipe_info(args.pipe_id)
        if info:
            print(json.dumps(info, indent=4))

    elif args.command == "remove-tags-from-content":
        response = remove_tags_from_content(
            args.content_type, args.id, args.tags)
        if response:
            print(json.dumps(response, indent=4))


if __name__ == "__main__":
    main()
