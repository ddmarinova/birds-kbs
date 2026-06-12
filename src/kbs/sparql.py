"""SPARQL query templates and ontology UI metadata."""

from __future__ import annotations

from dataclasses import dataclass


PREFIXES = """PREFIX birds: <http://birds.ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

DEFAULT_QUERY = f"""{PREFIXES}
SELECT ?species
WHERE {{
  ?species rdf:type birds:Species .
}}
ORDER BY ?species
"""


@dataclass(frozen=True)
class Option:
    """Selectable ontology resource."""

    label: str
    uri: str
    local_name: str


FILTER_DEFINITIONS = {
    "habitats": ("Местообитание", "Habitat", "hasTypicalHabitat", "habitat"),
    "diets": ("Храна", "Diet", "hasTypicalDiet", "diet"),
    "statuses": ("IUCN статус", "IUCNStatus", "hasIUCNStatus", "status"),
    "plumage": (
        "Оперение",
        "PlumagePattern",
        "hasTypicalPlumagePattern",
        "plumage",
    ),
    "migration": (
        "Миграционно поведение",
        "MigratoryBehaviour",
        "hasMigratoryBehaviour",
        "migration",
    ),
    "seasons": ("Размножителен сезон", "Season", "hasBreedingSeason", "season"),
}

QUESTION_LABELS = {
    "species_by_habitat": "Кои видове се срещат в избраното местообитание?",
    "species_by_diet": "Кои видове се хранят с избраната храна?",
    "observations_by_location": "Какви наблюдения на птици има за избраната локация?",
    "declining_or_threatened": "Кои видове са намаляващи или застрашени?",
    "similar_species": "Намери подобни видове",
    "explain_similarity": "Покажи защо видовете са подобни",
    "inferred_category": "Видове по клас от онтологията",
    "inverse_reasoner_demo": "Реален извод: наблюдения чрез обратна връзка",
    "reasoner_check": "Сравнение: с изводи и без изводи",
    "species_inverse_check": "Сравнение: видове и птици чрез обратна връзка",
    "subclass_reasoner_check": "Сравнение: тип през йерархия на класове",
    "morphology_subclass_check": "Сравнение: морфология към общ клас",
    "category_reasoner_check": "Сравнение: клас като изведен тип",
    "location_recommendations": "Препоръчай видове според локация",
    "species_location_recommendations": "Препоръчай локации за наблюдение на вид",
    "similar_habitat_different_diet": "Сходно местообитание, различна храна",
    "risky_species_by_location": "Рискови видове по локация",
    "diet_generalists": "Кои видове имат най-разнообразно меню?",
    "urban_at_risk": "Кои градски видове са застрашени?",
    "season_mismatch_observations": "Кои наблюдения на птици са извън размножителния сезон?",
    "morphology_profile": "Морфологичен профил на видовете",
    "taxonomic_path": "Таксономична верига на избрания вид",
}

BASIC_QUESTIONS = [
    "species_by_habitat",
    "species_by_diet",
    "observations_by_location",
    "declining_or_threatened",
]

RECOMMENDATION_QUESTIONS = [
    "similar_species",
    "explain_similarity",
    "location_recommendations",
    "species_location_recommendations",
    "similar_habitat_different_diet",
    "risky_species_by_location",
]

REASONER_QUESTIONS = [
    "inverse_reasoner_demo",
    "reasoner_check",
]

CURIOSITY_QUESTIONS = [
    "diet_generalists",
    "urban_at_risk",
    "season_mismatch_observations",
    "morphology_profile",
    "taxonomic_path",
]

REASONER_CATEGORY_OPTIONS = [
    Option("Застрашени видове", "http://birds.ontology#ThreatenedSpecies", "ThreatenedSpecies"),
    Option("Намаляващи видове", "http://birds.ontology#DecliningSpecies", "DecliningSpecies"),
    Option("Насекомоядни видове", "http://birds.ontology#InsectivorousSpecies", "InsectivorousSpecies"),
    Option("Градски видове", "http://birds.ontology#UrbanSpecies", "UrbanSpecies"),
    Option("Постоянни видове", "http://birds.ontology#ResidentSpecies", "ResidentSpecies"),
    Option("Мигриращи видове", "http://birds.ontology#MigratorySpecies", "MigratorySpecies"),
    Option("Видове от широколистни гори", "http://birds.ontology#DeciduousForestSpecies", "DeciduousForestSpecies"),
    Option("Видове с черно-бяло оперение", "http://birds.ontology#BlackWhiteSpecies", "BlackWhiteSpecies"),
]

CATEGORY_RULES = {
    "ThreatenedSpecies": ("hasIUCNStatus", ["VU", "EN", "CR"]),
    "DecliningSpecies": ("hasPopulationTrend", ["Decreasing"]),
    "InsectivorousSpecies": ("hasTypicalDiet", ["Insects"]),
    "UrbanSpecies": ("hasTypicalHabitat", ["UrbanParksAndGardens"]),
    "ResidentSpecies": ("hasMigratoryBehaviour", ["Resident"]),
    "MigratorySpecies": ("hasMigratoryBehaviour", ["Migratory"]),
    "DeciduousForestSpecies": ("hasTypicalHabitat", ["DeciduousForest"]),
    "BlackWhiteSpecies": ("hasTypicalPlumagePattern", ["BlackWhitePlumage"]),
}

SIMILARITY_CRITERIA = {
    "combined": ("Комбинирано", None),
    "habitat": ("По местообитание", "hasTypicalHabitat"),
    "diet": ("По храна", "hasTypicalDiet"),
    "plumage": ("По оперение", "hasTypicalPlumagePattern"),
    "migration": ("По миграционно поведение", "hasMigratoryBehaviour"),
}


def local_name(value: str) -> str:
    """Return a compact name for a URI or literal."""
    if "#" in value:
        return value.rsplit("#", 1)[1]
    if "/" in value:
        return value.rstrip("/").rsplit("/", 1)[1]
    return value


def humanize_local_name(value: str) -> str:
    """Make ontology identifiers easier to read in the UI."""
    text = local_name(value).replace("_", " ")
    result = []
    for index, char in enumerate(text):
        if index and char.isupper() and text[index - 1].islower():
            result.append(" ")
        result.append(char)
    return "".join(result)


def option_query(class_name: str) -> str:
    return f"""{PREFIXES}
