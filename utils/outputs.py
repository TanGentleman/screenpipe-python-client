from typing import List, Optional
from utils.sp_utils import convert_to_local_time
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
        self.last_frame_timestamp = convert_to_local_time(last_frame_timestamp)
        self.last_audio_timestamp = convert_to_local_time(last_audio_timestamp)
        self.frame_status = frame_status
        self.audio_status = audio_status
        self.message = message
        self.verbose_instructions = verbose_instructions


class OCR:
    def __init__(
            self,
            frame_id: int,
            text: str,
            timestamp: str,
            file_path: str,
            offset_index: int,
            app_name: str,
            window_name: str,
            tags: List[str],
            frame: Optional[str] = None):
        """
        Represents an OCR (Optical Character Recognition) output.

        Args:
            frame_id (int): The ID of the frame.
            text (str): The extracted text.
            timestamp (str): The timestamp of the OCR output in UTC timezone.
            file_path (str): The file path of the OCR output.
            offset_index (int): The offset index.
            app_name (str): The name of the application.
            window_name (str): The name of the window.
            tags (List[str]): The list of tags associated with the OCR output.
            frame (Optional[str], optional): The frame associated with the OCR output. Defaults to None.
        """
        self.frame_id = frame_id
        self.text = text
        self.timestamp = timestamp
        self.file_path = file_path
        self.offset_index = offset_index
        self.app_name = app_name
        self.window_name = window_name
        self.tags = tags
        self.frame = frame

        self._clean_data()

    def _clean_data(self):
        """
        Cleans the data (converts the timestamp to local time).
        """
        self.timestamp = convert_to_local_time(self.timestamp)

    def _get_frame_as_image(self) -> Optional[bytes]:
        """
        Get the frame as a byte array (image data).
        """
        import base64
        if self.frame:
            return base64.b64decode(self.frame)
        return None

    def save_frame(self, output_path: str):
        """
        Save the frame image to a file.

        Args:
            output_path (str): The output file path.
        """
        frame_data = self._get_frame_as_image()
        if not frame_data:
            print("No frame data found.")
            return
        with open(output_path, "wb") as file:
            file.write(frame_data)
        print(f"Frame saved as: {output_path}")
    
    def _convert_to_string(self, truncate: int = 50, trim_fields: bool = True) -> str:
        """
        Convert the OCR output to a string representation.

        Args:
            truncate (int, optional): The number of characters to truncate the text to. Defaults to 50.
            clean (bool, optional): If True, the output will be cleaned (without file path and tags). Defaults to True.

        Returns:
            str: _description_
        """
        # NOTE: Should I remove the file path?
        # I'm removing tags for now too.
        if trim_fields:
            return f"OCR(frame_id={self.frame_id}, text={self.text[:truncate]}..., timestamp={self.timestamp}, app_name={self.app_name}, window_name={self.window_name})"
        else:
            return f"OCR(frame_id={self.frame_id}, text={self.text[:truncate]}..., timestamp={self.timestamp}, file_path={self.file_path}, app_name={self.app_name}, window_name={self.window_name}, tags={self.tags})"

    def __str__(self):
        return self._convert_to_string()

    def __repr__(self):
        return self._convert_to_string(truncate=10)

class Audio:
    def __init__(
            self,
            chunk_id: int,
            transcription: str,
            timestamp: str,
            file_path: str,
            offset_index: int,
            tags: List[str],
            device_name: str,
            device_type: str):
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
        self.timestamp = timestamp
        self.file_path = file_path
        self.offset_index = offset_index
        self.tags = tags
        self.device_name = device_name
        self.device_type = device_type

        self._clean_data()

    def _clean_data(self):
        """
        Cleans the data (converts the timestamp to local time).
        """
        self.timestamp = convert_to_local_time(self.timestamp)
    
    def __str__(self):
        return f"Audio(chunk_id={self.chunk_id}, transcription={self.transcription}, timestamp={self.timestamp}, file_path={self.file_path}, offset_index={self.offset_index}, tags={self.tags}, device_name={self.device_name}, device_type={self.device_type})"


class SearchOutput:
    def __init__(self, data: List[dict], pagination: dict | None = None):
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
        if self.pagination is not None:
            assert isinstance(self.pagination, dict)
            assert isinstance(self.pagination["limit"], int)
            assert isinstance(self.pagination["offset"], int)
            assert isinstance(self.pagination["total"], int)
