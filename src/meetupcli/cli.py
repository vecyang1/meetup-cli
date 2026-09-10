# -*- coding: utf-8 -*-
"""
meetupcli.cli
~~~~~~~~~~~~~

Production-grade command line interface for meetupcli.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

import argparse
import json
import sys
import time
from typing import List, Optional

from . import __version__
from .client import MeetupClient
from .formatter import (
    format_bulk_events_csv,
    format_bulk_events_json,
    format_bulk_events_markdown,
    format_bulk_events_table,
    format_bulk_groups_csv,
    format_bulk_groups_json,
    format_bulk_groups_markdown,
    format_bulk_groups_table,
    format_events_csv,
    format_events_json,
    format_events_markdown,
    format_events_table,
    format_events_urls,
    format_groups_csv,
    format_groups_json,
    format_groups_markdown,
    format_groups_table,
    format_groups_urls,
    format_single_event_card,
    get_display_width,
    pad_display,
)
from .models import Event, Group
from .parser import MeetupError, MeetupNetworkError, MeetupNotFoundError, MeetupParseError
from .presets import list_presets, resolve_location, resolve_location_and_keywords

# Standardized Unix / Toolchain Exit Codes
EXIT_SUCCESS = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_NETWORK = 3
EXIT_PARSE = 4
EXIT_CONTRACT = 8


def create_parser() -> argparse.ArgumentParser:
    epilog_text = """Examples:
  meetup events tokyo --keywords ai
  meetup events tokyo -q "rust" --online
  meetup events tokyo,hanoi,nyc --keywords ai
  meetup bulk tokyo hanoi nyc --keywords "web3"
  meetup groups 'new york' --keywords python
  meetup event 315701498
  meetup cities
  meetup doctor
