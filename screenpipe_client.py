# import argparse
# import json
import logging
import requests
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base URL for the API
BASE_URL = "http://localhost:3030"

def search(
    query: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    app_name: Optional[str] = None,
    window_name: Optional[str] = None,
    include_frames: bool = False
) -> Dict:
    """
    Searches captured data (OCR, audio transcriptions, etc.) stored in ScreenPipe's local database based on filters such as content type, timestamps, app name, and window name.

    Args:
    query (str): The search term.
    content_type (str): The type of content to search (OCR, audio, etc.).
    limit (int): The maximum number of results per page.
    offset (int): The pagination offset.
    start_time (str): The start timestamp.
    end_time (str): The end timestamp.
    app_name (str): The application name.
    window_name (str): The window name.
    include_frames (bool): If True, fetch frame data for OCR content.

    Returns:
    dict: The search results.
    """
    if not query:
        logging.warning("Please provide a query. Searching spacebar instead.")
        query = " "
    
    all_content_type = content_type or "OCR and Audio"
    print(f"Searching for: {content_type or all_content_type}")
    params = {
        "q": query,
        "content_type": content_type,
        "limit": limit,
        "offset": offset,
        "start_time": start_time,
        "end_time": end_time,
        "app_name": app_name,
        "window_name": window_name,
        "include_frames": str(include_frames).lower()
    }

    params = {k: v for k, v in params.items() if v is not None}
    try:
        response = requests.get(f"{BASE_URL}/search", params=params)
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
        response = requests.get(f"{BASE_URL}/audio/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error listing audio devices: {e}")
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
        logging.warning("Content type 'ocr' is not used for the tags API. Please use 'vision' instead.")
        content_type = "vision"
    assert content_type in ["audio", "vision"], "Invalid content type. Must be 'audio' or 'vision'."
    try:
        response = requests.post(f"{BASE_URL}/tags/{content_type}/{id}", json={"tags": tags})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error adding tags to content: {e}")
        return None

def download_pipe(url: str) -> Dict:
    """
    Downloads a pipe (plugin) from a specified URL and stores it locally.

    Args:
    url (str): The URL of the pipe.

    Returns:
    dict: The response from the API.
    """
    try:
        response = requests.post(f"{BASE_URL}/pipes/download", json={"url": url})
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
        response = requests.post(f"{BASE_URL}/pipes/enable", json={"pipe_id": pipe_id})
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
        response = requests.post(f"{BASE_URL}/pipes/disable", json={"pipe_id": pipe_id})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error stopping pipe: {e}")
        return None

def health_check() -> Dict:
    """
    Returns the health status of the system, including the timestamps of the last frame and audio captures, and the overall system status.

    Returns:
    dict: The health status of the system.
    """
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking health: {e}")
        return None