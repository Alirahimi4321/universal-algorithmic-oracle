"""NEAT-Python neuroevolution engine - uses real NEAT algorithm."""
import logging
import math
import random
import os
import tempfile
try:
    import neat
    NEAT_AVAILABLE = True
except ImportError:
    NEAT_AVAILABLE = False

from ..population import PopulationManager
from ...evaluation.fitness import FitnessEvaluator
from ...symbolic.registry import list_systems
from ...genome.gene import Gene
from ...genome.chromosome import Chromosome
from .shared import create_chromosomes_from_positions, deap_fallback

logger = logging.getLogger(__name__)


class NEATEngine:
    """Engine using real NEAT (NeuroEvolution of Augmenting Topologies)."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.population_manager = PopulationManager(self.config)
        self.evaluator = FitnessEvaluator(config.get("fitness", {}))
        self.population = []
        self.best_history = []
        self.n_input = self.config.get("n_input", 10)
        self.n_output = self.config.get("n_output", 5)
        self.num_generations = self.config.get("num_generations", 30)
        self.pop_size = self.config.get("pop_size", 50)

    def _create_neat_config(self, n_input, n_output):
        """Create a NEAT config file dynamically."""
        config_content = f"""
[NEAT]
fitness_criterion     = max
fitness_threshold     = 1000
pop_size              = {self.pop_size}
reset_on_extinction   = False
no_fitness_termination = False

[DefaultGenome]
num_inputs            = {n_input}
num_outputs           = {n_output}
num_hidden            = 0
feed_forward          = True
activation_default    = sigmoid
activation_mutate_rate = 0.1
activation_options    = sigmoid tanh relu

aggregation_default   = sum
aggregation_mutate_rate = 0.0
aggregation_options   = sum

bias_init_mean        = 0.0
bias_init_stdev       = 1.0
bias_max_value        = 30.0
bias_min_value        = -30.0
bias_mutate_power     = 0.5
bias_mutate_rate      = 0.7
bias_replace_rate     = 0.1

compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5

conn_add_prob         = 0.5
conn_delete_prob      = 0.2
enabled_default       = True
enabled_mutate_rate   = 0.05

initial_connection    = full_direct

node_add_prob         = 0.3
node_delete_prob      = 0.1

response_init_mean    = 1.0
response_init_stdev   = 0.0
response_max_value    = 30.0
response_min_value    = -30.0
response_mutate_power = 0.0
response_mutate_rate  = 0.0
response_replace_rate = 0.0

weight_init_mean      = 0.0
weight_init_stdev     = 1.0
weight_max_value      = 30
weight_min_value      = -30
weight_mutate_power   = 0.5
weight_mutate_rate    = 0.8
weight_replace_rate   = 0.1

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = max
max_stagnation       = 20
species_elitism      = 2

[DefaultReproduction]
elitism            = 2
survival_threshold = 0.2
"""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.neat', delete=False)
        tmp.write(config_content)
        tmp.flush()
        return tmp.name

    def _eval_genomes(self, genomes, config, entropy_packet, systems):
        """Evaluate genomes using lightweight fitness."""
        numeric = entropy_packet.get("numeric_vector", [])
        for genome_id, genome in genomes:
            conns = list(genome.connections.values())
            if not conns:
                genome.fitness = 0.0
                continue

            weights = [c.weight for c in conns]
            enabled_count = sum(1 for c in conns if c.enabled)
            total = len(conns)

            n = min(len(weights), len(numeric))
            match_score = 0.0
            for i in range(n):
                w_norm = (weights[i] + 30) / 60.0
                n_val = (numeric[i] % 100) / 100.0
                diff = abs(w_norm - n_val)
                match_score += math.exp(-diff * 3)

            if n > 0:
                match_score /= n

            diversity = len(set(round(w, 2) for w in weights)) / max(len(weights), 1)
            enabled_ratio = enabled_count / max(total, 1)

            genome.fitness = match_score * 0.6 + diversity * 0.2 + enabled_ratio * 0.2

    def evolve(self, entropy_packet: dict, generations: int = 20):
        if not NEAT_AVAILABLE:
            return deap_fallback(entropy_packet, generations, self.config)

        try:
            systems = list(list_systems())
            if not systems:
                return deap_fallback(entropy_packet, generations, self.config)

            numeric = entropy_packet.get("numeric_vector", [])
            n_input = min(self.n_input, len(systems))
            n_output = min(self.n_output, len(systems))

            config_path = self._create_neat_config(n_input, n_output)
            try:
                config = neat.Config(
                    neat.DefaultGenome,
                    neat.DefaultReproduction,
                    neat.DefaultSpeciesSet,
                    neat.DefaultStagnation,
                    config_path,
                )

                pop = neat.Population(config)
                evaluator = lambda genomes, config: self._eval_genomes(
                    genomes, config, entropy_packet, systems,
                )
                pop.add_reporter(neat.StdOutReporter(False))
                stats = neat.StatisticsReporter()
                pop.add_reporter(stats)

                n_gen = min(generations, self.num_generations)
                pop.run(evaluator, n_gen)

                best_genomes = sorted(
                    pop.population.values(),
                    key=lambda g: g.fitness if g.fitness else 0.0,
                    reverse=True,
                )[:5]

                positions = []
                for genome in best_genomes:
                    weights = [c.weight for c in genome.connections.values()]
                    if weights:
                        positions.append(weights)

                if not positions:
                    return deap_fallback(entropy_packet, generations, self.config)

                results = []
                for i, pos in enumerate(positions[:5]):
                    n_genes = min(len(pos), len(systems))
                    genes = {}
                    edges = []
                    for j in range(n_genes):
                        sys_id = systems[j % len(systems)]
                        weight = max(0.05, min(1.0, abs(float(pos[j]))))
                        gene = Gene(
                            gene_id=f"neat_final_{i}_{j}",
                            system_id=sys_id,
                            backend="internal",
                            params={"weight": pos[j]},
                            input_slots=[f"in_{j}"],
                            output_slots=[f"out_{j}"],
                            weight=weight,
                            mutation_policy={"param_mutation_rate": 0.1},
                        )
                        genes[gene.gene_id] = gene
                        if j > 0:
                            edges.append((f"neat_final_{i}_{j-1}", gene.gene_id))

                    if genes:
                        from ...genome.chromosome import Chromosome
                        chrom = Chromosome(
                            chromosome_id=f"neat_final_{i}",
                            genes=genes, edges=edges,
                            fusion_schema={"type": "neural_weighted"},
                            output_mapping={"output": list(genes.keys())[-1]},
                        )
                        n = min(len(pos), len(numeric))
                        match_score = sum(math.exp(-abs((pos[k]+30)/60 - (numeric[k]%100)/100)*3) for k in range(n)) / max(n, 1)
                        chrom.fitness = {"total_fitness": match_score}
                        results.append(chrom)

                return results

            finally:
                try:
                    os.unlink(config_path)
                except OSError:
                    pass

        except Exception as e:
            logger.warning("NEAT engine failed: %s, using DEAP fallback", e)
            return deap_fallback(entropy_packet, generations, self.config)
