"""Lunar MCP Server wrapper - Chinese lunar calendar calculations."""
from __future__ import annotations

import logging
from typing import Any

from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    from zhdate import ZhDate
    HAS_LUNAR_MCP = True
except ImportError:
    HAS_LUNAR_MCP = False
    logger.info("lunar_mcp_server (zhdate) not available")

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ANIMALS = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
           "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]


@register_system
class LunarMCPWrapper(SymbolicSystemWrapper):
    """Wrapper for lunar_mcp_server (zhdate) Chinese lunar calendar."""
    SYSTEM_ID = "lunar_mcp"
    LIBRARY_BACKEND = "zhdate"

    def __init__(self) -> None:
        self.available: bool = HAS_LUNAR_MCP

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return self._build_output({}, [], {}, {"error": "lunar_mcp not available"}, params)

        try:
            import hashlib
            from datetime import date
            seed = entropy_packet.get("seed", 42) if isinstance(entropy_packet, dict) else 42
            hash_val = int(hashlib.md5(str(seed).encode()).hexdigest()[:8], 16)

            year = 1970 + (hash_val % 55)
            month = 1 + (hash_val % 12)
            day = 1 + (hash_val % 28)

            try:
                lunar = ZhDate.from_datetime(date(year, month, day))
                lunar_data = {
                    "lunar_year": lunar.lunar_year,
                    "lunar_month": lunar.lunar_month,
                    "lunar_day": lunar.lunar_day,
                    "is_leap_month": lunar.leap_month if hasattr(lunar, 'leap_month') else False,
                }
            except Exception:
                lunar_data = {"lunar_year": year, "lunar_month": month, "lunar_day": day}

            stem_idx = (hash_val % 10)
            branch_idx = (hash_val % 12)
            animal_idx = branch_idx

            numeric = [
                lunar_data.get("lunar_year", year) % 10 / 10.0,
                lunar_data.get("lunar_month", month) / 12.0,
                lunar_data.get("lunar_day", day) / 30.0,
                stem_idx / 10.0,
                branch_idx / 12.0,
            ]

            return self._build_output(
                symbolic_state={
                    "lunar_data": lunar_data,
                    "heavenly_stem": STEMS[stem_idx],
                    "earthly_branch": BRANCHES[branch_idx],
                    "animal": ANIMALS[animal_idx],
                    "stem_index": stem_idx,
                    "branch_index": branch_idx,
                },
                numeric_projection=numeric,
                structural_features={"has_lunar_data": bool(lunar_data)},
                raw_output={"lunar": lunar_data},
                params=params,
            )
        except Exception as e:
            logger.warning("lunar_mcp computation failed: %s", e)
            return self._build_output({}, [], {}, {"error": str(e)}, params)
