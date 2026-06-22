"""Yaegi (Vedic Astrology) wrapper for Kundali and Panchang generation."""
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    from yaegi import KundaliGenerator, PanchangGenerator
    YAEGI_AVAILABLE = True
except ImportError:
    YAEGI_AVAILABLE = False

RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
    "Tula (Libra)", "Vrischika (Scorpio)", "Dhanus (Sagittarius)",
    "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]


def _longitude_to_rashi(lon: float) -> str:
    idx = int(lon / 30) % 12
    return RASHIS[idx]


def _longitude_to_nakshatra(lon: float) -> str:
    nak_size = 360 / 27
    idx = int(lon / nak_size) % 27
    return NAKSHATRAS[idx]


def _extract_birth_params(entropy_packet: dict, params: dict | None) -> dict:
    params = params or {}
    cal_ctx = entropy_packet.get("calendar_context", {})
    return {
        "year": cal_ctx.get("year", 2024),
        "month": cal_ctx.get("month", 1),
        "day": cal_ctx.get("day", 1),
        "hour": cal_ctx.get("hour", 12),
        "minute": cal_ctx.get("minute", 0),
        "lat": params.get("lat", 28.6139),
        "lon": params.get("lon", 77.2090),
    }


def _parse_planetary_positions(raw_chart: dict) -> dict:
    positions = {}
    for planet_name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        data = raw_chart.get(planet_name, raw_chart.get(planet_name.lower(), {}))
        if isinstance(data, dict):
            lon = float(data.get("longitude", data.get("lon", 0)))
            positions[planet_name] = {
                "longitude": round(lon, 4),
                "rashi": _longitude_to_rashi(lon),
                "nakshatra": _longitude_to_nakshatra(lon),
                "degree_in_rashi": round(lon % 30, 2),
            }
        elif isinstance(data, (int, float)):
            lon = float(data)
            positions[planet_name] = {
                "longitude": round(lon, 4),
                "rashi": _longitude_to_rashi(lon),
                "nakshatra": _longitude_to_nakshatra(lon),
                "degree_in_rashi": round(lon % 30, 2),
            }
    return positions


