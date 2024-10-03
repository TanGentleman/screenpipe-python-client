from typing import Any, List, Optional
from utils import convert_to_pst
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
                "frame": Optional[Any]
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
                "device_type": str
            }
        }
    ],
    "pagination": {
        "limit": int,
        "offset": int,
        "total": int
    }
}

class HealthCheck:
    def __init__(self, status: str, last_frame_timestamp: str, last_audio_timestamp: str, frame_status: str, audio_status: str, message: str, verbose_instructions: Optional[str] = None):
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
        self.last_frame_timestamp = convert_to_pst(last_frame_timestamp)
        self.last_audio_timestamp = convert_to_pst(last_audio_timestamp)
        self.frame_status = frame_status
        self.audio_status = audio_status
        self.message = message
        self.verbose_instructions = verbose_instructions
    
class OCR:
    def __init__(self, frame_id: int, text: str, timestamp: str, file_path: str, offset_index: int, app_name: str, window_name: str, tags: List[str], frame: Optional[Any] = None):
        """
        Represents an OCR (Optical Character Recognition) output.

        Args:
            frame_id (int): The ID of the frame.
            text (str): The extracted text.
            timestamp (str): The timestamp of the OCR output in PST timezone.
            file_path (str): The file path of the OCR output.
            offset_index (int): The offset index.
            app_name (str): The name of the application.
            window_name (str): The name of the window.
            tags (List[str]): The list of tags associated with the OCR output.
            frame (Any, optional): The frame associated with the OCR output. Defaults to None.
        """
        self.frame_id = frame_id
        self.text = text
        self.timestamp = convert_to_pst(timestamp)
        self.file_path = file_path
        self.offset_index = offset_index
        self.app_name = app_name
        self.window_name = window_name
        self.tags = tags
        if frame:
            print("Frame data not supported yet")
            self.frame = frame

class Audio:
    def __init__(self, chunk_id: int, transcription: str, timestamp: str, file_path: str, offset_index: int, tags: List[str], device_name: str, device_type: str):
        """
        Represents an audio output.

        Args:
            chunk_id (int): The ID of the audio chunk.
            transcription (str): The transcribed text.
            timestamp (str): The timestamp of the audio output in PST timezone.
            file_path (str): The file path of the audio output.
            offset_index (int): The offset index.
            tags (List[str]): The list of tags associated with the audio output.
            device_name (str): The name of the device.
            device_type (str): The type of the device.
        """
        self.chunk_id = chunk_id
        self.transcription = transcription
        self.timestamp = convert_to_pst(timestamp)
        self.file_path = file_path
        self.offset_index = offset_index
        self.tags = tags
        self.device_name = device_name
        self.device_type = device_type

class SearchOutput:
    def __init__(self, data: List[dict], pagination: dict):
        """
        Represents the search output.

        Args:
            data (List[dict]): The list of data items.
            pagination (dict): The pagination information.
        """
        self.data = data
        self.pagination = pagination
        self.validate_data()
    
    def validate_data(self):
        """
        Validates the data items and pagination information.
        Raises a ValueError if the data is invalid.
        """
        for item in self.data:
            if item["type"] == "OCR":
                item["content"] = OCR(**item["content"]).__dict__
            elif item["type"] == "Audio":
                item["content"] = Audio(**item["content"]).__dict__
            else:
                raise ValueError("Invalid data type")
        assert isinstance(self.pagination, dict)
        assert isinstance(self.pagination["limit"], int)
        assert isinstance(self.pagination["offset"], int)
        assert isinstance(self.pagination["total"], int)