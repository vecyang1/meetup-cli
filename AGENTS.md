# AGENTS.md - Meetup CLI Operations & Maintenance

This document provides instructions for AI agents modifying or using `meetupcli`.

## Core Philosophy

- **Zero-Token, Zero-Key Extraction**: Meetup's public API is paywalled behind OAuth2/Pro, but their Next.js frontend embeds full Apollo Client state inside `<script id="__NEXT_DATA__">`. We read this authoritative state directly without running a headless browser or paying for API tokens.
- **Single Source of Truth**: Data in `__APOLLO_STATE__` is truth; `Event` and `Group` models are typed representations; CLI tables/JSON are projections.
- **Zero Runtime Dependencies**: The core package runs on standard Python 3.8+ (`urllib.request`, `json`, `re`, `argparse`, `dataclasses`). Do NOT add heavy dependencies like `requests`, `playwright`, `beautifulsoup4` or `selenium` unless absolutely unavoidable.
- **Two-Sided Verification**: Always test both the happy path (real pages, structured Apollo data) and adversarial error states (missing script tag, network error, 404, malformed JSON, calendar recurrence stubs).

## Verification Commands

Run hermetic and live tests:

```bash
cd meetup-cli
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run live contract health check:

```bash
./bin/meetup doctor
```

## Maintenance & Gotchas

1. **Recurring Event Stubs**: Meetup's Apollo state includes calendar recurrence placeholders like `Event:hwscbvyjcnbjb` that only have `id`, `dateTime`, and `group`, but NO `title` or `eventUrl`. The parser MUST filter these out (`if ev_data.get("__typename") == "Event" and ev_data.get("title"):`).
2. **Numeric Event ID Lookup**: `https://www.meetup.com/events/<id>/` returns 404. Meetup's canonical redirect URL for bare event IDs is `https://www.meetup.com/m/events/<id>/`.
3. **Exit Codes**:
   - `0`: Success
   - `1`: General runtime error / exception
   - `2`: CLI usage error (e.g. missing location)
   - `3`: Network / HTTP error
   - `4`: Parsing error (e.g. missing `__NEXT_DATA__`)
   - `8`: Contract check failure in `doctor`
