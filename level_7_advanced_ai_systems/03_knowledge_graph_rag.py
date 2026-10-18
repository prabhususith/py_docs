r"""
Knowledge Graph RAG (GraphRAG): Entity-Relationship Modeling & Multi-Hop Lineage
=================================================================================
Description: Enterprise Graph-Augmented Generation (GraphRAG) engine utilizing NetworkX.
             Models domain entities (microservices, databases, protocols, security vulnerabilities)
             and directed causal relationships, executing multi-hop graph traversals,
             blast-radius impact analysis, and relational context synthesis for LLM queries.
Enterprise Mapping:
- GraphRAG Paradigm (Microsoft GraphRAG): Addresses the structural limitation of pure vector
  search, which retrieves disconnected text chunks but fails at multi-hop relational reasoning
  (e.g., transitive dependencies: Service A -> Queue B -> Worker C -> Database D).
- NetworkX Graph Modeling: Direct equivalent to Neo4j / Amazon Neptune Cypher queries in Python.
  Provides algorithmic graph primitives (shortest paths, ancestor/descendant traversal,
  centrality metrics, and subgraph extraction).

Official Documentation References:
- NetworkX Official Documentation: https://networkx.org/
- Microsoft GraphRAG Research & Project: https://github.com/microsoft/graphrag
- NetworkX Directed Graph Algorithms: https://networkx.org/documentation/stable/reference/algorithms/traversal.html
"""

from __future__ import annotations

import collections
import json
from typing import Any, Final, NamedTuple, Sequence

import networkx as nx
from pydantic import BaseModel, Field


# ==============================================================================
# 1. Entity and Relationship Domain Schemas
# ==============================================================================
class GraphEntity(BaseModel):
    id: str = Field(..., description="Unique entity identifier", examples=["svc_payment_gateway"])
    entity_type: str = Field(..., description="Classification category (Service, Database, Queue, CVE)")
    attributes: dict[str, Any] = Field(default_factory=dict)


class GraphRelation(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = Field(..., description="Directed relationship verb (DEPENDS_ON, WRITES_TO, EXPOSES)")
    attributes: dict[str, Any] = Field(default_factory=dict)


class BlastRadiusReport(NamedTuple):
    origin_entity: str
    impacted_services: list[str]
    critical_paths: list[list[str]]
    total_impacted_nodes: int


# ==============================================================================
# 2. Knowledge Graph Engine (NetworkX DiGraph)
# ==============================================================================
class EnterpriseKnowledgeGraph:
    """
    Direct graph engine managing topology, multi-hop traversals,
    and relational context extraction.
    """

    def __init__(self) -> None:
        # Directed graph allowing asymmetric causal relationships (A -> B != B -> A)
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_entity(self, entity: GraphEntity) -> None:
        """Register entity node with associated attributes."""
        self.graph.add_node(
            entity.id,
            entity_type=entity.entity_type,
            **entity.attributes,
        )

    def add_relation(self, relation: GraphRelation) -> None:
        """Register directed edge representing relationship."""
        if not self.graph.has_node(relation.source_id):
            raise KeyError(f"Source entity '{relation.source_id}' does not exist in graph.")
        if not self.graph.has_node(relation.target_id):
            raise KeyError(f"Target entity '{relation.target_id}' does not exist in graph.")

        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_type=relation.relation_type,
            **relation.attributes,
        )

    def find_shortest_dependency_path(self, source_id: str, target_id: str) -> list[str] | None:
        """Compute shortest directed path between two entities."""
        try:
            path: list[str] = nx.shortest_path(self.graph, source=source_id, target=target_id)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def calculate_blast_radius(self, failed_entity_id: str) -> BlastRadiusReport:
        """
        Calculates all upstream dependencies that collapse if `failed_entity_id` crashes.
        Traverses ancestors in reverse direction (who depends on this node?).
        """
        if not self.graph.has_node(failed_entity_id):
            raise KeyError(f"Entity '{failed_entity_id}' not found in graph.")

        # In a dependency graph where A -> B means A DEPENDS_ON B,
        # if B fails, all nodes having a directed path to B are affected (predecessors/ancestors).
        # We can find all nodes that can reach failed_entity_id using reverse BFS / ancestor query.
        impacted_nodes: set[str] = nx.ancestors(self.graph, failed_entity_id)

        # Trace paths from each impacted service to the failed entity
        critical_paths: list[list[str]] = []
        impacted_services: list[str] = []

        for upstream_node in impacted_nodes:
            node_type = self.graph.nodes[upstream_node].get("entity_type", "")
            if node_type == "Service":
                impacted_services.append(upstream_node)
            path = nx.shortest_path(self.graph, source=upstream_node, target=failed_entity_id)
            critical_paths.append(path)

        return BlastRadiusReport(
            origin_entity=failed_entity_id,
            impacted_services=sorted(impacted_services),
            critical_paths=critical_paths,
            total_impacted_nodes=len(impacted_nodes),
        )

    def extract_subgraph_context(self, entity_id: str, hops: int = 1) -> str:
        """
        Extract k-hop ego network around entity and format as structured relationship triples.
        Produces relational context for GraphRAG prompt injection.
        """
        if not self.graph.has_node(entity_id):
            return f"Entity '{entity_id}' not present in Knowledge Graph."

        # Extract k-hop neighborhood using undirected view for complete relational boundary
        undirected_view = self.graph.to_undirected()
        subgraph_nodes = nx.single_source_shortest_path_length(undirected_view, entity_id, cutoff=hops).keys()
        subgraph = self.graph.subgraph(subgraph_nodes)

        triples: list[str] = []
        for u, v, data in subgraph.edges(data=True):
            rel = data.get("relation_type", "RELATED_TO")
            u_type = self.graph.nodes[u].get("entity_type", "")
            v_type = self.graph.nodes[v].get("entity_type", "")
            triples.append(f"({u} [{u_type}]) --[{rel}]--> ({v} [{v_type}])")

        return "\n".join(triples)


