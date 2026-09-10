# -*- coding: utf-8 -*-
"""
meetupcli.parser
~~~~~~~~~~~~~~~~

Extracts and normalizes Next.js __NEXT_DATA__ Apollo Client states
into typed Event, Group, and Venue models.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

import json
import re
from typing import Any, Dict, List, Optional

from .models import Event, FeeSettings, Group, Venue


class MeetupError(Exception):
    """Base exception for meetupcli."""
    pass


class MeetupNetworkError(MeetupError):
    """Network or transport error."""
    pass


class MeetupParseError(MeetupError):
    """HTML or JSON extraction/parsing error."""
    pass


class MeetupNotFoundError(MeetupError):
    """Requested event or resource was not found."""
    pass


NEXT_DATA_REGEX = re.compile("<script id=\"__NEXT_DATA__\" type=\"application/json\">(.*?)</script>", re.DOTALL)


def extract_next_data(html: str) -> Dict[str, Any]:
    """
    Extract JSON object from the __NEXT_DATA__ script tag in Meetup HTML.
    """
    if not html:
        raise MeetupParseError("Empty HTML response from Meetup")

    match = NEXT_DATA_REGEX.search(html)
    if not match:
        raise MeetupParseError('Could not locate <script id="__NEXT_DATA__"> in response')

    raw_json = match.group(1).strip()
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise MeetupParseError(f"Failed to decode __NEXT_DATA__ JSON: {exc}") from exc


def extract_apollo_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Apollo client state from Next.js data dictionary.
    """
    props = data.get("props", {})
    page_props = props.get("pageProps", {})
    apollo = page_props.get("__APOLLO_STATE__")
    if not isinstance(apollo, dict):
        raise MeetupParseError("__APOLLO_STATE__ not found in pageProps")
    return apollo


def parse_venue(venue_data: Any, apollo: Dict[str, Any]) -> Optional[Venue]:
    """
    Parse venue data or reference into a typed Venue instance.
    """
    if not venue_data:
        return None

    if isinstance(venue_data, dict):
        if "__ref" in venue_data:
            ref_key = venue_data["__ref"]
            venue_data = apollo.get(ref_key, {})
            if not isinstance(venue_data, dict):
                return None

        name = venue_data.get("name") or ""
        address = venue_data.get("address") or ""
        city = venue_data.get("city") or ""
        state = venue_data.get("state") or ""
        country = venue_data.get("country") or ""
        lat = venue_data.get("lat")
        lon = venue_data.get("lon")
        try:
            lat = float(lat) if lat is not None else None
        except (ValueError, TypeError):
            lat = None
        try:
            lon = float(lon) if lon is not None else None
        except (ValueError, TypeError):
            lon = None

        if not any([name, address, city, state, country]):
            return None

        return Venue(name=name, address=address, city=city, state=state, country=country, lat=lat, lon=lon)

    return None


def parse_fee_settings(fee_data: Any) -> Optional[FeeSettings]:
    """
    Parse fee settings into a typed FeeSettings instance.
    """
    if not fee_data or not isinstance(fee_data, dict):
        return None

    try:
        amount = float(fee_data.get("amount") or 0.0)
    except (ValueError, TypeError):
        amount = 0.0

    currency = str(fee_data.get("currency") or "USD")
    accepts = str(fee_data.get("accepts") or "")
    return FeeSettings(amount=amount, currency=currency, accepts=accepts)


