import logging
import requests
from typing import Dict, List, Optional

# Set up local logging for visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

SCREENPIPE_PORT = 3030
# Base URL for the API
SCREENPIPE_BASE_URL = f"http://localhost:{SCREENPIPE_PORT}"

# To use:
# ```python
# import screenpipe_client as s
# s.health_check()
# s.search(query='screenpipe', limit=2)
# ```
# Other functions can be used in a similar way


def health_check() -> Dict:
    """
    Returns the health status of the system, including the timestamps of the last frame and audio captures, and the overall system status.

    Returns:
    dict: The health status of the system.
    """
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/health")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking health: {e}")
        return None


def search(
    limit: int = 5,
    query: Optional[str] = None,
    content_type: Optional[str] = None,
    offset: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    app_name: Optional[str] = None,
    window_name: Optional[str] = None,
    include_frames: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Dict:
    """
    Searches captured data (OCR, audio transcriptions, etc.) stored in ScreenPipe's local database based on filters such as content type, timestamps, app name, and window name.

    Args:
    query (str): The search term.
    content_type (str): The type of content to search (ocr, audio, all.).
    limit (int): The maximum number of results per page.
    offset (int): The pagination offset.
    start_time (str): The start timestamp.
    end_time (str): The end timestamp.
    app_name (str): The application name.
    window_name (str): The window name.
    include_frames (bool): If True, fetch frame data for OCR content.
    min_length (int): Minimum length of the content.
    max_length (int): Maximum length of the content.

    Returns:
    dict: The search results.
    """
    if not query:
        logging.warning("Query is an empty string.")
        query = ""

    if content_type is None:
        content_type = "all"
    assert content_type in [
        "ocr", "audio", "all"], "Invalid content type. Must be 'ocr', 'audio', or 'all'."
    print(f"Searching for: {content_type}")
    params = {
        "q": query,
        "content_type": content_type,
        "limit": limit,
        "offset": offset,
        "start_time": start_time,
        "end_time": end_time,
        "app_name": app_name,
        "window_name": window_name,
        "include_frames": "true" if include_frames is True else None,
        "min_length": min_length,
        "max_length": max_length
    }

    # Remove None values from params dictionary
    params = {key: value for key, value in params.items() if value is not None}
    # print(params)
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/search", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching for content: {e}")
        return None


def list_audio_devices() -> List:
    """
    Lists all audio input and output devices available on the machine, including default devices.

    Returns:
    list: A list of audio devices.
    """
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/audio/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error listing audio devices: {e}")
        return None


def list_monitors() -> List:
    """
    Lists all monitors available on the machine, including default monitors.

    Returns:
    list: A list of monitors.
    """
    try:
        response = requests.post(f"{SCREENPIPE_BASE_URL}/vision/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error listing monitors: {e}")
        return None


def add_tags_to_content(content_type: str, id: int, tags: List[str]) -> Dict:
    """
    Adds custom tags to content items based on the content type (audio or vision).

    Args:
    content_type (str): The type of content. Can be "audio" or "vision".
    id (int): The ID of the content item.
    tags (list): A list of tags to add.

    Returns:
    dict: The response from the API.
    """
    if content_type == "ocr":
        logging.warning(
            "Content type 'ocr' is not used for the tags API. Please use 'vision' instead.")
        content_type = "vision"
    assert content_type in [
        "audio", "vision"], "Invalid content type. Must be 'audio' or 'vision'."
    try:
        response = requests.post(
            f"{SCREENPIPE_BASE_URL}/tags/{content_type}/{id}",
            json={
                "tags": tags})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error adding tags to content: {e}")
        return None


def remove_tags_from_content(
        content_type: str,
        id: int,
        tags: List[str]) -> Dict:
    """
    Removes custom tags from content items based on the content type (audio or vision).

    Args:
    content_type (str): The type of content. Can be "audio" or "vision".
    id (int): The ID of the content item.
    tags (list): A list of tags to remove.

    Returns:
    dict: The response from the API.
    """
    if content_type == "ocr":
        logging.warning(
            "Content type 'ocr' is not used for the tags API. Please use 'vision' instead.")
        content_type = "vision"
    assert content_type in [
        "audio", "vision"], "Invalid content type. Must be 'audio' or 'vision'."
    try:
        response = requests.delete(
            f"{SCREENPIPE_BASE_URL}/tags/{content_type}/{id}",
            json={
                "tags": tags})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error removing tags from content: {e}")
        return None


def get_pipe_info(pipe_id: str) -> Dict:
    """
    Retrieves information about a specific pipe.

    Args:
    pipe_id (str): The ID of the pipe.

    Returns:
    dict: The response from the API.
    """
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/pipes/info/{pipe_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting pipe info: {e}")
        return None


def list_pipes() -> List:
    """
    Lists all available pipes.

    Returns:
    list: A list of pipes.
    """
    try:
        response = requests.get(f"{SCREENPIPE_BASE_URL}/pipes/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error listing pipes: {e}")
        return None


def download_pipe(url: str) -> Dict:
    """
    Downloads a pipe (plugin) from a specified URL and stores it locally.

    Args:
    url (str): The URL of the pipe.

    Returns:
    dict: The response from the API.
    """
    PIPE_DOWNLOAD_TIMEOUT_SECS = 20
    try:
        response = requests.post(
            f"{SCREENPIPE_BASE_URL}/pipes/download",
            json={
                "url": url},
            timeout=PIPE_DOWNLOAD_TIMEOUT_SECS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading pipe: {e}")
        return None


def run_pipe(pipe_id: str) -> Dict:
    """
    Enables a pipe (plugin) to start processing data.

    Args:
    pipe_id (str): The ID of the pipe.

    Returns:
    dict: The response from the API.
    """
    try:
        response = requests.post(
            f"{SCREENPIPE_BASE_URL}/pipes/enable",
            json={
                "pipe_id": pipe_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error running pipe: {e}")
        return None


def stop_pipe(pipe_id: str) -> Dict:
    """
    Disables a pipe to stop processing data.

    Args:
    pipe_id (str): The ID of the pipe.

    Returns:
    dict: The response from the API.
    """
    try:
        response = requests.post(
            f"{SCREENPIPE_BASE_URL}/pipes/disable",
            json={
                "pipe_id": pipe_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error stopping pipe: {e}")
        return None


def update_pipe_configuration(pipe_id: str, config: Dict) -> Dict:
    """
    Updates the configuration of a specific pipe.

    Args:
    pipe_id (str): The ID of the pipe.
    config (dict): The new configuration settings for the pipe.

    Returns:
    dict: The response from the API.
    """
    try:
        response = requests.post(
            f"{SCREENPIPE_BASE_URL}/pipes/update",
            json={
                "pipe_id": pipe_id,
                "config": config
            })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error updating pipe configuration: {e}")
        return None
