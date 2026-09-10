# -*- coding: utf-8 -*-
"""
meetupcli
~~~~~~~~~

Fast, zero-token CLI & Python SDK for querying Meetup.com activities, events, and groups.
Extracts Next.js Apollo state with zero API keys or browser automation required.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

__version__ = "1.0.0"
__author__ = "V"
__license__ = "GPL-3.0-or-later"

from .client import MeetupClient
from .models import CityPreset, Event, FeeSettings, Group, Venue
from .parser import (
    MeetupError,
    MeetupNetworkError,
    MeetupNotFoundError,
    MeetupParseError,
)
from .presets import get_preset, list_presets, resolve_location

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
    "get_preset",
    "search_events",
    "search_groups",
    "get_event",
]

_default_client = None


def _get_client() -> MeetupClient:
    global _default_client
    if _default_client is None:
        _default_client = MeetupClient()
    return _default_client


def search_events(location: str, keywords: str = "", event_type: str = "all", limit: int = 20):
    """Convenience function to search events using a default client."""
    return _get_client().search_events(
        location=location,
        keywords=keywords,
        event_type=event_type,
        limit=limit,
    )


def search_groups(location: str, keywords: str = "", limit: int = 20):
    """Convenience function to search groups using a default client."""
    return _get_client().search_groups(
        location=location,
        keywords=keywords,
        limit=limit,
    )


def get_event(event_id_or_url: str):
    """Convenience function to fetch event details by ID or URL."""
    return _get_client().get_event(event_id_or_url)
