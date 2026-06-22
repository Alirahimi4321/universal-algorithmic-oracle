"""Notebook 01: Systems Overview - Show all registered symbolic systems and their capabilities."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all, list_systems, get_system


def main():
    register_all()
    systems = list_systems()

    print("=" * 70)
    print("  UNIVERSAL ALGORITHMIC ORACLE - Symbolic Systems Overview")
    print("=" * 70)
    print(f"\nTotal registered systems: {len(systems)}\n")

    categories = {
        "Astrology": [],
        "Gematria": [],
        "Cards": [],
        "Eastern": [],
        "Binary": [],
        "Divination": [],
        "Numerical": [],
        "Mayan": [],
        "Other": [],
    }

    for s in sorted(systems):
        if any(k in s for k in ["astrology", "vedic", "kundali", "panchang", "kerykeion",
                                  "flatlib", "ndastro", "libephemeris", "stellium", "jyotishganit",
                                  "ephem", "falak", "vedastro", "ketu", "astral", "skyfield", "yaegi"]):
            categories["Astrology"].append(s)
        elif any(k in s for k in ["gematria", "hebrew", "english_gematria", "numerology",
                                    "pythagorean", "figurate", "roman"]):
            categories["Gematria"].append(s)
        elif any(k in s for k in ["tarot", "arcanite", "runes", "lenormand", "ai_divination",
                                    "ai_tarot", "ai_iching", "ai_xiaoliuren", "fortune"]):
            categories["Cards"].append(s)
        elif any(k in s for k in ["bazi", "ziwei", "qimen", "tianji", "korean", "lunar",
                                    "hijri", "jalali", "sxtwl", "holidays", "lunar_mcp", "lunar_date"]):
            categories["Eastern"].append(s)
        elif any(k in s for k in ["iching", "geomancy", "ogham", "raml", "hafez"]):
            categories["Binary"].append(s)
        elif any(k in s for k in ["opendivination", "sixline", "divination"]):
            categories["Divination"].append(s)
        elif any(k in s for k in ["calendar", "tzolkin", "long_count", "pohualli", "mayacal"]):
            categories["Mayan"].append(s)
        else:
            categories["Other"].append(s)

    for cat, items in categories.items():
        if items:
            print(f"--- {cat} ({len(items)}) ---")
            for item in items:
                wrapper = get_system(item)
                if wrapper:
                    print(f"  {item:35s} backend={getattr(wrapper, 'BACKEND', 'unknown')}")
                else:
                    print(f"  {item:35s} (not loadable)")
            print()

    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    for cat, items in categories.items():
        if items:
            print(f"  {cat:15s}: {len(items)} systems")
    print(f"  {'TOTAL':15s}: {len(systems)} systems")
    print()


if __name__ == "__main__":
    main()
