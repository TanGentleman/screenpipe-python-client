import pytest
import os
import sys

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
