# -*- coding: utf-8 -*-
"""Live E2E tests against actual Meetup.com public pages."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from meetupcli.client import MeetupClient


class TestLiveE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = MeetupClient(timeout=20.0, max_retries=2)

    def test_live_doctor_healthy(self):
        diag = self.client.doctor()
        self.assertEqual(diag.get("status"), "HEALTHY")
        checks = diag.get("checks", [])
        self.assertTrue(len(checks) >= 2)
        for check in checks:
            self.assertEqual(check.get("status"), "PASS")

    def test_live_tokyo_events(self):
        events = self.client.search_events(location="tokyo", keywords="tech", limit=5)
        self.assertGreater(len(events), 0)
        e = events[0]
        self.assertTrue(bool(e.id))
        self.assertTrue(bool(e.title))
        self.assertTrue(bool(e.event_url))

    def test_live_hanoi_events(self):
        events = self.client.search_events(location="hanoi", limit=3)
        self.assertGreater(len(events), 0)
        for e in events:
            self.assertTrue(bool(e.title), "Every event must have a non-empty title")

    def test_live_new_york_groups(self):
        groups = self.client.search_groups(location="new-york", keywords="python", limit=3)
        self.assertGreater(len(groups), 0)
        g = groups[0]
        self.assertTrue(bool(g.name))
        self.assertGreater(g.member_count, 0)


if __name__ == "__main__":
    unittest.main()
