### API Documentation for `server.rs`
#### Overview
This document provides a detailed overview of the API endpoints defined in the `server.rs` file. Each endpoint is described with its HTTP method, URL, request parameters, request body, and response format.
#### Server Configuration
The server can be configured with the following options through the `Server` struct:
- `db`: Database manager for handling data operations
- `addr`: Socket address for the server to listen on
- `vision_control`: Control flag for vision processing
- `audio_devices_control`: Queue for audio device control commands
- `screenpipe_dir`: Base directory for screenpipe operations
- `pipe_manager`: Manager for handling pipes
- `vision_disabled`: Flag to disable vision processing
- `audio_disabled`: Flag to disable audio processing
- `ui_monitoring_enabled`: Flag to enable UI monitoring

#### Endpoints
1. **Search Content**
   - **Method**: `GET`
   - **URL**: `/search`
   - **Request Parameters**:
     - `q` (optional): Search query string.
     - `limit` (optional, default: 20): Number of results to return.
     - `offset` (optional, default: 0): Offset for pagination.
     - `content_type` (optional, default: `all`): Type of content to search (`ocr`, `audio`, `fts`, `all`).
     - `start_time` (optional): Start time for the search range.
     - `end_time` (optional): End time for the search range.
     - `app_name` (optional): Name of the application to filter by.
     - `window_name` (optional): Name of the window to filter by.
     - `include_frames` (optional, default: `false`): Include frames in the response.
     - `min_length` (optional): Minimum length of the content.
     - `max_length` (optional): Maximum length of the content.
   - **Request Body**: None
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "data": [
             {
               "type": "OCR",
               "content": {
                 "frame_id": 1,
                 "text": "Sample text",
                 "timestamp": "2023-10-01T12:00:00Z",
                 "file_path": "/path/to/frame.png",
                 "offset_index": 0,
                 "app_name": "SampleApp",
                 "window_name": "SampleWindow",
                 "tags": ["tag1", "tag2"],
                 "frame": "base64_encoded_frame_optional"
               }
             },
             {
               "type": "Audio",
               "content": {
                 "chunk_id": 1,
                 "transcription": "Sample transcription",
                 "timestamp": "2023-10-01T12:00:00Z",
                 "file_path": "/path/to/audio.mp3",
                 "offset_index": 0,
                 "tags": ["tag1", "tag2"],
                 "device_name": "Microphone",
                 "device_type": "input"
               }
             }
           ],
           "pagination": {
             "limit": 20,
             "offset": 0,
             "total": 100
           }
         }
         ```
     - **Error**:
       - **Status Code**: `500 Internal Server Error`
       - **Body**:
         ```json
         {
           "error": "Failed to perform search operations: <error_message>"
         }
         ```
2. **List Audio Devices**
   - **Method**: `GET`
   - **URL**: `/audio/list`
   - **Request Parameters**: None
   - **Request Body**: None
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         [
           {
             "name": "Microphone",
             "is_default": true
           },
           {
             "name": "Speakers",
             "is_default": false
           }
         ]
         ```
     - **Error**:
       - **Status Code**: `404 Not Found`
       - **Body**:
         ```json
         {
           "error": "No audio devices found"
         }
         ```
3. **List Monitors**
   - **Method**: `GET`
   - **URL**: `/vision/list`
   - **Request Parameters**: None
   - **Request Body**: None
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         [
           {
             "id": 1,
             "name": "Primary Monitor",
             "width": 1920,
             "height": 1080,
             "is_default": true
           },
           {
             "id": 2,
             "name": "Secondary Monitor",
             "width": 1280,
             "height": 720,
             "is_default": false
           }
         ]
         ```
     - **Error**:
       - **Status Code**: `404 Not Found`
       - **Body**:
         ```json
         {
           "error": "No monitors found"
         }
         ```
4. **Add Tags**
   - **Method**: `POST`
   - **URL**: `/tags/:content_type/:id`
   - **Request Parameters**:
     - `content_type`: Type of content (`vision`, `audio`).
     - `id`: ID of the content item.
   - **Request Body**:
     ```json
     {
       "tags": ["tag1", "tag2"]
     }
     ```
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "success": true
         }
         ```
     - **Error**:
       - **Status Code**: `400 Bad Request`
       - **Body**:
         ```json
         {
           "error": "Invalid content type"
         }
         ```
       - **Status Code**: `500 Internal Server Error`
       - **Body**:
         ```json
         {
           "error": "Failed to add tags: <error_message>"
         }
         ```
