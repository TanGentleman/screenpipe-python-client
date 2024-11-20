from baml_client import b
from baml_client.types import SearchParameters
from baml_py.errors import (
    BamlError,
    BamlValidationError
)


def baml_generate_search_params(
        query: str,
        current_iso_timestamp: str) -> SearchParameters | str:
    """
    Constructs search parameters from a user message and timestamp.
    Handles potential BAML errors and provides detailed error information.

    Args:
        user_message: The raw query message from the user
        current_iso_timestamp: Current timestamp in ISO format

    Returns:
        SearchParameters object or error string
    """
    try:
        response = b.ConstructSearch(query, current_iso_timestamp)
        return response
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        return e.raw_output
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise


def baml_generate_search_params_stream(
        query: str,
        current_iso_timestamp: str) -> SearchParameters | str:
    """
    Streams the construction of search parameters, showing intermediate results.
    Handles potential BAML errors and provides detailed error information.
    """
    try:
        stream = b.stream.ConstructSearch(
            query, current_iso_timestamp)
        for msg in stream:
            print(f"Partial result: {msg}")
        return stream.get_final_response()
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        return e.raw_output
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise
