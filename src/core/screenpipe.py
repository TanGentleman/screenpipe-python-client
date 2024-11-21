import logging
from typing import Dict, List, Literal, Optional
from httpx import Client, HTTPError


class ScreenpipeClient:
    """Client for interacting with the ScreenPipe API."""

    def __init__(self, port: int = 3030, host: str = "localhost"):
        """Initialize the ScreenPipe client.

        Args:
            port (int): Port number for the ScreenPipe server. Defaults to 3030.
            host (str): Host address for the ScreenPipe server. Defaults to "localhost".
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # API configuration
        self._base_url = f"http://{host}:{port}"
        self._session = Client()
        self._pipe_download_timeout = 20  # seconds

        # Valid content types
        self._valid_content_types = {"ocr", "audio", "all"}
        self._valid_tag_types = {"audio", "vision"}

    def _make_request(
            self,
            method: str,
            endpoint: str,
            **kwargs) -> Optional[Dict]:
        """Make an HTTP request to the ScreenPipe API.

        Args:
            method (str): HTTP method (get, post, delete)
            endpoint (str): API endpoint
            **kwargs: Additional arguments for the request

        Returns:
            Optional[Dict]: JSON response or None if request fails
        """
        try:
            url = f"{self._base_url}/{endpoint.lstrip('/')}"
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            self.logger.error("API request failed!")
            self.logger.debug(f"Error: {e}")
            return None

    def health_check(self) -> Optional[Dict]:
        """Check the health status of the ScreenPipe system.
        
        Returns:
            Optional[Dict]: Health status containing:
                - status: "healthy" or "unhealthy"
                - last_frame_timestamp: Last frame processing time
                - last_audio_timestamp: Last audio processing time  
                - last_ui_timestamp: Last UI monitoring time
                - frame_status: Status of frame processing
                - audio_status: Status of audio processing
                - ui_status: Status of UI monitoring
                - message: Status message
                - verbose_instructions: Troubleshooting steps if unhealthy
        """
        return self._make_request("get", "health")

    def search(
        self,
        limit: int = 20,
        query: str = "",
        content_type: Optional[Literal["ocr", "audio", "all"]] = "all",
        offset: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        app_name: Optional[str] = None,
        window_name: Optional[str] = None,
        include_frames: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Optional[Dict]:
        """Search captured data in ScreenPipe's database.
        
        Returns:
            Optional[Dict]: Search results containing:
                - data: List of content items (OCR or Audio)
                - pagination: Pagination info (limit, offset, total)
        """
        # Validate content type
        if content_type and content_type not in self._valid_content_types:
            raise ValueError(
                f"Invalid content_type. Must be one of: {self._valid_content_types}")

        params = {
            "q": query,
            "content_type": content_type,
            "limit": limit,
            "offset": offset,
            "start_time": start_time,
            "end_time": end_time,
            "app_name": app_name,
            "window_name": window_name,
            "include_frames": "true" if include_frames else None,
            "min_length": min_length,
            "max_length": max_length
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        self.logger.info(
            f"Searching for {limit} chunks. Type: {content_type or 'all'}")
        return self._make_request("get", "search", params=params)

    def list_audio_devices(self) -> Optional[List]:
        """List all available audio devices.
        
        Returns:
            Optional[List]: List of audio devices with name and default status
        """
        return self._make_request("get", "audio/list")

    def list_monitors(self) -> Optional[List]:
        """List all available monitors.
        
        Returns:
            Optional[List]: List of monitors with id, name, dimensions and default status
        """
        return self._make_request("get", "vision/list")

    def _validate_content_type_for_tags(self, content_type: str) -> str:
        """Validate and normalize content type for tag operations."""
        if content_type == "ocr":
            self.logger.warning(
                "Content type 'ocr' is not used for tags API. Using 'vision' instead.")
            content_type = "vision"
        if content_type not in self._valid_tag_types:
            raise ValueError(
                f"Invalid content_type. Must be one of: {self._valid_tag_types}")
        return content_type

    def add_tags_to_content(
            self,
            content_type: str,
            id: int,
            tags: List[str]) -> Optional[Dict]:
        """Add tags to content items.
        
        Returns:
            Optional[Dict]: Success status
        """
        content_type = self._validate_content_type_for_tags(content_type)
        return self._make_request(
            "post",
            f"tags/{content_type}/{id}",
            json={
                "tags": tags})

    def remove_tags_from_content(
            self,
            content_type: str,
            id: int,
            tags: List[str]) -> Optional[Dict]:
        """Remove tags from content items.
        
        Returns:
            Optional[Dict]: Success status
        """
        content_type = self._validate_content_type_for_tags(content_type)
        return self._make_request(
            "delete",
            f"tags/{content_type}/{id}",
            json={
                "tags": tags})

    # Pipe-related methods
    def get_pipe_info(self, pipe_id: str) -> Optional[Dict]:
        """Get information about a specific pipe.
        
        Returns:
            Optional[Dict]: Pipe details including id, name, description, enabled status,
                          configuration and current status
        """
        return self._make_request("get", f"pipes/info/{pipe_id}")

    def list_pipes(self) -> Optional[List]:
        """List all available pipes.
        
        Returns:
            Optional[List]: List of pipes with their details
        """
        return self._make_request("get", "pipes/list")

    def download_pipe(self, url: str) -> Optional[Dict]:
        """Download a pipe from URL.
        
        Returns:
            Optional[Dict]: Success message and pipe ID
        """
        return self._make_request(
            "post",
            "pipes/download",
            json={"url": url},
            timeout=self._pipe_download_timeout
        )

    def run_pipe(self, pipe_id: str) -> Optional[Dict]:
        """Enable and run a pipe.
        
        Returns:
            Optional[Dict]: Success message and pipe ID
        """
        return self._make_request(
            "post",
            "pipes/enable",
            json={
                "pipe_id": pipe_id})

    def stop_pipe(self, pipe_id: str) -> Optional[Dict]:
        """Stop a running pipe.
        
        Returns:
            Optional[Dict]: Success message and pipe ID
        """
        return self._make_request(
            "post",
            "pipes/disable",
            json={
                "pipe_id": pipe_id})

    def update_pipe_configuration(
            self,
            pipe_id: str,
            config: Dict) -> Optional[Dict]:
        """Update pipe configuration.
        
        Returns:
            Optional[Dict]: Success message and pipe ID
        """
        return self._make_request(
            "post",
            "pipes/update",
            json={"pipe_id": pipe_id, "config": config}
        )

    def add_content(
            self,
            device_name: str,
            content_type: str,
            frames: Optional[List[Dict]] = None,
            audio: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Add content (frames or audio) to the database.
        
        Args:
            device_name: Name of the device
            content_type: Type of content ("frames" or "audio") 
            frames: List of frame data including:
                - file_path: Path to frame image
                - timestamp: Frame timestamp
                - app_name: Application name
                - window_name: Window name
                - ocr_results: List of OCR results with text and metadata
                - tags: List of tags
            audio: List of audio data including:
                - device_name: Audio device name
                - is_input: Whether device is input
                - transcription: Audio transcription
                - audio_file_path: Path to audio file
                - duration_secs: Duration in seconds
                - start_offset: Start time offset
                
        Returns:
            Optional[Dict]: Success message
        """
        content = {
            "content_type": content_type,
            "data": {}
        }
        
        if frames:
            content["data"]["frames"] = frames
        if audio:
            content["data"]["audio"] = audio
            
        return self._make_request(
            "post",
            "add",
            json={
                "device_name": device_name,
                "content": content
            }
        )

    def stream_frames(
            self,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None) -> Optional[Dict]:
        """Stream frames between start and end time.
        
        Args:
            start_time: Start timestamp for stream range (ISO format)
            end_time: End timestamp for stream range (ISO format)
            
        Returns:
            Optional[Dict]: Server-sent events stream containing:
                - timestamp: Frame timestamp
                - devices: List of device data including:
                    - device_id: Device identifier
                    - frame: Base64 encoded frame image
                    - metadata: Frame metadata (path, app, window, OCR)
                    - audio: Associated audio data
        """
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._make_request("get", "stream/frames", params=params)

    def execute_input_control(self, action_type: str, action_data: Dict) -> Optional[Dict]:
        """Execute input control action (experimental).
        
        Args:
            action_type: Type of input action (e.g. "KeyPress", "MouseMove")
            action_data: Action-specific data:
                - For KeyPress: key name (e.g. "enter")
                - For MouseMove: x,y coordinates
            
        Returns:
            Optional[Dict]: Success message
        """
        return self._make_request(
            "post",
            "experimental/input_control",
            json={
                "action": {
                    "type": action_type,
                    "data": action_data
                }
            }
        )

    def execute_raw_sql(self, query: str) -> Optional[List[Dict]]:
        """Execute raw SQL query against the database.
        
        Args:
            query: SQL query string
            
        Returns:
            Optional[List[Dict]]: List of query results as dictionaries
        """
        return self._make_request(
            "post",
            "raw_sql",
            json={"query": query}
        )