def parse_event(event_dict: Dict[str, Any], apollo: Dict[str, Any]) -> Event:
    """
    Normalize an Apollo Event entity into an Event model.
    """
    event_id = str(event_dict.get("id") or "")
    title = str(event_dict.get("title") or "").strip()
    event_url = str(event_dict.get("eventUrl") or "").strip()
    date_time = str(event_dict.get("dateTime") or "")
    end_time = event_dict.get("endTime")
    if end_time:
        end_time = str(end_time)

    event_type = str(event_dict.get("eventType") or "PHYSICAL").upper()
    rsvp_state = str(event_dict.get("rsvpState") or "JOIN_OPEN")
    max_tickets = event_dict.get("maxTickets")
    if max_tickets is not None:
        try:
            max_tickets = int(max_tickets)
        except (ValueError, TypeError):
            max_tickets = None

    # RSVP count extraction
    rsvp_count = 0
    rsvps = event_dict.get("rsvps")
    if isinstance(rsvps, dict):
        cnt = rsvps.get("totalCount")
        if cnt is not None:
            try:
                rsvp_count = int(cnt)
            except (ValueError, TypeError):
                pass
    if rsvp_count == 0:
        for k in event_dict:
            if "rsvpStatus" in k and "YES" in k and isinstance(event_dict[k], dict):
                cnt = event_dict[k].get("totalCount")
                if cnt is not None:
                    try:
                        rsvp_count = int(cnt)
                        break
                    except (ValueError, TypeError):
                        pass

    # Group resolution
    group_id = ""
    group_name = ""
    group_urlname = ""
    group_ref = event_dict.get("group")
    if isinstance(group_ref, dict):
        if "__ref" in group_ref:
            group_obj = apollo.get(group_ref["__ref"], {})
            if isinstance(group_obj, dict):
                group_id = str(group_obj.get("id") or "")
                group_name = str(group_obj.get("name") or "")
                group_urlname = str(group_obj.get("urlname") or "")
        else:
            group_id = str(group_ref.get("id") or "")
            group_name = str(group_ref.get("name") or "")
            group_urlname = str(group_ref.get("urlname") or "")

    # Venue & fee resolution
    venue = parse_venue(event_dict.get("venue"), apollo)
    fee = parse_fee_settings(event_dict.get("feeSettings"))
    description = str(event_dict.get("description") or "").strip()
    is_saved = bool(event_dict.get("isSaved", False))
    is_attending = bool(event_dict.get("isAttending", False))

    # Topics
    topics: List[str] = []
    topics_raw = event_dict.get("topics")
    if isinstance(topics_raw, dict):
        edges = topics_raw.get("edges", [])
        if isinstance(edges, list):
            for edge in edges:
                node = edge.get("node", {}) if isinstance(edge, dict) else {}
                tname = node.get("name")
                if tname:
                    topics.append(str(tname))

    return Event(
        id=event_id,
        title=title,
        event_url=event_url,
        date_time=date_time,
        end_time=end_time,
        event_type=event_type,
        rsvp_count=rsvp_count,
        max_tickets=max_tickets,
        rsvp_state=rsvp_state,
        group_id=group_id,
        group_name=group_name,
        group_urlname=group_urlname,
        venue=venue,
        fee=fee,
        description=description,
        is_saved=is_saved,
        is_attending=is_attending,
        topics=topics,
    )


def parse_events_from_html(html: str) -> List[Event]:
    """
    Parse all search result events from Meetup find HTML.
    """
    data = extract_next_data(html)
    apollo = extract_apollo_state(data)

    root = apollo.get("ROOT_QUERY", {})
    ordered_refs: List[str] = []
    seen_refs = set()

    if isinstance(root, dict):
        for k, v in root.items():
            k_lower = k.lower()
            if any(term in k_lower for term in ["eventsearch", "rankedevents", "recommendedevents", "searchevents"]) or (
                "event" in k_lower and isinstance(v, dict) and "edges" in v
            ):
                if isinstance(v, dict):
                    edges = v.get("edges", [])
                    if isinstance(edges, list):
                        for edge in edges:
                            if isinstance(edge, dict):
                                if "__ref" in edge:
                                    edge_obj = apollo.get(edge["__ref"])
                                    node = edge_obj.get("node", {}) if isinstance(edge_obj, dict) else {}
                                else:
                                    node = edge.get("node", {})
                                if isinstance(node, dict) and "__ref" in node:
                                    ref = node["__ref"]
                                    if ref not in seen_refs:
                                        seen_refs.add(ref)
                                        ordered_refs.append(ref)

    for k in apollo.keys():
        if k.startswith("Event:") and k not in seen_refs:
            seen_refs.add(k)
            ordered_refs.append(k)

    events: List[Event] = []
    for ref in ordered_refs:
        ev_data = apollo.get(ref)
        if isinstance(ev_data, dict):
            if ev_data.get("__typename") == "Event" and ev_data.get("title"):
                events.append(parse_event(ev_data, apollo))

    return events


