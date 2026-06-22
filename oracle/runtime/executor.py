"""Main Pipeline Executor - ties all components together with support for all phases."""
import time
import json
import hashlib
from ..entropy.encoder import EntropyEncoder, EntropyPacket
from ..symbolic.registry import list_systems
from ..genome.chromosome import Chromosome
from ..genome.tree_genome import TreeGenome
from ..evolution.deap_engine import EvolutionaryEngine, AVAILABLE_SYSTEMS
from ..evolution.gp_engine import GPEngine
from ..evolution.nsga_engine import NSGAEngine
from ..evaluation.fitness import FitnessEvaluator
from ..memory.archive import EvolutionaryMemory
from ..memory.mutation_bank import MutationBank
from ..memory.experiment_ledger import ExperimentLedger
from ..output.oracle_output import OracleOutputBuilder, OracleOutput

# NEW: Enhanced engines
try:
    from ..evolution.engines.stochopy_engine import StochopyEngine
    HAS_STOCHOPY = True
except ImportError:
    HAS_STOCHOPY = False

try:
    from ..evolution.engines.psopy_engine import PsopyEngine
    HAS_PSOPY = True
except ImportError:
    HAS_PSOPY = False

try:
    from ..evolution.engines.evogine_engine import EvogineEngine
    HAS_EVOGINE = True
except ImportError:
    HAS_EVOGINE = False

# NEW: Correlation analyzer
try:
    from ..evaluation.correlation import SystemCorrelationAnalyzer
    HAS_CORRELATION = True
except ImportError:
    HAS_CORRELATION = False

# NEW: Graph analyzer
try:
    from ..evolution.graph_analysis import SystemGraphAnalyzer
    HAS_GRAPH = True
except ImportError:
    HAS_GRAPH = False

# NEW: Chaos analyzer
try:
    from ..evaluation.chaos_analysis import ChaosAnalyzer
    HAS_CHAOS = True
except ImportError:
    HAS_CHAOS = False

# NEW: Ketu astronomy
try:
    from ..symbolic.astrology.ketu_wrapper import KetuAstronomyWrapper
    HAS_KETU = True
except ImportError:
    HAS_KETU = False

# NEW: CMA engine (lazy - cma lib takes ~6s to import)
HAS_CMA = False
# NEW: Bayesian Optimization engine
HAS_BAYESIAN = False