SELECT ?item ?label
WHERE {{
  ?item rdf:type birds:{class_name} .
  ?item rdfs:label ?label .
  FILTER(LANGMATCHES(LANG(?label), "bg"))
}}
ORDER BY ?item
"""


def values_clause(variable: str, options: list[Option]) -> str:
    if not options:
        return ""
    values = " ".join(f"birds:{option.local_name}" for option in options)
    return f"  VALUES ?{variable} {{ {values} }}\n"


def predicate_values_clause(criterion: str) -> str:
    predicate = SIMILARITY_CRITERIA[criterion][1]
    if predicate:
        return f"  VALUES ?predicate {{ birds:{predicate} }}"

    return """  VALUES ?predicate {
    birds:hasTypicalHabitat
    birds:hasTypicalDiet
    birds:hasTypicalPlumagePattern
    birds:hasMigratoryBehaviour
  }"""


def category_rule_block(category_name: str) -> str:
    predicate, values = CATEGORY_RULES[category_name]
    value_list = " ".join(f"birds:{value}" for value in values)
    return f"""  UNION {{
    ?species rdf:type birds:Species ;
      birds:{predicate} ?categoryValue .
    VALUES ?categoryValue {{ {value_list} }}
  }}"""


def build_species_filter_query(filters: dict[str, list[Option]]) -> str:
    required_patterns = []

    for key, (_, _, predicate, variable) in FILTER_DEFINITIONS.items():
        if filters.get(key, []):
            required_patterns.append(values_clause(variable, filters[key]))
            required_patterns.append(f"  ?species birds:{predicate} ?{variable} .")

    return f"""{PREFIXES}
