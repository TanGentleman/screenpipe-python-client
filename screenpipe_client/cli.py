import argparse
import json
import logging
import sys

from .client import ScreenpipeClient


def main(argv=None) -> int:
    """Run the screenpipe-client command line."""
    parser = argparse.ArgumentParser(
        prog="screenpipe-client",
        description="Query a running screenpipe. Defaults to health-check.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3030)
    parser.add_argument(
        "--api-key", help="Bearer token; defaults to $SCREENPIPE_API_KEY")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", help="The search term")
    search_parser.add_argument(
        "--content-type",
        help="all, ocr, audio, input, accessibility, memory or parsed")
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

    subparsers.add_parser("list-audio-devices")  # No args

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

    subparsers.add_parser("health-check")  # No args

    subparsers.add_parser("list-monitors")

    subparsers.add_parser("list-pipes")

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

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    client = ScreenpipeClient(host=args.host, port=args.port, api_key=args.api_key)
    if args.command is None:
        args.command = "health-check"
    with client:
        response = run_command(client, args)
    if response is None:
        print(f"Request failed. Is screenpipe running on {args.host}:{args.port}?",
              file=sys.stderr)
        return 1
    print(json.dumps(response, indent=4))
    return 0


def run_command(client: ScreenpipeClient, args: argparse.Namespace):
    """Run one subcommand and return its JSON-ready response, or None on failure."""
    if args.command == "search":
        return client.search(
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
    if args.command == "health-check":
        return client.health_check()
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