"""
    shared_parent = argparse.ArgumentParser(add_help=False)
    shared_parent.add_argument("--proxy", help="HTTP/HTTPS proxy URL (e.g. http://127.0.0.1:7890)")
    shared_parent.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds (default: 15.0)")
    shared_parent.add_argument("--no-cache", action="store_true", help="Disable local request caching")
    shared_parent.add_argument("--cache-ttl", type=int, default=300, help="Cache TTL in seconds (default: 300)")
    shared_parent.add_argument("--verbose", action="store_true", help="Display full tracebacks on failure")

    parser = argparse.ArgumentParser(
        prog="meetup",
        description="meetupcli - Fast, zero-token CLI & Python SDK for querying Meetup.com activities, events, and groups.",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[shared_parent],
    )
    parser.add_argument("-v", "--version", action="version", version=f"meetupcli v{__version__}")

    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to execute")

    # Subcommand: events
    p_events = subparsers.add_parser("events", aliases=["e", "search", "s"], parents=[shared_parent], help="Search events in a city/region")
    p_events.add_argument("location", nargs="?", default="", help="City name, preset, slug, or comma-separated list of cities")
    p_events.add_argument("extra_keywords", nargs="*", help="Optional keywords (e.g. 'meetup tokyo ai')")
    p_events.add_argument("-l", "--location", dest="loc_flag", help="City or location override")
    p_events.add_argument("-c", "--cities", help="Comma-separated list of cities for bulk search")
    p_events.add_argument("-k", "-q", "--keywords", "--query", default="", help="Search keywords (e.g. ai, python, networking)")
    p_events.add_argument("-t", "--type", choices=["all", "in-person", "online"], default="all", help="Filter by event format")
    p_events.add_argument("--online", action="store_true", help="Shortcut to filter online events only")
    p_events.add_argument("--in-person", "--physical", action="store_true", dest="in_person", help="Shortcut to filter in-person events only")
    p_events.add_argument("--date-range", choices=["today", "tomorrow", "this-week", "this-weekend", "next-week"], help="Filter by date range")
    p_events.add_argument("-n", "--limit", type=int, default=20, help="Max results to display (default: 20)")
    p_events.add_argument("-j", "--concurrency", type=int, default=4, help="Concurrency for multi-city search (default: 4)")
    p_events.add_argument("--min-rsvps", type=int, default=0, help="Filter out events with fewer than N RSVPs")
    p_events.add_argument("--free-only", action="store_true", help="Only display free events")
    p_events.add_argument("--paid-only", action="store_true", help="Only display paid events")
    p_events.add_argument("--sort", choices=["relevance", "date", "rsvps", "title"], default="relevance", help="Sort results")
    p_events.add_argument("--match-keyword", action="store_true", help="Client-side strict filter to events matching keywords")
    p_events.add_argument("--json", action="store_true", help="Output raw JSON")
    p_events.add_argument("--markdown", "--md", action="store_true", dest="markdown", help="Output Markdown table")
    p_events.add_argument("--csv", action="store_true", help="Output CSV")
    p_events.add_argument("--urls-only", action="store_true", help="Output only URLs (one per line)")
    p_events.add_argument("-o", "--output", help="Save output directly to a file")

    # Subcommand: groups
    p_groups = subparsers.add_parser("groups", aliases=["g"], parents=[shared_parent], help="Search community groups in a city/region")
    p_groups.add_argument("location", nargs="?", default="", help="City name, preset, slug, or comma-separated list of cities")
    p_groups.add_argument("extra_keywords", nargs="*", help="Optional keywords (e.g. 'meetup groups tokyo python')")
    p_groups.add_argument("-l", "--location", dest="loc_flag", help="City or location override")
    p_groups.add_argument("-c", "--cities", help="Comma-separated list of cities for bulk group search")
    p_groups.add_argument("-k", "-q", "--keywords", "--query", default="", help="Search keywords")
    p_groups.add_argument("-n", "--limit", type=int, default=20, help="Max results to display (default: 20)")
    p_groups.add_argument("-j", "--concurrency", type=int, default=4, help="Concurrency for multi-city search (default: 4)")
    p_groups.add_argument("--min-members", type=int, default=0, help="Filter groups with fewer than N members")
    p_groups.add_argument("--sort", choices=["relevance", "members", "name"], default="relevance", help="Sort groups")
    p_groups.add_argument("--match-keyword", action="store_true", help="Strict keyword filter")
    p_groups.add_argument("--json", action="store_true", help="Output raw JSON")
    p_groups.add_argument("--markdown", "--md", action="store_true", dest="markdown", help="Output Markdown table")
    p_groups.add_argument("--csv", action="store_true", help="Output CSV")
    p_groups.add_argument("--urls-only", action="store_true", help="Output only group links")
    p_groups.add_argument("-o", "--output", help="Save output directly to a file")

    # Subcommand: bulk
    p_bulk = subparsers.add_parser("bulk", aliases=["b"], parents=[shared_parent], help="Concurrently search events across multiple cities")
    p_bulk.add_argument("cities", nargs="*", help="List of cities/locations to query (e.g. tokyo hanoi nyc)")
    p_bulk.add_argument("-c", "--cities", dest="cities_flag", help="Comma-separated list of cities (e.g. tokyo,hanoi,nyc)")
    p_bulk.add_argument("-k", "-q", "--keywords", "--query", default="", help="Search keywords across all cities")
    p_bulk.add_argument("-t", "--type", choices=["all", "in-person", "online"], default="all", help="Filter by event format")
    p_bulk.add_argument("--online", action="store_true", help="Shortcut to filter online events only")
    p_bulk.add_argument("--in-person", "--physical", action="store_true", dest="in_person", help="Shortcut to filter in-person events only")
    p_bulk.add_argument("--date-range", choices=["today", "tomorrow", "this-week", "this-weekend", "next-week"], help="Filter by date range")
    p_bulk.add_argument("-n", "--limit", type=int, default=10, help="Max results per city (default: 10)")
    p_bulk.add_argument("-j", "--concurrency", type=int, default=4, help="Concurrent HTTP worker threads (default: 4)")
    p_bulk.add_argument("--min-rsvps", type=int, default=0, help="Filter out events with fewer than N RSVPs")
    p_bulk.add_argument("--free-only", action="store_true", help="Only display free events")
    p_bulk.add_argument("--paid-only", action="store_true", help="Only display paid events")
    p_bulk.add_argument("--sort", choices=["relevance", "date", "rsvps", "title"], default="relevance", help="Sort results")
    p_bulk.add_argument("--match-keyword", action="store_true", help="Strict keyword filter")
    p_bulk.add_argument("--json", action="store_true", help="Output raw JSON")
    p_bulk.add_argument("--markdown", "--md", action="store_true", dest="markdown", help="Output Markdown")
    p_bulk.add_argument("--csv", action="store_true", help="Output CSV")
    p_bulk.add_argument("--urls-only", action="store_true", help="Output only URLs (one per line)")
    p_bulk.add_argument("-o", "--output", help="Save output directly to a file")

    # Subcommand: event
    p_event = subparsers.add_parser("event", aliases=["view", "info"], parents=[shared_parent], help="Fetch detailed information for an event")
    p_event.add_argument("target", help="Event ID or full Meetup event URL")
    p_event.add_argument("--json", action="store_true", help="Output raw JSON")
    p_event.add_argument("--markdown", "--md", action="store_true", dest="markdown", help="Output Markdown card")
    p_event.add_argument("-o", "--output", help="Save output directly to a file")

    # Subcommand: cities
    p_cities = subparsers.add_parser("cities", aliases=["presets"], parents=[shared_parent], help="List supported city presets and location slugs")
    p_cities.add_argument("--json", action="store_true", help="Output presets in JSON format")

    # Subcommand: doctor
    p_doctor = subparsers.add_parser("doctor", parents=[shared_parent], help="Live diagnostic and contract test against Meetup.com")
    p_doctor.add_argument("--json", action="store_true", help="Output diagnostic report in JSON format")

    # Subcommand: cache
    p_cache = subparsers.add_parser("cache", parents=[shared_parent], help="Inspect or clear local response cache")
    p_cache.add_argument("action", choices=["status", "list", "clear"], nargs="?", default="status", help="Action to perform")
    p_cache.add_argument("--json", action="store_true", help="Output cache details in JSON format")

    return parser


def write_output(content: str, out_file: Optional[str] = None) -> None:
    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content + chr(10))
    else:
        print(content)


def handle_events(client: MeetupClient, args: argparse.Namespace) -> int:
    raw_loc = (args.loc_flag or args.location or "").strip()
    cities_str = getattr(args, "cities", None)

    # Resolve positional extra keywords if any
    extra_kws = " ".join(getattr(args, "extra_keywords", []) or []).strip()
    effective_keywords = (args.keywords or "").strip()
    if extra_kws:
        effective_keywords = f"{effective_keywords} {extra_kws}".strip() if effective_keywords else extra_kws

    # Resolve format flag shortcuts
    ev_type = "online" if getattr(args, "online", False) else ("in-person" if getattr(args, "in_person", False) else args.type)
    date_range = getattr(args, "date_range", None)

    # Check if bulk multi-city query
    cities_list: List[str] = []
    if cities_str:
        cities_list = [c.strip() for c in cities_str.split(",") if c.strip()]
    elif "," in raw_loc:
        cities_list = [c.strip() for c in raw_loc.split(",") if c.strip()]

    if cities_list and len(cities_list) > 1:
        concurrency = getattr(args, "concurrency", 4)
        bulk_res = client.search_events_bulk(
            locations=cities_list,
            keywords=effective_keywords,
            event_type=ev_type,
            limit_per_city=args.limit,
            concurrency=concurrency,
            strict_keywords=args.match_keyword,
            date_range=date_range,
        )
        for c_loc in bulk_res:
            cev = bulk_res[c_loc]
            if args.free_only:
                cev = [e for e in cev if e.is_free]
            if args.paid_only:
                cev = [e for e in cev if not e.is_free]
            if args.min_rsvps > 0:
                cev = [e for e in cev if e.rsvp_count >= args.min_rsvps]
            if args.sort == "date":
                cev.sort(key=lambda x: x.date_time or "")
            elif args.sort == "rsvps":
                cev.sort(key=lambda x: x.rsvp_count, reverse=True)
            elif args.sort == "title":
                cev.sort(key=lambda x: x.title.lower())
            bulk_res[c_loc] = cev

        if args.json:
            write_output(format_bulk_events_json(bulk_res), args.output)
        elif args.markdown:
            write_output(format_bulk_events_markdown(bulk_res), args.output)
        elif args.csv:
            write_output(format_bulk_events_csv(bulk_res), args.output)
        elif args.urls_only:
            all_urls = []
            for cev in bulk_res.values():
                for e in cev:
                    if e.event_url:
                        all_urls.append(e.event_url)
            write_output("\n".join(all_urls), args.output)
        else:
            write_output(format_bulk_events_table(bulk_res), args.output)
        return EXIT_SUCCESS

    loc = raw_loc or (cities_list[0] if cities_list else "")
    if not loc:
        sys.stderr.write("Error: Location is required. E.g. 'meetup events tokyo' or 'meetup events -l hanoi'\n")
        return EXIT_USAGE

    resolved_loc, trailing_kw = resolve_location_and_keywords(loc)
    if trailing_kw:
        effective_keywords = f"{effective_keywords} {trailing_kw}".strip() if effective_keywords else trailing_kw

    events = client.search_events(
        location=resolved_loc,
        keywords=effective_keywords,
        event_type=ev_type,
        limit=args.limit * 2 if args.match_keyword else args.limit,
        strict_keywords=args.match_keyword,
        date_range=date_range,
    )

    # Post-filtering
    if args.free_only:
        events = [e for e in events if e.is_free]
    if args.paid_only:
        events = [e for e in events if not e.is_free]
    if args.min_rsvps > 0:
        events = [e for e in events if e.rsvp_count >= args.min_rsvps]

    # Sorting
    if args.sort == "date":
        events.sort(key=lambda x: x.date_time or "")
    elif args.sort == "rsvps":
        events.sort(key=lambda x: x.rsvp_count, reverse=True)
    elif args.sort == "title":
        events.sort(key=lambda x: x.title.lower())

    if args.limit and len(events) > args.limit:
        events = events[:args.limit]

    # Format
    if args.json:
        write_output(format_events_json(events), args.output)
    elif args.markdown:
        write_output(format_events_markdown(events), args.output)
    elif args.csv:
        write_output(format_events_csv(events), args.output)
    elif args.urls_only:
        write_output(format_events_urls(events), args.output)
    else:
        write_output(format_events_table(events), args.output)

    return EXIT_SUCCESS


def handle_groups(client: MeetupClient, args: argparse.Namespace) -> int:
    raw_loc = (args.loc_flag or args.location or "").strip()
    cities_str = getattr(args, "cities", None)

    # Resolve positional extra keywords if any
    extra_kws = " ".join(getattr(args, "extra_keywords", []) or []).strip()
    effective_keywords = (args.keywords or "").strip()
    if extra_kws:
        effective_keywords = f"{effective_keywords} {extra_kws}".strip() if effective_keywords else extra_kws

    # Check if bulk multi-city query
    cities_list: List[str] = []
    if cities_str:
        cities_list = [c.strip() for c in cities_str.split(",") if c.strip()]
    elif "," in raw_loc:
        cities_list = [c.strip() for c in raw_loc.split(",") if c.strip()]

    if cities_list and len(cities_list) > 1:
        concurrency = getattr(args, "concurrency", 4)
        bulk_res = client.search_groups_bulk(
            locations=cities_list,
            keywords=effective_keywords,
            limit_per_city=args.limit,
            concurrency=concurrency,
            strict_keywords=args.match_keyword,
        )
        for c_loc in bulk_res:
            cgrps = bulk_res[c_loc]
            if args.min_members > 0:
                cgrps = [g for g in cgrps if g.member_count >= args.min_members]
            if args.sort == "members":
                cgrps.sort(key=lambda x: x.member_count, reverse=True)
            elif args.sort == "name":
                cgrps.sort(key=lambda x: x.name.lower())
            bulk_res[c_loc] = cgrps

        if args.json:
            write_output(format_bulk_groups_json(bulk_res), args.output)
        elif args.markdown:
            write_output(format_bulk_groups_markdown(bulk_res), args.output)
        elif args.csv:
            write_output(format_bulk_groups_csv(bulk_res), args.output)
        elif args.urls_only:
            all_urls = []
            for cgrps in bulk_res.values():
                for g in cgrps:
                    if g.link:
                        all_urls.append(g.link)
            write_output("\n".join(all_urls), args.output)
        else:
            write_output(format_bulk_groups_table(bulk_res), args.output)
        return EXIT_SUCCESS

    loc = raw_loc or (cities_list[0] if cities_list else "")
    if not loc:
        sys.stderr.write("Error: Location is required. E.g. 'meetup groups tokyo'\n")
        return EXIT_USAGE

    resolved_loc, trailing_kw = resolve_location_and_keywords(loc)
    if trailing_kw:
        effective_keywords = f"{effective_keywords} {trailing_kw}".strip() if effective_keywords else trailing_kw

    groups = client.search_groups(
        location=resolved_loc,
        keywords=effective_keywords,
        limit=args.limit,
        strict_keywords=args.match_keyword,
    )

    if args.min_members > 0:
        groups = [g for g in groups if g.member_count >= args.min_members]

    if args.sort == "members":
        groups.sort(key=lambda x: x.member_count, reverse=True)
    elif args.sort == "name":
        groups.sort(key=lambda x: x.name.lower())

    if args.json:
        write_output(format_groups_json(groups), args.output)
    elif args.markdown:
        write_output(format_groups_markdown(groups), args.output)
    elif args.csv:
        write_output(format_groups_csv(groups), args.output)
    elif args.urls_only:
        write_output(format_groups_urls(groups), args.output)
    else:
        write_output(format_groups_table(groups), args.output)

    return EXIT_SUCCESS


def handle_event(client: MeetupClient, args: argparse.Namespace) -> int:
    target = args.target.strip()
    event = client.get_event(target)
    if args.json:
        write_output(json.dumps(event.to_dict(), indent=2, ensure_ascii=False), args.output)
    elif args.markdown:
        fee_display = event.fee.display_fee() if event.fee else "Free"
        md_lines = [
            f"# {event.title}",
            "",
            f"- **Group**: {event.group_name}",
            f"- **Date**: {event.formatted_date()}",
            f"- **Location**: {event.location_display()}",
            f"- **RSVPs**: {event.rsvp_count} going",
            f"- **Fee**: {fee_display}",
            f"- **URL**: [{event.event_url}]({event.event_url})",
            "",
            "## Description",
            "",
            event.description,
        ]
        write_output("\n".join(md_lines), args.output)
    else:
        write_output(format_single_event_card(event), args.output)

    return EXIT_SUCCESS


def handle_cities(args: argparse.Namespace) -> int:
    presets = list_presets()
    if args.json:
        print(json.dumps([p.to_dict() for p in presets], indent=2, ensure_ascii=False))
        return EXIT_SUCCESS

    headers = ["CITY", "COUNTRY", "LOCATION SLUG", "ALIASES"]
    rows = []
    for p in presets:
        rows.append([p.name, p.country_code, p.slug, ", ".join(p.aliases[:4])])

    col_widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            col_widths[i] = max(col_widths[i], len(c))

    def pad(s: str, w: int) -> str:
        return s.ljust(w)

    sep = "-" * (sum(col_widths) + (len(col_widths) - 1) * 2)
    print(sep)
    print("  ".join(pad(headers[i], col_widths[i]) for i in range(len(headers))))
    print(sep)
    for r in rows:
        print("  ".join(pad(r[i], col_widths[i]) for i in range(len(r))))
    print(sep)
    return EXIT_SUCCESS


def handle_doctor(client: MeetupClient, args: argparse.Namespace) -> int:
    sys.stderr.write("Running live contract tests against Meetup.com...\n")
    diag = client.doctor()

    if args.json:
        print(json.dumps(diag, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print(f"🩺 meetupcli doctor report: {diag.get('status')}")
        print(f"⏱️  Total latency: {diag.get('latency_ms')} ms")
        print("-" * 60)
        for check in diag.get("checks", []):
            name = check.get("name")
            status = check.get("status")
            icon = "✅" if status == "PASS" else "❌"
            ms = check.get("latency_ms", 0)
            print(f"{icon} {name}: {status} ({ms} ms)")
            if check.get("sample_event"):
                print(f"   Sample: {check['sample_event']['title']} ({check['sample_event']['date']})")
            if check.get("sample_group"):
                print(f"   Sample: {check['sample_group']['name']} ({check['sample_group']['members']:,} members)")
            if check.get("error"):
                print(f"   Error: {check['error']}")
        print("=" * 60)

    return EXIT_SUCCESS if diag.get("status") == "HEALTHY" else EXIT_CONTRACT


def handle_cache(client: MeetupClient, args: argparse.Namespace) -> int:
    if args.action == "clear":
        count = client.clear_cache()
        print(f"Cleared {count} cached response files.")
        return EXIT_SUCCESS
    elif args.action == "list":
        cpath = client.cache_path
        if not cpath or not cpath.exists():
            if getattr(args, "json", False):
                print("[]")
            else:
                print("Cache directory does not exist.")
            return EXIT_SUCCESS
        files = sorted(cpath.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            if getattr(args, "json", False):
                print("[]")
            else:
                print("No cached responses found.")
            return EXIT_SUCCESS

        entries = []
        now = time.time()
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                cached_at = data.get("cached_at", f.stat().st_mtime)
                age_sec = int(now - cached_at)
                is_valid = client.cache_ttl > 0 and (age_sec < client.cache_ttl)
                entries.append({
                    "hash": f.stem,
                    "url": data.get("url", ""),
                    "cached_at": cached_at,
                    "age_seconds": age_sec,
                    "size_bytes": f.stat().st_size,
                    "valid": is_valid,
                })
            except Exception:
                continue

        if getattr(args, "json", False):
            print(json.dumps(entries, indent=2, ensure_ascii=False))
            return EXIT_SUCCESS

        headers = ["HASH", "AGE", "SIZE", "STATUS", "CACHED URL"]
        rows = []
        for e in entries:
            age_s = e["age_seconds"]
            if age_s < 60:
                age_display = f"{age_s}s ago"
            elif age_s < 3600:
                age_display = f"{age_s // 60}m ago"
            elif age_s < 86400:
                age_display = f"{age_s // 3600}h ago"
            else:
                age_display = f"{age_s // 86400}d ago"

            size_display = f"{e['size_bytes'] / 1024:.1f} KB"
            status_display = "VALID" if e["valid"] else "EXPIRED"
            rows.append([
                e["hash"][:10],
                age_display,
                size_display,
                status_display,
                e["url"],
            ])

        col_widths = [get_display_width(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], get_display_width(cell))

        col_widths[4] = min(col_widths[4], 55)

        sep = "-" * (sum(col_widths) + (len(col_widths) - 1) * 2)
        print(sep)
        print("  ".join(pad_display(headers[i], col_widths[i]) for i in range(len(headers))))
        print(sep)
        for row in rows:
            print("  ".join(pad_display(row[i], col_widths[i]) for i in range(len(row))))
        print(sep)
        return EXIT_SUCCESS
    else:
        # Action: status
        cpath = client.cache_path
        if not cpath or not cpath.exists():
            print("Cache directory does not exist.")
            return EXIT_SUCCESS
        files = list(cpath.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        if getattr(args, "json", False):
            print(json.dumps({
                "cache_directory": str(cpath),
                "cached_files": len(files),
                "total_size_bytes": total_size,
            }, indent=2))
            return EXIT_SUCCESS
        print(f"Cache Directory: {cpath}")
        print(f"Cached files:    {len(files)}")
        print(f"Total size:      {total_size / 1024:.1f} KB")
        return EXIT_SUCCESS


def handle_bulk(client: MeetupClient, args: argparse.Namespace) -> int:
    cities: List[str] = []
    if getattr(args, "cities_flag", None):
        cities.extend([c.strip() for c in args.cities_flag.split(",") if c.strip()])
    if getattr(args, "cities", None):
        for item in args.cities:
            for c in item.split(","):
                c_clean = c.strip()
                if c_clean and c_clean not in cities:
                    cities.append(c_clean)

    if not cities:
        sys.stderr.write("Error: At least one city is required for bulk search. E.g. 'meetup bulk tokyo hanoi nyc' or 'meetup bulk -c tokyo,hanoi'\n")
        return EXIT_USAGE

    ev_type = "online" if getattr(args, "online", False) else ("in-person" if getattr(args, "in_person", False) else args.type)
    date_range = getattr(args, "date_range", None)
    concurrency = getattr(args, "concurrency", 4)

    bulk_res = client.search_events_bulk(
        locations=cities,
        keywords=args.keywords,
        event_type=ev_type,
        limit_per_city=args.limit,
        concurrency=concurrency,
        strict_keywords=args.match_keyword,
        date_range=date_range,
    )

    for c_loc in bulk_res:
        cev = bulk_res[c_loc]
        if args.free_only:
            cev = [e for e in cev if e.is_free]
        if args.paid_only:
            cev = [e for e in cev if not e.is_free]
        if getattr(args, "min_rsvps", 0) > 0:
            cev = [e for e in cev if e.rsvp_count >= args.min_rsvps]
        if getattr(args, "sort", None) == "date":
            cev.sort(key=lambda x: x.date_time or "")
        elif getattr(args, "sort", None) == "rsvps":
            cev.sort(key=lambda x: x.rsvp_count, reverse=True)
        elif getattr(args, "sort", None) == "title":
            cev.sort(key=lambda x: x.title.lower())
        bulk_res[c_loc] = cev

    if args.json:
        write_output(format_bulk_events_json(bulk_res), args.output)
    elif args.markdown:
        write_output(format_bulk_events_markdown(bulk_res), args.output)
    elif args.csv:
        write_output(format_bulk_events_csv(bulk_res), args.output)
    elif getattr(args, "urls_only", False):
        all_urls = []
        for cev in bulk_res.values():
            for e in cev:
                if e.event_url:
                    all_urls.append(e.event_url)
        write_output("\n".join(all_urls), args.output)
    else:
        write_output(format_bulk_events_table(bulk_res), args.output)

    return EXIT_SUCCESS


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    known_subcommands = {
        "events", "e", "search", "s",
        "groups", "g",
        "bulk", "b",
        "event", "view", "info",
        "cities", "presets",
        "doctor",
        "cache",
    }
    flags_with_args = {"--proxy", "--timeout", "--cache-ttl"}

    if not argv:
        create_parser().print_help()
        return EXIT_SUCCESS

    # Find the first positional token (ignoring options and their arguments)
    first_pos_idx = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in flags_with_args:
            i += 2
            continue
        if any(arg.startswith(f"{f}=") for f in flags_with_args):
            i += 1
            continue
        if arg.startswith("-"):
            i += 1
            continue
        first_pos_idx = i
        break

    if first_pos_idx is not None:
        first_pos = argv[first_pos_idx]
        if first_pos not in known_subcommands:
            argv = argv[:first_pos_idx] + ["events"] + argv[first_pos_idx:]

    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return EXIT_SUCCESS

    client = MeetupClient(
        timeout=args.timeout,
        proxy=args.proxy,
        cache_ttl=0 if args.no_cache else args.cache_ttl,
    )

    try:
        sub = args.subcommand
        if sub in ("events", "e", "search", "s"):
            return handle_events(client, args)
        elif sub in ("groups", "g"):
            return handle_groups(client, args)
        elif sub in ("bulk", "b"):
            return handle_bulk(client, args)
        elif sub in ("event", "view", "info"):
            return handle_event(client, args)
        elif sub in ("cities", "presets"):
            return handle_cities(args)
        elif sub == "doctor":
            return handle_doctor(client, args)
        elif sub == "cache":
            return handle_cache(client, args)
        else:
            parser.print_help()
            return EXIT_USAGE
    except MeetupNotFoundError as exc:
        sys.stderr.write(f"[Error: Not Found] {exc}\n")
        return EXIT_GENERAL
    except MeetupNetworkError as exc:
        sys.stderr.write(f"[Error: Network] {exc}\n")
        return EXIT_NETWORK
    except MeetupParseError as exc:
        sys.stderr.write(f"[Error: Parse] {exc}\n")
        return EXIT_PARSE
    except KeyboardInterrupt:
        sys.stderr.write("\nOperation cancelled by user.\n")
        return 130
    except Exception as exc:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            sys.stderr.write(f"[Error] {exc}\n")
        return EXIT_GENERAL


if __name__ == "__main__":
    sys.exit(main())
