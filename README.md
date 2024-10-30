# screenpipe-python-client
 
The following is a Python client for the Screenpipe API! Should make it a lot easier for the community to troubleshoot/interact with the Screenpipe API more intuitively. The API reference in docs.md is based on the source code of https://github.com/mediar-ai/screenpipe/blob/main/screenpipe-server/src/server.rs. The screenpipe desktop app is not needed for this project. 

Check INSTRUCTIONS.md for a place to start! For Open WebUI integration, check out the files in the `open-webui-workspace` folder.

For developers, use screenpipe_client.py as an SDK for Python integrations.

For instance, to check screenpipe status:
```bash
cd screenpipe_python_client
python cli.py health-check
```

Below is the main function of cli.py. I made it so you can easily test out the various functions of the SDK.

```python
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
```

Feel welcome to beep @ me on Discord or by interacting on this repo if you find this useful! Cheers :D
