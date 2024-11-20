import pytest

@pytest.fixture(scope="session")
def base_fixture():
    """
    Base fixture available to all tests.
    """
    # Setup code
    yield
    # Teardown code 