SELECT ?species
WHERE {{
  ?species rdf:type birds:Species .
{chr(10).join(required_patterns)}
}}
ORDER BY ?species
"""


def build_question_query(
    question: str,
    selected: Option | None = None,
    criterion: str = "combined",
) -> str:
    if question == "species_by_habitat" and selected:
        return build_species_filter_query({"habitats": [selected]})

    if question == "species_by_diet" and selected:
        return build_species_filter_query({"diets": [selected]})

    if question == "observations_by_location" and selected:
        return f"""{PREFIXES}
SELECT
  ?observation
  ?date
  ?species
  ?bird
  ?behavior
WHERE {{
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{selected.local_name} ;
    birds:observedBird ?bird ;
    birds:observedOn ?date .
  ?bird birds:belongsToSpecies ?species .
  ?observation birds:hasObservedBehavior ?behavior .
}}
ORDER BY DESC(?date)
"""

    if question == "declining_or_threatened":
        return f"""{PREFIXES}
SELECT
  ?species
  ?status
  ?trend
WHERE {{
  ?species rdf:type birds:Species ;
    birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}}
ORDER BY ?species
"""

    if question == "similar_species" and selected:
        return f"""{PREFIXES}
SELECT
  ?similarSpecies
  (COUNT(DISTINCT ?sharedValue) AS ?score)
WHERE {{
  VALUES ?target {{ birds:{selected.local_name} }}
{predicate_values_clause(criterion)}

  ?target ?predicate ?sharedValue .
  ?similarSpecies rdf:type birds:Species ;
    ?predicate ?sharedValue .
  FILTER(?similarSpecies != ?target)
}}
GROUP BY ?similarSpecies
ORDER BY DESC(?score) ?similarSpecies
"""

    if question == "explain_similarity" and selected:
        return f"""{PREFIXES}
SELECT
  ?similarSpecies
  ?criterion
  ?sharedValue
WHERE {{
  VALUES ?target {{ birds:{selected.local_name} }}
{predicate_values_clause(criterion)}

  ?target ?predicate ?sharedValue .
  ?similarSpecies rdf:type birds:Species ;
    ?predicate ?sharedValue .
  FILTER(?similarSpecies != ?target)

  BIND(
    IF(?predicate = birds:hasTypicalHabitat, "местообитание",
    IF(?predicate = birds:hasTypicalDiet, "храна",
    IF(?predicate = birds:hasTypicalPlumagePattern, "оперение", "миграция")))
    AS ?criterion
  )
}}
ORDER BY ?similarSpecies ?criterion ?sharedValue
"""

    if question == "inferred_category" and selected:
        fallback_block = ""
        if selected.local_name in CATEGORY_RULES:
            fallback_block = category_rule_block(selected.local_name)

        return f"""{PREFIXES}
SELECT DISTINCT
  ?species
  ("{selected.local_name}" AS ?category)
WHERE {{
  {{
    ?species rdf:type birds:{selected.local_name} .
  }}
{fallback_block}
}}
ORDER BY ?species
"""

    if question in {"inverse_reasoner_demo", "reasoner_check"} and selected:
        return f"""{PREFIXES}
SELECT ?bird ?observation ?date
WHERE {{
  ?bird birds:belongsToSpecies birds:{selected.local_name} ;
    birds:hasObservation ?observation .
  ?observation birds:observedOn ?date .
}}
ORDER BY ?bird ?date
"""

    if question == "species_inverse_check" and selected:
        return f"""{PREFIXES}
SELECT
  ?species
  ?bird
WHERE {{
  VALUES ?species {{ birds:{selected.local_name} }}
  ?species birds:isSpeciesOf ?bird .
}}
ORDER BY ?species ?bird
"""

    if question == "subclass_reasoner_check" and selected:
        return f"""{PREFIXES}
SELECT
  ?species
  ?inferredType
WHERE {{
  VALUES ?species {{ birds:{selected.local_name} }}
  ?species rdf:type birds:Taxon .
  BIND("Taxon" AS ?inferredType)
}}
ORDER BY ?species
"""

    if question == "morphology_subclass_check" and selected:
        return f"""{PREFIXES}
