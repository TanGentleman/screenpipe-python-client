import unittest
import json
import requests
import time
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        content_type = "ocr"
        id = 1
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

    def test_download_pipe(self):
        url = "https://github.com/mediar-ai/screenpipe/tree/main/examples/typescript/pipe-stream-ocr-text"

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
        pipe_id = "pipe-stream-ocr-text"

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
        pipe_id = "pipe-stream-ocr-text"

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

    def test_search_with_invalid_query(self):
        query = None
        content_type = "ocr"
        limit = 10
        offset = 0
        start_time = "2022-01-01T00:00:00Z"
        end_time = "2025-01-01T23:59:59Z"
        app_name = "test_app"
        window_name = "test_window"
        include_frames = True

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

    def test_list_audio_devices_with_invalid_request(self):
        logger.info('Testing list audio devices with invalid request functionality')
        try:
            response = requests.get(f"{self.base_url}/audio/list", timeout=0.1)
            response.raise_for_status()
            logger.info('List audio devices with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during list audio devices with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

    def test_add_tags_to_content_with_invalid_request(self):
        content_type = "ocr"
        id = 1
        tags = ["test_tag"]

        logger.info('Testing add tags to content with invalid request functionality')
        try:
            response = requests.post(f"{self.base_url}/tags/{content_type}/{id}", json={"tags": tags}, timeout=0.1)
            response.raise_for_status()
            logger.info('Add tags to content with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during add tags to content with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

    def test_download_pipe_with_invalid_request(self):
        url = "https://github.com/mediar-ai/screenpipe/tree/main/examples/typescript/pipe-stream-ocr-text"

        logger.info('Testing download pipe with invalid request functionality')
        try:
            response = requests.post(f"{self.base_url}/pipes/download", json={"url": url}, timeout=0.1)
            response.raise_for_status()
            logger.info('Download pipe with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during download pipe with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

    def test_run_pipe_with_invalid_request(self):
        pipe_id = "pipe-stream-ocr-text"

        logger.info('Testing run pipe with invalid request functionality')
        try:
            response = requests.post(f"{self.base_url}/pipes/enable", json={"pipe_id": pipe_id}, timeout=0.1)
            response.raise_for_status()
            logger.info('Run pipe with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during run pipe with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

    def test_stop_pipe_with_invalid_request(self):
        pipe_id = "pipe-stream-ocr-text"

        logger.info('Testing stop pipe with invalid request functionality')
        try:
            response = requests.post(f"{self.base_url}/pipes/disable", json={"pipe_id": pipe_id}, timeout=0.1)
            response.raise_for_status()
            logger.info('Stop pipe with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during stop pipe with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

    def test_health_check_with_invalid_request(self):
        logger.info('Testing health check with invalid request functionality')
        try:
            response = requests.get(f"{self.base_url}/health", timeout=0.1)
            response.raise_for_status()
            logger.info('Health check with invalid request response: %s', response)
        except requests.exceptions.RequestException as e:
            logger.error('Error during health check with invalid request test: %s', e)
            self.assertIsInstance(e, requests.exceptions.RequestException)

def run_current_tests():
    ONLY_HEALTH = False
    CURRENT_TESTS = [
        # "test_search",
        "test_list_audio_devices",
        # "test_add_tags_to_content",
        # "test_download_pipe",
        # "test_run_pipe",
        # "test_stop_pipe",
        "test_health_check",
        # "test_search_with_invalid_query",
        # "test_list_audio_devices_with_invalid_request",
        # "test_add_tags_to_content_with_invalid_request",
        # "test_download_pipe_with_invalid_request",
        # "test_run_pipe_with_invalid_request",
        # "test_stop_pipe_with_invalid_request",
        # "test_health_check_with_invalid_request"
    ]
    suite = unittest.TestSuite()
    if ONLY_HEALTH:
        CURRENT_TESTS = ["test_health_check"]
    for test in CURRENT_TESTS:
        suite.addTest(TestScreenPipeClient(test))
    unittest.TextTestRunner().run(suite)

def main():
    # unittest.main()
    run_current_tests()

if __name__ == "__main__":
    run_current_tests()
