"""Chinese number conversion wrapper using cn2an."""
import time
from ..base import SymbolicSystemWrapper, SymbolicOutput
from ..registry import register_system

try:
    import cn2an
    CN2AN_AVAILABLE = True
except ImportError:
    CN2AN_AVAILABLE = False


@register_system
class Cn2AnWrapper(SymbolicSystemWrapper):
    SYSTEM_ID = "cn2an"
    LIBRARY_BACKEND = "cn2an"

    def compute(self, entropy_packet: dict, params: dict | None = None) -> SymbolicOutput:
        params = params or {}
        text = entropy_packet.get("normalized_text", "")
        seed = entropy_packet.get("seed", 0)

        cn2an_val = 0
        an2cn_val = ""
        transform_result = ""

        if CN2AN_AVAILABLE:
            try:
                cn2an_val = cn2an.cn2an(text, "direct")
            except Exception:
                pass
            try:
                digits = "".join(c for c in text if c.isdigit())
                if digits:
                    an2cn_val = cn2an.an2cn(digits)
            except Exception:
                pass
            try:
                transform_result = str(cn2an.transform(text))
            except Exception:
                pass

        digit_sum = sum(int(d) for d in str(abs(cn2an_val))) if cn2an_val else 0
        reduced = cn2an_val
        while reduced >= 10 and reduced > 0:
            reduced = sum(int(d) for d in str(reduced))

        symbolic_state = {
            "input": text,
            "cn2an_value": cn2an_val,
            "an2cn_value": an2cn_val,
            "transform": transform_result,
            "digit_sum": digit_sum,
            "reduced": reduced,
        }
        numeric_projection = [cn2an_val, digit_sum, reduced, len(text), seed % 1000]
        structural_features = {
            "has_chinese_digits": any(c in text for c in "零一二三四五六七八九十百千万亿"),
            "has_arabic_digits": any(c.isdigit() for c in text),
            "value_magnitude": len(str(cn2an_val)) if cn2an_val else 0,
        }
        return self._build_output(
            symbolic_state=symbolic_state,
            numeric_projection=numeric_projection,
            structural_features=structural_features,
            params=params,
        )
