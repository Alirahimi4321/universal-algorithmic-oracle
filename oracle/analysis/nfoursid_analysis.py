"""State Space System Identification using N4SID (nfoursid)."""
import logging
import numpy as np

logger = logging.getLogger(__name__)

HAS_NFOURSID = False
try:
    from nfoursid.nfoursid import NFourSID
    HAS_NFOURSID = True
except ImportError:
    pass


class StateSpaceAnalyzer:
    """Identify state-space models from time series data using N4SID."""

    def __init__(self):
        self.available = HAS_NFOURSID

    def identify(self, output_data: list[list[float]], n_markov: int = 20, n_block: int = 30) -> dict:
        if not self.available:
            return {"error": "nfoursid not available"}
        try:
            arr = np.array(output_data, dtype=float)
            nf = NFourSID()
            nf.set_input_output_data(output=arr)
            nf.subspace_identification(n_markov=n_markov, n_block=n_block)
            return {
                "status": "success",
                "data_length": len(arr),
                "n_markov": n_markov,
                "n_block": n_block,
                "method": "N4SID",
            }
        except Exception as e:
            return {"error": str(e)}
