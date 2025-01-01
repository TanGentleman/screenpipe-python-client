import logging
from typing import Dict, List, Literal, Optional
from httpx import Client, AsyncClient, HTTPError

DEFAULT_SEARCH_LIMIT = 20  # Updated to match server default

class ScreenpipeClient:
    """Client for interacting with the ScreenPipe API."""

    def __init__(self, port: int = 3030, host: str = "localhost"):
        """Initialize the ScreenPipe client.

        Args:
            port (int): Port number for the ScreenPipe server. Defaults to 3030.
            host (str): Host address for the ScreenPipe server. Defaults to "localhost".
        """
        self._configure_logging()
        self._configure_api(host, port)
        self._configure_valid_types()

    def _configure_logging(self) -> None:
        """Configure logging settings."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _configure_api(self, host: str, port: int) -> None:
        """Configure API connection settings.
        
        Args:
            host: Host address for the ScreenPipe server
            port: Port number for the ScreenPipe server
        """
        self._base_url = f"http://{host}:{port}"
        self._sync_session: Optional[Client] = None
        self._async_session: Optional[AsyncClient] = None

    def _configure_valid_types(self) -> None:
        """Configure valid content and tag types."""
        self._valid_content_types = frozenset({"ocr", "audio", "all"})
        self._valid_tag_types = frozenset({"audio", "vision"})
        # Add new valid types for content addition
        self._valid_add_types = frozenset({"frames", "transcription"})

    @property
    def sync_session(self) -> Client:
        """Get or create synchronous HTTP session.
        
        Returns:
            Client: Synchronous HTTP client session
        """
        if self._sync_session is None:
            self._sync_session = Client()
        return self._sync_session

    @property
    def async_session(self) -> AsyncClient:
        """Get or create asynchronous HTTP session.
        
        Returns:
            AsyncClient: Asynchronous HTTP client session
        """
        if self._async_session is None:
            self._async_session = AsyncClient()
        return self._async_session

    def __enter__(self) -> 'ScreenpipeClient':
        """Context manager entry for synchronous usage.
        
        Returns:
            ScreenpipeClient: The client instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit for synchronous usage."""
        self.close()

    async def __aenter__(self) -> 'ScreenpipeClient':
        """Context manager entry for asynchronous usage.
        
        Returns:
            ScreenpipeClient: The client instance
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit for asynchronous usage."""
        await self.aclose()

    def _make_request(
            self,
            method: str,
            endpoint: str,
            **kwargs) -> Optional[Dict]:
        """Make a synchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Optional[Dict]: JSON response data if successful, None otherwise
        """
        try:
            url = f"{self._base_url}/{endpoint.lstrip('/')}"
            response = self.sync_session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            self.logger.error("API request failed!")
            self.logger.debug(f"Error: {e}")
            return None

    async def _make_request_async(
            self,
            method: str,
            endpoint: str,
            **kwargs) -> Optional[Dict]:
        """Make an asynchronous HTTP request."""
        try:
            url = f"{self._base_url}/{endpoint.lstrip('/')}"
            response = await self.async_session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            self.logger.error("API request failed!")
            self.logger.debug(f"Error: {e}")
            return None

    def close(self) -> None:
        """Close synchronous session."""
        if self._sync_session:
            self._sync_session.close()
            self._sync_session = None

    async def aclose(self) -> None:
        """Close asynchronous session."""
        if self._async_session:
            await self._async_session.aclose()
            self._async_session = None

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
        limit: int = DEFAULT_SEARCH_LIMIT,
        query: Optional[str] = None,
        content_type: Optional[Literal["ocr", "audio", "all"]] = "all",
        offset: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        app_name: Optional[str] = None,
        window_name: Optional[str] = None,
        include_frames: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        speaker_ids: Optional[List[int]] = None
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
            "max_length": max_length,
            "speaker_ids": ",".join(map(str, speaker_ids)) if speaker_ids else None
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
        PIPE_DOWNLOAD_TIMEOUT = 30
        return self._make_request(
            "post",
            "pipes/download",
            json={"url": url},
            timeout=PIPE_DOWNLOAD_TIMEOUT
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

    def delete_pipe(self, pipe_id: str) -> Optional[Dict]:
        """Delete a pipe.
        
        Returns:
            Optional[Dict]: Success message
        """
        return self._make_request(
            "post",
            "pipes/delete",
            json={"pipe_id": pipe_id}
        )

    def add_content(
            self,
            device_name: str,
            content_type: str,
            frames: Optional[List[Dict]] = None,
            transcription: Optional[Dict] = None) -> Optional[Dict]:
        """Add content (frames or transcription) to the database.
        
        Args:
            device_name: Name of the device
            content_type: Type of content ("frames" or "transcription")
            frames: List of frame data including:
                - file_path: Path to frame image
                - timestamp: Frame timestamp
                - app_name: Application name
                - window_name: Window name
                - ocr_results: List of OCR results with text and metadata
                - tags: List of tags
            transcription: Audio transcription data including:
                - transcription: Transcription text
                - transcription_engine: Engine used for transcription
                
        Returns:
            Optional[Dict]: Success message
        """
        if content_type not in self._valid_add_types:
            raise ValueError(f"Invalid content_type. Must be one of: {self._valid_add_types}")

        content = {
            "content_type": content_type,
            "data": {}
        }
        
        if frames:
            content["data"]["frames"] = frames
        elif transcription:
            content["data"]["transcription"] = transcription
        else:
            raise ValueError("Either frames or transcription must be provided")
            
        return self._make_request(
            "post",
            "add",
            json={
                "device_name": device_name,
                "content": content
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

    def merge_frames(self, video_paths: List[str]) -> Optional[Dict]:
        """Merge multiple video frames into a single video.
        
        Args:
            video_paths: List of paths to video files to merge
            
        Returns:
            Optional[Dict]: Path to merged video file
        """
        return self._make_request(
            "post",
            "experimental/frames/merge",
            json={"video_paths": video_paths}
        )

    def validate_media(self, file_path: str) -> Optional[Dict]:
        """Validate a media file.
        
        Args:
            file_path: Path to media file to validate
            
        Returns:
            Optional[Dict]: Validation status
        """
        return self._make_request(
            "get",
            "experimental/validate/media",
            params={"file_path": file_path}
        )

    # Add new speaker-related methods
    def get_unnamed_speakers(
        self, 
        limit: int = DEFAULT_SEARCH_LIMIT,
        offset: int = 0,
        speaker_ids: Optional[List[int]] = None
    ) -> Optional[List[Dict]]:
        """Get unnamed speakers.
        
        Args:
            limit: Maximum number of results to return
            offset: Pagination offset
            speaker_ids: List of speaker IDs to include
            
        Returns:
            Optional[List[Dict]]: List of unnamed speakers
        """
        params = {
            "limit": limit,
            "offset": offset,
            "speaker_ids": ",".join(map(str, speaker_ids)) if speaker_ids else None
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._make_request("get", "speakers/unnamed", params=params)

    def update_speaker(
        self,
        speaker_id: int,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Update speaker information."""
        payload = {"id": speaker_id}
        if name:
            payload["name"] = name
        if metadata:
            payload["metadata"] = metadata
        return self._make_request("post", "speakers/update", json=payload)

    def stream_frames(
        self,
        start_time: str,
        end_time: str
    ) -> Optional[Dict]:
        """Stream frames between specified timestamps.
        
        Args:
            start_time: Start timestamp in ISO format
            end_time: End timestamp in ISO format
            
        Returns:
            Optional[Dict]: Streaming response (SSE)
        """
        return self._make_request(
            "get",
            "stream/frames",
            params={
                "start_time": start_time,
                "end_time": end_time
            }
        )


if __name__ == "__main__":
    with ScreenpipeClient() as client:
        health = client.health_check()
        if health and health.get("status") == "healthy":
            print("Screenpipe is active")
        else:
            print("Screenpipe is not active")
