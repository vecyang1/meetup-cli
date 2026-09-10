# -*- coding: utf-8 -*-
"""Unit tests for meetupcli data models."""

import unittest
from meetupcli.models import Venue, FeeSettings, Group, Event, CityPreset


class TestModels(unittest.TestCase):

    def test_venue_formatting(self):
        v = Venue(name="Google Japan", address="Roppongi Hills", city="Tokyo", state="", country="JP")
        self.assertEqual(v.formatted_address(), "Google Japan, Roppongi Hills, Tokyo, JP")

        v_empty = Venue()
        self.assertEqual(v_empty.formatted_address(), "Venue details not specified")

        v_partial = Venue(city="Hanoi", country="VN")
        self.assertEqual(v_partial.formatted_address(), "Hanoi, VN")

    def test_fee_settings(self):
        free = FeeSettings(amount=0.0, currency="USD")
        self.assertTrue(free.is_free())
        self.assertEqual(free.display_fee(), "Free")

        paid_usd = FeeSettings(amount=15.0, currency="USD")
        self.assertFalse(paid_usd.is_free())
        self.assertEqual(paid_usd.display_fee(), "$15")

        paid_jpy = FeeSettings(amount=1000.0, currency="JPY")
        self.assertFalse(paid_jpy.is_free())
        self.assertEqual(paid_jpy.display_fee(), "JPY 1000")

    def test_group_properties(self):
        g = Group(
            id="123",
            name="Tokyo AI Developers",
            urlname="tokyo-ai",
            city="Tokyo",
            country="jp",
            member_count=1500,
            rating=4.8,
            rating_count=50,
        )
        self.assertEqual(g.display_location(), "Tokyo, JP")
        d = g.to_dict()
        self.assertEqual(d["id"], "123")
        self.assertEqual(d["member_count"], 1500)

    def test_event_properties(self):
        e_physical = Event(
            id="ev_01",
            title="Tokyo Python Hackathon",
            event_url="https://meetup.com/ev_01",
            date_time="2026-10-15T18:30:00+09:00",
            event_type="PHYSICAL",
            rsvp_count=42,
            venue=Venue(name="Blink Community", city="Tokyo"),
        )
        self.assertFalse(e_physical.is_online)
        self.assertTrue(e_physical.is_free)
        self.assertEqual(e_physical.formatted_date(), "2026-10-15 18:30")
        self.assertIn("Blink Community", e_physical.location_display())

        e_online = Event(
            id="ev_02",
            title="Global AI Webinar",
            event_url="https://meetup.com/ev_02",
            event_type="ONLINE",
            fee=FeeSettings(amount=20, currency="USD"),
        )
        self.assertTrue(e_online.is_online)
        self.assertFalse(e_online.is_free)
        self.assertEqual(e_online.location_display(), "Online Event")

        d = e_online.to_dict()
        self.assertTrue(d["is_online"])
        self.assertFalse(d["is_free"])


if __name__ == "__main__":
    unittest.main()
