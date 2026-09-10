# -*- coding: utf-8 -*-
"""Unit and integration tests for the meetup CLI commands."""

import io
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

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

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_command_collision_keyword(self, mock_search):
        mock_search.return_value = []
        for kw in ["doctor", "info", "cache", "events", "e", "s", "cities"]:
            mock_search.reset_mock()
            with patch("sys.stdout", new=io.StringIO()):
                code = main(["tokyo", "-q", kw])
                self.assertEqual(code, EXIT_SUCCESS, f"Failed for keyword matching command: {kw}")
                mock_search.assert_called_once()
                self.assertEqual(mock_search.call_args[1]["location"], "tokyo")
                self.assertEqual(mock_search.call_args[1]["keywords"], kw)

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_positional_keywords(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            # meetup tokyo ai
            code = main(["tokyo", "ai"])
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertEqual(mock_search.call_args[1]["location"], "tokyo")
            self.assertEqual(mock_search.call_args[1]["keywords"], "ai")

        mock_search.reset_mock()
        with patch("sys.stdout", new=io.StringIO()):
            # meetup events tokyo python web3
            code = main(["events", "tokyo", "python", "web3"])
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertEqual(mock_search.call_args[1]["location"], "tokyo")
            self.assertEqual(mock_search.call_args[1]["keywords"], "python web3")

    @patch("meetupcli.client.MeetupClient.search_events")
    def test_smart_preset_splitting(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            # Quoted string with city + keyword
            code = main(["hanoi AI"])
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertEqual(mock_search.call_args[1]["location"], "hanoi")
            self.assertEqual(mock_search.call_args[1]["keywords"], "AI")

        mock_search.reset_mock()
        with patch("sys.stdout", new=io.StringIO()):
            # Quoted multi-word preset + keyword
            code = main(["new york tech"])
            self.assertEqual(code, EXIT_SUCCESS)
            self.assertEqual(mock_search.call_args[1]["location"], "new york")
            self.assertEqual(mock_search.call_args[1]["keywords"], "tech")

    @patch("meetupcli.client.MeetupClient.search_groups")
    def test_groups_positional_keywords(self, mock_search):
        mock_search.return_value = []
        with patch("sys.stdout", new=io.StringIO()):
            code = main(["groups", "tokyo", "python", "--match-keyword"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_search.assert_called_once()
            self.assertEqual(mock_search.call_args[1]["location"], "tokyo")
            self.assertEqual(mock_search.call_args[1]["keywords"], "python")
            self.assertTrue(mock_search.call_args[1]["strict_keywords"])

    @patch("meetupcli.client.MeetupClient.search_groups_bulk")
    def test_groups_multi_city(self, mock_bulk):
        mock_bulk.return_value = {
            "tokyo": [Group(id="1", name="Tokyo Python", link="https://meetup.com/tokyo-python", member_count=500)],
            "hanoi": [Group(id="2", name="Hanoi AI", link="https://meetup.com/hanoi-ai", member_count=300)],
        }
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["groups", "tokyo,hanoi", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            mock_bulk.assert_called_once()
            data = json.loads(fake_out.getvalue())
            self.assertIn("tokyo", data)
            self.assertIn("hanoi", data)
            self.assertEqual(data["tokyo"][0]["name"], "Tokyo Python")

    def test_cache_command_list_and_json(self):
        import tempfile, shutil
        from pathlib import Path
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a mock cache file in home / .cache / meetupcli
            cache_folder = Path(temp_dir) / ".cache" / "meetupcli"
            cache_folder.mkdir(parents=True, exist_ok=True)
            mock_cache_file = cache_folder / "test12345.json"
            mock_cache_file.write_text(json.dumps({
                "url": "https://www.meetup.com/find/?location=jp--tokyo",
                "cached_at": 1725900000.0,
                "html": "<html></html>"
            }))
            with patch("pathlib.Path.home", return_value=Path(temp_dir)):
                with patch("sys.stdout", new=io.StringIO()) as fake_out:
                    code = main(["--cache-ttl", "300", "cache", "list"])
                    self.assertEqual(code, EXIT_SUCCESS)
                    out = fake_out.getvalue()
                    self.assertIn("HASH", out)
                    self.assertIn("test12345", out)

                with patch("sys.stdout", new=io.StringIO()) as fake_out:
                    code = main(["--cache-ttl", "300", "cache", "list", "--json"])
                    self.assertEqual(code, EXIT_SUCCESS)
                    data = json.loads(fake_out.getvalue())
                    self.assertIsInstance(data, list)
                    self.assertEqual(data[0]["hash"], "test12345")
                    self.assertIn("jp--tokyo", data[0]["url"])

                with patch("sys.stdout", new=io.StringIO()) as fake_out:
                    code = main(["cache", "status", "--json"])
                    self.assertEqual(code, EXIT_SUCCESS)
                    data = json.loads(fake_out.getvalue())
                    self.assertEqual(data["cached_files"], 1)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch("meetupcli.client.MeetupClient.search_events_bulk")
    def test_bulk_parity_urls_and_filters(self, mock_bulk):
        mock_bulk.return_value = {
            "tokyo": [
                Event(id="1", title="Tokyo Py", event_url="https://meetup.com/1", rsvp_count=10),
                Event(id="2", title="Tokyo AI", event_url="https://meetup.com/2", rsvp_count=2),
            ],
            "hanoi": [
                Event(id="3", title="Hanoi AI", event_url="https://meetup.com/3", rsvp_count=20),
            ],
        }
        # Test urls-only on bulk
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["bulk", "tokyo", "hanoi", "--urls-only"])
            self.assertEqual(code, EXIT_SUCCESS)
            out = fake_out.getvalue().strip().splitlines()
            self.assertEqual(len(out), 3)
            self.assertIn("https://meetup.com/1", out)

        # Test min-rsvps filter on bulk
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["bulk", "tokyo", "hanoi", "--min-rsvps", "5", "--json"])
            self.assertEqual(code, EXIT_SUCCESS)
            data = json.loads(fake_out.getvalue())
            self.assertEqual(len(data["tokyo"]), 1)  # Only Tokyo Py (10)
            self.assertEqual(data["tokyo"][0]["id"], "1")


if __name__ == "__main__":
    unittest.main()

