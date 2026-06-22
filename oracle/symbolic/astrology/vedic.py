"""Vedic (Jyotish) astrology wrapper using pyswisseph for planetary positions."""
import math
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import swisseph as swe
    swe.set_ephe_path(None)
    PYWISSWEPH_AVAILABLE = True
except ImportError:
    PYWISSWEPH_AVAILABLE = False

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

TITHIS = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya",
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
    "Kimstughna", "Shakuni", "Chatushpada", "Nagloita", "Kimstughna",
    "Bava", "Balava", "Kaulava", "Taitila", "Gara",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Nagloita",
]

PLANETS = {
    "Sun": swe.SUN if PYWISSWEPH_AVAILABLE else 0,
    "Moon": swe.MOON if PYWISSWEPH_AVAILABLE else 1,
    "Mars": swe.MARS if PYWISSWEPH_AVAILABLE else 4,
    "Mercury": swe.MERCURY if PYWISSWEPH_AVAILABLE else 2,
    "Jupiter": swe.JUPITER if PYWISSWEPH_AVAILABLE else 5,
    "Venus": swe.VENUS if PYWISSWEPH_AVAILABLE else 3,
    "Saturn": swe.SATURN if PYWISSWEPH_AVAILABLE else 6,
    "Rahu": 10 if PYWISSWEPH_AVAILABLE else 10,
    "Ketu": 11 if PYWISSWEPH_AVAILABLE else 11,
}


