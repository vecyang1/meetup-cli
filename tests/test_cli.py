# -*- coding: utf-8 -*-
"""Unit and integration tests for the meetup CLI commands."""

import io
import json
import unittest
from unittest.mock import patch, MagicMock
from meetupcli.cli import main, EXIT_SUCCESS, EXIT_USAGE, EXIT_CONTRACT
from meetupcli.models import Event, Group, Venue, FeeSettings


class TestCli(unittest.TestCase):

    def test_cities_command(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["cities"])
            self.assertEqual(code, EXIT_SUCCESS)
            output = fake_out.getvalue()
            self.assertIn("Tokyo", output)
            self.assertIn("Hanoi", output)

    def test_cities_json_command(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["cities", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            data = json.loads(fake_out.getvalue())
            self.assertIsInstance(data, list)
            self.assertTrue(any(item["name"] == "Tokyo" for item in data))

    def test_events_missing_location_usage_error(self):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = main(["events"])
            self.assertEqual(code, EXIT_USAGE)
            self.assertIn("Error: Location is required", fake_err.getvalue())

    def test_groups_missing_location_usage_error(self):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = main(["groups"])
            self.assertEqual(code, EXIT_USAGE)
            self.assertIn("Error: Location is required", fake_err.getvalue())

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_events_table_output(self, mock_search):
        mock_search.return_value = [
            Event(
                id="123",
                title="Tokyo Python Sprint",
                event_url="https://meetup.com/events/123/",
                date_time="2026-10-01T18:00:00+09:00",
                event_type="PHYSICAL",
                rsvp_count=10,
                venue=Venue(name="Tokyo Hackerspace", city="Tokyo"),
                group_name="Tokyo Python",
            )
        ]
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["events", "tokyo"])
            self.assertEqual(code, EXIT_SUCCESS)
            output = fake_out.getvalue()
            self.assertIn("Tokyo Python Sprint", output)
            self.assertIn("Tokyo Python", output)

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_events_json_output(self, mock_search):
        mock_search.return_value = [
            Event(
                id="123",
                title="Tokyo Python Sprint",
                event_url="https://meetup.com/events/123/",
                date_time="2026-10-01T18:00:00+09:00",
                event_type="PHYSICAL",
                rsvp_count=10,
            )
        ]
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["events", "tokyo", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            data = json.loads(fake_out.getvalue())
            self.assertIsInstance(data, list)
            self.assertEqual(data[0]["title"], "Tokyo Python Sprint")

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_events_markdown_output(self, mock_search):
        mock_search.return_value = [
            Event(
                id="123",
                title="Tokyo Python Sprint",
                event_url="https://meetup.com/events/123/",
                date_time="2026-10-01T18:00:00+09:00",
                event_type="PHYSICAL",
                rsvp_count=10,
                group_name="Tokyo Python",
            )
        ]
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["events", "tokyo", "--markdown"])
            self.assertEqual(code, EXIT_SUCCESS)
            out = fake_out.getvalue()
            self.assertIn("| Date | Event Title | Group |", out)
            self.assertIn("Tokyo Python Sprint", out)

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_events_csv_output(self, mock_search):
        mock_search.return_value = [
            Event(
                id="123",
                title="Tokyo Python Sprint",
                event_url="https://meetup.com/events/123/",
                date_time="2026-10-01T18:00:00+09:00",
                event_type="PHYSICAL",
                rsvp_count=10,
                group_name="Tokyo Python",
            )
        ]
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["events", "tokyo", "--csv"])
            self.assertEqual(code, EXIT_SUCCESS)
            out = fake_out.getvalue()
            self.assertTrue(out.startswith("id,title,date_time"))
            self.assertIn("123,Tokyo Python Sprint", out)

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_shorthand_positional_location(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["tokyo", "--keywords", "ai"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_search.assert_called_once()
            call_kwargs = mock_search.call_args[1]
            self.assertEqual(call_kwargs["location"], "tokyo")
            self.assertEqual(call_kwargs["keywords"], "ai")

    @patch("meetupcli.client.MeetupClient.doctor")
    def test_doctor_healthy_and_degraded(self, mock_doctor):
        mock_doctor.return_value = {"status": "HEALTHY", "latency_ms": 120, "checks": []}
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["doctor"])
            self.assertEqual(code, EXIT_SUCCESS)

        mock_doctor.return_value = {"status": "DEGRADED", "latency_ms": 120, "checks": []}
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["doctor"])
            self.assertEqual(code, EXIT_CONTRACT)

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_shorthand_with_leading_flags(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["--no-cache", "tokyo"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_search.assert_called_once()
            self.assertEqual(mock_search.call_args[1]["location"], "tokyo")

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_events_flag_shortcuts_and_aliases(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            # Test -q and --online
            code = main(["events", "tokyo", "-q", "rust", "--online"])
            self.assertEqual(code, EXIT_SUCCESS)
            call_kwargs = mock_search.call_args[1]
            self.assertEqual(call_kwargs["keywords"], "rust")
            self.assertEqual(call_kwargs["event_type"], "online")

    @patch("meetupcli.client.MeetupClient.search_events_bulk")
    def test_bulk_command(self, mock_bulk):
        mock_bulk.return_value = {"tokyo": [], "hanoi": []}
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["bulk", "tokyo", "hanoi", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_bulk.assert_called_once()
            self.assertEqual(mock_bulk.call_args[1]["locations"], ["tokyo", "hanoi"])
            data = json.loads(fake_out.getvalue())
            self.assertIn("tokyo", data)
            self.assertIn("hanoi", data)

    @patch("meetupcli.client.MeetupClient.search_events_bulk")
    def test_events_multi_city_comma(self, mock_bulk):
        mock_bulk.return_value = {"tokyo": [], "hanoi": []}
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["events", "tokyo,hanoi", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_bulk.assert_called_once()
            self.assertEqual(mock_bulk.call_args[1]["locations"], ["tokyo", "hanoi"])


if __name__ == "__main__":
    unittest.main()
