"""Western Astrology wrapper using pyswisseph + kerykeion."""
import math
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import swisseph as swe
    swe.set_ephe_path(None)
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False

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

PLANETS_INTERNAL = {
    0: "Sun", 1: "Moon", 2: "Mercury", 3: "Venus", 4: "Mars",
    5: "Jupiter", 6: "Saturn", 7: "Uranus", 8: "Neptune", 9: "Pluto",
}

ASPECT_DEGREES = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition"}
ASPECT_ORBS = {"conjunction": 8, "sextile": 6, "square": 8, "trine": 8, "opposition": 10}

def _get_planets():
    if SWISSEPH_AVAILABLE:
        return {swe.SUN: "Sun", swe.MOON: "Moon", swe.MERCURY: "Mercury",
                swe.VENUS: "Venus", swe.MARS: "Mars", swe.JUPITER: "Jupiter",
                swe.SATURN: "Saturn", swe.URANUS: "Uranus", swe.NEPTUNE: "Neptune",
                swe.PLUTO: "Pluto"}
    return PLANETS_INTERNAL


@register_system
class WesternAstrologyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "astrology_western"
    LIBRARY_BACKEND = "pyswisseph" if SWISSEPH_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)

        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)
        minute = cal_ctx.get("minute", 0)
        lat = params.get("lat", 35.6892)
        lon = params.get("lon", 51.3890)
        house_system = params.get("house_system", b'P')

        if SWISSEPH_AVAILABLE:
            try:
                return self._compute_swisseph(year, month, day, hour, minute, lat, lon, house_system, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, hour, seed, params)

    def _compute_swisseph(self, year, month, day, hour, minute, lat, lon, house_system, seed, params):
        julian_day = swe.julday(year, month, day, hour + minute / 60.0)
        planetary_positions = {}
        planet_longitudes = {}
        planets_map = _get_planets()

        for planet_id, planet_name in planets_map.items():
            try:
                result = swe.calc_ut(julian_day, planet_id)
                if result and len(result[0]) > 0:
                    lon_val = result[0][0]
                    sign_idx = int(lon_val / 30)
                    sign = ZODIAC_SIGNS[sign_idx % 12]
                    degree_in_sign = lon_val % 30
                    planetary_positions[planet_name] = {
                        "sign": sign, "degree": round(degree_in_sign, 2),
                        "longitude": round(lon_val, 4),
                        "element": ELEMENTS.get(sign, "Unknown"),
                    }
                    planet_longitudes[planet_name] = lon_val
            except Exception:
                planetary_positions[planet_name] = {"sign": "Unknown", "degree": 0, "longitude": 0, "element": "Unknown"}

        try:
            houses_cusps, ascmc = swe.houses(julian_day, lat, lon, house_system[0] if isinstance(house_system, bytes) else ord(house_system[0]))
            houses = {}
            for i, cusp in enumerate(houses_cusps[:12]):
                sign_idx = int(cusp / 30)
                houses[i + 1] = {"cusp_degree": round(cusp, 2), "sign": ZODIAC_SIGNS[sign_idx % 12]}
            ascendant = ascmc[0]
            mc = ascmc[1]
        except Exception:
            houses = {i: {"cusp_degree": 0, "sign": "Unknown"} for i in range(1, 13)}
            ascendant = 0
            mc = 0

        aspects = []
        planet_names = list(planet_longitudes.keys())
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                p1, p2 = planet_names[i], planet_names[j]
                diff = abs(planet_longitudes[p1] - planet_longitudes[p2])
                if diff > 180:
                    diff = 360 - diff
                for asp_deg, asp_name in ASPECT_DEGREES.items():
                    orb = ASPECT_ORBS.get(asp_name, 8)
                    if abs(diff - asp_deg) <= orb:
                        aspects.append({"planets": [p1, p2], "type": asp_name, "orb": round(abs(diff - asp_deg), 2)})

        sun_sign = planetary_positions.get("Sun", {}).get("sign", "Unknown")
        moon_sign = planetary_positions.get("Moon", {}).get("sign", "Unknown")
        rising_sign = ZODIAC_SIGNS[int(ascendant / 30) % 12] if ascendant else "Unknown"

        symbolic_state = {
            "sun_sign": sun_sign, "moon_sign": moon_sign, "rising_sign": rising_sign,
            "planetary_positions": planetary_positions, "houses": houses, "aspects": aspects,
            "ascendant": round(ascendant, 2), "mc": round(mc, 2),
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for pname, pdata in planetary_positions.items():
            elem = pdata.get("element", "Fire")
            if elem in element_count:
                element_count[elem] += 1

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign) if sun_sign in ZODIAC_SIGNS else 0,
            ZODIAC_SIGNS.index(moon_sign) if moon_sign in ZODIAC_SIGNS else 0,
            ZODIAC_SIGNS.index(rising_sign) if rising_sign in ZODIAC_SIGNS else 0,
            round(ascendant, 2), round(mc, 2),
            len(aspects), sum(element_count.values()),
            seed % 1000,
        ]

        structural_features = {
            "element_balance": max(element_count.values()) / max(sum(element_count.values()), 1),
            "cardinal_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Aries", "Cancer", "Libra", "Capricorn"]),
            "fixed_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Taurus", "Leo", "Scorpio", "Aquarius"]),
            "mutable_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Gemini", "Virgo", "Sagittarius", "Pisces"]),
            "aspect_density": len(aspects) / max(len(planetary_positions), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state, numeric_projection=numeric_projection,
            structural_features=structural_features, params=params,
        )

    def _compute_internal(self, year, month, day, hour, seed, params):
        import hashlib
        h = hashlib.sha256(f"{year}{month}{day}{hour}{seed}".encode()).digest()
        sun_idx = ((month - 1) * 2 + (1 if day > 15 else 0)) % 12
        sun_sign = ZODIAC_SIGNS[sun_idx]
        moon_sign = ZODIAC_SIGNS[h[0] % 12]
        rising_sign = ZODIAC_SIGNS[(h[1] + hour) % 12]

        planetary_positions = {}
        planets_map = _get_planets()
        for i, (pid, pname) in enumerate(planets_map.items()):
            idx = (h[i % len(h)] + i * 3) % 12
            sign = ZODIAC_SIGNS[idx]
            planetary_positions[pname] = {
                "sign": sign, "degree": round((h[(i+2) % len(h)] % 30), 2),
                "longitude": round(idx * 30 + (h[(i+3) % len(h)] % 30), 4),
                "element": ELEMENTS.get(sign, "Unknown"),
            }

        houses = {}
        for i in range(1, 13):
            idx = (h[i % len(h)] + i) % 12
            houses[i] = {"cusp_degree": round(idx * 30 + (h[(i+1) % len(h)] % 30), 2), "sign": ZODIAC_SIGNS[idx]}

        aspects = []
        signs_list = list(planetary_positions.values())
        for i in range(len(signs_list)):
            for j in range(i + 1, len(signs_list)):
                diff = abs(ZODIAC_SIGNS.index(signs_list[i]["sign"]) - ZODIAC_SIGNS.index(signs_list[j]["sign"]))
                if diff > 6:
                    diff = 12 - diff
                if diff == 0:
                    aspects.append({"planets": [list(planetary_positions.keys())[i], list(planetary_positions.keys())[j]], "type": "conjunction"})
                elif diff == 3:
                    aspects.append({"planets": [list(planetary_positions.keys())[i], list(planetary_positions.keys())[j]], "type": "square"})
                elif diff == 4:
                    aspects.append({"planets": [list(planetary_positions.keys())[i], list(planetary_positions.keys())[j]], "type": "trine"})

        symbolic_state = {
            "sun_sign": sun_sign, "moon_sign": moon_sign, "rising_sign": rising_sign,
            "planetary_positions": planetary_positions, "houses": houses, "aspects": aspects,
            "ascendant": round(h[4] * 30 / 255, 2), "mc": round(h[5] * 30 / 255, 2),
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for pname, pdata in planetary_positions.items():
            elem = pdata.get("element", "Fire")
            if elem in element_count:
                element_count[elem] += 1

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign), ZODIAC_SIGNS.index(moon_sign), ZODIAC_SIGNS.index(rising_sign),
            symbolic_state["ascendant"], symbolic_state["mc"],
            len(aspects), sum(element_count.values()), seed % 1000,
        ]

        structural_features = {
            "element_balance": max(element_count.values()) / max(sum(element_count.values()), 1),
            "cardinal_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Aries", "Cancer", "Libra", "Capricorn"]),
            "fixed_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Taurus", "Leo", "Scorpio", "Aquarius"]),
            "mutable_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Gemini", "Virgo", "Sagittarius", "Pisces"]),
            "aspect_density": len(aspects) / max(len(planetary_positions), 1),
        }

        return self._build_output(
            symbolic_state=symbolic_state, numeric_projection=numeric_projection,
            structural_features=structural_features, params=params,
        )

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
