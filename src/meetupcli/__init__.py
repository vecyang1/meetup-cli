# -*- coding: utf-8 -*-
"""
meetupcli
~~~~~~~~~

Fast, zero-token CLI & Python SDK for querying Meetup.com activities, events, and groups.
Extracts Next.js Apollo state with zero API keys or browser automation required.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

__version__ = "1.2.0"
__author__ = "V"
__license__ = "GPL-3.0-or-later"

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
)
from .models import CityPreset, Event, FeeSettings, Group, Venue
from .parser import (
    MeetupError,
    MeetupNetworkError,
    MeetupNotFoundError,
    MeetupParseError,
)
from .presets import (
    get_preset,
    list_presets,
    resolve_location,
    resolve_location_and_keywords,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "MeetupClient",
    "Event",
    "Group",
    "Venue",
    "FeeSettings",
    "CityPreset",
    "MeetupError",
    "MeetupNetworkError",
    "MeetupParseError",
    "MeetupNotFoundError",
    "list_presets",
    "resolve_location",
    "resolve_location_and_keywords",
    "get_preset",
    "search_events",
    "search_groups",
    "search_events_bulk",
    "search_groups_bulk",
    "get_event",
    "format_events_table",
    "format_events_json",
    "format_events_markdown",
    "format_events_csv",
    "format_events_urls",
    "format_groups_table",
    "format_groups_json",
    "format_groups_markdown",
    "format_groups_csv",
    "format_groups_urls",
    "format_bulk_events_table",
    "format_bulk_events_json",
    "format_bulk_events_markdown",
    "format_bulk_events_csv",
    "format_bulk_groups_table",
    "format_bulk_groups_json",
    "format_bulk_groups_markdown",
    "format_bulk_groups_csv",
    "format_single_event_card",
]

_default_client = None


def _get_client() -> MeetupClient:
    global _default_client
    if _default_client is None:
        _default_client = MeetupClient()
    return _default_client


def search_events(
    location: str,
    keywords: str = "",
    query: str = None,
    event_type: str = "all",
    limit: int = 20,
    strict_keywords: bool = False,
    date_range: str = None,
    distance: str = None,
):
    """Convenience function to search events using a default client."""
    return _get_client().search_events(
        location=location,
        keywords=keywords,
        query=query,
        event_type=event_type,
        limit=limit,
        strict_keywords=strict_keywords,
        date_range=date_range,
        distance=distance,
    )


def search_groups(
    location: str,
    keywords: str = "",
    query: str = None,
    limit: int = 20,
    strict_keywords: bool = False,
):
    """Convenience function to search groups using a default client."""
    return _get_client().search_groups(
        location=location,
        keywords=keywords,
        query=query,
        limit=limit,
        strict_keywords=strict_keywords,
    )


def search_events_bulk(
    locations: list,
    keywords: str = "",
    query: str = None,
    event_type: str = "all",
    limit_per_city: int = 10,
    concurrency: int = 4,
    strict_keywords: bool = False,
    date_range: str = None,
    distance: str = None,
):
    """Convenience function to concurrently search events across multiple locations."""
    return _get_client().search_events_bulk(
        locations=locations,
        keywords=keywords,
        query=query,
        event_type=event_type,
        limit_per_city=limit_per_city,
        concurrency=concurrency,
        strict_keywords=strict_keywords,
        date_range=date_range,
        distance=distance,
    )


def search_groups_bulk(
    locations: list,
    keywords: str = "",
    query: str = None,
    limit_per_city: int = 10,
    concurrency: int = 4,
    strict_keywords: bool = False,
):
    """Convenience function to concurrently search groups across multiple locations."""
    return _get_client().search_groups_bulk(
        locations=locations,
        keywords=keywords,
        query=query,
        limit_per_city=limit_per_city,
        concurrency=concurrency,
        strict_keywords=strict_keywords,
    )


def get_event(event_id_or_url: str):
    """Convenience function to fetch event details by ID or URL."""
    return _get_client().get_event(event_id_or_url)
