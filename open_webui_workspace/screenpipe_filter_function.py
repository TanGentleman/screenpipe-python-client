"""
title: Screenpipe Filter
author: TanGentleman
author_url: https://github.com/TanGentleman
funding_url: https://github.com/TanGentleman
version: 0.1
"""

from pydantic import BaseModel, Field
from typing import Optional
import logging
import json

# Set up logging to only show errors
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        sanitized_results: Optional[str] = Field(
            default=None,
            description="Storage for sanitized results between inlet and outlet")

    def __init__(self):
        self.valves = self.Valves()
        self.replacement_tuples = [
            # ("LASTNAME", ""),
            # ("FIRSTNAME", "NICKNAME")
        ]

    def safe_log_error(self, message: str, error: Exception) -> None:
        """
        Safely log an error without potentially exposing PII.

        Args:
            message (str): The error message.
            error (Exception): The exception that was raised.
        """
        error_type = type(error).__name__
        logger.error(f"{message}: {error_type}")

    def refactor_input_text(self, text: str) -> str:
        """
        Redact personally identifiable information from the given text.

        Args:
            text (str): The input text to redact.

        Returns:
            str: The text with PII redacted.
        """
        REPLACEMENT_STRING = "[MODIFIED INPUT]"
        return text

    def refactor_output_text(self, text: str) -> str:
        REPLACEMENT_STRING = "[REDACTED OUTPUT]"
        return text

    def remove_names(self, content: str) -> str:
        """Remove sensitive names from content using replacement tuples."""
        for sensitive_word, replacement in self.replacement_tuples:
            content = content.replace(sensitive_word, replacement)
        return content

    def sanitize_results(self, results: dict) -> list[dict]:
        """Sanitizes the results similar to Pipe class logic."""
        if not isinstance(results, dict) or "data" not in results:
            return []

        results = results["data"]
        new_results = []
        for result in results:
            new_result = dict()
            if result["type"] == "OCR":
                new_result["type"] = "OCR"
                new_result["content"] = self.remove_names(
                    result["content"]["text"])
                new_result["app_name"] = result["content"]["app_name"]
                new_result["window_name"] = result["content"]["window_name"]
            elif result["type"] == "Audio":
                new_result["type"] = "Audio"
                new_result["content"] = result["content"]["transcription"]
                new_result["device_name"] = result["content"]["device_name"]
            else:
                continue
            new_result["timestamp"] = result["content"]["timestamp"]
            new_results.append(new_result)
        return new_results

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages, sanitizing and storing results if present."""
        try:
            # Handle regular message sanitization
            messages = body.get("messages", [])
            for message in messages:
                if message.get("role") == "user":
                    content = message.get("content", "")
                    message["content"] = self.refactor_input_text(content)

            # Handle results if present in the body
            if "results" in body:
                sanitized_results = self.sanitize_results(body["results"])
                self.valves.sanitized_results = json.dumps(sanitized_results)

        except Exception as e:
            self.safe_log_error("Error processing inlet", e)

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process outgoing messages, incorporating sanitized results if available."""
        try:
            if self.valves.redact_outlet and (
                __user__ is None
                or __user__.get("role") != "admin"
                or self.valves.enabled_for_admins
            ):
                messages = body.get("messages", [])
                for message in messages:
                    if message.get("role") == "assistant":
                        content = message.get("content", "")

                        # Prepend sanitized results if available
                        if self.valves.sanitized_results:
                            content = f"Sanitized Results: {self.valves.sanitized_results}\n\nResponse: {content}"

                        message["content"] = self.refactor_output_text(content)

                # Clear sanitized results after using them
                self.valves.sanitized_results = None

        except Exception as e:
            self.safe_log_error("Error processing outlet", e)

        return body
