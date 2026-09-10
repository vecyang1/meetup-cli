# -*- coding: utf-8 -*-
"""
meetupcli.formatter
~~~~~~~~~~~~~~~~~~~

Output formatters for CLI presentation: Terminal Table, JSON, Markdown, CSV, and URLs.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

import csv
import io
import json
import shutil
from typing import Any, Dict, List, Optional
from .models import Event, Group


def _sanitize_csv_cell(val: Any) -> str:
    s = str(val or "").strip()
    if s and s[0] in ("=", "+", "-", "@"):
        return f"'{s}"
    return s


def format_events_json(events: List[Event], pretty: bool = True) -> str:
    raw = [e.to_dict() for e in events]
    return json.dumps(raw, indent=2 if pretty else None, ensure_ascii=False)


def format_groups_json(groups: List[Group], pretty: bool = True) -> str:
    raw = [g.to_dict() for g in groups]
    return json.dumps(raw, indent=2 if pretty else None, ensure_ascii=False)


def format_events_urls(events: List[Event]) -> str:
    return "\n".join([e.event_url for e in events if e.event_url])


def format_groups_urls(groups: List[Group]) -> str:
    return "\n".join([g.link for g in groups if g.link])


def format_events_csv(events: List[Event]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    headers = [
        "id",
        "title",
        "date_time",
        "event_type",
        "rsvp_count",
        "fee",
        "group_name",
        "location",
        "event_url",
    ]
    writer.writerow(headers)
    for e in events:
        fee_str = e.fee.display_fee() if e.fee else "Free"
        row = [
            _sanitize_csv_cell(e.id),
            _sanitize_csv_cell(e.title),
            _sanitize_csv_cell(e.formatted_date()),
            _sanitize_csv_cell(e.event_type),
            _sanitize_csv_cell(e.rsvp_count),
            _sanitize_csv_cell(fee_str),
            _sanitize_csv_cell(e.group_name),
            _sanitize_csv_cell(e.location_display()),
            _sanitize_csv_cell(e.event_url),
        ]
        writer.writerow(row)
    return output.getvalue().strip()


def format_groups_csv(groups: List[Group]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    headers = [
        "id",
        "name",
        "members",
        "rating",
        "location",
        "link",
    ]
    writer.writerow(headers)
    for g in groups:
        row = [
            _sanitize_csv_cell(g.id),
            _sanitize_csv_cell(g.name),
            _sanitize_csv_cell(g.member_count),
            _sanitize_csv_cell(f"{g.rating:.1f}" if g.rating else "N/A"),
            _sanitize_csv_cell(g.display_location()),
            _sanitize_csv_cell(g.link),
        ]
        writer.writerow(row)
    return output.getvalue().strip()


def format_events_markdown(events: List[Event]) -> str:
    lines = [
        "| Date | Event Title | Group | RSVPs | Fee | Location | Link |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in events:
        title = e.title.replace("|", "-").strip()
        grp = e.group_name.replace("|", "-").strip()
        fee_str = e.fee.display_fee() if e.fee else "Free"
        loc = e.location_display().replace("|", "-").strip()
        link = f"[View Event]({e.event_url})" if e.event_url else "N/A"
        lines.append(f"| {e.formatted_date()} | {title} | {grp} | {e.rsvp_count} | {fee_str} | {loc} | {link} |")
    return "\n".join(lines)


def format_groups_markdown(groups: List[Group]) -> str:
    lines = [
        "| Group Name | Members | Rating | Location | Link |",
        "|---|---|---|---|---|",
    ]
    for g in groups:
        name = g.name.replace("|", "-").strip()
        rating_str = f"{g.rating:.1f} ({g.rating_count})" if g.rating else "N/A"
        loc = g.display_location().replace("|", "-").strip()
        link = f"[Join Group]({g.link})" if g.link else "N/A"
        lines.append(f"| {name} | {g.member_count} | {rating_str} | {loc} | {link} |")
    return "\n".join(lines)


def format_events_table(events: List[Event]) -> str:
    if not events:
        return "No events found matching your criteria."

    rows: List[List[str]] = []
    for e in events:
        date_str = e.formatted_date()
        fee_str = e.fee.display_fee() if e.fee else "Free"
        rsvps_str = f"{e.rsvp_count} going"
        loc_str = "Online" if e.is_online else (e.venue.city if e.venue and e.venue.city else "In-Person")
        rows.append([
            date_str,
            e.title,
            e.group_name,
            rsvps_str,
            fee_str,
            loc_str,
            e.event_url,
        ])

    headers = ["DATE", "EVENT TITLE", "GROUP", "RSVPS", "FEE", "TYPE", "LINK"]

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    col_widths[1] = min(col_widths[1], 36)
    col_widths[2] = min(col_widths[2], 24)
    col_widths[6] = min(col_widths[6], 42)

    def pad_cell(s: str, w: int) -> str:
        if len(s) > w:
            return s[:w - 1] + "…"
        return s.ljust(w)

    sep_line = "-" * (sum(col_widths) + (len(col_widths) - 1) * 2)
    header_line = "  ".join(pad_cell(headers[i], col_widths[i]) for i in range(len(headers)))

    table_lines = [sep_line, header_line, sep_line]
    for row in rows:
        row_str = "  ".join(pad_cell(row[i], col_widths[i]) for i in range(len(row)))
        table_lines.append(row_str)
    table_lines.append(sep_line)
    return "\n".join(table_lines)


def format_groups_table(groups: List[Group]) -> str:
    if not groups:
        return "No groups found matching your criteria."

    headers = ["GROUP NAME", "MEMBERS", "RATING", "LOCATION", "LINK"]
    rows: List[List[str]] = []
    for g in groups:
        rating_str = f"{g.rating:.1f}★" if g.rating else "-"
        rows.append([
            g.name,
            f"{g.member_count:,}",
            rating_str,
            g.display_location(),
            g.link,
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    col_widths[0] = min(col_widths[0], 36)
    col_widths[3] = min(col_widths[3], 24)
    col_widths[4] = min(col_widths[4], 42)

    def pad_cell(s: str, w: int) -> str:
        if len(s) > w:
            return s[:w - 1] + "…"
        return s.ljust(w)

    sep_line = "-" * (sum(col_widths) + (len(col_widths) - 1) * 2)
    header_line = "  ".join(pad_cell(headers[i], col_widths[i]) for i in range(len(headers)))

    table_lines = [sep_line, header_line, sep_line]
    for row in rows:
        row_str = "  ".join(pad_cell(row[i], col_widths[i]) for i in range(len(row)))
        table_lines.append(row_str)
    table_lines.append(sep_line)
    return "\n".join(table_lines)


def format_single_event_card(event: Event) -> str:
    lines = [
        "=" * 72,
        f"📌 {event.title}",
        "=" * 72,
        f"👥 Host Group:  {event.group_name or 'N/A'}",
        f"📅 Date & Time: {event.formatted_date()}",
    ]
    if event.end_time:
        lines.append(f"🏁 End Time:    {event.end_time}")
    lines.append(f"📍 Location:    {event.location_display()}")
    lines.append(f"🎟️ RSVPs:       {event.rsvp_count} going" + (f" (Max: {event.max_tickets})" if event.max_tickets else ""))
    fee_str = event.fee.display_fee() if event.fee else "Free"
    lines.append(f"💰 Admission:   {fee_str}")
    lines.append(f"🔗 URL:         {event.event_url}")
    if event.topics:
        lines.append(f"🏷️ Topics:      {', '.join(event.topics)}")
    if event.description:
        lines.append("-" * 72)
        lines.append("📝 Description:")
        lines.append(event.description.strip())
    lines.append("=" * 72)
    return "\n".join(lines)
