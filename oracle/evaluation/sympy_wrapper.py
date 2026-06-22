"""SymPy wrapper - symbolic mathematics for oracle computations."""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import sympy
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False
    logger.info("sympy not available")


class SymPyWrapper:
    """Wrapper for SymPy symbolic mathematics."""
    SYSTEM_ID = "sympy"

    def __init__(self) -> None:
        self.available: bool = HAS_SYMPY

    def symbolic_analysis(self, numbers: list[float]) -> dict[str, Any]:
        """Analyze numbers using symbolic mathematics."""
        if not self.available:
            return {"error": "sympy not available"}

        try:
            x = sympy.Symbol('x')

            ratios = []
            for i in range(len(numbers) - 1):
                if numbers[i] != 0:
                    ratios.append(numbers[i+1] / numbers[i])

            golden = float(sympy.Float(sympy.GoldenRatio))
            pi = float(sympy.pi)
            e = float(sympy.E)
            phi = float(sympy.sqrt(5) + 1) / 2

            deviations = [abs(r - golden) for r in ratios] if ratios else [0]

            return {
                "golden_ratio": golden,
                "pi": pi,
                "euler_e": e,
                "phi": phi,
                "ratios": ratios[:5],
                "golden_deviation": sum(deviations) / max(len(deviations), 1),
                "has_golden_pattern": any(d < 0.01 for d in deviations),
            }
        except Exception as e:
            logger.warning(f"sympy analysis failed: {e}")
            return {"error": str(e)}

    def prime_analysis(self, n: int) -> dict[str, Any]:
        """Analyze number n for prime properties."""
        if not self.available:
            return {"error": "sympy not available"}

        try:
            is_prime = sympy.isprime(n)
            factors = list(sympy.factorint(n).keys()) if n > 1 else []
            primes_below = list(sympy.primerange(0, min(n, 100)))

            return {
                "number": n,
                "is_prime": is_prime,
                "factors": factors,
                "primes_below_count": len(primes_below),
                "prime_sum": sum(primes_below),
            }
        except Exception as e:
            logger.warning(f"sympy prime analysis failed: {e}")
            return {"error": str(e)}