5. **Remove Tags**
   - **Method**: `DELETE`
   - **URL**: `/tags/:content_type/:id`
   - **Request Parameters**:
     - `content_type`: Type of content (`vision`, `audio`).
     - `id`: ID of the content item.
   - **Request Body**:
     ```json
     {
       "tags": ["tag1", "tag2"]
     }
     ```
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "success": true
         }
         ```
     - **Error**:
       - **Status Code**: `400 Bad Request`
       - **Body**:
         ```json
         {
           "error": "Invalid content type"
         }
         ```
       - **Status Code**: `500 Internal Server Error`
       - **Body**:
         ```json
         {
           "error": "Failed to remove tags: <error_message>"
         }
         ```

6. **Get Pipe Info**
   - **Method**: `GET`
   - **URL**: `/pipes/info/:pipe_id`
   - **Request Parameters**:
     - `pipe_id`: ID of the pipe.
   - **Request Body**: None
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "id": "pipe-id",
           "name": "Pipe Name",
           "description": "Pipe Description",
           "enabled": true,
           "config": {
             "key": "value"
           },
           "status": "running"
         }
         ```
     - **Error**:
       - **Status Code**: `404 Not Found`
       - **Body**:
         ```json
         {
           "error": "Pipe not found"
         }
         ```

7. **List Pipes**
   - **Method**: `GET`
   - **URL**: `/pipes/list`
   - **Request Parameters**: None
   - **Request Body**: None
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         [
           {
             "id": "pipe-id1",
             "name": "Pipe Name 1",
             "description": "Pipe Description 1",
             "enabled": true,
             "config": {
               "key": "value"
             },
             "status": "running"
           },
           {
             "id": "pipe-id2",
             "name": "Pipe Name 2",
             "description": "Pipe Description 2",
             "enabled": false,
             "config": {
               "key": "value"
             },
             "status": "stopped"
           }
         ]
         ```

8. **Download Pipe**
   - **Method**: `POST`
   - **URL**: `/pipes/download`
   - **Request Body**:
     ```json
     {
       "url": "https://github.com/mediar-ai/screenpipe/tree/main/examples/typescript/pipe-stream-ocr-text"
     }
     ```
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "message": "Pipe pipe-stream-ocr-text downloaded successfully",
           "pipe_id": "pipe-stream-ocr-text"
         }
         ```
     - **Error**:
       - **Status Code**: `500 Internal Server Error`
       - **Body**:
         ```json
         {
           "error": "Failed to download pipe: <error_message>"
         }
         ```

9. **Run Pipe**
   - **Method**: `POST`
   - **URL**: `/pipes/enable`
   - **Request Body**:
     ```json
     {
       "pipe_id": "pipe-id"
     }
     ```
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "message": "Pipe pipe-id started",
           "pipe_id": "pipe-id"
         }
         ```
     - **Error**:
       - **Status Code**: `400 Bad Request`
       - **Body**:
         ```json
         {
           "error": "Failed to start pipe: <error_message>"
         }
         ```

10. **Stop Pipe**
    - **Method**: `POST`
    - **URL**: `/pipes/disable`
    - **Request Body**:
      ```json
      {
        "pipe_id": "pipe-id"
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "message": "Pipe pipe-id stopped",
            "pipe_id": "pipe-id"
          }
          ```
      - **Error**:
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "Failed to stop pipe: <error_message>"
          }
          ```