SELECT
  ?morphology
  ?inferredType
WHERE {{
  VALUES ?morphology {{ birds:{selected.local_name} }}
  ?morphology rdf:type birds:Morphology .
  BIND("Morphology" AS ?inferredType)
}}
ORDER BY ?morphology
"""

    if question == "category_reasoner_check" and selected:
        return f"""{PREFIXES}
SELECT
  ?species
  ("{selected.local_name}" AS ?inferredType)
WHERE {{
  ?species rdf:type birds:{selected.local_name} .
}}
ORDER BY ?species
"""

    if question == "location_recommendations" and selected:
        return f"""{PREFIXES}
SELECT
  ?recommendedSpecies
  (COUNT(DISTINCT ?sharedHabitat) AS ?score)
WHERE {{
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{selected.local_name} ;
    birds:observedBird ?observedBird .
  ?observedBird birds:belongsToSpecies ?observedSpecies .
  ?observedSpecies birds:hasTypicalHabitat ?sharedHabitat .

  ?recommendedSpecies rdf:type birds:Species ;
    birds:hasTypicalHabitat ?sharedHabitat .
  FILTER(?recommendedSpecies != ?observedSpecies)
  FILTER NOT EXISTS {{
    ?existingObservation birds:isObservedAtLocation birds:{selected.local_name} ;
      birds:observedBird ?existingBird .
    ?existingBird birds:belongsToSpecies ?recommendedSpecies .
  }}

}}
GROUP BY ?recommendedSpecies
ORDER BY DESC(?score) ?recommendedSpecies
"""

    if question == "species_location_recommendations" and selected:
        return f"""{PREFIXES}
SELECT DISTINCT
  ?location
  ?observedSpecies
  ?sharedHabitat
WHERE {{
  VALUES ?target {{ birds:{selected.local_name} }}
  ?target birds:hasTypicalHabitat ?sharedHabitat .

  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation ?location ;
    birds:observedBird ?bird .
  ?bird birds:belongsToSpecies ?observedSpecies .
  ?observedSpecies birds:hasTypicalHabitat ?sharedHabitat .
}}
ORDER BY ?location ?observedSpecies
"""

    if question == "similar_habitat_different_diet" and selected:
        return f"""{PREFIXES}
SELECT DISTINCT
  ?similarSpecies
  ?sharedHabitat
  ?differentDiet
WHERE {{
  VALUES ?target {{ birds:{selected.local_name} }}
  ?target birds:hasTypicalHabitat ?sharedHabitat ;
    birds:hasTypicalDiet ?targetDiet .

  ?similarSpecies rdf:type birds:Species ;
    birds:hasTypicalHabitat ?sharedHabitat ;
    birds:hasTypicalDiet ?differentDiet .
  FILTER(?similarSpecies != ?target)
  FILTER(?differentDiet != ?targetDiet)
}}
ORDER BY ?similarSpecies ?sharedHabitat ?differentDiet
"""

    if question == "risky_species_by_location" and selected:
        return f"""{PREFIXES}
SELECT DISTINCT
  ?species
  ?status
  ?trend
WHERE {{
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{selected.local_name} ;
    birds:observedBird ?bird .
  ?bird birds:belongsToSpecies ?species .
  ?species birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}}
ORDER BY ?species
"""

    if question == "diet_generalists":
        return f"""{PREFIXES}
SELECT
  ?species
  (COUNT(DISTINCT ?diet) AS ?dietCount)
WHERE {{
  ?species rdf:type birds:Species ;
    birds:hasTypicalDiet ?diet .
}}
GROUP BY ?species
HAVING(COUNT(DISTINCT ?diet) >= 3)
ORDER BY DESC(?dietCount) ?species
"""

    if question == "urban_at_risk":
        return f"""{PREFIXES}
SELECT
  ?species
  ?status
  ?trend
WHERE {{
  ?species rdf:type birds:Species ;
    birds:hasTypicalHabitat birds:UrbanParksAndGardens ;
    birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}}
ORDER BY ?species
"""

    if question == "season_mismatch_observations":
        return f"""{PREFIXES}