class OraclePipeline:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.encoder = EntropyEncoder()
        self.memory = EvolutionaryMemory(self.config.get("memory_path", "data/oracle_memory.db"))
        # Ensure the data directory exists for the SQLite DB
        import os
        os.makedirs(os.path.dirname(self.config.get("memory_path", "data/oracle_memory.db")), exist_ok=True)
        self.mutation_bank = MutationBank(self.config.get("memory_path", "data/oracle_memory.db"))
        self.experiment_ledger = ExperimentLedger(self.config.get("memory_path", "data/oracle_memory.db"))
        self.output_builder = OracleOutputBuilder()
        self.ga_engine = EvolutionaryEngine(self.config.get("evolution", {}))
        self.gp_engine = GPEngine(self.config.get("evolution", {}))
        self.nsga_engine = NSGAEngine(self.config.get("evolution", {}))

        # NEW: Enhanced engines
        if HAS_STOCHOPY:
            self.stochopy_engine = StochopyEngine(self.config.get("evolution", {}))
        if HAS_PSOPY:
            self.psopy_engine = PsopyEngine(self.config.get("evolution", {}))
        if HAS_EVOGINE:
            self.evogine_engine = EvogineEngine(self.config.get("evolution", {}))
        
        # Lazy-init for heavy engines (cma takes ~6s, bayesian takes ~3s)
        self._cma_engine = None
        self._bayesian_engine = None

        # NEW: Analyzers
        if HAS_CORRELATION:
            self.correlation_analyzer = SystemCorrelationAnalyzer()
        if HAS_GRAPH:
            self.graph_analyzer = SystemGraphAnalyzer()
        if HAS_CHAOS:
            self.chaos_analyzer = ChaosAnalyzer()
        if HAS_KETU:
            self.ketu_wrapper = KetuAstronomyWrapper()

    def ask(
        self,
        question: str,
        timestamp: float | None = None,
        location: dict | None = None,
        extra_numbers: list[int] | None = None,
        generations: int = 50,
        engine: str = "ga",
    ) -> OracleOutput:
        from ..sanitizer import sanitize_question, sanitize_seed
        question = sanitize_question(question)
        if timestamp is not None:
            timestamp = float(sanitize_seed(int(timestamp * 1000))) / 1000.0

        entropy_packet = self.encoder.encode(question, timestamp, location, extra_numbers)
        ep_dict = self._packet_to_dict(entropy_packet)

        if engine == "gp":
            evolved = self._run_gp(ep_dict, generations)
        elif engine == "nsga":
            evolved = self._run_nsga(ep_dict, generations)
        elif engine == "stochopy" and HAS_STOCHOPY:
            evolved = self._run_stochopy(ep_dict, generations)
        elif engine == "psopy" and HAS_PSOPY:
            evolved = self._run_psopy(ep_dict, generations)
        elif engine == "evogine" and HAS_EVOGINE:
            evolved = self._run_evogine(ep_dict, generations)
        elif engine == "cma" and HAS_CMA:
            evolved = self._run_cma(ep_dict, generations)
        elif engine == "bayesian" and HAS_BAYESIAN:
            evolved = self._run_bayesian(ep_dict, generations)
        else:
            evolved = self._run_ga(ep_dict, generations)

        best = evolved[0] if evolved else None
        if best is None:
            return OracleOutput(
                answer="Evolution failed to produce a viable oracle.",
                disclaimer=OracleOutputBuilder.DISCLAIMER,
            )

        execution_result = best.execute(ep_dict)

        self._safe_save_chromosome(best)
        output = self.output_builder.build(best, execution_result, ep_dict)
        self._safe_register_experiment(question, entropy_packet, best, output)

        return output

    def _safe_save_chromosome(self, chromosome):
        """Save chromosome with proper error handling."""
        try:
            self.memory.save_chromosome(chromosome)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save chromosome: {e}")

    def _safe_register_experiment(self, question, entropy_packet, best, output):
        """Register experiment with proper error handling."""
        try:
            oracle_id = best.chromosome_id if isinstance(best, Chromosome) else getattr(best, 'genome_id', 'unknown')
            entropy_sig = ""
            if hasattr(entropy_packet, 'question_signature') and isinstance(entropy_packet.question_signature, dict):
                entropy_sig = entropy_packet.question_signature.get("hash_hex", "")
            graph_hash = hashlib.md5(json.dumps(best.to_dict(), default=str).encode()).hexdigest()[:16] if hasattr(best, 'to_dict') else ""
            self.experiment_ledger.register_experiment(
                question_text=question,
                entropy_signature=entropy_sig,
                oracle_id=oracle_id,
                oracle_version="0.1.0",
                oracle_graph_hash=graph_hash,
                prediction_payload=output.to_dict(),
                time_horizon="unknown",
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to register experiment: {e}")

    def ask_tree(
        self,
        question: str,
        timestamp: float | None = None,
        generations: int = 30,
    ) -> OracleOutput:
        entropy_packet = self.encoder.encode(question, timestamp)
        ep_dict = self._packet_to_dict(entropy_packet)

        self.gp_engine.initialize_population()
        evolved = self.gp_engine.evolve(ep_dict, generations=generations)

        best = evolved[0] if evolved else None
        if best is None:
            return OracleOutput(
                answer="GP evolution failed.",
                disclaimer=OracleOutputBuilder.DISCLAIMER,
            )

        execution_result = best.execute(ep_dict)
        return self._build_tree_output(best, execution_result, ep_dict)

    def _run_ga(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if not self.ga_engine.population:
            self.ga_engine.initialize_population()
        return self.ga_engine.evolve(ep_dict, generations=generations)

    def _run_gp(self, ep_dict: dict, generations: int) -> list:
        self.gp_engine.initialize_population()
        return self.gp_engine.evolve(ep_dict, generations=generations)

    def _run_nsga(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        return self.nsga_engine.evolve(ep_dict, generations=generations)

    def _run_stochopy(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if not self.stochopy_engine.population:
            self.stochopy_engine.initialize_population()
        return self.stochopy_engine.evolve(ep_dict, generations=generations)

    def _run_psopy(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if not self.psopy_engine.population:
            self.psopy_engine.initialize_population()
        return self.psopy_engine.evolve(ep_dict, generations=generations)

    def _run_evogine(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if not self.evogine_engine.population:
            self.evogine_engine.initialize_population()
        return self.evogine_engine.evolve(ep_dict, generations=generations)

    def _run_cma(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if self._cma_engine is None:
            from ..evolution.engines.cma_engine import CMAEngine
            self._cma_engine = CMAEngine(self.config.get("evolution", {}))
        if not self._cma_engine.population:
            self._cma_engine.initialize_population()
        return self._cma_engine.evolve(ep_dict, generations=generations)

    def _run_bayesian(self, ep_dict: dict, generations: int) -> list[Chromosome]:
        if self._bayesian_engine is None:
            from ..evolution.engines.bayesian_engine import BayesianOptEngine
            self._bayesian_engine = BayesianOptEngine(self.config.get("evolution", {}))
        if not self._bayesian_engine.population:
            self._bayesian_engine.initialize_population()
        return self._bayesian_engine.evolve(ep_dict, generations=generations)

    def _packet_to_dict(self, packet: EntropyPacket) -> dict:
        """Convert an :class:`EntropyPacket` to a plain ``dict`` using ``asdict``.

        Using ``dataclasses.asdict`` guarantees that **all** fields of the packet are
        included automatically, keeping the conversion in sync with any future
        changes to the dataclass definition.
        """
        from dataclasses import asdict
        return asdict(packet)

    def _build_tree_output(self, tree: TreeGenome, result: dict, ep_dict: dict) -> OracleOutput:
        systems = [n.system_id for n in tree.get_all_system_nodes() if n.system_id]
        confidence = result.get("oracle_confidence", 0.0)

        return OracleOutput(
            answer=self._generate_answer(result, confidence, systems),
            symbolic_answer={"phase": "evolved", "polarity": "dynamic"},
            numeric_signature=result.get("fused_numeric", [])[:20],
            oracle_confidence=confidence,
            dominant_systems=list(set(systems)),
            evolved_structure={"tree_depth": tree.depth, "tree_size": tree.size},
            explanation_trace=[f"Tree genome: depth={tree.depth}, size={tree.size}"],
            lineage_id=tree.genome_id,
            generation=tree.generation,
            fitness=tree.fitness,
            disclaimer=OracleOutputBuilder.DISCLAIMER,
        )

    def _generate_answer(self, result: dict, confidence: float, systems: list[str]) -> str:
        fused = result.get("fused_numeric", [])
        if not fused:
            return "Insufficient data for oracle response."
        return (
            f"Evolved structure (confidence={confidence:.2f}) using {len(set(systems))} system(s): "
            f"{', '.join(set(systems))}. "
            f"Numeric signature length: {len(fused)}."
        )

    def get_available_engines(self) -> list[str]:
        engines = ["ga", "gp", "nsga"]
        if HAS_STOCHOPY:
            engines.append("stochopy")
        if HAS_PSOPY:
            engines.append("psopy")
        if HAS_EVOGINE:
            engines.append("evogine")
        # cma and bayesian are always available (lazy import)
        engines.append("cma")
        engines.append("bayesian")
        return engines

    def get_available_systems(self) -> list[str]:
        return list_systems()

    def get_evolution_history(self, engine: str = "ga") -> list[dict]:
        if engine == "gp":
            return self.gp_engine.best_history
        elif engine == "nsga":
            return self.nsga_engine.best_history
        return self.ga_engine.best_history
