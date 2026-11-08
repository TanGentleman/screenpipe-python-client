import pytest
import os
import sys

# These need a running screenpipe, the core server or an LLM key.
LIVE_TESTS = (
    "tests/unit/test_sdk.py",
    "tests/unit/test_valves.py",
    "tests/integration/test_pipeline.py",
    "tests/integration/test_async.py",
)

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")

# Add the src directory to Python path
sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def base_fixture():
    """
    Base fixture available to all tests.
    """
    # Setup code
    yield
    # Teardown code


def pytest_ignore_collect(collection_path, config):
    """Skip live tests unless SCREENPIPE_LIVE=1."""
    if os.environ.get("SCREENPIPE_LIVE") == "1":
        return None
    path = collection_path.as_posix()
    return True if path.endswith(LIVE_TESTS) else None