SELECT
  ?observation
  ?date
  ?species
  ?season
  ?observedSeason
WHERE {{
  ?observation rdf:type birds:Observation ;
    birds:observedBird ?bird ;
    birds:observedOn ?date .
  ?bird birds:belongsToSpecies ?species .
  ?species birds:hasBreedingSeason ?season .

  BIND(MONTH(?date) AS ?month)
  BIND(
    IF(?month IN (3, 4, 5), birds:Spring,
    IF(?month IN (6, 7, 8), birds:Summer,
    IF(?month IN (9, 10, 11), birds:Autumn, birds:Winter)))
    AS ?observedSeasonResource
  )
  BIND(?observedSeasonResource AS ?observedSeason)
  FILTER NOT EXISTS {{
    ?species birds:hasBreedingSeason ?observedSeasonResource .
  }}
}}
ORDER BY ?date
"""

    if question == "morphology_profile":
        return f"""{PREFIXES}
SELECT
  ?species
  ?beak
  ?legs
  ?tail
  ?wings
  ?plumage
WHERE {{
  ?species rdf:type birds:Species .
  ?species birds:hasBeakMorphology ?beak ;
    birds:hasLegMorphology ?legs ;
    birds:hasTailMorphology ?tail ;
    birds:hasWingMorphology ?wings ;
    birds:hasTypicalPlumagePattern ?plumage .
}}
ORDER BY ?species
"""

    if question == "taxonomic_path" and selected:
        return f"""{PREFIXES}
SELECT
  ?species
  ?genus
  ?family
  ?order
  ?class
  ?phylum
  ?kingdom
WHERE {{
  VALUES ?species {{ birds:{selected.local_name} }}
  ?species birds:hasParentTaxon ?genus .
  ?genus birds:hasParentTaxon ?family .
  ?family birds:hasParentTaxon ?order .
  ?order birds:hasParentTaxon ?class .
  ?class birds:hasParentTaxon ?phylum .
  ?phylum birds:hasParentTaxon ?kingdom .
}}
"""

    return DEFAULT_QUERY


def build_species_profile_query(selected: Option) -> str:
    return f"""{PREFIXES}
SELECT
  ?property
  ?value
WHERE {{
  VALUES ?species {{ birds:{selected.local_name} }}
  {{
    BIND("Вид" AS ?property)
    BIND(?species AS ?value)
  }}
  UNION {{
    ?species birds:foundInRegion ?value .
    BIND("Регион" AS ?property)
  }}
  UNION {{
    ?species birds:hasIUCNStatus ?value .
    BIND("IUCN статус" AS ?property)
  }}
  UNION {{
    ?species birds:hasPopulationTrend ?value .
    BIND("Популационна тенденция" AS ?property)
  }}
  UNION {{
    ?species birds:hasMigratoryBehaviour ?value .
    BIND("Миграционно поведение" AS ?property)
  }}
  UNION {{
    ?species birds:hasTypicalHabitat ?value .
    BIND("Местообитание" AS ?property)
  }}
  UNION {{
    ?species birds:hasTypicalDiet ?value .
    BIND("Храна" AS ?property)
  }}
  UNION {{
    ?species birds:hasBreedingSeason ?value .
    BIND("Размножителен сезон" AS ?property)
  }}
  UNION {{
    ?species birds:hasTypicalPlumagePattern ?value .
    BIND("Оперение" AS ?property)
  }}
  UNION {{
    ?species birds:hasBeakMorphology ?value .
    BIND("Клюн" AS ?property)
  }}
  UNION {{
    ?species birds:hasLegMorphology ?value .
    BIND("Крака" AS ?property)
  }}
  UNION {{
    ?species birds:hasTailMorphology ?value .
    BIND("Опашка" AS ?property)
  }}
  UNION {{
    ?species birds:hasWingMorphology ?value .
    BIND("Крила" AS ?property)
  }}
  UNION {{
    ?species birds:hasParentTaxon ?value .
    BIND("Род" AS ?property)
  }}
}}
ORDER BY ?property ?value
"""
