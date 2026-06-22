"""Evolutionary engines collection - all engines from document section 12.

Uses lazy imports to avoid slow startup.
"""
import importlib

_LAZY_IMPORTS = {
    # 12.1 Genetic Algorithms
    "PyGADEngine": (".pygad_engine", "PyGADEngine"),
    "GeneticAlgorithm2Engine": (".geneticalgorithm2_engine", "GeneticAlgorithm2Engine"),
    "PyEasyGAEngine": (".pyeasyga_engine", "PyEasyGAEngine"),
    "InspyredEngine": (".inspyred_engine", "InspyredEngine"),
    # 12.2 Genetic Programming
    "GPlearnEngine": (".gplearn_engine", "GPlearnEngine"),
    "TpotEngine": (".tpot_engine", "TpotEngine"),
    "KarooGPEngine": (".karoo_engine", "KarooGPEngine"),
    # 12.3 Evolution Strategies
    "NevergradEngine": (".nevergrad_engine", "NevergradEngine"),
    "EvosaxEngine": (".evosax_engine", "EvosaxEngine"),
    "PyGMOEngine": (".pygmo_engine", "PyGMOEngine"),
    # 12.4 Differential Evolution / 12.5 MOEA
    "PyMOOEngine": (".pymoo_engine", "PyMOOEngine"),
    # 12.6 Swarm Intelligence
    "PySwarmEngine": (".pyswarm_engine", "PySwarmEngine"),
    "MealpyEngine": (".mealpy_engine", "MealpyEngine"),
    "NiaPyEngine": (".niapy_engine", "NiaPyEngine"),
    # 12.7 Metaheuristics
    "PyMetaheuristicEngine": (".pymetaheuristic_engine", "PyMetaheuristicEngine"),
    # 12.8 Neuroevolution
    "NEATEngine": (".neat_engine", "NEATEngine"),
    # NEW: Stochopy (CMA-ES/DE/PSO)
    "StochopyEngine": (".stochopy_engine", "StochopyEngine"),
    # NEW: Psopy (fast PSO)
    "PsopyEngine": (".psopy_engine", "PsopyEngine"),
    # NEW: Evogine (GA/CMA-ES/DE/Island/NSGA/MAP-Elites)
    "EvogineEngine": (".evogine_engine", "EvogineEngine"),
    # NEW: CMA library
    "CMAEngine": (".cma_engine", "CMAEngine"),
    # NEW: Bayesian Optimization
    "BayesianOptEngine": (".bayesian_engine", "BayesianOptEngine"),
    # NEW: DirectSearch (direct search optimization)
    "DirectSearchEngine": (".directsearch_engine", "DirectSearchEngine"),
}

__all__ = list(_LAZY_IMPORTS.keys())


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        try:
            mod = importlib.import_module(module_path, package=__name__)
            return getattr(mod, attr_name)
        except Exception as e:
            raise ImportError(f"Could not import {name} from {module_path}: {e}") from e
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(__all__)
