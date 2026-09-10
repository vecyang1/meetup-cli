# meetupcli Architecture

## Data Flow & Extraction Pipeline

```
Meetup.com Web Pages (/find/, /m/events/<id>/)
        │
        ▼ (urllib.request with Desktop User-Agent)
Raw Next.js SSR HTML
        │
        ▼ (extract_next_data via Regex)
<script id="__NEXT_DATA__"> JSON
        │
        ▼ (extract_apollo_state)
Apollo Client InMemoryCache (__APOLLO_STATE__)
        │
        ├── ROOT_QUERY (Ordered eventSearch / groupSearch edges)
        ├── Event:<id> (Title, dateTime, feeSettings, venue, rsvps)
        ├── Group:<id> (Name, memberCount, rating, urlname)
        └── Venue / Member references
        │
        ▼ (Normalizer & Filter: parser.py)
Typed Models (Event, Group, Venue, FeeSettings)
        │
        ▼ (formatter.py)
Presentations: Terminal Table | JSON | Markdown | CSV | URLs
```

## Key Modules

- `models.py`: Authoritative dataclasses defining the contract.
- `presets.py`: Global city presets and intelligent location resolver mapping common city names and aliases to Meetup location slugs.
- `parser.py`: Robust Next.js and Apollo state extractor with error boundaries for missing script tags, corrupt JSON, and recurring calendar stubs.
- `client.py`: HTTP transport with caching, retries, exponential backoff, proxy support, and automated `doctor` health diagnostics.
- `formatter.py`: Flexible rendering engine for terminal stdout, piping, or programmatic file output.
- `cli.py`: Production-grade command-line interface with intuitive subcommands, global arguments, and standardized exit codes.
