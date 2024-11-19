"""
ScreenPipe Chat Client
Provides an interactive chat interface for the ScreenPipe API
"""

import itertools
import json
import sys
import threading
import time
import requests
from typing import Optional, Dict, Any, Union

# Configuration
API_BASE_URL = "http://localhost:3333"


class Spinner:
    """Displays an animated spinner while processing."""

    def __init__(self, message="Processing..."):
        self.spinner = itertools.cycle(["-", "/", "|", "\\"])
        self.busy = False
        self.delay = 0.05
        self.message = message
        self.thread = None

    def write(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _spin(self):
        while self.busy:
            self.write(f"\r{self.message} {next(self.spinner)}")
            time.sleep(self.delay)
        self.write("\r\033[K")  # Clear the line

    def __enter__(self):
        self.busy = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.busy = False
        time.sleep(self.delay)
        if self.thread:
            self.thread.join()
        self.write("\r")  # Move cursor to beginning of line


def process_api_stream_response(response: requests.Response) -> str:
    """Process streaming response from HTTP request."""
    full_response = ""
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        if not line.startswith('data: '):
            continue

        data = line[6:]  # Remove 'data: ' prefix
        if data == '[DONE]':
            continue

        chunk_data = json.loads(data)
        chunk_content = ""

        if isinstance(chunk_data, str):
            chunk_content = chunk_data
        elif isinstance(chunk_data, dict) and 'choices' in chunk_data:
            chunk_content = chunk_data['choices'][0]['delta'].get(
                'content', '')

        if chunk_content:
            print(chunk_content, end="", flush=True)
            full_response += chunk_content

    print()
    return full_response


def chat_with_api(messages: list) -> Union[Dict[str, Any], str]:
    """
    Send chat messages to the API and handle the response.
    Returns either the outlet response dict or an error string.
    """
    stream = True
    try:
        # Process inlet
        with Spinner("Processing your request..."):
            inlet_response = requests.post(
                f"{API_BASE_URL}/filter/inlet",
                json={"messages": messages, "stream": stream}
            )
            inlet_data = inlet_response.json()

        # Process pipe
        if inlet_data["stream"]:
            print("\nAssistant: ", end="", flush=True)
            pipe_response = requests.post(
                f"{API_BASE_URL}/pipe/stream",
                json=inlet_data,
                stream=True
            )
            response_content = process_api_stream_response(pipe_response)
        else:
            with Spinner("Processing your request..."):
                pipe_response = requests.post(
                    f"{API_BASE_URL}/pipe/completion",
                    json=inlet_data
                )
                response_data = pipe_response.json()
                response_content = response_data["response_string"]

        # Process outlet
        inlet_data["messages"].append(
            {"role": "assistant", "content": response_content})
        outlet_response = requests.post(
            f"{API_BASE_URL}/filter/outlet",
            json=inlet_data
        )
        return outlet_response.json()

    except requests.exceptions.RequestException as e:
        return f"Error communicating with API: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def update_valves() -> dict:
    """Call the update valves endpoint and return status message."""
    try:
        response = requests.post(f"{API_BASE_URL}/valves/update")
        if response.status_code == 200:
            return response.json()
        return {
            "Error": f"Error refreshing valves. Status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"Error": f"Error communicating with API: {str(e)}"}
    except Exception as e:
        return {"Error": f"Unexpected error: {str(e)}"}


def chat_loop():
    """
    Main chat loop that processes user input and displays responses.
    """
    messages = []

    print(
        "Assistant: Welcome! I can help you analyze your screen recordings and audio data.\n"
        "You can ask about your recent activities, OCR text, or audio transcriptions.")
    print("(Type 'quit' to exit, 'refresh' to update valves)")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break

        if user_input.lower() == "refresh":
            status = update_valves()
            print(f"\nAssistant: {status}")
            continue

        messages.append({"role": "user", "content": user_input})

        response = chat_with_api(messages)

        if isinstance(response, str):
            print(f"\nError: {response}")
            continue

        if isinstance(response, dict) and "messages" in response:
            assistant_message = response["messages"][-1]["content"]
            messages.append(
                {"role": "assistant", "content": assistant_message})
            if not response.get("stream"):  # Check stream flag from response
                print("\nAssistant:", assistant_message)
        else:
            print("\nError: Unexpected response format from API")


if __name__ == "__main__":
    try:
        chat_loop()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
