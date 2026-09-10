# -*- coding: utf-8 -*-
"""Unit tests for city presets and location resolver."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from meetupcli.presets import (
    get_preset,
    list_presets,
    resolve_location,
    resolve_location_and_keywords,
)


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

    def test_resolve_multilingual_aliases(self):
        self.assertEqual(resolve_location("东京"), "jp--tokyo")
        self.assertEqual(resolve_location("河内"), "vn--hanoi")
        self.assertEqual(resolve_location("上海"), "cn--shanghai")
        self.assertEqual(resolve_location("北京"), "cn--beijing")
        self.assertEqual(resolve_location("台北"), "tw--taipei")
        self.assertEqual(resolve_location("纽约"), "us--ny--new-york")
        self.assertEqual(resolve_location("旧金山"), "us--ca--san-francisco")
        self.assertEqual(resolve_location("伦敦"), "gb--greater-london")
        self.assertEqual(resolve_location("Hà Nội"), "vn--hanoi")
        self.assertEqual(resolve_location("胡志明"), "vn--ho-chi-minh-city")
        self.assertEqual(resolve_location("柏林"), "de--berlin")

    def test_get_preset(self):
        p = get_preset("tokyo")
        self.assertIsNotNone(p)
        self.assertEqual(p.slug, "jp--tokyo")

        self.assertIsNone(get_preset("nonexistent_city_xyz"))

    def test_resolve_location_and_keywords(self):
        # Single preset city
        loc, kw = resolve_location_and_keywords("tokyo")
        self.assertEqual(loc, "tokyo")
        self.assertEqual(kw, "")

        # City with keyword
        loc, kw = resolve_location_and_keywords("hanoi AI")
        self.assertEqual(loc, "hanoi")
        self.assertEqual(kw, "AI")

        # Multi-word preset with keyword
        loc, kw = resolve_location_and_keywords("new york tech")
        self.assertEqual(loc, "new york")
        self.assertEqual(kw, "tech")

        # Multilingual preset with keyword
        loc, kw = resolve_location_and_keywords("东京 python web3")
        self.assertEqual(loc, "东京")
        self.assertEqual(kw, "python web3")

        # Already a slug with no keywords
        loc, kw = resolve_location_and_keywords("jp--tokyo")
        self.assertEqual(loc, "jp--tokyo")
        self.assertEqual(kw, "")


if __name__ == "__main__":
    unittest.main()