def parse_group(group_dict: Dict[str, Any], apollo: Dict[str, Any]) -> Group:
    """
    Normalize an Apollo Group entity into a Group model.
    """
    group_id = str(group_dict.get("id") or "")
    name = str(group_dict.get("name") or "").strip()
    urlname = str(group_dict.get("urlname") or "").strip()
    link = str(group_dict.get("link") or "").strip()
    if not link and urlname:
        link = f"https://www.meetup.com/{urlname}/"

    description = str(group_dict.get("description") or "").strip()
    city = str(group_dict.get("city") or "")
    state = str(group_dict.get("state") or "")
    country = str(group_dict.get("country") or "")
    timezone = str(group_dict.get("timezone") or "")

    # Stats
    member_count = 0
    stats = group_dict.get("stats")
    rating: Optional[float] = None
    rating_count = 0
    if isinstance(stats, dict):
        member_counts = stats.get("memberCounts")
        if isinstance(member_counts, dict):
            try:
                member_count = int(member_counts.get("all") or 0)
            except (ValueError, TypeError):
                pass
        ratings = stats.get("eventRatings")
        if isinstance(ratings, dict):
            try:
                avg = ratings.get("average")
                rating = float(avg) if avg is not None else None
            except (ValueError, TypeError):
                rating = None
            try:
                rating_count = int(ratings.get("totalRatings") or 0)
            except (ValueError, TypeError):
                rating_count = 0

    return Group(
        id=group_id,
        name=name,
        urlname=urlname,
        link=link,
        description=description,
        city=city,
        state=state,
        country=country,
        timezone=timezone,
        member_count=member_count,
        rating=rating,
        rating_count=rating_count,
    )


def parse_groups_from_html(html: str) -> List[Group]:
    """
    Parse groups from Meetup search HTML (source=GROUPS).
    """
    data = extract_next_data(html)
    apollo = extract_apollo_state(data)

    root = apollo.get("ROOT_QUERY", {})
    ordered_refs: List[str] = []
    seen_refs = set()

    if isinstance(root, dict):
        for k, v in root.items():
            k_lower = k.lower()
            if any(term in k_lower for term in ["groupsearch", "rankedgroups", "recommendedgroups", "searchgroups"]) or (
                "group" in k_lower and isinstance(v, dict) and "edges" in v
            ):
                if isinstance(v, dict):
                    edges = v.get("edges", [])
                    if isinstance(edges, list):
                        for edge in edges:
                            if isinstance(edge, dict):
                                if "__ref" in edge:
                                    edge_obj = apollo.get(edge["__ref"])
                                    node = edge_obj.get("node", {}) if isinstance(edge_obj, dict) else {}
                                else:
                                    node = edge.get("node", {})
                                if isinstance(node, dict) and "__ref" in node:
                                    ref = node["__ref"]
                                    if ref not in seen_refs:
                                        seen_refs.add(ref)
                                        ordered_refs.append(ref)

    for k in apollo.keys():
        if k.startswith("Group:") and k not in seen_refs:
            seen_refs.add(k)
            ordered_refs.append(k)

    groups: List[Group] = []
    for ref in ordered_refs:
        g_data = apollo.get(ref)
        if isinstance(g_data, dict):
            if g_data.get("__typename") == "Group" or "name" in g_data:
                groups.append(parse_group(g_data, apollo))

    return groups


def parse_single_event_html(html: str) -> Event:
    """
    Parse an Event from an event detail page HTML.
    Uses authoritative root event query pointer when available.
    """
    data = extract_next_data(html)
    apollo = extract_apollo_state(data)

    # 1. First check ROOT_QUERY for authoritative event pointer
    root = apollo.get("ROOT_QUERY", {})
    target_ref = None
    if isinstance(root, dict):
        for k, v in root.items():
            if k.startswith("event(") and isinstance(v, dict) and "__ref" in v:
                target_ref = v["__ref"]
                break

    # 2. If target ref found and exists in apollo
    if target_ref and target_ref in apollo:
        return parse_event(apollo[target_ref], apollo)

    # 3. Fallback to scanning Event: keys
    event_keys = [k for k in apollo.keys() if k.startswith("Event:")]
    if not event_keys:
        raise MeetupNotFoundError("No Event entity found on this page")

    ev_dict = apollo[event_keys[0]]
    return parse_event(ev_dict, apollo)
