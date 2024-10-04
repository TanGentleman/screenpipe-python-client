import unittest
import logging
from screenpipe_client import (
    search,
    list_audio_devices,
    add_tags_to_content,
    download_pipe,
    run_pipe,
    stop_pipe,
    health_check
)
# Third party -- Downloading can be DANGEROUS!
STREAM_TEXT_URL = "https://github.com/mediar-ai/screenpipe/tree/main/examples/typescript/pipe-stream-ocr-text"

# NOTE: Constants need work, though it should return results for any populated DB
# CONSTANTS
VALID_QUERY = " "
VALID_START_TIME = "2024-01-01T00:00:00Z"
VALID_END_TIME = "2025-01-01T23:59:59Z"
VALID_APP_NAME = None
VALID_WINDOW_NAME = None

INCLUDE_FRAMES = False
CURRENT_LIMIT = 1

# TEST RUN:
OCR_CONTENT_TYPE = "ocr"
AUDIO_CONTENT_TYPE = "audio"
ALL_CONTENT_TYPE = "all"
DEFAULT_CONTENT_TYPE = AUDIO_CONTENT_TYPE
VISION_ID = 31814  # IF this ID doesn't match an OCR frame_id, it will not tag the frame!

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestScreenPipeClient(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://localhost:3030"
        logger.info('Setting up test case')

    def test_search(self):
        query = VALID_QUERY
        content_type = DEFAULT_CONTENT_TYPE
        limit = CURRENT_LIMIT
        offset = 0
        start_time = VALID_START_TIME
        end_time = VALID_END_TIME
        app_name = VALID_APP_NAME
        window_name = VALID_WINDOW_NAME
        include_frames = INCLUDE_FRAMES

        logger.info('Testing search functionality')
        try:
            response = search(
                query=query,
                content_type=content_type,
                limit=limit,
                offset=offset,
                start_time=start_time,
                end_time=end_time,
                app_name=app_name,
                window_name=window_name,
                include_frames=include_frames
            )
            logger.info('Search response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during search test: %s', e)
            self.fail('Search test failed')

    def test_list_audio_devices(self):
        logger.info('Testing list audio devices functionality')
        try:
            response = list_audio_devices()
            logger.info('List audio devices response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, list)
        except Exception as e:
            logger.error('Error during list audio devices test: %s', e)
            self.fail('List audio devices test failed')

    def test_add_tags_to_content(self):
        content_type = "vision"
        id = VISION_ID
        tags = ["test_tag"]

        logger.info('Testing add tags to content functionality')
        try:
            response = add_tags_to_content(content_type, id, tags)
            logger.info('Add tags to content response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during add tags to content test: %s', e)
            self.fail('Add tags to content test failed')

    def test_download_pipe(self) -> bool:
        """
        Tests the download pipe functionality

        Returns:
            bool: True if no exceptions are raised
        """
        url = STREAM_TEXT_URL
        logger.info('Testing download pipe functionality')
        try:
            response = download_pipe(url)
            logger.info('Download pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
            return True
        except Exception as e:
            logger.error('Error during download pipe test: %s', e)
            return False

    def test_run_pipe(self) -> bool:
        """
        Tests the run pipe functionality

        Returns:
            bool: True if no exceptions are raised
        """
        pipe_id = "pipe-stream-ocr-text"

        logger.info('Testing run pipe functionality')
        try:
            response = run_pipe(pipe_id)
            logger.info('Run pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
            return True
        except Exception as e:
            logger.error('Error during run pipe test: %s', e)
            return False

    def test_stop_pipe(self) -> bool:
        """
        Tests the stop pipe functionality

        Returns:
            bool: True if no exceptions are raised
        """
        pipe_id = "pipe-stream-ocr-text"

        logger.info('Testing stop pipe functionality')
        try:
            response = stop_pipe(pipe_id)
            logger.info('Stop pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
            return True
        except Exception as e:
            logger.error('Error during stop pipe test: %s', e)
            return False

    def test_health_check(self) -> bool:
        """
        Tests the health check functionality

        Returns:
            bool: True if no exceptions are raised
        """
        logger.info('Testing health check functionality')
        try:
            response = health_check()
            logger.info('Health check response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
            return True
        except Exception as e:
            logger.error('Error during health check test: %s', e)
            return False

    def test_audio_search_with_none_query(self):
        query = None
        content_type = "ocr"
        limit = 1
        offset = 0
        start_time = "2022-01-01T00:00:00Z"
        end_time = "2025-01-01T23:59:59Z"
        app_name = "test_app"
        window_name = "test_window"
        include_frames = INCLUDE_FRAMES

        logger.info('Testing search with invalid query functionality')
        try:
            response = search(
                query=query,
                content_type=content_type,
                limit=limit,
                offset=offset,
                start_time=start_time,
                end_time=end_time,
                app_name=None,
                window_name=None,
                include_frames=include_frames
            )
            logger.info('Search with invalid query response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during search with invalid query test: %s', e)
            self.fail('Search with invalid query test failed')


# TEST_CONSTANTS
HEALTH_CHECK = "test_health_check"
SEARCH = "test_search"
LIST_AUDIO_DEVICES = "test_list_audio_devices"
ADD_TAGS_TO_CONTENT = "test_add_tags_to_content"
SEARCH_WITH_NONE_QUERY = "test_audio_search_with_none_query"

# PIPE CONSTANTS
RUN_PIPE = "test_run_pipe"
STOP_PIPE = "test_stop_pipe"
DOWNLOAD_PIPE = "test_download_pipe"


def run_pipes_workflow():
    HEALTHY_MSG = "Online"
    UNHEALTHY_MSG = "Offline"

    res = TestScreenPipeClient(HEALTH_CHECK)
    if TestScreenPipeClient(HEALTH_CHECK) is False:
        print("Offline")
        return
    print("Online")
    # PIPE_ID = "pipe-stream-ocr-text"
    # Run the pipe. If pipe not present, download the pipe.
    pipe_id = "pipe-stream-ocr-text"
    if TestScreenPipeClient(RUN_PIPE) is None:
        print("Pipe not running. Starting pipe...")
        return


def run_current_tests():
    ONLY_HEALTH = False
    ADD_PIPES = True
    CURRENT_TESTS = [
        "test_health_check",
        "test_search",
        "test_list_audio_devices",
        "test_add_tags_to_content",
        "test_audio_search_with_none_query",
    ]

    # CONSTANTS
    ONLY_HEALTH = False
    ADD_PIPES = True

    suite = unittest.TestSuite()

    if ADD_PIPES:
        CURRENT_TESTS.append("test_download_pipe")
        CURRENT_TESTS.append("test_run_pipe")

    if ONLY_HEALTH:
        CURRENT_TESTS = ["test_health_check"]
    elif ADD_PIPES:
        CURRENT_TESTS.append("test_stop_pipe")

    for test in CURRENT_TESTS:
        suite.addTest(TestScreenPipeClient(test))

    unittest.TextTestRunner().run(suite)


def main():
    # unittest.main()
    # run_current_tests()
    run_pipes_workflow()


if __name__ == "__main__":
    main()
