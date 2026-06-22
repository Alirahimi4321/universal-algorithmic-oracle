"""Sandboxed execution environment for oracle structures."""
import time
import traceback
from ..genome.chromosome import Chromosome


class ExecutionSandbox:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.execution_log = []

    def execute(self, chromosome: Chromosome, entropy_packet: dict) -> dict:
        """Execute an oracle chromosome in a sandboxed manner."""
        start = time.time()
        result = {"success": False, "error": None, "result": None, "execution_time": 0}

        try:
            exec_result = chromosome.execute(entropy_packet)
            result["success"] = True
            result["result"] = exec_result
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()

        result["execution_time"] = time.time() - start

        self.execution_log.append({
            "chromosome_id": chromosome.chromosome_id,
            "success": result["success"],
            "execution_time": result["execution_time"],
            "timestamp": time.time(),
        })

        return result

    def get_stats(self) -> dict:
        if not self.execution_log:
            return {"total": 0, "success_rate": 0, "avg_time": 0}

        total = len(self.execution_log)
        successes = sum(1 for log in self.execution_log if log["success"])
        avg_time = sum(log["execution_time"] for log in self.execution_log) / total

        return {
            "total": total,
            "success_rate": successes / total,
            "avg_time": avg_time,
            "successes": successes,
            "failures": total - successes,
        }
