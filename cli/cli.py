import argparse
import json
import sys
from src import ScreenpipeClient, SearchOutput, HealthCheck


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

        python cli.py install-pipe --source URL_OR_PATH

        python cli.py enable-pipe --pipe-id PIPE_ID

        python cli.py disable-pipe --pipe-id PIPE_ID

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
            --content-type: all, ocr, audio, input, accessibility or memory
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

        install-pipe (alias download-pipe):
            --source: URL or local path of the pipe

        enable-pipe, disable-pipe, run-pipe, stop-pipe:
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
        help="all, ocr, audio, input, accessibility or memory")
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

    install_pipe_parser = subparsers.add_parser(
        "install-pipe", aliases=["download-pipe"])
    install_pipe_parser.add_argument(
        "--source", "--url", dest="source", help="URL or local path of the pipe")

    for name, help_text in [
            ("enable-pipe", "Enable a pipe's schedule"),
            ("disable-pipe", "Disable a pipe's schedule"),
            ("run-pipe", "Run a pipe once, now"),
            ("stop-pipe", "Stop a pipe's current run")]:
        pipe_parser = subparsers.add_parser(name, help=help_text)
        pipe_parser.add_argument("--pipe-id", help="The ID of the pipe")

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

    client = ScreenpipeClient()
    if args.command is None:
        args.command = "health-check"
    response = run_command(client, args)
    if response is None:
        print("Request failed. Is screenpipe running on localhost:3030?",
              file=sys.stderr)
        return 1
    print(json.dumps(response, indent=4))
    return 0


def run_command(client: ScreenpipeClient, args: argparse.Namespace):
    """Run one subcommand and return its JSON-ready response, or None on failure."""
    if args.command == "search":
        results = client.search(
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
        return SearchOutput(results).to_dict() if results else None
    if args.command == "health-check":
        status = client.health_check()
        if not status:
            return None
        try:
            return HealthCheck(**status).to_dict()
        except Exception:
            return status
    if args.command == "list-audio-devices":
        return client.list_audio_devices()
    if args.command == "list-monitors":
        return client.list_monitors()
    if args.command == "list-pipes":
        return client.list_pipes()
    if args.command == "get-pipe-info":
        return client.get_pipe_info(args.pipe_id)
    if args.command in ("install-pipe", "download-pipe"):
        return client.install_pipe(args.source)
    if args.command == "enable-pipe":
        return client.enable_pipe(args.pipe_id)
    if args.command == "disable-pipe":
        return client.enable_pipe(args.pipe_id, enabled=False)
    if args.command == "run-pipe":
        return client.run_pipe(args.pipe_id)
    if args.command == "stop-pipe":
        return client.stop_pipe(args.pipe_id)
    if args.command == "add-tags-to-content":
        return client.add_tags_to_content(args.content_type, args.id, args.tags)
    if args.command == "remove-tags-from-content":
        return client.remove_tags_from_content(
            args.content_type, args.id, args.tags)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
