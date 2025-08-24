"""Utilities for syncing NetworkX graphs with a Neo4j database."""
from __future__ import annotations

from typing import Any

import networkx as nx
from neo4j import GraphDatabase


def export_to_neo4j(G: nx.Graph, uri: str, user: str, password: str) -> None:
    """Export a NetworkX graph to a Neo4j database.

    Parameters
    ----------
    G: nx.Graph
        Graph to export. Node identifiers are stored on the `id` field in
        Neo4j. Node and edge attributes are stored as properties.
    uri, user, password: str
        Connection information for the Neo4j database.
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")

        # Create nodes
        nodes = [{"id": n, **data} for n, data in G.nodes(data=True)]
        session.run(
            "UNWIND $nodes AS node CREATE (n:Node {id: node.id}) SET n += node",
            nodes=nodes,
        )

        # Create relationships
        edges = [
            {"source": u, "target": v, **data} for u, v, data in G.edges(data=True)
        ]
        session.run(
            """
            UNWIND $rels AS rel
            MATCH (a:Node {id: rel.source}), (b:Node {id: rel.target})
            CREATE (a)-[r:REL]->(b)
            SET r += rel
            """,
            rels=edges,
        )
    driver.close()


def import_from_neo4j(uri: str, user: str, password: str) -> nx.Graph:
    """Import all nodes and edges from a Neo4j database into a NetworkX graph.

    The function creates an undirected :class:`networkx.Graph` containing every
    node and relationship present in the database. Node labels are stored in the
    ``labels`` attribute and relationship types in the ``type`` attribute.
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))
    G = nx.Graph()
    with driver.session() as session:
        node_records = session.run(
            "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props"
        )
        for record in node_records:
            node_id = record["id"]
            props: dict[str, Any] = record["props"] or {}
            props["labels"] = record["labels"]
            G.add_node(node_id, **props)

        rel_records = session.run(
            "MATCH (a)-[r]->(b) RETURN id(a) AS source, id(b) AS target, type(r) AS type, properties(r) AS props"
        )
        for record in rel_records:
            source = record["source"]
            target = record["target"]
            props = record["props"] or {}
            props["type"] = record["type"]
            G.add_edge(source, target, **props)
    driver.close()
    return G
