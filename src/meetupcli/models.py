# -*- coding: utf-8 -*-
"""
meetupcli.models
~~~~~~~~~~~~~~~~

Data models for Meetup events, groups, venues, fees, and search results.
Designed with single-source-of-truth and contract typing.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Venue:
    name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None

    def formatted_address(self) -> str:
        parts = [p for p in [self.name, self.address, self.city, self.state, self.country] if p]
        return ", ".join(parts) if parts else "Venue details not specified"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeeSettings:
    amount: float = 0.0
    currency: str = "USD"
    accepts: str = ""

    def is_free(self) -> bool:
        return self.amount <= 0

    def display_fee(self) -> str:
        if self.is_free():
            return "Free"
        sym = "$" if self.currency == "USD" else f"{self.currency} "
        return f"{sym}{self.amount:g}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Group:
    id: str
    name: str
    urlname: str = ""
    link: str = ""
    description: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    timezone: str = ""
    member_count: int = 0
    rating: Optional[float] = None
    rating_count: int = 0
    photo_url: Optional[str] = None

    def display_location(self) -> str:
        parts = [p for p in [self.city, self.state, self.country.upper() if self.country else ""] if p]
        return ", ".join(parts) if parts else "Location not specified"

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["display_location"] = self.display_location()
        return res


@dataclass
class Event:
    id: str
    title: str
    event_url: str
    date_time: str = ""
    end_time: Optional[str] = None
    event_type: str = "PHYSICAL"  # PHYSICAL or ONLINE
    rsvp_count: int = 0
    max_tickets: Optional[int] = None
    rsvp_state: str = "JOIN_OPEN"
    group_id: str = ""
    group_name: str = ""
    group_urlname: str = ""
    venue: Optional[Venue] = None
    fee: Optional[FeeSettings] = None
    description: str = ""
    is_saved: bool = False
    is_attending: bool = False
    topics: List[str] = field(default_factory=list)

    @property
    def is_online(self) -> bool:
        return self.event_type.upper() == "ONLINE"

    @property
    def is_free(self) -> bool:
        if self.fee is None:
            return True
        return self.fee.is_free()

    def location_display(self) -> str:
        if self.is_online:
            return "Online Event"
        if self.venue:
            return self.venue.formatted_address()
        return "Physical (Location TBD)"

    def formatted_date(self) -> str:
        if not self.date_time:
            return "Date TBD"
        try:
            raw = self.date_time
            if "[" in raw:
                raw = raw.split("[")[0]
            raw = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return self.date_time

    @property
    def fee_settings(self) -> Optional[FeeSettings]:
        """Compatibility alias for self.fee."""
        return self.fee

    def formatted_end_time(self) -> Optional[str]:
        if not self.end_time:
            return None
        try:
            raw = self.end_time
            if "[" in raw:
                raw = raw.split("[")[0]
            raw = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return self.end_time

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["is_online"] = self.is_online
        res["is_free"] = self.is_free
        res["formatted_date"] = self.formatted_date()
        res["formatted_end_time"] = self.formatted_end_time()
        res["location_display"] = self.location_display()
        return res


@dataclass
class CityPreset:
    name: str
    slug: str
    country_code: str
    aliases: List[str] = field(default_factory=list)
    lat: Optional[float] = None
    lon: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
