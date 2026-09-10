# meetupcli (meetup-cli)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](pyproject.toml)
[![Tests: 56 passing](https://img.shields.io/badge/Tests-56%20passing-success.svg)](tests/)

Fast, production-grade CLI & Python SDK for querying [Meetup.com](https://www.meetup.com) tech events, social activities, networking meetups, and developer communities.

**Zero API keys. Zero browser automation. Zero external dependencies.**

---

## Highlights

- **Direct Apollo Cache Extraction**: Extracts authoritative Next.js SSR Apollo Client state (`<script id="__NEXT_DATA__">`) without Puppeteer/Playwright or API keys.
- **Zero Runtime Dependencies**: Built entirely with Python's standard library (`urllib`, `concurrent.futures`, `json`, `re`, `dataclasses`, `argparse`, `unicodedata`). Runs out of the box on Python 3.8+.
- **Multi-City Bulk Research & Concurrency**: Query activities across multiple cities in parallel with `meetup bulk tokyo hanoi nyc` or `meetup events tokyo,hanoi,shanghai`.
- **City Presets & Multilingual Geocoding**: Curated shortcuts for 30+ global hubs with native language resolution (e.g. `东京`, `河内`, `上海`, `北京`, `纽约`, `旧金山`, `台北`, `Hà Nội`) and automatic slug resolution.
- **CJK Terminal Alignment**: Pixel-perfect ASCII table rendering with East Asian character width calculation (`unicodedata`).
- **Rich Multi-Format Outputs**: Terminal table, raw JSON (`--json`), clean Markdown (`--markdown`), RFC-4180 CSV (`--csv`), and newline-separated links (`--urls-only`).
- **Flexible Filters**: Filter by keywords (`-k` or `-q`), format (`--online` or `--in-person`), date range (`--date-range`), free/paid status (`--free-only`, `--paid-only`), and minimum RSVPs (`--min-rsvps`).
- **Single Event Inspector**: Look up full event details and markdown descriptions using a bare numeric ID (e.g. `315701498`) or full URL.
- **Built-in Health Doctor**: `meetup doctor` continuously tests the live Meetup SSR schema contracts.
- **Smart Response Caching**: Fast local file cache (`~/.cache/meetupcli`) to save bandwidth and prevent rate-limiting during exploratory research.

---

## Installation

### Option 1: Symlink to User PATH (Instant, Recommended)

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/bin/meetup" ~/.local/bin/meetup
ln -sf "$(pwd)/bin/meetupcli" ~/.local/bin/meetupcli
```

### Option 2: Editable pip install

```bash
cd meetup-cli
pip install -e .
```

---

## CLI Usage & Examples

### 1. Searching Events

```bash
# Search tech events in Tokyo
meetup events tokyo --keywords tech --limit 5

# Positional shorthand with keywords works directly
meetup tokyo ai
meetup "hanoi AI"
meetup "new york tech"

# Filter only in-person events in Hanoi with at least 5 RSVPs
meetup events hanoi --type in-person --min-rsvps 5

# Multi-city concurrent events query
meetup events tokyo,hanoi,shanghai -q "ai"

# Export New York Python events to JSON
meetup events 'new york' --keywords python --json -o ny_python.json

# Export to Markdown table
meetup events sf --keywords "vibe coding" --markdown

# Export only event URLs for batch scraping or curl
meetup events london --keywords "web3" --urls-only
```

### 2. Searching Groups & Communities

```bash
# Find Python groups in Tokyo (positional or flag)
meetup groups tokyo python
meetup groups tokyo --keywords python

# Multi-city concurrent groups search
meetup groups tokyo,hanoi -q "ai"

# Filter groups with at least 500 members
meetup groups tokyo --keywords ai --min-members 500

# Output groups in CSV format
meetup groups 'san francisco' --keywords robotics --csv
```

### 3. Inspecting a Single Event

```bash
# Using numeric event ID
meetup event 315701498

# Using full event URL
meetup event "https://www.meetup.com/tokyo-international-social-club/events/315701498/"

# Export event description as Markdown
meetup event 315701498 --markdown
```

### 4. Listing Supported City Presets

```bash
meetup cities
meetup cities --json
```

### 5. Running Health Diagnostics (Doctor)

Verify that Meetup's frontend structure has not changed:

```bash
meetup doctor
meetup doctor --json
```

### 6. Cache Management

```bash
# View cache statistics
meetup cache status
meetup cache status --json

# List cached responses with age, size, and validity
meetup cache list
meetup cache list --json

# Clear local cache
meetup cache clear
```

---

## Python SDK Usage

You can use `meetupcli` as an imported library in any Python project or AI agent workflow:

```python
from meetupcli import MeetupClient

client = MeetupClient(timeout=15.0, cache_ttl=300)

# Search events
events = client.search_events(location="tokyo", keywords="ai", event_type="in-person", limit=5)
for event in events:
    print(f"[{event.formatted_date()}] {event.title} ({event.rsvp_count} going)")
    print(f"Location: {event.location_display()}")
    print(f"URL: {event.event_url}\n")

# Search groups
groups = client.search_groups(location="hanoi", keywords="tech", limit=5)
for group in groups:
    print(f"{group.name}: {group.member_count:,} members ({group.link})")

# Fetch single event
event = client.get_event("315701498")
print(event.title)
print(event.description)
```

---

## Standardized Exit Codes

Following Unix toolchain conventions:
- `0`: Success
- `1`: General runtime error / unhandled exception
- `2`: Usage error (e.g. missing required location argument)
- `3`: Network / HTTP error (timeout, connection refused, 5xx)
- `4`: Parsing error (missing or unparseable `__NEXT_DATA__`)
- `8`: Contract failure in `doctor` diagnostic check

---

## Testing & Verification

Run the full two-sided test suite (56 unit and live E2E tests):

```bash
cd meetup-cli
python3 -m unittest discover -s tests -v
```

---

## License

GNU General Public License v3.0 or later ([GPL-3.0-or-later](LICENSE)).
