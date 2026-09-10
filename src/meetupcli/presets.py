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
    CityPreset(name="Tokyo", slug="jp--tokyo", country_code="JP", aliases=["tokyo", "tyo", "shibuya", "shinjuku", "japan", "东京", "東京", "とうきょう"]),
    CityPreset(name="Hanoi", slug="vn--hanoi", country_code="VN", aliases=["hanoi", "ha noi", "han", "vietnam", "河内", "hà nội"]),
    CityPreset(name="Ho Chi Minh City", slug="vn--ho-chi-minh-city", country_code="VN", aliases=["hcm", "saigon", "hochiminh", "hcmc", "sgn", "胡志明", "西贡", "thành phố hồ chí minh", "tp hcm"]),
    CityPreset(name="Da Nang", slug="vn--da-nang", country_code="VN", aliases=["danang", "da nang", "dad", "岘港", "đà nẵng"]),
    CityPreset(name="New York", slug="us--ny--new-york", country_code="US", aliases=["nyc", "new york", "new york city", "manhattan", "brooklyn", "纽约"]),
    CityPreset(name="San Francisco", slug="us--ca--san-francisco", country_code="US", aliases=["sf", "san francisco", "bay area", "silicon valley", "sfo", "旧金山", "三藩市"]),
    CityPreset(name="London", slug="gb--greater-london", country_code="GB", aliases=["london", "greater london", "uk", "lon", "伦敦"]),
    CityPreset(name="Shanghai", slug="cn--shanghai", country_code="CN", aliases=["shanghai", "sh", "上海"]),
    CityPreset(name="Beijing", slug="cn--beijing", country_code="CN", aliases=["beijing", "bj", "北京"]),
    CityPreset(name="Taipei", slug="tw--taipei", country_code="TW", aliases=["taipei", "taiwan", "tpe", "台北"]),
    CityPreset(name="Singapore", slug="sg--singapore", country_code="SG", aliases=["singapore", "sg", "sin", "新加坡", "狮城"]),
    CityPreset(name="Hong Kong", slug="hk--hong-kong", country_code="HK", aliases=["hong kong", "hk", "hongkong", "hkg", "香港"]),
    CityPreset(name="Bangkok", slug="th--bangkok", country_code="TH", aliases=["bangkok", "thailand", "bkk", "曼谷"]),
    CityPreset(name="Chiang Mai", slug="th--chiang-mai", country_code="TH", aliases=["chiang mai", "chiangmai", "cnx", "清迈"]),
    CityPreset(name="Seoul", slug="kr--seoul", country_code="KR", aliases=["seoul", "korea", "sel", "首尔", "汉城", "서울"]),
    CityPreset(name="Berlin", slug="de--berlin", country_code="DE", aliases=["berlin", "germany", "ber", "柏林"]),
    CityPreset(name="Paris", slug="fr--paris", country_code="FR", aliases=["paris", "france", "par", "巴黎"]),
    CityPreset(name="Amsterdam", slug="nl--amsterdam", country_code="NL", aliases=["amsterdam", "netherlands", "ams", "阿姆斯特丹"]),
    CityPreset(name="Toronto", slug="ca--on--toronto", country_code="CA", aliases=["toronto", "canada", "yto", "多伦多"]),
    CityPreset(name="Vancouver", slug="ca--bc--vancouver", country_code="CA", aliases=["vancouver", "yvr", "温哥华"]),
    CityPreset(name="Sydney", slug="au--sydney", country_code="AU", aliases=["sydney", "australia", "syd", "悉尼", "雪梨"]),
    CityPreset(name="Melbourne", slug="au--melbourne", country_code="AU", aliases=["melbourne", "mel", "墨尔本"]),
    CityPreset(name="Dubai", slug="ae--dubai", country_code="AE", aliases=["dubai", "uae", "dxb", "迪拜"]),
    CityPreset(name="Austin", slug="us--tx--austin", country_code="US", aliases=["austin", "atx", "奥斯汀"]),
    CityPreset(name="Seattle", slug="us--wa--seattle", country_code="US", aliases=["seattle", "sea", "西雅图"]),
    CityPreset(name="Boston", slug="us--ma--boston", country_code="US", aliases=["boston", "bos", "波士顿"]),
    CityPreset(name="Los Angeles", slug="us--ca--los-angeles", country_code="US", aliases=["la", "los angeles", "lax", "洛杉矶"]),
    CityPreset(name="Chicago", slug="us--il--chicago", country_code="US", aliases=["chicago", "chi", "芝加哥"]),
    CityPreset(name="Dublin", slug="ie--dublin", country_code="IE", aliases=["dublin", "ireland", "dub", "都柏林"]),
    CityPreset(name="Zurich", slug="ch--zurich", country_code="CH", aliases=["zurich", "switzerland", "zrh", "苏黎世"]),
    CityPreset(name="Munich", slug="de--munich", country_code="DE", aliases=["munich", "muc", "慕尼黑"]),
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
    If matched against presets (including multilingual aliases), returns the canonical slug.
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
    
    # Check simplified whitespace / punctuation (unicode-safe)
    simplified = re.sub(r"[\s\-_,.]+", "", norm)
    if simplified:
        for k, preset in _LOOKUP.items():
            if re.sub(r"[\s\-_,.]+", "", k) == simplified:
                return preset.slug
            
    # Fallback to the user's plain query (Meetup SSR accepts plain city names)
    return clean


def get_preset(query: str) -> Optional[CityPreset]:
    """Find a preset by name, slug, or alias."""
    if not query:
        return None
    norm = query.strip().lower()
    if norm in _LOOKUP:
        return _LOOKUP[norm]
    simplified = re.sub(r"[\s\-_,.]+", "", norm)
    if simplified:
        for k, preset in _LOOKUP.items():
            if re.sub(r"[\s\-_,.]+", "", k) == simplified:
                return preset
    return None
