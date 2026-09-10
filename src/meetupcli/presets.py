# -*- coding: utf-8 -*-
"""
meetupcli.presets
~~~~~~~~~~~~~~~~~

Curated global city presets and smart location resolution for Meetup.com.

License: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

import re
from typing import Dict, List, Optional
from .models import CityPreset

# Curated registry of high-frequency tech & nomad hubs
PRESETS: List[CityPreset] = [
    CityPreset(name="Tokyo", slug="jp--tokyo", country_code="JP", aliases=["tokyo", "tyo", "shibuya", "shinjuku", "japan"]),
    CityPreset(name="Hanoi", slug="vn--hanoi", country_code="VN", aliases=["hanoi", "ha noi", "han", "vietnam"]),
    CityPreset(name="Ho Chi Minh City", slug="vn--ho-chi-minh-city", country_code="VN", aliases=["hcm", "saigon", "hochiminh", "hcmc", "sgn"]),
    CityPreset(name="Da Nang", slug="vn--da-nang", country_code="VN", aliases=["danang", "da nang", "dad"]),
    CityPreset(name="New York", slug="us--ny--new-york", country_code="US", aliases=["nyc", "new york", "new york city", "manhattan", "brooklyn"]),
    CityPreset(name="San Francisco", slug="us--ca--san-francisco", country_code="US", aliases=["sf", "san francisco", "bay area", "silicon valley", "sfo"]),
    CityPreset(name="London", slug="gb--greater-london", country_code="GB", aliases=["london", "greater london", "uk", "lon"]),
    CityPreset(name="Shanghai", slug="cn--shanghai", country_code="CN", aliases=["shanghai", "sh"]),
    CityPreset(name="Beijing", slug="cn--beijing", country_code="CN", aliases=["beijing", "bj"]),
    CityPreset(name="Taipei", slug="tw--taipei", country_code="TW", aliases=["taipei", "taiwan", "tpe"]),
    CityPreset(name="Singapore", slug="sg--singapore", country_code="SG", aliases=["singapore", "sg", "sin"]),
    CityPreset(name="Hong Kong", slug="hk--hong-kong", country_code="HK", aliases=["hong kong", "hk", "hongkong", "hkg"]),
    CityPreset(name="Bangkok", slug="th--bangkok", country_code="TH", aliases=["bangkok", "thailand", "bkk"]),
    CityPreset(name="Chiang Mai", slug="th--chiang-mai", country_code="TH", aliases=["chiang mai", "chiangmai", "cnx"]),
    CityPreset(name="Seoul", slug="kr--seoul", country_code="KR", aliases=["seoul", "korea", "sel"]),
    CityPreset(name="Berlin", slug="de--berlin", country_code="DE", aliases=["berlin", "germany", "ber"]),
    CityPreset(name="Paris", slug="fr--paris", country_code="FR", aliases=["paris", "france", "par"]),
    CityPreset(name="Amsterdam", slug="nl--amsterdam", country_code="NL", aliases=["amsterdam", "netherlands", "ams"]),
    CityPreset(name="Toronto", slug="ca--on--toronto", country_code="CA", aliases=["toronto", "canada", "yto"]),
    CityPreset(name="Vancouver", slug="ca--bc--vancouver", country_code="CA", aliases=["vancouver", "yvr"]),
    CityPreset(name="Sydney", slug="au--sydney", country_code="AU", aliases=["sydney", "australia", "syd"]),
    CityPreset(name="Melbourne", slug="au--melbourne", country_code="AU", aliases=["melbourne", "mel"]),
    CityPreset(name="Dubai", slug="ae--dubai", country_code="AE", aliases=["dubai", "uae", "dxb"]),
    CityPreset(name="Austin", slug="us--tx--austin", country_code="US", aliases=["austin", "atx"]),
    CityPreset(name="Seattle", slug="us--wa--seattle", country_code="US", aliases=["seattle", "sea"]),
    CityPreset(name="Boston", slug="us--ma--boston", country_code="US", aliases=["boston", "bos"]),
    CityPreset(name="Los Angeles", slug="us--ca--los-angeles", country_code="US", aliases=["la", "los angeles", "lax"]),
    CityPreset(name="Chicago", slug="us--il--chicago", country_code="US", aliases=["chicago", "chi"]),
    CityPreset(name="Dublin", slug="ie--dublin", country_code="IE", aliases=["dublin", "ireland", "dub"]),
    CityPreset(name="Zurich", slug="ch--zurich", country_code="CH", aliases=["zurich", "switzerland", "zrh"]),
    CityPreset(name="Munich", slug="de--munich", country_code="DE", aliases=["munich", "muc"]),
]

_LOOKUP: Dict[str, CityPreset] = {}
for p in PRESETS:
    _LOOKUP[p.name.lower()] = p
    _LOOKUP[p.slug.lower()] = p
    for a in p.aliases:
        _LOOKUP[a.lower()] = p


def list_presets() -> List[CityPreset]:
    """Return all available city presets."""
    return list(PRESETS)


def resolve_location(location: str) -> str:
    """
    Resolve a city name or alias to a Meetup location slug.
    If already a slug (e.g. contains '--'), returns it untouched.
    If matched against presets, returns the canonical slug.
    Otherwise, returns the cleaned user string for Meetup's geocoder.
    """
    if not location or not location.strip():
        return ""
    
    clean = location.strip()
    norm = clean.lower()
    
    # Already a slug?
    if "--" in clean:
        return clean
    
    if norm in _LOOKUP:
        return _LOOKUP[norm].slug
    
    # Check simplified whitespace / punctuation
    simplified = re.sub(r"[^a-z0-9]", "", norm)
    for k, preset in _LOOKUP.items():
        if re.sub(r"[^a-z0-9]", "", k) == simplified:
            return preset.slug
            
    # Fallback to the user's plain query (Meetup SSR accepts plain city names)
    return clean


def get_preset(query: str) -> Optional[CityPreset]:
    """Find a preset by name, slug, or alias."""
    if not query:
        return None
    norm = query.strip().lower()
    return _LOOKUP.get(norm)
