# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-10

### Fixed
- **CLI Subcommand Collision on Keyword Arguments**: Fixed severe argument parser collision where checking `any(arg in known_commands for arg in argv)` caused user queries containing subcommand names (e.g. `meetup tokyo -q doctor`, `meetup tokyo -q info`, `meetup tokyo -q cache`) to treat the query term as a subcommand and crash argparse with `invalid choice: 'tokyo'`. Replaced with non-option positional token inspection.
- **CSV Sanitizer Zero RSVPs and Members Erasure**: In `formatter.py`, `_sanitize_csv_cell(val)` used `str(val or "")`, which evaluated numeric `0` to `""`, wiping out all `0` RSVPs and `0` member counts in CSV output. Fixed to preserve `0` and negative numbers while continuing to guard against spreadsheet formula injection (`=`, `+`, `-`, `@`).
- **Terminal Table and Markdown Embedded Newlines**: Embedded `\n` or `\r` characters in event titles and group names broke table rows and Markdown formatting. Sanitized multi-line whitespace across table and markdown formatters.
- **Python 3.8-3.10 ISO 8601 Timestamp Compatibility**: In `models.py`, `datetime.fromisoformat()` in Python <= 3.10 could not parse trailing `'Z'` timezone offsets. Added `'Z'` to `'+00:00'` normalization to guarantee compatibility across all Python 3.8+ versions.
- **Apollo Group Parsing Edge Case**: Guarded `parse_groups_from_html()` in `parser.py` against incomplete Apollo Group cache references that lacked a `name` attribute.
- **Test Suite Portability**: Added `sys.path.insert(0, ...)` across all unit test files and `tests/__init__.py`, enabling clean `python3 -m unittest discover` out-of-the-box without requiring manual `PYTHONPATH=src`.

### Added
- **Positional Keywords Support**: Added `extra_keywords` to `events` and `groups` subparsers, enabling intuitive syntax like `meetup tokyo ai` and `meetup groups tokyo python`.
- **Smart Location & Keyword Splitting**: Added `resolve_location_and_keywords()` in `presets.py` to transparently separate known location presets from trailing keywords (e.g. `meetup "hanoi AI"`, `meetup "new york tech"`).
- **Cache Inspection Subcommand (`meetup cache list`)**: Fully implemented cached response listing with file hash, relative age, size in KB, validity status (`VALID`/`EXPIRED`), cached URL, and `--json` export support.
- **Multi-City Groups Discovery**: Added multi-city search to `groups` subcommand (`meetup groups tokyo,hanoi`), with `--cities`, `--concurrency`, `--match-keyword`, and formatters `format_bulk_groups_table`, `format_bulk_groups_json`, `format_bulk_groups_markdown`, and `format_bulk_groups_csv`.
- **Bulk Subcommand Feature Parity**: Added `--urls-only`, `--min-rsvps`, and `--sort` flags to `meetup bulk`.
- **Group Dictionary Location Field**: Added `display_location` to `Group.to_dict()` output.
- **Expanded Test Coverage**: Expanded test suite from 45 to 56 tests covering argument collision, CSV sanitization, cache listing, multi-city groups, and smart preset splitting.

## [1.1.0] - 2026-09-10

### Fixed
- **Apollo Search Ranking Edge Resolution**: Fixed critical bug in `parser.py` where default searches without keywords (`recommendedEvents` and `recommendedGroups`) failed to resolve `ROOT_QUERY` ordered edges and dereference edge objects (`RecommendedEventsEdge`), falling back to unordered hash map keys.
- **CLI Shorthand Argument Resolution**: Fixed argument parsing crash when flags preceded positional shorthand (e.g. `meetup --no-cache tokyo` failing with `invalid choice: 'tokyo'`).
- **CJK Terminal Display Width Alignment**: Replaced naive `len()` string padding in `formatter.py` with `unicodedata.east_asian_width` calculation, ensuring tables containing Chinese, Japanese, or East Asian characters and emojis stay aligned.
- **Documentation & Contract Parity**: Added `-q` as alias for `-k`/`--keywords`, `--online` and `--in-person` flag shortcuts, `query` parameter alias in Python SDK, and `fee_settings` compatibility property on `Event`.
- **Event End Time Formatting**: Added `Event.formatted_end_time()` to format event end times consistently with `formatted_date()` instead of displaying raw ISO strings.

### Added
- **Multi-City Bulk Research & Concurrency**: Added `meetup bulk` subcommand and multi-location comma syntax in `meetup events tokyo,hanoi,nyc` powered by `concurrent.futures.ThreadPoolExecutor` with configurable `--concurrency` worker threads.
- **Multilingual Preset Geocoding**: Enriched `presets.py` with Chinese, Japanese, and Vietnamese aliases (e.g. `东京`, `河内`, `上海`, `北京`, `纽约`, `旧金山`, `台北`, `Hà Nội`) and Unicode-safe location normalization.
- **Python SDK Bulk Search**: Exported `search_events_bulk` and `search_groups_bulk` in `meetupcli` package.
- **Comprehensive Test Suite Expansion**: Added unit tests for CJK table width alignment, multi-city bulk search, `query` alias, and Apollo edge dereferencing (expanded from 32 to 45 passing tests).

## [1.0.0] - 2026-09-10

### Added
- Initial release of `meetupcli` (`meetup` command line tool & Python SDK).
- Next.js SSR Apollo Client state parser (`__NEXT_DATA__` & `__APOLLO_STATE__`) extracting normalized events, groups, venues, fees, and RSVP counts without requiring private API tokens or browser automation.
- `events` subcommand: Query local and online events with filters for location, keywords, format (`all`, `in-person`, `online`), fees (`--free-only`, `--paid-only`), minimum RSVPs (`--min-rsvps`), and sorting (`relevance`, `date`, `rsvps`, `title`).
- `groups` subcommand: Search community groups and clubs with filters for member count and ratings.
- `event` subcommand: Inspect full details and descriptions for individual events using numeric ID (via `/m/events/<id>/` shortlink resolver) or full URL.
- `cities` subcommand: Curated registry of 30+ global city presets and smart alias resolver (Tokyo, Hanoi, New York, San Francisco, London, Shanghai, Beijing, Taipei, Singapore, Bangkok, Berlin, Paris, etc.).
- `doctor` subcommand: Live contract diagnostic runner verifying network reachability, Apollo state integrity, and parser contracts against Meetup.com with exit code `8` on failure.
- `cache` subcommand: File-based caching (`~/.cache/meetupcli`) with configurable TTL (`--cache-ttl`, `--no-cache`) and cache statistics/clearing.
- Multi-format output engines: Terminal ASCII/Unicode table with auto column sizing, raw JSON (`--json`), clean Markdown tables/cards (`--markdown`), RFC-4180 CSV (`--csv`), and newline-separated links (`--urls-only`).
- Dual CLI entry points `bin/meetup` and `bin/meetupcli`, installable via `ln -sf` into `~/.local/bin/`.
- Pure Python standard library implementation with zero external runtime dependencies.
- Two-sided verification test suite with 32 unit and live E2E integration tests passing.
