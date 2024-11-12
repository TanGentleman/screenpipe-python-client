from baml_client import b
from baml_client.types import SearchParameters
from baml_py.errors import (
    BamlError,
    BamlValidationError
)


def construct_search_params(
        raw_query: str,
        current_iso_timestamp: str) -> SearchParameters | str:
    """
    Constructs search parameters from a raw query string.
    Handles potential BAML errors and provides detailed error information.
    """
    try:
        response = b.ConstructSearchParameters(
            raw_query, current_iso_timestamp)
        return response
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        return e.raw_output
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise


def construct_search_params_stream(
        raw_query: str,
        current_iso_timestamp: str) -> SearchParameters:
    """
    Streams the construction of search parameters, showing intermediate results.
    Handles potential BAML errors and provides detailed error information.
    """
    try:
        stream = b.stream.ConstructSearchParameters(
            raw_query, current_iso_timestamp)
        for msg in stream:
            print(f"Partial result: {msg}")
        return stream.get_final_response()
    except BamlValidationError as e:
        print(
            f"Validation Error:\nPrompt: {e.prompt}\nOutput: {e.raw_output}\nMessage: {e.message}")
        raise
    except BamlError as e:
        print(f"BAML Error: {e}")
        raise
