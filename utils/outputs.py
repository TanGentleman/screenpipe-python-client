from typing import List, Optional
from utils.time_utils import format_timestamp

FRAME_DATA_SUPPORTED = False
if FRAME_DATA_SUPPORTED:
    import base64


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
    def __init__(
            self,
            frame_id: int,
            text: str,
            timestamp: str,
            file_path: str,
            app_name: str,
            window_name: str,
            tags: List[str],
            offset_index: Optional[int] = None,
            frame: Optional[str] = None,
            clean_data: bool = True):
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
        self.text = text
        self.timestamp = timestamp
        self.app_name = app_name
        self.window_name = window_name
        self.tags = tags
        
        self.ignored_fields = {
            "frame_id": frame_id,
            "frame": frame,
            "offset_index": offset_index,
            "file_path": file_path
        }

        if clean_data:
            self._clean_data()

    def _clean_data(self):
        """
        Cleans the data (converts the timestamp to local time).
        """
        self.original_timestamp = self.timestamp
        self.timestamp = format_timestamp(self.original_timestamp)
        self.ignored_fields = {}

    def _get_frame_as_image(self) -> Optional[bytes]:
        """
        Get the frame as a byte array (image data).
        """
        if self.frame:
            try:
                return base64.b64decode(self.frame)
            except ImportError:
                print("Make sure to enable frame support in outputs.py!")
            except Exception as e:
                print(f"Error decoding frame: {e}")
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

    def __repr__(self):
        tags_str = f", tags={self.tags}" if self.tags else ""
        return (
            f"OCR(frame_id={self.frame_id}, "
            f"app='{self.app_name}' ({self.window_name}), "
            f"timestamp='{self.timestamp}', "
            f"text='{self.text[:50]}{'...' if len(self.text) > 50 else ''}'"
            f"{tags_str})"
        )

    def to_dict(self):
        return {
            "type": "OCR",
            "content": self.__dict__
        }

    def __str__(self):
        return self.__repr__()


class Audio:
    def __init__(
            self,
            chunk_id: int,
            transcription: str,
            timestamp: str,
            tags: List[str],
            device_name: str,
            device_type: str,
            file_path: Optional[str] = None,
            offset_index: Optional[int] = None):
        """
        Represents an audio output.

        Args:
            chunk_id (int): The ID of the audio chunk.
            transcription (str): The transcribed text.
            timestamp (str): The timestamp of the audio output in PST timezone.
            file_path (str): The file path of the audio output.
            offset_index (int): The offset index. Ignored.
            tags (List[str]): The list of tags associated with the audio output.
            device_name (str): The name of the device.
            device_type (str): The type of the device.
        """
        self.chunk_id = chunk_id
        self.transcription = transcription
        self.timestamp = timestamp
        self.tags = tags
        self.device_name = device_name
        self.device_type = device_type

        self.ignored_fields = {
            "file_path": file_path,
            "offset_index": offset_index
        }

        CLEAN_DATA = True
        if CLEAN_DATA:
            self._clean_data()

    def _clean_data(self):
        """
        Cleans the data (converts the timestamp to local time).
        """
        self.original_timestamp = self.timestamp
        self.timestamp = format_timestamp(self.original_timestamp)
        del self.ignored_fields

    def __repr__(self):
        tags_str = f", tags={self.tags}" if self.tags else ""
        return (
            f"Audio(chunk_id={self.chunk_id}, "
            f"device='{self.device_name}' ({self.device_type}), "
            f"timestamp='{self.timestamp}', "
            f"transcription='{self.transcription[:50]}{'...' if len(self.transcription) > 50 else ''}'"
            f"{tags_str}")

    def to_dict(self):
        return {
            "type": "Audio",
            "content": self.__dict__
            # NOTE: Should I show original_timestamp?
        }

    def __str__(self):
        return self.__repr__()


class SearchOutput:
    def __init__(self, response_object: dict,
                 data: Optional[List[dict]] = None,
                 pagination: Optional[dict] = None):
        """
        Represents the search output from the Screenpipe API.

        Args:
            response_object (dict): The raw API response object
            data (List[dict], optional): The list of data items containing OCR and Audio content
            pagination (dict, optional): The pagination information including limit, offset and total
        """
        self.data = data or response_object.get('data', [])
        self.chunks = []
        self.pagination = pagination or response_object.get('pagination')

        INITIALIZE_DATA_OBJECTS = True
        if INITIALIZE_DATA_OBJECTS:
            self.initialize_data_objects()
        else:
            self.validate_data_dicts()

    def validate_data_dicts(self):
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

    def initialize_data_objects(self):
        """
        Initializes OCR and Audio data objects from the raw data.

        Raises:
            ValueError: If an invalid data type is encountered
        """
        ocr_count = 0
        audio_count = 0

        for item in self.data:
            if item["type"] == "OCR":
                self.chunks.append(OCR(**item["content"]))
                ocr_count += 1
            elif item["type"] == "Audio":
                self.chunks.append(Audio(**item["content"]))
                audio_count += 1
            else:
                raise ValueError(f"Invalid data type: {item['type']}")

        print(
            f"Initialized {ocr_count + audio_count} data objects "
            f"({ocr_count} OCR, {audio_count} Audio)"
        )

    def __repr__(self):
        return f"SearchOutput(data={self.data}" if not self.chunks else f"SearchOutput(chunks={self.chunks})"

    def __str__(self):
        return self.__repr__()

    def to_dict(self):
        return {
            "data": [chunk.to_dict() for chunk in self.chunks],
            "pagination": self.pagination
        }
