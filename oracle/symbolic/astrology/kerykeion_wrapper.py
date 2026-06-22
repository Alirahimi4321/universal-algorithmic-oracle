"""Western Astrology wrapper using kerykeion library."""
import hashlib
import math
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from kerykeion import AstrologicalSubject
    KERYKEION_AVAILABLE = True
except ImportError:
    KERYKEION_AVAILABLE = False

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

QUALITIES = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable",
}

PLANETS_KERYKEION = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]


@register_system
class KerykeionAstrologyWrapper(SymbolicSystemWrapper):
    """Western astrology computation using kerykeion library."""
    SYSTEM_ID = "astrology_kerykeion"
    LIBRARY_BACKEND = "kerykeion" if KERYKEION_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        cal_ctx = entropy_packet.get("calendar_context", {})
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)
        minute = cal_ctx.get("minute", 0)
        lat = params.get("lat", 35.6892)
        lon = params.get("lon", 51.3890)
        city = params.get("city", "Tehran")
        nation = params.get("nation", "IR")

        if KERYKEION_AVAILABLE:
            try:
                return self._compute_kerykeion(year, month, day, hour, minute, city, nation, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, hour, seed, params)

    def _compute_kerykeion(self, year, month, day, hour, minute, city, nation, seed, params):
        subject = AstrologicalSubject(
            name="Oracle",
            year=year, month=month, day=day, hour=hour, minute=minute,
            city=city, nation=nation,
        )

        planetary_positions = {}
        for planet in PLANETS_KERYKEION:
            try:
                p_data = getattr(subject, planet, None)
                if p_data and hasattr(p_data, 'sign'):
                    sign = p_data.sign
                    abs_pos = getattr(p_data, 'abs_pos', 0)
                    retro = getattr(p_data, 'retrograde', False)
                    planetary_positions[planet.capitalize()] = {
                        "sign": sign,
                        "degree": round(abs_pos % 30, 2),
                        "longitude": round(abs_pos, 4),
                        "element": ELEMENTS.get(sign, "Unknown"),
                        "quality": QUALITIES.get(sign, "Unknown"),
                        "retrograde": retro,
                    }
            except Exception:
                pass

        houses = {}
        try:
            houses_data = getattr(subject, 'houses', [])
            for i, house in enumerate(houses_data[:12], 1):
                if hasattr(house, 'sign'):
                    houses[i] = {
                        "sign": house.sign,
                        "cusp_degree": round(getattr(house, 'abs_pos', 0) % 30, 2),
                    }
        except Exception:
            pass

        aspects = []
        try:
            aspects_data = getattr(subject, 'aspects', [])
            for asp in aspects_data:
                aspects.append({
                    "planets": [getattr(asp, 'p1', ''), getattr(asp, 'p2', '')],
                    "type": getattr(asp, 'aspect_name', ''),
                    "orb": round(getattr(asp, 'orb', 0), 2),
                })
        except Exception:
            pass

        sun_sign = planetary_positions.get("Sun", {}).get("sign", "Unknown")
        moon_sign = planetary_positions.get("Moon", {}).get("sign", "Unknown")
        rising_sign = "Unknown"
        try:
            asc_data = getattr(subject, 'ascendant', None)
            if asc_data and hasattr(asc_data, 'sign'):
                rising_sign = asc_data.sign
        except Exception:
            pass

        symbolic_state = {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "planetary_positions": planetary_positions,
            "houses": houses,
            "aspects": aspects,
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour, "minute": minute},
            "location": {"city": city, "nation": nation},
        }

        element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for pdata in planetary_positions.values():
            elem = pdata.get("element", "Fire")
            if elem in element_count:
                element_count[elem] += 1

        quality_count = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
        for pdata in planetary_positions.values():
            qual = pdata.get("quality", "Cardinal")
            if qual in quality_count:
                quality_count[qual] += 1

        retrograde_count = sum(1 for p in planetary_positions.values() if p.get("retrograde", False))

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign) if sun_sign in ZODIAC_SIGNS else 0,
            ZODIAC_SIGNS.index(moon_sign) if moon_sign in ZODIAC_SIGNS else 0,
            ZODIAC_SIGNS.index(rising_sign) if rising_sign in ZODIAC_SIGNS else 0,
            retrograde_count,
            len(aspects),
            len(houses),
            sum(element_count.values()),
            sum(quality_count.values()),
            seed % 1000,
        ]

        structural_features = {
            "element_balance": max(element_count.values()) / max(sum(element_count.values()), 1),
            "quality_balance": max(quality_count.values()) / max(sum(quality_count.values()), 1),
            "cardinal_count": quality_count.get("Cardinal", 0),
            "fixed_count": quality_count.get("Fixed", 0),
            "mutable_count": quality_count.get("Mutable", 0),
            "aspect_density": len(aspects) / max(len(planetary_positions), 1),
            "retrograde_ratio": retrograde_count / max(len(planetary_positions), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, year, month, day, hour, seed, params):
        h = hashlib.sha256(f"kerykeion_{year}_{month}_{day}_{hour}_{seed}".encode()).digest()
        sun_idx = ((month - 1) * 2 + (1 if day > 15 else 0)) % 12
        sun_sign = ZODIAC_SIGNS[sun_idx]
        moon_sign = ZODIAC_SIGNS[h[0] % 12]
        rising_sign = ZODIAC_SIGNS[(h[1] + hour) % 12]

        planetary_positions = {}
        for i, planet in enumerate(PLANETS_KERYKEION):
            idx = (h[i % len(h)] + i * 3) % 12
            sign = ZODIAC_SIGNS[idx]
            planetary_positions[planet.capitalize()] = {
                "sign": sign,
                "degree": round(h[(i+2) % len(h)] % 30, 2),
                "longitude": round(idx * 30 + h[(i+3) % len(h)] % 30, 4),
                "element": ELEMENTS.get(sign, "Unknown"),
                "quality": QUALITIES.get(sign, "Unknown"),
                "retrograde": (h[i] % 4) == 0,
            }

        symbolic_state = {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "planetary_positions": planetary_positions,
        }

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign),
            ZODIAC_SIGNS.index(moon_sign),
            ZODIAC_SIGNS.index(rising_sign),
            sum(1 for p in planetary_positions.values() if p["retrograde"]),
            len(planetary_positions),
            seed % 1000,
        ]

        structural_features = {
            "element_balance": 0.25,
            "quality_balance": 0.33,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
