"""Neo4j graph store for lineage tracking and graph queries.

Per design doc section 21.2: lineage graph storage with Neo4j.
Requires a running Neo4j server instance.
"""
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    logger.info("neo4j driver not available")


class Neo4jGraphStore:
    """Graph store using Neo4j for oracle lineage tracking."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.available = False

        if not HAS_NEO4J:
            logger.warning("Neo4j driver not installed")
            return

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            self.available = True
            self._init_schema()
            logger.info("Connected to Neo4j at %s", uri)
        except Exception as e:
            logger.warning("Neo4j connection failed: %s", e)
            self.driver = None

    def _init_schema(self):
        """Create indexes and constraints."""
        if not self.driver:
            return
        with self.driver.session() as session:
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (c:Chromosome) ON (c.chromosome_id)
            """)
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (o:Oracle) ON (o.oracle_id)
            """)
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (g:Generation) ON (g.generation)
            """)
            session.commit()

    def store_chromosome(
        self,
        chromosome_id: str,
        generation: int,
        fitness: float,
        systems: list[str],
        parent_ids: list[str] = None,
        metadata: dict = None,
    ) -> bool:
        """Store a chromosome as a graph node with parent edges."""
        if not self.driver:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (c:Chromosome {chromosome_id: $chrom_id})
                SET c.generation = $gen,
                    c.fitness = $fitness,
                    c.systems = $systems,
                    c.metadata = $metadata,
                    c.timestamp = $timestamp
            """, chrom_id=chromosome_id, gen=generation, fitness=fitness,
                systems=json.dumps(systems), metadata=json.dumps(metadata or {}),
                timestamp=time.time())

            for parent_id in (parent_ids or []):
                session.run("""
                    MATCH (p:Chromosome {chromosome_id: $parent_id})
                    MATCH (c:Chromosome {chromosome_id: $chrom_id})
                    MERGE (p)-[:EVOLVED_TO]->(c)
                """, parent_id=parent_id, chrom_id=chromosome_id)

            return True

    def store_oracle(
        self,
        oracle_id: str,
        chromosome_id: str,
        generation: int,
        version: str,
    ) -> bool:
        """Store an oracle node linked to its chromosome."""
        if not self.driver:
            return False

        with self.driver.session() as session:
            session.run("""
                MERGE (o:Oracle {oracle_id: $oracle_id})
                SET o.chromosome_id = $chrom_id,
                    o.generation = $gen,
                    o.version = $version,
                    o.timestamp = $timestamp
            """, oracle_id=oracle_id, chrom_id=chromosome_id,
                gen=generation, version=version, timestamp=time.time())

            session.run("""
                MATCH (o:Oracle {oracle_id: $oracle_id})
                MATCH (c:Chromosome {chromosome_id: $chrom_id})
                MERGE (o)-[:USES]->(c)
            """, oracle_id=oracle_id, chrom_id=chromosome_id)

            return True

    def get_lineage(self, chromosome_id: str, max_depth: int = 10) -> dict:
        """Get the lineage tree of a chromosome."""
        if not self.driver:
            return {"nodes": [], "edges": []}

        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (ancestor:Chromosome)-[:EVOLVED_TO*0..""" + str(max_depth) + """]->(descendant:Chromosome {chromosome_id: $chrom_id})
                RETURN nodes(path) as nodes, relationships(path) as rels
            """, chrom_id=chromosome_id)

            nodes = []
            edges = []
            for record in result:
                for node in record["nodes"]:
                    nodes.append({
                        "chromosome_id": node["chromosome_id"],
                        "generation": node["generation"],
                        "fitness": node["fitness"],
                    })
                for rel in record["rels"]:
                    edges.append({
                        "from": rel.start_node["chromosome_id"],
                        "to": rel.end_node["chromosome_id"],
                        "type": type(rel).__name__,
                    })

            return {"nodes": nodes, "edges": edges}

    def get_best_chromosomes(self, limit: int = 10) -> list[dict]:
        """Get the best chromosomes by fitness."""
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chromosome)
                RETURN c.chromosome_id as chrom_id, c.generation as gen,
                       c.fitness as fitness, c.systems as systems
                ORDER BY c.fitness DESC
                LIMIT $limit
            """, limit=limit)

            return [
                {
                    "chromosome_id": r["chrom_id"],
                    "generation": r["gen"],
                    "fitness": r["fitness"],
                    "systems": json.loads(r["systems"]) if r["systems"] else [],
                }
                for r in result
            ]

    def get_generation_stats(self) -> list[dict]:
        """Get fitness statistics per generation."""
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chromosome)
                RETURN c.generation as gen,
                       avg(c.fitness) as avg_fitness,
                       max(c.fitness) as max_fitness,
                       count(c) as count
                ORDER BY c.generation
            """)

            return [
                {
                    "generation": r["gen"],
                    "avg_fitness": r["avg_fitness"],
                    "max_fitness": r["max_fitness"],
                    "count": r["count"],
                }
                for r in result
            ]

    def close(self):
        if self.driver:
            self.driver.close()
