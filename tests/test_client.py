# -*- coding: utf-8 -*-
"""Unit tests for MeetupClient transport, caching, and error handling."""

import io
import shutil
import tempfile
import unittest
import urllib.error
from unittest.mock import MagicMock, patch
from meetupcli.client import MeetupClient
from meetupcli.parser import MeetupNotFoundError, MeetupNetworkError


class TestClient(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.client = MeetupClient(cache_dir=self.temp_dir, cache_ttl=60, max_retries=1)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_hits_and_clearing(self):
        mock_response = io.BytesIO(b"<html><head></head><body>Sample Content</body></html>")
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        self.client._opener = mock_opener

        url = "https://www.meetup.com/find/?location=jp--tokyo"
        
        # 1st fetch: network call
        html1 = self.client.fetch(url, use_cache=True)
        self.assertEqual(html1, "<html><head></head><body>Sample Content</body></html>")
        self.assertEqual(mock_opener.open.call_count, 1)

        # 2nd fetch: should hit local disk cache
        html2 = self.client.fetch(url, use_cache=True)
        self.assertEqual(html2, html1)
        self.assertEqual(mock_opener.open.call_count, 1)  # not called again

        # Clear cache
        deleted = self.client.clear_cache()
        self.assertEqual(deleted, 1)

        # 3rd fetch: cache cleared, hits network again
        mock_opener.open.return_value = io.BytesIO(b"<html><body>Fresh Content</body></html>")
        html3 = self.client.fetch(url, use_cache=True)
        self.assertEqual(html3, "<html><body>Fresh Content</body></html>")
        self.assertEqual(mock_opener.open.call_count, 2)

    def test_http_404_error(self):
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError(
            url="https://meetup.com/events/9999999999/",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        self.client._opener = mock_opener

        with self.assertRaises(MeetupNotFoundError):
            self.client.fetch("https://meetup.com/events/9999999999/", use_cache=False)

    def test_http_500_retry_and_network_error(self):
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError(
            url="https://meetup.com/fail",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        self.client._opener = mock_opener

        with self.assertRaises(MeetupNetworkError):
            self.client.fetch("https://meetup.com/fail", use_cache=False)
        # 1 initial + 1 retry = 2 attempts
        self.assertEqual(mock_opener.open.call_count, 2)


if __name__ == "__main__":
    unittest.main()
