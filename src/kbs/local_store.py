"""Local RDF store for running SPARQL without GraphDB."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

from kbs.sparql import CATEGORY_RULES

BIRDS = Namespace("http://birds.ontology#")
ONTOLOGY_PATH = Path(__file__).resolve().parents[2] / "ontology.rdf"


def load_graph(infer: bool = True) -> Graph:
    """Load ontology from disk and optionally add simple inferred triples."""
    graph = Graph()
    graph.parse(ONTOLOGY_PATH)

    if infer:
        add_inferred_triples(graph)

    return graph


def add_inferred_triples(graph: Graph) -> None:
    """Add the small inference set used by the UI demos."""
    add_inverse_triples(graph)
    add_subclass_types(graph)
    add_category_types(graph)


def add_inverse_triples(graph: Graph) -> None:
    for bird, observation in graph.subject_objects(BIRDS.hasObservation):
        graph.add((observation, BIRDS.observedBird, bird))
    for observation, bird in graph.subject_objects(BIRDS.observedBird):
        graph.add((bird, BIRDS.hasObservation, observation))

    for bird, species in graph.subject_objects(BIRDS.belongsToSpecies):
        graph.add((species, BIRDS.isSpeciesOf, bird))
    for species, bird in graph.subject_objects(BIRDS.isSpeciesOf):
        graph.add((bird, BIRDS.belongsToSpecies, species))


def add_subclass_types(graph: Graph) -> None:
    subclass_pairs = set(graph.subject_objects(RDFS.subClassOf))
    changed = True

    while changed:
        changed = False
        for child, parent in list(subclass_pairs):
            for next_parent in graph.objects(parent, RDFS.subClassOf):
                pair = (child, next_parent)
                if pair not in subclass_pairs:
                    subclass_pairs.add(pair)
                    changed = True

    for subject, class_uri in list(graph.subject_objects(RDF.type)):
        for _, parent in [pair for pair in subclass_pairs if pair[0] == class_uri]:
            graph.add((subject, RDF.type, parent))


def add_category_types(graph: Graph) -> None:
    for category, (predicate_name, values) in CATEGORY_RULES.items():
        predicate = BIRDS[predicate_name]
        category_uri = BIRDS[category]
        value_uris = {BIRDS[value] for value in values}

        for species, value in graph.subject_objects(predicate):
            if value in value_uris:
                graph.add((species, RDF.type, category_uri))


def query_to_sparql_json(graph: Graph, query: str) -> dict[str, Any]:
    """Convert rdflib query result to SPARQL JSON result shape."""
    result = graph.query(query)

    if result.type == "ASK":
        return {"boolean": bool(result)}

    variables = [str(variable) for variable in result.vars]
    bindings = []

    for row in result:
        binding = {}
        for variable, value in zip(variables, row, strict=True):
            if value is None:
                continue
            binding[variable] = binding_value(value)
        bindings.append(binding)

    return {
        "head": {"vars": variables},
        "results": {"bindings": bindings},
    }


def binding_value(value: URIRef | Literal | Any) -> dict[str, str]:
    if isinstance(value, URIRef):
        return {"type": "uri", "value": str(value)}

    if isinstance(value, Literal):
        payload = {"type": "literal", "value": str(value)}
        if value.datatype:
            payload["datatype"] = str(value.datatype)
        if value.language:
            payload["xml:lang"] = value.language
        return payload

    return {"type": "literal", "value": str(value)}
