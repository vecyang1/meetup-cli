# Meetup Client API Contract

## Python SDK Usage

```python
from meetupcli import MeetupClient, Event, Group, Venue

client = MeetupClient(timeout=15.0, cache_ttl=300)

# Search events in Tokyo
events = client.search_events(location="tokyo", keywords="ai", event_type="all", limit=10)
for ev in events:
    print(ev.formatted_date(), ev.title, ev.location_display())

# Search community groups in Hanoi
groups = client.search_groups(location="hanoi", keywords="tech", limit=5)
for g in groups:
    print(g.name, g.member_count, g.display_location())

# Get single event details
event = client.get_event("315701498")
print(event.title, event.description)

# Diagnostic contract check
report = client.doctor()
assert report["status"] == "HEALTHY"
```
