# -*- coding: utf-8 -*-
"""
meetupcli.client
~~~~~~~~~~~~~~~~

HTTP Client for Meetup.com with caching, retries, proxy support, and diagnostics.
Zero external runtime dependencies.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Event, Group
from .parser import (
    MeetupError,
    MeetupNetworkError,
    MeetupNotFoundError,
    MeetupParseError,
    parse_events_from_html,
    parse_groups_from_html,
    parse_single_event_html,
)
from .presets import resolve_location

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class MeetupClient:
    """
    Meetup.com API client using Next.js SSR Apollo cache extraction.
    """

    def __init__(
        self,
        base_url: str = "https://www.meetup.com",
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 15.0,
        proxy: Optional[str] = None,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 300,  # 5 minutes default
        max_retries: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self.proxy = proxy or os.environ.get("MEETUP_PROXY") or os.environ.get("HTTP_PROXY")
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries

        if cache_dir is not None:
            self.cache_path = Path(cache_dir)
        else:
            default_cache = Path.home() / ".cache" / "meetupcli"
            self.cache_path = default_cache

        try:
            self.cache_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.cache_path = None

        self._opener = self._build_opener()

    def _build_opener(self) -> urllib.request.OpenerDirector:
        handlers: List[Any] = []
        if self.proxy:
            handlers.append(urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy}))
        return urllib.request.build_opener(*handlers)

    def _cache_key(self, url: str) -> Optional[Path]:
        if not self.cache_path:
            return None
        hashed = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_path / f"{hashed}.json"

    def _get_from_cache(self, url: str) -> Optional[str]:
        if self.cache_ttl <= 0:
            return None
        cfile = self._cache_key(url)
        if not cfile or not cfile.exists():
            return None
        try:
            content = json.loads(cfile.read_text(encoding="utf-8"))
            cached_at = content.get("cached_at", 0)
            if (time.time() - cached_at) < self.cache_ttl:
                return content.get("html")
        except Exception:
            return None
        return None

    def _save_to_cache(self, url: str, html: str) -> None:
        if self.cache_ttl <= 0:
            return
        cfile = self._cache_key(url)
        if not cfile:
            return
        try:
            payload = {
                "url": url,
                "cached_at": time.time(),
                "html": html,
            }
            cfile.write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass

    def clear_cache(self) -> int:
        """Clear all cached files and return the number of files deleted."""
        if not self.cache_path or not self.cache_path.exists():
            return 0
        deleted = 0
        for f in self.cache_path.glob("*.json"):
            try:
                f.unlink()
                deleted += 1
            except Exception:
                pass
        return deleted

    def fetch(self, url: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> str:
        """
        Fetch HTML content from a Meetup URL with caching and retries.
        """
        if params:
            encoded_params = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None and v != ""})
            sep = "&" if "?" in url else "?"
            full_url = f"{url}{sep}{encoded_params}"
        else:
            full_url = url

        if use_cache:
            cached = self._get_from_cache(full_url)
            if cached:
                return cached

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(full_url, headers=headers)
                with self._opener.open(req, timeout=self.timeout) as resp:
                    raw_bytes = resp.read()
                    html = raw_bytes.decode("utf-8", errors="replace")
                    if use_cache:
                        self._save_to_cache(full_url, html)
                    return html
            except urllib.error.HTTPError as exc:
                last_err = exc
                if exc.code == 404:
                    raise MeetupNotFoundError(f"Resource not found (HTTP 404): {full_url}") from exc
                if exc.code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise MeetupNetworkError(f"HTTP error {exc.code} for {full_url}: {exc.reason}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_err = exc
                if attempt < self.max_retries:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise MeetupNetworkError(f"Network error connecting to {full_url}: {exc}") from exc

        raise MeetupNetworkError(f"Failed to fetch {full_url} after {self.max_retries} retries: {last_err}")

    def search_events(
        self,
        location: str,
        keywords: str = "",
        event_type: str = "all",  # 'all', 'inPerson', 'online'
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[Event]:
        """
        Search events in a given location with keywords and type filters.
        """
        loc_slug = resolve_location(location)
        params: Dict[str, Any] = {
            "source": "EVENTS",
        }
        if loc_slug:
            params["location"] = loc_slug
        if keywords:
            params["keywords"] = keywords
            
        et = event_type.lower()
        if et in ("inperson", "in-person", "physical"):
            params["eventType"] = "inPerson"
        elif et == "online":
            params["eventType"] = "online"

        url = f"{self.base_url}/find/"
        html = self.fetch(url, params=params, use_cache=use_cache)
        events = parse_events_from_html(html)

        # Apply client-side filters if needed
        if et in ("inperson", "in-person", "physical"):
            events = [e for e in events if not e.is_online]
        elif et == "online":
            events = [e for e in events if e.is_online]

        if limit and limit > 0:
            events = events[:limit]

        return events

    def search_groups(
        self,
        location: str,
        keywords: str = "",
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[Group]:
        """
        Search groups / communities in a given location.
        """
        loc_slug = resolve_location(location)
        params: Dict[str, Any] = {
            "source": "GROUPS",
        }
        if loc_slug:
            params["location"] = loc_slug
        if keywords:
            params["keywords"] = keywords

        url = f"{self.base_url}/find/"
        html = self.fetch(url, params=params, use_cache=use_cache)
        groups = parse_groups_from_html(html)

        if limit and limit > 0:
            groups = groups[:limit]

        return groups

    def get_event(self, event_id_or_url: str, use_cache: bool = True) -> Event:
        """
        Fetch detailed information for a single event by ID or URL.
        """
        target = event_id_or_url.strip()
        if target.startswith("http://") or target.startswith("https://"):
            url = target
        else:
            # Numeric or token ID - Meetup has event URL redirection: https://www.meetup.com/m/events/<id>/
            url = f"{self.base_url}/m/events/{target}/"

        html = self.fetch(url, use_cache=use_cache)
        return parse_single_event_html(html)

    def doctor(self) -> Dict[str, Any]:
        """
        Live contract health check against Meetup.com.
        Tests:
        1. Connectivity & latency to Meetup find page
        2. Next.js __NEXT_DATA__ integrity
        3. Apollo state schema validation
        4. Group search schema validation
        Returns diagnostic dictionary.
        """
        t0 = time.time()
        diag: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "UNKNOWN",
            "checks": [],
            "latency_ms": 0.0,
        }

        # Check 1: Event search contract
        try:
            c1_t0 = time.time()
            events = self.search_events(location="jp--tokyo", keywords="tech", limit=5, use_cache=False)
            c1_ms = round((time.time() - c1_t0) * 1000, 1)
            if not events:
                diag["checks"].append({
                    "name": "events_contract",
                    "status": "FAIL",
                    "latency_ms": c1_ms,
                    "error": "No events parsed from live Tokyo query",
                })
            else:
                first = events[0]
                has_title = bool(first.title)
                has_id = bool(first.id)
                has_url = bool(first.event_url)
                if has_title and has_id and has_url:
                    diag["checks"].append({
                        "name": "events_contract",
                        "status": "PASS",
                        "latency_ms": c1_ms,
                        "count": len(events),
                        "sample_event": {
                            "id": first.id,
                            "title": first.title,
                            "group": first.group_name,
                            "date": first.formatted_date(),
                            "location": first.location_display(),
                        },
                    })
                else:
                    diag["checks"].append({
                        "name": "events_contract",
                        "status": "FAIL",
                        "latency_ms": c1_ms,
                        "error": f"Missing required fields in parsed event: id={has_id}, title={has_title}, url={has_url}",
                    })
        except Exception as exc:
            diag["checks"].append({
                "name": "events_contract",
                "status": "ERROR",
                "error": str(exc),
            })

        # Check 2: Group search contract
        try:
            c2_t0 = time.time()
            groups = self.search_groups(location="jp--tokyo", keywords="tech", limit=5, use_cache=False)
            c2_ms = round((time.time() - c2_t0) * 1000, 1)
            if not groups:
                diag["checks"].append({
                    "name": "groups_contract",
                    "status": "FAIL",
                    "latency_ms": c2_ms,
                    "error": "No groups parsed from live Tokyo query",
                })
            else:
                g_first = groups[0]
                if g_first.id and g_first.name:
                    diag["checks"].append({
                        "name": "groups_contract",
                        "status": "PASS",
                        "latency_ms": c2_ms,
                        "count": len(groups),
                        "sample_group": {
                            "id": g_first.id,
                            "name": g_first.name,
                            "members": g_first.member_count,
                        },
                    })
                else:
                    diag["checks"].append({
                        "name": "groups_contract",
                        "status": "FAIL",
                        "latency_ms": c2_ms,
                        "error": "Missing required fields in parsed group",
                    })
        except Exception as exc:
            diag["checks"].append({
                "name": "groups_contract",
                "status": "ERROR",
                "error": str(exc),
            })

        total_ms = round((time.time() - t0) * 1000, 1)
        diag["latency_ms"] = total_ms

        all_pass = all(c.get("status") == "PASS" for c in diag["checks"])
        diag["status"] = "HEALTHY" if all_pass else "DEGRADED"
        return diag
