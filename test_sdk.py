import unittest
import logging
from utils.screenpipe_client import (
    search,
    list_audio_devices,
    add_tags_to_content,
    remove_tags_from_content,
    download_pipe,
    run_pipe,
    stop_pipe,
    health_check,
    list_monitors,
    get_pipe_info,
    list_pipes,
    update_pipe_configuration
)
# Third party -- Downloading can be DANGEROUS!
STREAM_TEXT_URL = "https://github.com/mediar-ai/screenpipe/tree/main/examples/typescript/pipe-screen-time-storyteller"
PIPE_NAME = "pipe-screen-time-storyteller"
# NOTE: Constants need work, though it should return results for any populated DB
# CONSTANTS
VALID_QUERY = " "
VALID_START_TIME = "2024-01-01T00:00:00Z"
VALID_END_TIME = "2025-01-01T23:59:59Z"

INCLUDE_FRAMES = False
CURRENT_LIMIT = 1

# TEST RUN:
OCR_CONTENT_TYPE = "ocr"
AUDIO_CONTENT_TYPE = "audio"
ALL_CONTENT_TYPE = "all"
DEFAULT_CONTENT_TYPE = AUDIO_CONTENT_TYPE
VISION_ID = 49040  # IF this ID doesn't match an OCR frame_id, it will not tag the frame!

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

    def test_remove_tags_from_content(self):
        content_type = "vision"
        id = VISION_ID
        tags = ["test_tag"]

        logger.info('Testing remove tags from content functionality')
        try:
            response = remove_tags_from_content(content_type, id, tags)
            logger.info('Remove tags from content response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during remove tags from content test: %s', e)
            self.fail('Remove tags from content test failed')

    def test_download_pipe(self):
        url = STREAM_TEXT_URL
        logger.info('Testing download pipe functionality')
        try:
            response = download_pipe(url)
            logger.info('Download pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during download pipe test: %s', e)
            self.fail('Download pipe test failed')

    def test_run_pipe(self):
        pipe_id = PIPE_NAME

        logger.info('Testing run pipe functionality')
        try:
            response = run_pipe(pipe_id)
            logger.info('Run pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during run pipe test: %s', e)
            self.fail('Run pipe test failed')

    def test_stop_pipe(self):
        pipe_id = PIPE_NAME

        logger.info('Testing stop pipe functionality')
        try:
            response = stop_pipe(pipe_id)
            logger.info('Stop pipe response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during stop pipe test: %s', e)
            self.fail('Stop pipe test failed')

    def test_health_check(self):
        logger.info('Testing health check functionality')
        try:
            response = health_check()
            logger.info('Health check response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during health check test: %s', e)
            self.fail('Health check test failed')

    def test_list_monitors(self):
        logger.info('Testing list monitors functionality')
        try:
            response = list_monitors()
            logger.info('List monitors response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, list)
        except Exception as e:
            logger.error('Error during list monitors test: %s', e)
            self.fail('List monitors test failed')

    def test_get_pipe_info(self):
        pipe_id = PIPE_NAME

        logger.info('Testing get pipe info functionality')
        try:
            response = get_pipe_info(pipe_id)
            logger.info('Get pipe info response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during get pipe info test: %s', e)
            self.fail('Get pipe info test failed')

    def test_list_pipes(self):
        logger.info('Testing list pipes functionality')
        try:
            response = list_pipes()
            logger.info('List pipes response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, list)
        except Exception as e:
            logger.error('Error during list pipes test: %s', e)
            self.fail('List pipes test failed')

    def test_update_pipe_configuration(self):
        pipe_id = PIPE_NAME
        config = {"key": "value"}

        logger.info('Testing update pipe configuration functionality')
        try:
            response = update_pipe_configuration(pipe_id, config)
            logger.info('Update pipe configuration response: %s', response)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, dict)
        except Exception as e:
            logger.error('Error during update pipe configuration test: %s', e)
            self.fail('Update pipe configuration test failed')


# TEST_CONSTANTS
HEALTH_CHECK = "test_health_check"
SEARCH = "test_search"
LIST_AUDIO_DEVICES = "test_list_audio_devices"
ADD_TAGS_TO_CONTENT = "test_add_tags_to_content"
REMOVE_TAGS_FROM_CONTENT = "test_remove_tags_from_content"
DOWNLOAD_PIPE = "test_download_pipe"
RUN_PIPE = "test_run_pipe"
STOP_PIPE = "test_stop_pipe"
LIST_MONITORS = "test_list_monitors"
GET_PIPE_INFO = "test_get_pipe_info"
LIST_PIPES = "test_list_pipes"
UPDATE_PIPE_CONFIGURATION = "test_update_pipe_configuration"


def create_test_suite():
    CURRENT_TESTS = [
        HEALTH_CHECK,
        # SEARCH,
        # LIST_AUDIO_DEVICES,
        # ADD_TAGS_TO_CONTENT,
        # REMOVE_TAGS_FROM_CONTENT,
        # DOWNLOAD_PIPE,
        # RUN_PIPE,
        # STOP_PIPE,
        # LIST_MONITORS,
        # GET_PIPE_INFO,
        # LIST_PIPES,
        # UPDATE_PIPE_CONFIGURATION
    ]
    suite = unittest.TestSuite()
    for test in CURRENT_TESTS:
        suite.addTest(TestScreenPipeClient(test))
    return suite


def run_tests():
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
