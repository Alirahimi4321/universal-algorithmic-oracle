"""Jalali core wrapper - low-level Persian calendar calculations."""
from __future__ import annotations

import logging
from typing import Optional

from oracle.symbolic.base import SymbolicOutput
from ..registry import register_system

logger = logging.getLogger(__name__)

try:
    import jalali_core
    HAS_JALALI_CORE = True
except ImportError:
    HAS_JALALI_CORE = False
    logger.info("jalali_core not available")


@register_system
class JalaliCoreWrapper:
    """Wrapper for jalali_core Persian calendar."""
    SYSTEM_ID = "jalali_core"

    def __init__(self) -> None:
        self.available: bool = HAS_JALALI_CORE

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        if not self.available:
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="jalali_core", raw_output={"error": "jalali_core not available"})

        try:
            from datetime import datetime
            today = datetime.now()

            jy, jm, jd = jalali_core.GregorianToJalali(
                today.year, today.month, today.day
            ).getJalaliList()

            numeric = [
                jy / 1400.0,
                jm / 12.0,
                jd / 31.0,
                today.hour / 24.0,
            ]

            symbolic_state = {
                "jalali_year": jy,
                "jalali_month": jm,
                "jalali_day": jd,
                "month_name_jalali": [
                    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
                ][jm - 1] if 1 <= jm <= 12 else "unknown",
            }

            return SymbolicOutput(
                system_id=self.SYSTEM_ID,
                library_backend="jalali_core",
                symbolic_state=symbolic_state,
                numeric_projection=numeric,
                structural_features={},
            )
        except Exception as e:
            logger.warning(f"jalali_core computation failed: {e}")
            return SymbolicOutput(system_id=self.SYSTEM_ID, library_backend="jalali_core", raw_output={"error": str(e)})