@register_system
class YaegiKundaliWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "yaegi_kundali"
    LIBRARY_BACKEND = "yaegi"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if YAEGI_AVAILABLE:
            try:
                return self._compute_with_yaegi(entropy_packet, params)
            except Exception:
                pass
        return self._compute_fallback(entropy_packet, params)

    def _compute_with_yaegi(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        birth = _extract_birth_params(entropy_packet, params)

        gen = KundaliGenerator()
        raw_chart = gen.generate(
            year=birth["year"],
            month=birth["month"],
            day=birth["day"],
            hour=birth["hour"],
            minute=birth["minute"],
            lat=birth["lat"],
            lon=birth["lon"],
        )

        planetary_positions = _parse_planetary_positions(raw_chart)

        asc_lon = float(raw_chart.get("ascendant", raw_chart.get("asc", {}).get("longitude", 0)))
        asc_rashi = _longitude_to_rashi(asc_lon)
        asc_nakshatra = _longitude_to_nakshatra(asc_lon)

        sun_lon = planetary_positions.get("Sun", {}).get("longitude", 0)
        moon_lon = planetary_positions.get("Moon", {}).get("longitude", 0)
        tithi_idx = int(((moon_lon - sun_lon) % 360) / 12) % 30

        symbolic_state = {
            "planetary_positions": planetary_positions,
            "ascendant": {"longitude": round(asc_lon, 4), "rashi": asc_rashi, "nakshatra": asc_nakshatra},
            "tithi_index": tithi_idx,
            "birth_data": birth,
            "chart_type": "kundali",
        }

        rashi_indices = [RASHIS.index(v["rashi"]) % 12 for v in planetary_positions.values() if v.get("rashi") in RASHIS]
        nak_indices = [NAKSHATRAS.index(v["nakshatra"]) % 27 for v in planetary_positions.values() if v.get("nakshatra") in NAKSHATRAS]

        numeric_projection = [
            planetary_positions.get("Sun", {}).get("longitude", 0) / 360,
            planetary_positions.get("Moon", {}).get("longitude", 0) / 360,
            planetary_positions.get("Mars", {}).get("longitude", 0) / 360,
            asc_lon / 360,
            len(planetary_positions),
            sum(rashi_indices) % 12 if rashi_indices else 0,
            sum(nak_indices) % 27 if nak_indices else 0,
            tithi_idx / 30,
        ]

        structural_features = {
            "rashi_diversity": len(set(rashi_indices)) / 12 if rashi_indices else 0,
            "nakshatra_diversity": len(set(nak_indices)) / 27 if nak_indices else 0,
            "planetary_count": len(planetary_positions),
            "has_all_planets": 1 if len(planetary_positions) >= 7 else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=raw_chart if isinstance(raw_chart, dict) else {},
            params=params,
        )

    def _compute_fallback(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        import hashlib
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        birth = _extract_birth_params(entropy_packet, params)

        h = hashlib.sha256(f"{seed}_yaegi_kundali".encode()).digest()

        planetary_positions = {}
        planet_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        for i, pname in enumerate(planet_names):
            lon = (h[i] * 3 + h[i + 7] * 0.5) % 360
            planetary_positions[pname] = {
                "longitude": round(lon, 4),
                "rashi": _longitude_to_rashi(lon),
                "nakshatra": _longitude_to_nakshatra(lon),
                "degree_in_rashi": round(lon % 30, 2),
            }

        asc_lon = (h[14] * 3 + h[15] * 1.5) % 360
        asc_rashi = _longitude_to_rashi(asc_lon)
        asc_nakshatra = _longitude_to_nakshatra(asc_lon)

        sun_lon = planetary_positions.get("Sun", {}).get("longitude", 0)
        moon_lon = planetary_positions.get("Moon", {}).get("longitude", 0)
        tithi_idx = int(((moon_lon - sun_lon) % 360) / 12) % 30

        symbolic_state = {
            "planetary_positions": planetary_positions,
            "ascendant": {"longitude": round(asc_lon, 4), "rashi": asc_rashi, "nakshatra": asc_nakshatra},
            "tithi_index": tithi_idx,
            "birth_data": birth,
            "chart_type": "kundali",
            "fallback": True,
        }

        rashi_indices = [RASHIS.index(v["rashi"]) % 12 for v in planetary_positions.values()]
        nak_indices = [NAKSHATRAS.index(v["nakshatra"]) % 27 for v in planetary_positions.values()]

        numeric_projection = [
            sun_lon / 360,
            moon_lon / 360,
            planetary_positions.get("Mars", {}).get("longitude", 0) / 360,
            asc_lon / 360,
            len(planetary_positions),
            sum(rashi_indices) % 12 if rashi_indices else 0,
            sum(nak_indices) % 27 if nak_indices else 0,
            tithi_idx / 30,
        ]

        structural_features = {
            "rashi_diversity": len(set(rashi_indices)) / 12 if rashi_indices else 0,
            "nakshatra_diversity": len(set(nak_indices)) / 27 if nak_indices else 0,
            "planetary_count": len(planetary_positions),
            "has_all_planets": 1 if len(planetary_positions) >= 7 else 0,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )


@register_system
class YaegiPanchangWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "yaegi_panchang"
    LIBRARY_BACKEND = "yaegi"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if YAEGI_AVAILABLE:
            try:
                return self._compute_with_yaegi(entropy_packet, params)
            except Exception:
                pass
        return self._compute_fallback(entropy_packet, params)

    def _compute_with_yaegi(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        birth = _extract_birth_params(entropy_packet, params)
        seed = entropy_packet.get("seed", 0)

        gen = PanchangGenerator()
        raw_panchang = gen.generate(
            year=birth["year"],
            month=birth["month"],
            day=birth["day"],
            hour=birth["hour"],
            minute=birth["minute"],
            lat=birth["lat"],
            lon=birth["lon"],
        )

        tithi = raw_panchang.get("tithi", "Unknown")
        nakshatra = raw_panchang.get("nakshatra", "Unknown")
        yoga = raw_panchang.get("yoga", "Unknown")
        karana = raw_panchang.get("karana", "Unknown")
        vara = raw_panchang.get("vara", raw_panchang.get("day", "Unknown"))

        tithi_idx = 0
        nak_idx = 0
        for i, t in enumerate(["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
                                "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                                "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima"]):
            if tithi.startswith(t) or tithi == t:
                tithi_idx = i
                break

        symbolic_state = {
            "tithi": tithi,
            "nakshatra": nakshatra,
            "yoga": yoga,
            "karana": karana,
            "vara": vara,
            "birth_data": birth,
            "panchang_type": "panchang",
        }

        numeric_projection = [
            tithi_idx / 15,
            NAKSHATRAS.index(nakshatra) / 27 if nakshatra in NAKSHATRAS else 0,
            seed % 100 / 100,
            birth["lat"] / 90,
            birth["lon"] / 180,
            hash(tithi) % 100 / 100,
            hash(nakshatra) % 100 / 100,
            hash(yoga) % 100 / 100,
        ]

        structural_features = {
            "tithi_index": tithi_idx,
            "has_nakshatra": 1 if nakshatra and nakshatra != "Unknown" else 0,
            "has_yoga": 1 if yoga and yoga != "Unknown" else 0,
            "has_karana": 1 if karana and karana != "Unknown" else 0,
            "element_hash": hash(f"{tithi}_{nakshatra}") % 12,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            raw_output=raw_panchang if isinstance(raw_panchang, dict) else {},
            params=params,
        )

    def _compute_fallback(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        import hashlib
        params = params or {}
        seed = entropy_packet.get("seed", 0)
        birth = _extract_birth_params(entropy_packet, params)

        h = hashlib.sha256(f"{seed}_yaegi_panchang".encode()).digest()

        TITHIS = [
            "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
        ]
        YOGAS = [
            "Vishkambha", "Priti", "Ayushman", "Soubhagya", "Shobhana",
            "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
            "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
            "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
            "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
            "Indra", "Vaidhriti",
        ]
        KARANAS = [
            "Kimstughna", "Shakuni", "Chatushpada", "Nagloita",
            "Bava", "Balava", "Kaulava", "Taitila", "Gara",
            "Vanija", "Vishti",
        ]

        tithi_idx = h[0] % 15
        nak_idx = h[1] % 27
        yoga_idx = h[2] % 27
        karana_idx = h[3] % 11

        symbolic_state = {
            "tithi": TITHIS[tithi_idx],
            "nakshatra": NAKSHATRAS[nak_idx],
            "yoga": YOGAS[yoga_idx],
            "karana": KARANAS[karana_idx],
            "vara": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][h[4] % 7],
            "birth_data": birth,
            "panchang_type": "panchang",
            "fallback": True,
        }

        numeric_projection = [
            tithi_idx / 15,
            nak_idx / 27,
            yoga_idx / 27,
            karana_idx / 11,
            birth["lat"] / 90,
            birth["lon"] / 180,
            h[5] / 255,
            h[6] / 255,
        ]

        structural_features = {
            "tithi_index": tithi_idx,
            "has_nakshatra": 1,
            "has_yoga": 1,
            "has_karana": 1,
            "element_hash": (tithi_idx + nak_idx + yoga_idx) % 12,
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
