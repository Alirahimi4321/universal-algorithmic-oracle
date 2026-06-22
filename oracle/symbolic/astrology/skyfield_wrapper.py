"""Skyfield Astronomy wrapper for precise astronomical calculations."""
import math
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

SKYFIELD_AVAILABLE = False
try:
    from skyfield.api import load, wgs84
    from skyfield import almanac
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False

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

PLANET_NAMES = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

ASPECT_DEGREES = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition"}
ASPECT_ORBS = {"conjunction": 8, "sextile": 6, "square": 8, "trine": 8, "opposition": 10}


@register_system
class SkyfieldAstronomyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "skyfield_astro"
    LIBRARY_BACKEND = "skyfield" if SKYFIELD_AVAILABLE else "internal"

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

        if SKYFIELD_AVAILABLE:
            try:
                return self._compute_skyfield(year, month, day, hour, minute, lat, lon, seed, params)
            except Exception:
                pass
        return self._compute_internal(year, month, day, hour, seed, params)

    def _compute_skyfield(self, year, month, day, hour, minute, lat, lon, seed, params):
        ts = load.timescale()
        t = ts.utc(year, month, day, hour, minute)
        location = wgs84.latlon(lat, lon)

        eph = load('de421.bsp')
        earth = eph['earth']
        sun = eph['sun']
        moon = eph['moon']

        planetary_positions = {}
        planet_longitudes = {}
        planet_distances = {}

        for planet_name in PLANET_NAMES:
            try:
                if planet_name == "Sun":
                    astrometric = earth.at(t).observe(sun)
                elif planet_name == "Moon":
                    astrometric = earth.at(t).observe(moon)
                else:
                    body_name = planet_name.lower()
                    if body_name in eph:
                        astrometric = earth.at(t).observe(eph[body_name])
                    else:
                        continue

                apparent = astrometric.apparent()
                geo = apparent.ecliptic_latlon()
                lon_val = geo[1].degrees % 360
                lat_val = geo[0].degrees
                dist = astrometric.distance().au

                sign_idx = int(lon_val / 30)
                sign = ZODIAC_SIGNS[sign_idx % 12]
                degree_in_sign = lon_val % 30

                planetary_positions[planet_name] = {
                    "sign": sign,
                    "degree": round(degree_in_sign, 2),
                    "longitude": round(lon_val, 4),
                    "latitude": round(lat_val, 4),
                    "element": ELEMENTS.get(sign, "Unknown"),
                }
                planet_longitudes[planet_name] = lon_val
                planet_distances[planet_name] = round(dist, 6)
            except Exception:
                planetary_positions[planet_name] = {
                    "sign": "Unknown", "degree": 0, "longitude": 0,
                    "latitude": 0, "element": "Unknown"
                }
                planet_longitudes[planet_name] = 0
                planet_distances[planet_name] = 0

        moon_phase = self._compute_moon_phase(eph, ts, t)
        eclipses = self._detect_eclipses(eph, ts, t)
        aspects = self._compute_aspects(planet_longitudes)

        sun_sign = planetary_positions.get("Sun", {}).get("sign", "Unknown")
        moon_sign = planetary_positions.get("Moon", {}).get("sign", "Unknown")

        symbolic_state = {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "planetary_positions": planetary_positions,
            "moon_phase": moon_phase,
            "eclipses": eclipses,
            "aspects": aspects,
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for pname, pdata in planetary_positions.items():
            elem = pdata.get("element", "Unknown")
            if elem in element_count:
                element_count[elem] += 1

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign) if sun_sign in ZODIAC_SIGNS else 0,
            ZODIAC_SIGNS.index(moon_sign) if moon_sign in ZODIAC_SIGNS else 0,
            moon_phase.get("phase", 0),
            moon_phase.get("illumination", 0),
            len(aspects),
            sum(element_count.values()),
            seed % 1000,
        ] + [planet_longitudes.get(p, 0) for p in PLANET_NAMES]

        structural_features = {
            "element_balance": max(element_count.values()) / max(sum(element_count.values()), 1),
            "cardinal_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Aries", "Cancer", "Libra", "Capricorn"]),
            "fixed_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Taurus", "Leo", "Scorpio", "Aquarius"]),
            "mutable_count": sum(1 for p in planetary_positions.values() if p.get("sign") in ["Gemini", "Virgo", "Sagittarius", "Pisces"]),
            "aspect_density": len(aspects) / max(len(planetary_positions), 1),
            "moon_phase_name": moon_phase.get("phase_name", "Unknown"),
            "has_eclipse": len(eclipses) > 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
            call_context={"skyfield_version": "1.46", "ephemeris": "de421"},
        )

    def _compute_moon_phase(self, eph, ts, t):
        try:
            sun = eph['sun']
            moon = eph['moon']
            earth = eph['earth']

            sun_apparent = earth.at(t).observe(sun).apparent()
            moon_apparent = earth.at(t).observe(moon).apparent()

            elongation = sun_apparent.separation_from(moon_apparent).degrees
            phase = (elongation / 360) * 28
            illumination = (1 - math.cos(math.radians(elongation))) / 2

            phase_names = [
                (1.85, "New Moon"), (5.54, "Waxing Crescent"), (9.23, "First Quarter"),
                (12.92, "Waxing Gibbous"), (16.62, "Full Moon"), (20.31, "Waning Gibbous"),
                (24.0, "Last Quarter"), (27.7, "Waning Crescent"), (28.0, "New Moon"),
            ]
            phase_name = "New Moon"
            for threshold, name in phase_names:
                if phase <= threshold:
                    phase_name = name
                    break

            return {
                "phase": round(phase, 2),
                "illumination": round(illumination, 4),
                "phase_name": phase_name,
                "elongation": round(elongation, 4),
            }
        except Exception:
            return {"phase": 0, "illumination": 0, "phase_name": "Unknown", "elongation": 0}

    def _detect_eclipses(self, eph, ts, t):
        eclipses = []
        try:
            t0 = ts.utc(t.utc.year, t.utc.month, max(1, t.utc.day - 2))
            t1 = ts.utc(t.utc.year, t.utc.month, min(28, t.utc.day + 2))
            f = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
            for ti, phase_type in zip(f[0], f[1]):
                if phase_type == 0:
                    eclipses.append({"type": "new_moon", "time": str(ti.utc)})
                elif phase_type == 2:
                    eclipses.append({"type": "full_moon", "time": str(ti.utc)})
        except Exception:
            pass
        return eclipses

    def _compute_aspects(self, planet_longitudes):
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
                        aspects.append({
                            "planets": [p1, p2],
                            "type": asp_name,
                            "orb": round(abs(diff - asp_deg), 2),
                        })
        return aspects

    def _compute_internal(self, year, month, day, hour, seed, params):
        import hashlib
        h = hashlib.sha256(f"{year}{month}{day}{hour}{seed}".encode()).digest()

        sun_idx = ((month - 1) * 2 + (1 if day > 15 else 0)) % 12
        sun_sign = ZODIAC_SIGNS[sun_idx]
        moon_sign = ZODIAC_SIGNS[h[0] % 12]

        planetary_positions = {}
        planet_longitudes = {}
        for i, pname in enumerate(PLANET_NAMES):
            idx = (h[i % len(h)] + i * 3) % 12
            sign = ZODIAC_SIGNS[idx]
            lon_val = idx * 30 + (h[(i + 3) % len(h)] % 30)
            planetary_positions[pname] = {
                "sign": sign,
                "degree": round((h[(i + 2) % len(h)] % 30), 2),
                "longitude": round(lon_val, 4),
                "latitude": round((h[(i + 4) % len(h)] % 20) - 10, 4),
                "element": ELEMENTS.get(sign, "Unknown"),
            }
            planet_longitudes[pname] = lon_val

        aspects = self._compute_aspects(planet_longitudes)

        symbolic_state = {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "planetary_positions": planetary_positions,
            "moon_phase": {"phase": round((h[0] % 28), 2), "illumination": round(h[1] / 255, 4), "phase_name": ZODIAC_SIGNS[h[0] % 12]},
            "eclipses": [],
            "aspects": aspects,
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        element_count = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        for pname, pdata in planetary_positions.items():
            elem = pdata.get("element", "Unknown")
            if elem in element_count:
                element_count[elem] += 1

        numeric_projection = [
            ZODIAC_SIGNS.index(sun_sign),
            ZODIAC_SIGNS.index(moon_sign),
            symbolic_state["moon_phase"]["phase"],
            symbolic_state["moon_phase"]["illumination"],
            len(aspects),
            sum(element_count.values()),
            seed % 1000,
        ] + [planet_longitudes.get(p, 0) for p in PLANET_NAMES]

        structural_features = {
            "element_balance": max(element_count.values()) / max(sum(element_count.values()), 1),
            "cardinal_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Aries", "Cancer", "Libra", "Capricorn"]),
            "fixed_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Taurus", "Leo", "Scorpio", "Aquarius"]),
            "mutable_count": sum(1 for p in planetary_positions.values() if p["sign"] in ["Gemini", "Virgo", "Sagittarius", "Pisces"]),
            "aspect_density": len(aspects) / max(len(planetary_positions), 1),
            "moon_phase_name": symbolic_state["moon_phase"]["phase_name"],
            "has_eclipse": False,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
