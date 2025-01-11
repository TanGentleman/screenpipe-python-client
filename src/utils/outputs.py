from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..utils.time_utils import format_timestamp

# From server
expected_output = {
    "data": [
        {
            "type": "OCR",
            "content": {
                "frame_id": int,
                "text": str,
                "timestamp": str,
                "file_path": str,
                "offset_index": int,
                "app_name": str,
                "window_name": str,
                "tags": list,
                "frame": Optional[str]
            }
        },
        {
            "type": "Audio", 
            "content": {
                "chunk_id": int,
                "transcription": str,
                "timestamp": str,
                "file_path": str,
                "offset_index": int,
                "tags": list,
                "device_name": str,
                "device_type": str,
                "speaker": {
                    "id": int,
                    "name": str,
                    "metadata": str
                },
                "start_time": float,
                "end_time": float
            }
        }
    ],
    "pagination": {
        "limit": int,
        "offset": int,
        "total": int
    }
}

class Chunk(BaseModel):
    pass

class OCR(Chunk):
    """Document model for OCR data in MongoDB"""
    frame_id: int
    text: str
    timestamp: datetime
    app_name: str
    window_name: str
    tags: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None

class Audio(Chunk):
    """Document model for Audio data in MongoDB"""
    chunk_id: int
    transcription: str
    timestamp: datetime
    device_name: str
    device_type: str
    tags: List[str] = Field(default_factory=list)
    start_time: float
    end_time: float
    speaker: dict = Field(default_factory=dict)
    file_path: Optional[str] = None


class HealthCheck:
    def __init__(
            self,
            status: str,
            last_frame_timestamp: str,
            last_audio_timestamp: str,
            frame_status: str,
            audio_status: str,
            message: str,
            verbose_instructions: Optional[str] = None):
        """
        Represents the health check status.

        Args:
            status (str): The overall status of the health check.
            last_frame_timestamp (str): The timestamp of the last processed frame in PST timezone.
            last_audio_timestamp (str): The timestamp of the last processed audio chunk in PST timezone.
            frame_status (str): The status of the frame processing.
            audio_status (str): The status of the audio processing.
            message (str): A message describing the health check status.
            verbose_instructions (str, optional): Optional verbose instructions. Defaults to None.
        """
        self.status = status
        self.last_frame_timestamp = format_timestamp(last_frame_timestamp)
        self.last_audio_timestamp = format_timestamp(last_audio_timestamp)
        self.frame_status = frame_status
        self.audio_status = audio_status
        self.message = message
        if verbose_instructions:
            self.verbose_instructions = verbose_instructions

    def to_dict(self):
        return self.__dict__


class OCR:
    """Handles OCR data conversion to MongoDB document format"""
    def __init__(
            self,
            frame_id: int,
            text: str,
            timestamp: str,
            file_path: Optional[str],
            app_name: str,
            window_name: str,
            tags: List[str],
            frame: Optional[str] = None,
            **kwargs):
        self.frame_id = frame_id
        self.text = text
        self.timestamp = timestamp
        self.app_name = app_name
        self.window_name = window_name
        self.tags = tags
        self.frame = frame
        self.file_path = file_path

    def to_document(self) -> OCR:
        """Convert to MongoDB document"""
        return OCR(
            frame_id=self.frame_id,
            text=self.text,
            timestamp=datetime.fromisoformat(self.timestamp),
            app_name=self.app_name,
            window_name=self.window_name,
            tags=self.tags,
            file_path=self.file_path
        )

class Audio:
    """Handles Audio data conversion to MongoDB document format"""
    def __init__(
            self,
            chunk_id: int,
            transcription: str,
            timestamp: str,
            tags: List[str],
            device_name: str,
            device_type: str,
            start_time: str,
            end_time: str,
            file_path: Optional[str] = None,
            speaker: Optional[dict] = None,
            **kwargs):
        self.chunk_id = chunk_id
        self.transcription = transcription
        self.timestamp = timestamp
        self.tags = tags
        self.device_name = device_name
        self.device_type = device_type
        self.start_time = start_time
        self.end_time = end_time
        self.file_path = file_path
        self.speaker = speaker or {}

    def to_document(self) -> Audio:
        """Convert to MongoDB document"""
        return Audio(
            chunk_id=self.chunk_id,
            transcription=self.transcription,
            timestamp=datetime.fromisoformat(self.timestamp),
            device_name=self.device_name,
            device_type=self.device_type,
            tags=self.tags,
            start_time=float(self.start_time),
            end_time=float(self.end_time),
            speaker=self.speaker,
            file_path=self.file_path
        )

class SearchOutput:
    """Handles search results and conversion to MongoDB documents"""
    def __init__(self, response_object: dict, create_documents: bool = False):
        self.data = response_object.get('data', [])
        self.pagination = response_object.get('pagination')
        if create_documents:
            self.documents = self._initialize_chunks()

    def _initialize_chunks(self) -> List[OCR | Audio]:
        """Initialize OCR and Audio objects from raw data"""
        chunks = []
        for item in self.data:
            if item["type"] == "OCR":
                chunks.append(OCR(**item["content"]))
            elif item["type"] == "Audio":
                chunks.append(Audio(**item["content"]))
            else:
                raise ValueError(f"Invalid data type: {item['type']}")
        return chunks

    def get_documents(self) -> List[Chunk]:
        """Get MongoDB-ready documents"""
        if not self.documents:
            self.documents = self._initialize_chunks()

        return [chunk.to_document() for chunk in self.documents]
    
    def to_dict(self):
        return {
            "data": self.data,
            "pagination": self.pagination
        }
