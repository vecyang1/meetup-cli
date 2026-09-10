# -*- coding: utf-8 -*-
"""Unit tests for city presets and location resolver."""

import unittest
from meetupcli.presets import list_presets, resolve_location, get_preset


class TestPresets(unittest.TestCase):

    def test_list_presets(self):
        presets = list_presets()
        self.assertGreater(len(presets), 20)
        names = [p.name for p in presets]
        self.assertIn("Tokyo", names)
        self.assertIn("Hanoi", names)
        self.assertIn("New York", names)
        self.assertIn("San Francisco", names)
        self.assertIn("London", names)

    def test_resolve_slug_passthrough(self):
        self.assertEqual(resolve_location("jp--tokyo"), "jp--tokyo")
        self.assertEqual(resolve_location("vn--hanoi"), "vn--hanoi")
        self.assertEqual(resolve_location("custom--location--slug"), "custom--location--slug")

    def test_resolve_city_names(self):
        self.assertEqual(resolve_location("Tokyo"), "jp--tokyo")
        self.assertEqual(resolve_location("tokyo"), "jp--tokyo")
        self.assertEqual(resolve_location("TOKYO"), "jp--tokyo")
        self.assertEqual(resolve_location("Hanoi"), "vn--hanoi")
        self.assertEqual(resolve_location("New York"), "us--ny--new-york")

    def test_resolve_aliases(self):
        self.assertEqual(resolve_location("nyc"), "us--ny--new-york")
        self.assertEqual(resolve_location("sf"), "us--ca--san-francisco")
        self.assertEqual(resolve_location("bay area"), "us--ca--san-francisco")
        self.assertEqual(resolve_location("silicon valley"), "us--ca--san-francisco")
        self.assertEqual(resolve_location("hcm"), "vn--ho-chi-minh-city")
        self.assertEqual(resolve_location("saigon"), "vn--ho-chi-minh-city")
        self.assertEqual(resolve_location("uk"), "gb--greater-london")

    def test_resolve_fallback(self):
        self.assertEqual(resolve_location("Kuala Lumpur"), "Kuala Lumpur")
        self.assertEqual(resolve_location("Da Lat"), "Da Lat")
        self.assertEqual(resolve_location(""), "")

    def test_get_preset(self):
        p = get_preset("tokyo")
        self.assertIsNotNone(p)
        self.assertEqual(p.slug, "jp--tokyo")

        self.assertIsNone(get_preset("nonexistent_city_xyz"))


if __name__ == "__main__":
    unittest.main()
