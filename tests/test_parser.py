# -*- coding: utf-8 -*-
"""Unit tests for Meetup HTML and Apollo state parsing."""

import json
import unittest
from meetupcli.parser import (
    MeetupParseError,
    MeetupNotFoundError,
    extract_next_data,
    extract_apollo_state,
    parse_events_from_html,
    parse_groups_from_html,
    parse_single_event_html,
)


def _build_mock_html(apollo_state):
    payload = {
        "props": {
            "pageProps": {
                "__APOLLO_STATE__": apollo_state,
            }
        }
    }
    return f"""<!DOCTYPE html>
<html>
<head>
<script id="__NEXT_DATA__" type="application/json">
{json.dumps(payload)}
</script>
</head>
<body><h1>Meetup</h1></body>
</html>"""


class TestParser(unittest.TestCase):

    def test_extract_next_data_malformed(self):
        with self.assertRaises(MeetupParseError):
            extract_next_data("<html><body>No next data here</body></html>")

        with self.assertRaises(MeetupParseError):
            extract_next_data("")

        corrupt = '<script id="__NEXT_DATA__" type="application/json">{invalid json}</script>'
        with self.assertRaises(MeetupParseError):
            extract_next_data(corrupt)

    def test_extract_apollo_state_missing(self):
        with self.assertRaises(MeetupParseError):
            extract_apollo_state({"props": {"pageProps": {}}})

    def test_parse_events_happy_path(self):
        apollo = {
            "ROOT_QUERY": {
                "eventSearch": {
                    "edges": [
                        {"node": {"__ref": "Event:101"}},
                        {"node": {"__ref": "Event:102"}},
                    ]
                }
            },
            "Event:101": {
                "__typename": "Event",
                "id": "101",
                "title": "Tokyo AI Builders",
                "eventUrl": "https://meetup.com/tokyo-ai/events/101/",
                "dateTime": "2026-10-01T19:00:00+09:00",
                "eventType": "PHYSICAL",
                "rsvps": {"totalCount": 45},
                "group": {"__ref": "Group:201"},
                "venue": {"name": "Shibuya WeWork", "city": "Tokyo", "country": "jp"},
                "feeSettings": {"amount": 10, "currency": "USD"},
            },
            "Event:102": {
                "__typename": "Event",
                "id": "102",
                "title": "Online Rust Workshop",
                "eventUrl": "https://meetup.com/rust/events/102/",
                "dateTime": "2026-10-05T10:00:00Z",
                "eventType": "ONLINE",
                "rsvps": {"totalCount": 120},
                "group": {"id": "202", "name": "Global Rustacean"},
                "feeSettings": None,
            },
            # Calendar recurrence stub without title - must be filtered out
            "Event:stub99": {
                "__typename": "Event",
                "id": "stub99",
                "dateTime": "2026-11-01T19:00:00Z",
            },
            "Group:201": {
                "__typename": "Group",
                "id": "201",
                "name": "Tokyo AI Community",
                "urlname": "tokyo-ai",
            }
        }
        html = _build_mock_html(apollo)
        events = parse_events_from_html(html)

        self.assertEqual(len(events), 2)
        e1 = events[0]
        self.assertEqual(e1.id, "101")
        self.assertEqual(e1.title, "Tokyo AI Builders")
        self.assertEqual(e1.group_name, "Tokyo AI Community")
        self.assertEqual(e1.rsvp_count, 45)
        self.assertFalse(e1.is_online)
        self.assertFalse(e1.is_free)
        self.assertIn("Shibuya WeWork", e1.location_display())

        e2 = events[1]
        self.assertEqual(e2.id, "102")
        self.assertTrue(e2.is_online)
        self.assertTrue(e2.is_free)
        self.assertEqual(e2.group_name, "Global Rustacean")

    def test_parse_groups_happy_path(self):
        apollo = {
            "ROOT_QUERY": {
                "groupSearch": {
                    "edges": [
                        {"node": {"__ref": "Group:501"}}
                    ]
                }
            },
            "Group:501": {
                "__typename": "Group",
                "id": "501",
                "name": "Hanoi Tech Founders",
                "urlname": "hanoi-tech",
                "link": "https://meetup.com/hanoi-tech/",
                "city": "Hanoi",
                "country": "vn",
                "stats": {
                    "memberCounts": {"all": 850},
                    "eventRatings": {"average": 4.9, "totalRatings": 35},
                }
            }
        }
        html = _build_mock_html(apollo)
        groups = parse_groups_from_html(html)

        self.assertEqual(len(groups), 1)
        g = groups[0]
        self.assertEqual(g.id, "501")
        self.assertEqual(g.name, "Hanoi Tech Founders")
        self.assertEqual(g.member_count, 850)
        self.assertAlmostEqual(g.rating, 4.9)
        self.assertEqual(g.rating_count, 35)
        self.assertEqual(g.display_location(), "Hanoi, VN")

    def test_parse_single_event_happy_and_missing(self):
        apollo = {
            "Event:777": {
                "__typename": "Event",
                "id": "777",
                "title": "Single Event Deep Dive",
                "eventUrl": "https://meetup.com/events/777/",
                "description": "Full markdown description here.",
                "dateTime": "2026-12-01T15:00:00Z",
            }
        }
        html = _build_mock_html(apollo)
        ev = parse_single_event_html(html)
        self.assertEqual(ev.id, "777")
        self.assertEqual(ev.title, "Single Event Deep Dive")
        self.assertEqual(ev.description, "Full markdown description here.")

        # Test missing event
        empty_html = _build_mock_html({})
        with self.assertRaises(MeetupNotFoundError):
            parse_single_event_html(empty_html)


if __name__ == "__main__":
    unittest.main()
