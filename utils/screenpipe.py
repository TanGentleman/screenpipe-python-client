import logging
from typing import Dict, List, Literal, Optional
import requests

class ScreenPipeClient:
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
        self._session = requests.Session()
        self._pipe_download_timeout = 20  # seconds
        
        # Valid content types
        self._valid_content_types = {"ocr", "audio", "all"}
        self._valid_tag_types = {"audio", "vision"}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
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
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None

    def health_check(self) -> Optional[Dict]:
        """Check the health status of the ScreenPipe system."""
        return self._make_request("get", "health")

    def search(
        self,
        limit: int = 5,
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
        """Search captured data in ScreenPipe's database."""
        # Validate content type
        if content_type and content_type not in self._valid_content_types:
            raise ValueError(f"Invalid content_type. Must be one of: {self._valid_content_types}")

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
        
        self.logger.info(f"Searching for {limit} chunks. Type: {content_type or 'all'}")
        return self._make_request("get", "search", params=params)

    def list_audio_devices(self) -> Optional[List]:
        """List all available audio devices."""
        return self._make_request("get", "audio/list")

    def list_monitors(self) -> Optional[List]:
        """List all available monitors."""
        return self._make_request("post", "vision/list")

    def _validate_content_type_for_tags(self, content_type: str) -> str:
        """Validate and normalize content type for tag operations."""
        if content_type == "ocr":
            self.logger.warning("Content type 'ocr' is not used for tags API. Using 'vision' instead.")
            content_type = "vision"
        if content_type not in self._valid_tag_types:
            raise ValueError(f"Invalid content_type. Must be one of: {self._valid_tag_types}")
        return content_type

    def add_tags_to_content(self, content_type: str, id: int, tags: List[str]) -> Optional[Dict]:
        """Add tags to content items."""
        content_type = self._validate_content_type_for_tags(content_type)
        return self._make_request("post", f"tags/{content_type}/{id}", json={"tags": tags})

    def remove_tags_from_content(self, content_type: str, id: int, tags: List[str]) -> Optional[Dict]:
        """Remove tags from content items."""
        content_type = self._validate_content_type_for_tags(content_type)
        return self._make_request("delete", f"tags/{content_type}/{id}", json={"tags": tags})

    # Pipe-related methods
    def get_pipe_info(self, pipe_id: str) -> Optional[Dict]:
        """Get information about a specific pipe."""
        return self._make_request("get", f"pipes/info/{pipe_id}")

    def list_pipes(self) -> Optional[List]:
        """List all available pipes."""
        return self._make_request("get", "pipes/list")

    def download_pipe(self, url: str) -> Optional[Dict]:
        """Download a pipe from URL."""
        return self._make_request(
            "post", 
            "pipes/download",
            json={"url": url},
            timeout=self._pipe_download_timeout
        )

    def run_pipe(self, pipe_id: str) -> Optional[Dict]:
        """Enable and run a pipe."""
        return self._make_request("post", "pipes/enable", json={"pipe_id": pipe_id})

    def stop_pipe(self, pipe_id: str) -> Optional[Dict]:
        """Stop a running pipe."""
        return self._make_request("post", "pipes/disable", json={"pipe_id": pipe_id})

    def update_pipe_configuration(self, pipe_id: str, config: Dict) -> Optional[Dict]:
        """Update pipe configuration."""
        return self._make_request(
            "post",
            "pipes/update",
            json={"pipe_id": pipe_id, "config": config}
        )