11. **Update Pipe Configuration**
    - **Method**: `POST`
    - **URL**: `/pipes/update`
    - **Request Body**:
      ```json
      {
        "pipe_id": "pipe-id",
        "config": {
          "key": "value"
        }
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "message": "Pipe pipe-id config updated",
            "pipe_id": "pipe-id"
          }
          ```
      - **Error**:
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "Failed to update pipe config: <error_message>"
          }
          ```

12. **Merge Videos**
    - **Method**: `POST`
    - **URL**: `/experimental/frames/merge`
    - **Request Body**:
      ```json
      {
        "video_paths": ["/path/to/video1.mp4", "/path/to/video2.mp4"]
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "video_path": "/path/to/merged_video.mp4"
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**:
          ```json
          {
            "error": "Failed to merge frames: <error_message>"
          }
          ```

13. **Health Check**
    - **Method**: `GET`
    - **URL**: `/health`
    - **Request Parameters**: None
    - **Request Body**: None
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "status": "healthy",
            "last_frame_timestamp": "2023-10-01T12:00:00Z",
            "last_audio_timestamp": "2023-10-01T12:00:00Z",
            "last_ui_timestamp": "2023-10-01T12:00:00Z",
            "frame_status": "ok",
            "audio_status": "ok",
            "ui_status": "ok",
            "message": "all systems are functioning normally.",
            "verbose_instructions": null
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**:
          ```json
          {
            "status": "unhealthy",
            "last_frame_timestamp": "2023-10-01T12:00:00Z",
            "last_audio_timestamp": "2023-10-01T12:00:00Z",
            "last_ui_timestamp": "2023-10-01T12:00:00Z",
            "frame_status": "stale",
            "audio_status": "stale",
            "ui_status": "stale",
            "message": "some systems are not functioning properly: vision, audio, ui monitoring. frame status: stale, audio status: stale, ui status: stale",
            "verbose_instructions": "if you're experiencing issues, please try the following steps:\n1. restart the application.\n2. if using a desktop app, reset your screenpipe os audio/screen recording permissions.\n3. if the problem persists, please contact support with the details of this health check at louis@screenpi.pe.\n4. last, here are some faq to help you troubleshoot: https://github.com/mediar-ai/screenpipe/blob/main/content/docs/notes.md"
          }
          ```
14. **Execute Raw SQL Query**
    - **Method**: `POST`
    - **URL**: `/raw_sql`
    - **Request Body**:
      ```json
      {
        "query": "SELECT * FROM table_name"
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**: JSON with query result
          ```json
          [
            {
              "column1": "value1",
              "column2": "value2"
            },
            {
              "column1": "value3",
              "column2": "value4"
            }
          ]
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**: JSON indicating failure reason
          ```json
          {
            "error": "Failed to execute raw SQL query: <error_message>"
          }
          ```

15. **Add Content to Database**
    - **Method**: `POST`
    - **URL**: `/add`
    - **Request Body**:
      ```json
      {
        "device_name": "device1",
        "content": {
          "content_type": "frames",
          "data": {
            "frames": [
              {
                "file_path": "/path/to/frame1.png",
                "timestamp": "2023-10-01T12:00:00Z",
                "app_name": "SampleApp",
                "window_name": "SampleWindow",
                "ocr_results": [
                  {
                    "text": "Sample text",
                    "text_json": "{\"key\": \"value\"}",
                    "ocr_engine": "Tesseract",
                    "focused": true
                  }
                ],
                "tags": ["tag1", "tag2"]
              }
            ]
          }
        }
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "success": true,
            "message": "Frames added successfully"
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**:
          ```json
          {
            "error": "Failed to add frames: <error_message>"
          }
          ```

16. **Stream Frames**
    - **Method**: `GET`
    - **URL**: `/stream/frames`
    - **Request Parameters**:
      - `start_time`: Start time for the stream range.
      - `end_time`: End time for the stream range.
    - **Request Body**: None
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**: SSE stream of JSON objects with frame data.
          ```json
          {
            "timestamp": "2023-10-01T12:00:00Z",
            "devices": [
              {
                "device_id": "device1",
                "frame": "base64_encoded_frame",
                "metadata": {
                  "file_path": "/path/to/frame1.png",
                  "app_name": "SampleApp",
                  "window_name": "SampleWindow",
                  "ocr_text": "Sample text"
                },
                "audio": [
                  {
                    "device_name": "Microphone",
                    "is_input": true,
                    "transcription": "Sample transcription",
                    "audio_file_path": "/path/to/audio.mp3",
                    "duration_secs": 10.5,
                    "start_offset": 0.0
                  }
                ]
              }
            ]
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**: JSON indicating failure reason
          ```json
          {
            "error": "frame cache not initialized"
          }
          ```

17. **Input Control (Experimental)**
    - **Method**: `POST`
    - **URL**: `/experimental/input_control`
    - **Request Body**:
      ```json
      {
        "action": {
          "type": "KeyPress",
          "data": "enter"
        }
      }
      ```
      Or for mouse actions (example):
      ```json
      {
        "action": {
          "type": "MouseMove",
          "data": {"x": 100, "y": 200}
        }
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**: JSON indicating success
          ```json
          {
            "success": true
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error` or `400 Bad Request`
        - **Body**: JSON indicating failure reason
          ```json
          {
            "error": "Unsupported key: <key>"
          }
          ```