# ==============================================================================
# 3. GraphRAG Contextual Prompt Synthesizer
# ==============================================================================
class GraphRAGSynthesizer:
    """Synthesizes combined Vector + Graph knowledge into an LLM prompt envelope."""

    def __init__(self, kg: EnterpriseKnowledgeGraph) -> None:
        self.kg: EnterpriseKnowledgeGraph = kg

    def build_graph_augmented_prompt(self, entity_focus: str, query: str) -> str:
        """Build Graph-Augmented LLM prompt."""
        graph_triples = self.kg.extract_subgraph_context(entity_focus, hops=2)
        blast_report = self.kg.calculate_blast_radius(entity_focus)

        prompt = f"""<system_instructions>
You are an Enterprise Infrastructure Architect evaluating system topology and outage impact.
Use the Knowledge Graph relational triples and blast radius analysis to answer the query.
</system_instructions>

<knowledge_graph_topology entity="{entity_focus}">
--- Direct Relational Triples (2-Hop Ego Graph) ---
{graph_triples}

--- Downstream Blast Radius Impact ---
Failed Origin: {blast_report.origin_entity}
Directly Impacted Microservices: {', '.join(blast_report.impacted_services)}
Total Cascade Nodes Affected: {blast_report.total_impacted_nodes}
</knowledge_graph_topology>

<user_query>
{query}
</user_query>
"""
        return prompt


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
def main() -> None:
    print("=" * 70)
    print(" LEVEL 7: 03_KNOWLEDGE_GRAPH_RAG - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    kg = EnterpriseKnowledgeGraph()

    # 1. Populate Microservice Infrastructure Topology
    print("\n--- 1. Populating Enterprise Knowledge Graph Topology ---")
    entities = [
        GraphEntity(id="api_gateway", entity_type="Service", attributes={"tier": "Edge", "port": 443}),
        GraphEntity(id="billing_service", entity_type="Service", attributes={"tier": "Core", "port": 8080}),
        GraphEntity(id="payment_processor", entity_type="Service", attributes={"tier": "Core", "port": 9000}),
        GraphEntity(id="redis_broker", entity_type="Queue", attributes={"cluster": "redis-cluster-1"}),
        GraphEntity(id="celery_worker", entity_type="WorkerPool", attributes={"concurrency": 16}),
        GraphEntity(id="postgres_primary", entity_type="Database", attributes={"engine": "PostgreSQL-16"}),
    ]
    for ent in entities:
        kg.add_entity(ent)

    # Define Directed Dependency Relationships
    # (A -> B denotes: A DEPENDS_ON B)
    relations = [
        GraphRelation(source_id="api_gateway", target_id="billing_service", relation_type="ROUTES_TO"),
        GraphRelation(source_id="billing_service", target_id="payment_processor", relation_type="INVOKES_RPC"),
        GraphRelation(source_id="billing_service", target_id="redis_broker", relation_type="ENQUEUES_TASK"),
        GraphRelation(source_id="celery_worker", target_id="redis_broker", relation_type="CONSUMES_FROM"),
        GraphRelation(source_id="payment_processor", target_id="postgres_primary", relation_type="PERSISTS_TO"),
        GraphRelation(source_id="celery_worker", target_id="postgres_primary", relation_type="MUTATES_RECORD"),
    ]
    for rel in relations:
        kg.add_relation(rel)

    print(f"  Graph provisioned: {kg.graph.number_of_nodes()} Nodes, {kg.graph.number_of_edges()} Directed Edges.")
    assert kg.graph.number_of_nodes() == 6
    assert kg.graph.number_of_edges() == 6

    # 2. Multi-Hop Dependency Traversal
    print("\n--- 2. Multi-Hop Lineage Path Discovery ---")
    # Find path from Edge Gateway to Postgres Primary
    path = kg.find_shortest_dependency_path("api_gateway", "postgres_primary")
    print(f"  Shortest Dependency Path (Edge to DB): {' -> '.join(path or [])}")
    assert path == ["api_gateway", "billing_service", "payment_processor", "postgres_primary"]
    print("  [PASS] Successfully resolved 4-hop directed causal lineage.")

    # 3. Outage Blast Radius Calculation
    print("\n--- 3. Single-Point-of-Failure Blast Radius Analysis ---")
    # Simulate Postgres Primary failure
    blast = kg.calculate_blast_radius("postgres_primary")
    print(f"  Simulated Outage at: '{blast.origin_entity}'")
    print(f"  Total Cascade Impacted Nodes: {blast.total_impacted_nodes}")
    print(f"  Impacted Microservices:       {blast.impacted_services}")
    assert "billing_service" in blast.impacted_services
    assert "payment_processor" in blast.impacted_services
    assert "api_gateway" in blast.impacted_services
    print("  [PASS] Blast radius algorithm accurately discovered all upstream dependencies.")

    # 4. GraphRAG Prompt Synthesis
    print("\n--- 4. GraphRAG Relational Prompt Synthesis ---")
    synthesizer = GraphRAGSynthesizer(kg)
    prompt = synthesizer.build_graph_augmented_prompt(
        entity_focus="postgres_primary",
        query="What services will experience downtime if postgres_primary undergoes unannounced maintenance?",
    )
    print("  Synthesized Prompt Preview:\n")
    print(prompt[:500] + "\n  ... [truncated for display]")
    assert "<knowledge_graph_topology" in prompt
    assert "billing_service" in prompt

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 03_knowledge_graph_rag module executed cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
