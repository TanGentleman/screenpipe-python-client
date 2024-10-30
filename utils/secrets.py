LLM_API_KEY = "SECRET-KEY"
REPLACEMENT_TUPLES = [
    # ("LASTNAME", ""),
    # ("FIRSTNAME", "NICKNAME"),
]

def ensure_tuple_list_valid(replacement_tuples: list[tuple[str, str]]) -> bool:
    """Ensures that the replacement_tuples list is valid."""
    assert isinstance(replacement_tuples, list), "replacement_tuples must be a list"
    for item in replacement_tuples:
        assert isinstance(item, tuple) and len(item) == 2, "Each item in replacement_tuples must be a tuple of length 2"
        assert isinstance(item[0], str) and isinstance(item[1], str), "Each element in the tuples must be a string"

ensure_tuple_list_valid(REPLACEMENT_TUPLES)
