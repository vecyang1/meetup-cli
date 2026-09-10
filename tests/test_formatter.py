# -*- coding: utf-8 -*-
"""Unit tests for formatter display width, CJK terminal alignment, and bulk renderers."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from meetupcli.formatter import (
    _sanitize_csv_cell,
    format_bulk_events_csv,
    format_bulk_events_json,
    format_bulk_events_markdown,
    format_bulk_events_table,
    format_bulk_groups_csv,
    format_bulk_groups_json,
    format_bulk_groups_markdown,
    format_bulk_groups_table,
    format_events_csv,
    format_events_markdown,
    format_events_table,
    format_groups_csv,
    format_groups_markdown,
    format_groups_table,
    get_display_width,
    pad_display,
    truncate_to_display_width,
)
from meetupcli.models import Event, FeeSettings, Group, Venue


class TestFormatter(unittest.TestCase):

    def test_display_width_ascii_and_cjk(self):
        self.assertEqual(get_display_width("hello"), 5)
        self.assertEqual(get_display_width("东京"), 4)
        self.assertEqual(get_display_width("Hà Nội"), 6)
        self.assertEqual(get_display_width("东京 AI 开发者"), 14)

    def test_truncate_and_pad_display(self):
        padded = pad_display("东京", 10)
        self.assertEqual(get_display_width(padded), 10)
        self.assertTrue(padded.startswith("东京"))

        truncated = truncate_to_display_width("东京人工智能开发者大会", 10)
        self.assertLessEqual(get_display_width(truncated), 10)
        self.assertTrue(truncated.endswith("…"))

    def test_table_alignment_with_cjk(self):
        events = [
            Event(id="1", title="东京 AI 聚会", group_name="Tokyo AI", event_url="https://meetup.com/1"),
            Event(id="2", title="Python Sprinters", group_name="Py Tokyo", event_url="https://meetup.com/2"),
        ]
        table = format_events_table(events)
        lines = table.split("\n")
        # Line lengths in display cells should be equal
        widths = [get_display_width(l) for l in lines]
        self.assertEqual(widths[0], widths[1])
        self.assertEqual(widths[1], widths[2])
        self.assertEqual(widths[3], widths[4])

    def test_csv_sanitizer_zero_and_negative(self):
        # Numeric 0 should NOT be blanked out to empty string
        self.assertEqual(_sanitize_csv_cell(0), "0")
        self.assertEqual(_sanitize_csv_cell("0"), "0")
        # None should be empty string
        self.assertEqual(_sanitize_csv_cell(None), "")
        # Negative numbers should remain numeric strings without single quote
        self.assertEqual(_sanitize_csv_cell(-5), "-5")
        self.assertEqual(_sanitize_csv_cell("-122.4"), "-122.4")
        # Formula injection should be escaped with leading single quote
        self.assertEqual(_sanitize_csv_cell("=cmd|' /C calc'!A0"), "'=cmd|' /C calc'!A0")
        self.assertEqual(_sanitize_csv_cell("+cmd"), "'+cmd")
        self.assertEqual(_sanitize_csv_cell("@SUM(A1:A10)"), "'@SUM(A1:A10)")

    def test_newline_stripping_in_table_and_markdown(self):
        ev = Event(
            id="1",
            title="Tokyo Tech\nNew Line Title",
            group_name="Tokyo\nGroup",
            event_url="https://meetup.com/1",
        )
        table = format_events_table([ev])
        # Table lines should not have broken sublines
        lines = table.split("\n")
        self.assertEqual(len(lines), 5)  # sep, header, sep, row, sep
        self.assertIn("Tokyo Tech New Line Title", table)

        md = format_events_markdown([ev])
        self.assertIn("Tokyo Tech New Line Title", md)
        self.assertNotIn("\nNew Line Title", md)

    def test_bulk_formatters(self):
        ev = Event(id="101", title="Hanoi Founders", event_url="https://meetup.com/101")
        bulk_data = {"tokyo": [], "hanoi": [ev]}

        # JSON
        raw_json = format_bulk_events_json(bulk_data)
        parsed = json.loads(raw_json)
        self.assertIn("tokyo", parsed)
        self.assertIn("hanoi", parsed)
        self.assertEqual(len(parsed["hanoi"]), 1)

        # Markdown
        md = format_bulk_events_markdown(bulk_data)
        self.assertIn("Location: `tokyo`", md)
        self.assertIn("Location: `hanoi`", md)
        self.assertIn("Hanoi Founders", md)

        # Table
        tbl = format_bulk_events_table(bulk_data)
        self.assertIn("Location: tokyo", tbl)
        self.assertIn("Location: hanoi", tbl)

        # CSV
        csv_out = format_bulk_events_csv(bulk_data)
        self.assertIn("search_city,id,title", csv_out)
        self.assertIn("hanoi,101,Hanoi Founders", csv_out)

    def test_bulk_groups_formatters(self):
        grp = Group(id="202", name="Tokyo Rust", link="https://meetup.com/tokyo-rust", member_count=1200)
        bulk_data = {"tokyo": [grp], "hanoi": []}

        # JSON
        raw_json = format_bulk_groups_json(bulk_data)
        parsed = json.loads(raw_json)
        self.assertIn("tokyo", parsed)
        self.assertIn("hanoi", parsed)
        self.assertEqual(parsed["tokyo"][0]["name"], "Tokyo Rust")

        # Markdown
        md = format_bulk_groups_markdown(bulk_data)
        self.assertIn("Location: `tokyo`", md)
        self.assertIn("Tokyo Rust", md)

        # Table
        tbl = format_bulk_groups_table(bulk_data)
        self.assertIn("Location: tokyo", tbl)
        self.assertIn("Tokyo Rust", tbl)

        # CSV
        csv_out = format_bulk_groups_csv(bulk_data)
        self.assertIn("search_city,id,name,members", csv_out)
        self.assertIn("tokyo,202,Tokyo Rust,1200", csv_out)


if __name__ == "__main__":
    unittest.main()
