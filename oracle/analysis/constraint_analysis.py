"""Constraint satisfaction solver using python-constraint."""
import logging

logger = logging.getLogger(__name__)

HAS_CONSTRAINT = False
try:
    from constraint import Problem, AllDifferentConstraint, Constraint
    HAS_CONSTRAINT = True
except ImportError:
    pass


class ConstraintSolver:
    """Solve constraint satisfaction problems."""

    def __init__(self):
        self.available = HAS_CONSTRAINT

    def solve(self, variables: dict, constraints_list: list = None) -> dict:
        if not self.available:
            return {"error": "constraint not available"}
        try:
            problem = Problem()
            for var_name, domain in variables.items():
                problem.addVariables(var_name, domain)

            if constraints_list:
                for c in constraints_list:
                    if c.get("type") == "alldifferent":
                        problem.addConstraint(AllDifferentConstraint(), c.get("variables", []))
                    elif c.get("function"):
                        func = eval(c["function"]) if isinstance(c["function"], str) else c["function"]
                        problem.addConstraint(func, c.get("variables", []))

            solutions = problem.getSolutions()
            return {
                "num_solutions": len(solutions),
                "solutions": solutions[:100],
                "variables": list(variables.keys()),
            }
        except Exception as e:
            logger.warning("constraint solver failed: %s", e)
            return {"error": str(e)}

    def analyze(self, data: dict) -> dict:
        variables = data.get("variables", {})
        constraints_list = data.get("constraints", [])
        return self.solve(variables, constraints_list)
