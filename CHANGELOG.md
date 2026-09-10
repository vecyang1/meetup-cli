# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
