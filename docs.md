### API Documentation for `server.rs`

#### Overview
This document provides a detailed overview of the API endpoints defined in the `server.rs` file. Each endpoint is described with its HTTP method, URL, request parameters, request body, and response format.

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
               "type": "ocr",
               "content": {
                 "frame_id": 1,
                 "text": "Sample text",
                 "timestamp": "2023-10-01T12:00:00Z",
                 "file_path": "/path/to/frame.png",
                 "offset_index": 0,
                 "app_name": "SampleApp",
                 "window_name": "SampleWindow",
                 "tags": ["tag1", "tag2"],
                 "frame": "base64_encoded_frame"
               }
             },
             {
               "type": "audio",
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
             },
             {
               "type": "fts",
               "content": {
                 "text_id": 1,
                 "matched_text": "Sample matched text",
                 "frame_id": 1,
                 "timestamp": "2023-10-01T12:00:00Z",
                 "app_name": "SampleApp",
                 "window_name": "SampleWindow",
                 "file_path": "/path/to/frame.png",
                 "original_frame_text": "Original text",
                 "tags": ["tag1", "tag2"]
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
   - **Method**: `POST`
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
           "pipe_id": "pipe-stream-ocr-text",
           "name": "Stream OCR Text",
           "description": "A pipe that streams OCR text",
           "config": {
             "key": "value"
           }
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
             "pipe_id": "pipe-stream-ocr-text",
             "name": "Stream OCR Text",
             "description": "A pipe that streams OCR text",
             "config": {
               "key": "value"
             }
           },
           {
             "pipe_id": "pipe-security-check",
             "name": "Security Check",
             "description": "A pipe that performs security checks",
             "config": {
               "key": "value"
             }
           }
         ]
         ```

8. **Download Pipe**
   - **Method**: `POST`
   - **URL**: `/pipes/download`
   - **Request Parameters**: None
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
           "message": "Pipe /path/to/pipe downloaded successfully",
           "pipe_id": "/path/to/pipe"
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
   - **Request Parameters**: None
   - **Request Body**:
     ```json
     {
       "pipe_id": "pipe-stream-ocr-text"
     }
     ```
   - **Response**:
     - **Success**:
       - **Status Code**: `200 OK`
       - **Body**:
         ```json
         {
           "message": "Pipe pipe-stream-ocr-text started",
           "pipe_id": "pipe-stream-ocr-text"
         }
         ```
     - **Error**:
       - **Status Code**: `400 Bad Request`
       - **Body**:
         ```json
         {
           "error": "<error_message>"
         }
         ```

10. **Stop Pipe**
    - **Method**: `POST`
    - **URL**: `/pipes/disable`
    - **Request Parameters**: None
    - **Request Body**:
      ```json
      {
        "pipe_id": "pipe-stream-ocr-text"
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "message": "Pipe pipe-stream-ocr-text stopped",
            "pipe_id": "pipe-stream-ocr-text"
          }
          ```
      - **Error**:
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "<error_message>"
          }
          ```

11. **Update Pipe Configuration**
    - **Method**: `POST`
    - **URL**: `/pipes/update`
    - **Request Parameters**: None
    - **Request Body**:
      ```json
      {
        "pipe_id": "pipe-stream-ocr-text",
        "config": {
          "key": "value",
          "another_key": "another_value"
        }
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "message": "Pipe pipe-stream-ocr-text config updated",
            "pipe_id": "pipe-stream-ocr-text"
          }
          ```
      - **Error**:
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "<error_message>"
          }
          ```

12. **Merge Videos**
    - **Method**: `POST`
    - **URL**: `/experimental/frames/merge`
    - **Request Parameters**: None
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
            "frame_status": "ok",
            "audio_status": "ok",
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
            "last_frame_timestamp": null,
            "last_audio_timestamp": null,
            "frame_status": "stale",
            "audio_status": "stale",
            "message": "some systems are not functioning properly: vision, audio. frame status: stale, audio status: stale",
            "verbose_instructions": "if you're experiencing issues, please try the following steps:\n1. restart the application.\n2. if using a desktop app, reset your screenpipe os audio/screen recording permissions.\n3. if the problem persists, please contact support with the details of this health check at louis@screenpi.pe.\n4. last, here are some faq to help you troubleshoot: https://github.com/mediar-ai/screenpipe/blob/main/content/docs/notes.md"
          }
          ```

14. **Execute Raw SQL Query**
    - **Method**: `POST`
    - **URL**: `/raw_sql`
    - **Request Parameters**: None
    - **Request Body**:
      ```json
      {
        "query": "SELECT * FROM table_name"
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "result": [
              {
                "column1": "value1",
                "column2": "value2"
              },
              {
                "column1": "value3",
                "column2": "value4"
              }
            ]
          }
          ```
      - **Error**:
        - **Status Code**: `500 Internal Server Error`
        - **Body**:
          ```json
          {
            "error": "Failed to execute raw SQL query: <error_message>"
          }
          ```

15. **LLM Chat (if LLM feature is enabled)**
    - **Method**: `POST`
    - **URL**: `/llm/chat`
    - **Request Parameters**: None
    - **Request Body**:
      ```json
      {
        "message": "Hello, how are you?",
        "stream": false
      }
      ```
    - **Response**:
      - **Success**:
        - **Status Code**: `200 OK`
        - **Body**:
          ```json
          {
            "response": "Hello! I'm doing well, thank you. How can I assist you today?"
          }
          ```
      - **Error**:
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "Stream not supported"
          }
          ```
        - **Status Code**: `400 Bad Request`
        - **Body**:
          ```json
          {
            "error": "LLM is not enabled"
          }
          ```
        - **Status Code**: `500 Internal Server Error`
        - **Body**:
          ```json
          {
            "error": "Failed to chat: <error_message>"
          }
          ```