@register_system
class VedicAstrologyWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "astrology_vedic"
    LIBRARY_BACKEND = "pyswisseph" if PYWISSWEPH_AVAILABLE else "internal"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        if PYWISSWEPH_AVAILABLE:
            try:
                return self._compute_with_swe(entropy_packet, params)
            except Exception:
                pass
        return self._compute_internal(entropy_packet, params)

    def _longitude_to_rashi(self, lon: float) -> str:
        idx = int(lon / 30) % 12
        return RASHIS[idx]

    def _longitude_to_nakshatra(self, lon: float) -> str:
        nak_size = 360 / 27
        idx = int(lon / nak_size) % 27
        return NAKSHATRAS[idx]

    def _longitude_to_tithi(self, sun_lon: float, moon_lon: float) -> str:
        diff = (moon_lon - sun_lon) % 360
        tithi_idx = int(diff / 12) % 30
        return TITHIS[tithi_idx]

    def _compute_with_swe(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        cal_ctx = entropy_packet.get("calendar_context", {})
        seed = entropy_packet.get("seed", 0)
        year = cal_ctx.get("year", 2024)
        month = cal_ctx.get("month", 1)
        day = cal_ctx.get("day", 1)
        hour = cal_ctx.get("hour", 12)
        lat = params.get("lat", 28.6139)
        lon = params.get("lon", 77.2090)

        julian_day = swe.julday(year, month, day, hour)

        planetary_positions = {}
        planet_longitudes = {}
        for pname, planet_id in PLANETS.items():
            if pname in ("Rahu", "Ketu"):
                continue
            try:
                result = swe.calc_ut(julian_day, planet_id)
                if result and len(result[0]) > 0:
                    p_lon = result[0][0]
                    rashi = self._longitude_to_rashi(p_lon)
                    nakshatra = self._longitude_to_nakshatra(p_lon)
                    planetary_positions[pname] = {
                        "longitude": round(p_lon, 4),
                        "rashi": rashi,
                        "nakshatra": nakshatra,
                        "degree_in_rashi": round(p_lon % 30, 2),
                    }
                    planet_longitudes[pname] = p_lon
            except Exception:
                planetary_positions[pname] = {"longitude": 0, "rashi": RASHIS[0], "nakshatra": NAKSHATRAS[0], "degree_in_rashi": 0}

        sun_lon = planet_longitudes.get("Sun", 0)
        moon_lon = planet_longitudes.get("Moon", 0)
        tithi = self._longitude_to_tithi(sun_lon, moon_lon)

        try:
            houses_cusps, ascmc = swe.houses(julian_day, lat, lon, ord('P'))
            asc_rashi = self._longitude_to_rashi(ascmc[0])
            asc_nakshatra = self._longitude_to_nakshatra(ascmc[0])
        except Exception:
            asc_rashi = RASHIS[0]
            asc_nakshatra = NAKSHATRAS[0]
            ascmc = [0] * 10

        yoga = YOGAS[seed % len(YOGAS)]
        karana = KARANAS[seed % len(KARANAS)]

        symbolic_state = {
            "planetary_positions": planetary_positions,
            "ascendant_rashi": asc_rashi,
            "ascendant_nakshatra": asc_nakshatra,
            "tithi": tithi,
            "yoga": yoga,
            "karana": karana,
            "birth_data": {"year": year, "month": month, "day": day, "hour": hour},
        }

        rashi_indices = [RASHIS.index(planetary_positions[p]["rashi"]) % 12 for p in planetary_positions if planetary_positions[p].get("rashi") in RASHIS]
        nak_indices = [NAKSHATRAS.index(planetary_positions[p]["nakshatra"]) % 27 for p in planetary_positions if planetary_positions[p].get("nakshatra") in NAKSHATRAS]

        numeric_projection = [
            rashi_indices[0] if rashi_indices else 0,
            rashi_indices[1] if len(rashi_indices) > 1 else 0,
            rashi_indices[2] if len(rashi_indices) > 2 else 0,
            RASHIS.index(asc_rashi) % 12,
            len(planetary_positions),
            len(nak_indices),
            sum(rashi_indices) % 12 if rashi_indices else 0,
            sum(nak_indices) % 27 if nak_indices else 0,
            TITHIS.index(tithi) % 30,
            YOGAS.index(yoga) % 27,
            seed % 1000,
            (year - 1911) % 60,
        ]

        structural_features = {
            "rashi_diversity": len(set(rashi_indices)) / 12 if rashi_indices else 0,
            "nakshatra_diversity": len(set(nak_indices)) / 27 if nak_indices else 0,
            "element_balance": len(set(rashi_indices)) / max(len(rashi_indices), 1),
            "planetary_count": len(planetary_positions),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )

    def _compute_internal(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        seed = entropy_packet.get("seed", 0)

        import hashlib
        h = hashlib.sha256(f"{seed}_vedic".encode()).digest()

        planetary_positions = {}
        planet_longitudes = {}
        planet_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        for i, pname in enumerate(planet_names):
            p_lon = (h[i] * 3 + h[i + 7] * 0.5) % 360
            rashi = self._longitude_to_rashi(p_lon)
            nakshatra = self._longitude_to_nakshatra(p_lon)
            planetary_positions[pname] = {
                "longitude": round(p_lon, 4),
                "rashi": rashi,
                "nakshatra": nakshatra,
                "degree_in_rashi": round(p_lon % 30, 2),
            }
            planet_longitudes[pname] = p_lon

        sun_lon = planet_longitudes.get("Sun", 0)
        moon_lon = planet_longitudes.get("Moon", 0)
        tithi = self._longitude_to_tithi(sun_lon, moon_lon)

        asc_lon = (h[14] * 3 + h[15] * 1.5) % 360
        asc_rashi = self._longitude_to_rashi(asc_lon)
        asc_nakshatra = self._longitude_to_nakshatra(asc_lon)

        yoga = YOGAS[h[16] % len(YOGAS)]
        karana = KARANAS[h[17] % len(KARANAS)]

        symbolic_state = {
            "planetary_positions": planetary_positions,
            "ascendant_rashi": asc_rashi,
            "ascendant_nakshatra": asc_nakshatra,
            "tithi": tithi,
            "yoga": yoga,
            "karana": karana,
        }

        rashi_indices = [RASHIS.index(planetary_positions[p]["rashi"]) % 12 for p in planetary_positions]
        nak_indices = [NAKSHATRAS.index(planetary_positions[p]["nakshatra"]) % 27 for p in planetary_positions]

        numeric_projection = [
            rashi_indices[0] if rashi_indices else 0,
            rashi_indices[1] if len(rashi_indices) > 1 else 0,
            rashi_indices[2] if len(rashi_indices) > 2 else 0,
            RASHIS.index(asc_rashi) % 12,
            len(planetary_positions),
            len(nak_indices),
            sum(rashi_indices) % 12 if rashi_indices else 0,
            sum(nak_indices) % 27 if nak_indices else 0,
            TITHIS.index(tithi) % 30,
            YOGAS.index(yoga) % 27,
            seed % 1000,
            len(RASHIS),
        ]

        structural_features = {
            "rashi_diversity": len(set(rashi_indices)) / 12,
            "nakshatra_diversity": len(set(nak_indices)) / 27,
            "element_balance": len(set(rashi_indices)) / max(len(rashi_indices), 1),
            "planetary_count": len(planetary_positions),
        }

        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
