# SPARQL Requests

This file is a dictionary-style catalog of the SPARQL requests used by the app.
Runtime query generation stays in `src/kbs/sparql.py`.

## Prefixes

```sparql
PREFIX birds: <http://birds.ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

## Query Dictionary

### `default_species`

Lists all species.

```sparql
SELECT DISTINCT ?species
WHERE {
  ?species rdf:type birds:Species .
}
ORDER BY ?species
```

### `dropdown_options`

Loads Bulgarian labels for dropdown options of a selected class.

```sparql
SELECT DISTINCT ?item ?label
WHERE {
  ?item rdf:type birds:{class_name} .
  ?item rdfs:label ?label .
  FILTER(LANGMATCHES(LANG(?label), "bg"))
}
ORDER BY ?item
```

### `filter_species`

Filters species by selected habitats, diets, statuses, plumage patterns, migration behaviour, and seasons.

```sparql
SELECT DISTINCT ?species
WHERE {
  ?species rdf:type birds:Species .

  VALUES ?habitat { birds:{habitat_1} birds:{habitat_2} }
  ?species birds:hasTypicalHabitat ?habitat .

  VALUES ?diet { birds:{diet_1} birds:{diet_2} }
  ?species birds:hasTypicalDiet ?diet .

  VALUES ?status { birds:{status_1} birds:{status_2} }
  ?species birds:hasIUCNStatus ?status .

  VALUES ?plumage { birds:{plumage_1} birds:{plumage_2} }
  ?species birds:hasTypicalPlumagePattern ?plumage .

  VALUES ?migration { birds:{migration_1} birds:{migration_2} }
  ?species birds:hasMigratoryBehaviour ?migration .

  VALUES ?season { birds:{season_1} birds:{season_2} }
  ?species birds:hasBreedingSeason ?season .
}
ORDER BY ?species
```

### `species_by_habitat`

Lists species that use a selected habitat.

```sparql
SELECT DISTINCT ?species
WHERE {
  ?species rdf:type birds:Species .
  VALUES ?habitat { birds:{habitat} }
  ?species birds:hasTypicalHabitat ?habitat .
}
ORDER BY ?species
```

### `species_by_diet`

Lists species that use a selected diet.

```sparql
SELECT DISTINCT ?species
WHERE {
  ?species rdf:type birds:Species .
  VALUES ?diet { birds:{diet} }
  ?species birds:hasTypicalDiet ?diet .
}
ORDER BY ?species
```

### `observations_by_location`

Lists observations from a selected location.

```sparql
SELECT DISTINCT
  ?observation
  ?date
  ?species
  ?bird
  ?behavior
WHERE {
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{location} ;
    birds:observedBird ?bird ;
    birds:observedOn ?date .
  ?bird birds:belongsToSpecies ?species .
  ?observation birds:hasObservedBehavior ?behavior .
}
ORDER BY DESC(?date)
```

### `declining_or_threatened`

Lists species that are threatened or have a decreasing population trend.

```sparql
SELECT DISTINCT
  ?species
  ?status
  ?trend
WHERE {
  ?species rdf:type birds:Species ;
    birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}
ORDER BY ?species
```

### `similar_species`

Scores species by shared values with a selected target species.

```sparql
SELECT
  ?similarSpecies
  (COUNT(DISTINCT ?sharedValue) AS ?score)
WHERE {
  VALUES ?target { birds:{species} }
  VALUES ?predicate {
    birds:hasTypicalHabitat
    birds:hasTypicalDiet
    birds:hasTypicalPlumagePattern
    birds:hasMigratoryBehaviour
  }

  ?target ?predicate ?sharedValue .
  ?similarSpecies rdf:type birds:Species ;
    ?predicate ?sharedValue .
  FILTER(?similarSpecies != ?target)
}
GROUP BY ?similarSpecies
ORDER BY DESC(?score) ?similarSpecies
```

### `explain_similarity`

Shows which values are shared with a selected target species.

```sparql
SELECT DISTINCT
  ?similarSpecies
  ?criterion
  ?sharedValue
WHERE {
  VALUES ?target { birds:{species} }
  VALUES ?predicate {
    birds:hasTypicalHabitat
    birds:hasTypicalDiet
    birds:hasTypicalPlumagePattern
    birds:hasMigratoryBehaviour
  }

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
}
ORDER BY ?similarSpecies ?criterion ?sharedValue
```

### `inferred_category`

Lists species from an inferred ontology category.

```sparql
SELECT DISTINCT
  ?species
  ("{category}" AS ?category)
WHERE {
  {
    ?species rdf:type birds:{category} .
  }
  UNION {
    ?species rdf:type birds:Species ;
      birds:{categoryPredicate} ?categoryValue .
    VALUES ?categoryValue { birds:{categoryValue_1} birds:{categoryValue_2} }
  }
}
ORDER BY ?species
```

### `inverse_reasoner_demo`

Uses inverse reasoning to find observations for birds of a selected species.

```sparql
SELECT DISTINCT ?bird ?observation ?date
WHERE {
  ?bird birds:belongsToSpecies birds:{species} ;
    birds:hasObservation ?observation .
  ?observation birds:observedOn ?date .
}
ORDER BY ?bird ?date
```

### `species_inverse_check`

Checks inverse species-to-bird relation.

```sparql
SELECT DISTINCT
  ?species
  ?bird
WHERE {
  VALUES ?species { birds:{species} }
  ?species birds:isSpeciesOf ?bird .
}
ORDER BY ?species ?bird
```

### `subclass_reasoner_check`

Checks whether a selected species is inferred as a taxon.

```sparql
SELECT DISTINCT
  ?species
  ?inferredType
WHERE {
  VALUES ?species { birds:{species} }
  ?species rdf:type birds:Taxon .
  BIND("Taxon" AS ?inferredType)
}
ORDER BY ?species
```

### `morphology_subclass_check`

Checks whether a selected morphology resource is inferred as morphology.

```sparql
SELECT DISTINCT
  ?morphology
  ?inferredType
WHERE {
  VALUES ?morphology { birds:{morphology} }
  ?morphology rdf:type birds:Morphology .
  BIND("Morphology" AS ?inferredType)
}
ORDER BY ?morphology
```

### `category_reasoner_check`

Checks species inferred into a selected category.

```sparql
SELECT DISTINCT
  ?species
  ("{category}" AS ?inferredType)
WHERE {
  ?species rdf:type birds:{category} .
}
ORDER BY ?species
```

### `location_recommendations`

Recommends species for a location based on shared habitats.

```sparql
SELECT
  ?recommendedSpecies
  (COUNT(DISTINCT ?sharedHabitat) AS ?score)
WHERE {
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{location} ;
    birds:observedBird ?observedBird .
  ?observedBird birds:belongsToSpecies ?observedSpecies .
  ?observedSpecies birds:hasTypicalHabitat ?sharedHabitat .

  ?recommendedSpecies rdf:type birds:Species ;
    birds:hasTypicalHabitat ?sharedHabitat .
  FILTER(?recommendedSpecies != ?observedSpecies)
  FILTER NOT EXISTS {
    ?existingObservation birds:isObservedAtLocation birds:{location} ;
      birds:observedBird ?existingBird .
    ?existingBird birds:belongsToSpecies ?recommendedSpecies .
  }
}
GROUP BY ?recommendedSpecies
ORDER BY DESC(?score) ?recommendedSpecies
```

### `species_location_recommendations`

Recommends observation locations for a selected species.

```sparql
SELECT DISTINCT
  ?location
  ?observedSpecies
  ?sharedHabitat
WHERE {
  VALUES ?target { birds:{species} }
  ?target birds:hasTypicalHabitat ?sharedHabitat .

  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation ?location ;
    birds:observedBird ?bird .
  ?bird birds:belongsToSpecies ?observedSpecies .
  ?observedSpecies birds:hasTypicalHabitat ?sharedHabitat .
}
ORDER BY ?location ?observedSpecies
```

### `similar_habitat_different_diet`

Finds species with a shared habitat but different diet.

```sparql
SELECT DISTINCT
  ?similarSpecies
  ?sharedHabitat
  ?differentDiet
WHERE {
  VALUES ?target { birds:{species} }
  ?target birds:hasTypicalHabitat ?sharedHabitat ;
    birds:hasTypicalDiet ?targetDiet .

  ?similarSpecies rdf:type birds:Species ;
    birds:hasTypicalHabitat ?sharedHabitat ;
    birds:hasTypicalDiet ?differentDiet .
  FILTER(?similarSpecies != ?target)
  FILTER(?differentDiet != ?targetDiet)
}
ORDER BY ?similarSpecies ?sharedHabitat ?differentDiet
```

### `risky_species_by_location`

Lists risky species observed at a selected location.

```sparql
SELECT DISTINCT
  ?species
  ?status
  ?trend
WHERE {
  ?observation rdf:type birds:Observation ;
    birds:isObservedAtLocation birds:{location} ;
    birds:observedBird ?bird .
  ?bird birds:belongsToSpecies ?species .
  ?species birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}
ORDER BY ?species
```

### `diet_generalists`

Lists species with at least three different diet values.

```sparql
SELECT
  ?species
  (COUNT(DISTINCT ?diet) AS ?dietCount)
WHERE {
  ?species rdf:type birds:Species ;
    birds:hasTypicalDiet ?diet .
}
GROUP BY ?species
HAVING(COUNT(DISTINCT ?diet) >= 3)
ORDER BY DESC(?dietCount) ?species
```

### `urban_at_risk`

Lists urban species that are threatened or decreasing.

```sparql
SELECT DISTINCT
  ?species
  ?status
  ?trend
WHERE {
  ?species rdf:type birds:Species ;
    birds:hasTypicalHabitat birds:UrbanParksAndGardens ;
    birds:hasIUCNStatus ?status ;
    birds:hasPopulationTrend ?trend .
  FILTER(?status IN (birds:VU, birds:EN, birds:CR) || ?trend = birds:Decreasing)
}
ORDER BY ?species
```

### `season_mismatch_observations`

Lists observations made outside a species breeding season.

```sparql
SELECT DISTINCT
  ?observation
  ?date
  ?species
  ?season
  ?observedSeason
WHERE {
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
  FILTER NOT EXISTS {
    ?species birds:hasBreedingSeason ?observedSeasonResource .
  }
}
ORDER BY ?date
```

### `morphology_profile`

Lists morphology attributes for all species.

```sparql
SELECT DISTINCT
  ?species
  ?beak
  ?legs
  ?tail
  ?wings
  ?plumage
WHERE {
  ?species rdf:type birds:Species .
  ?species birds:hasBeakMorphology ?beak ;
    birds:hasLegMorphology ?legs ;
    birds:hasTailMorphology ?tail ;
    birds:hasWingMorphology ?wings ;
    birds:hasTypicalPlumagePattern ?plumage .
}
ORDER BY ?species
```

### `taxonomic_path`

Shows the taxonomic chain for a selected species.

```sparql
SELECT DISTINCT
  ?species
  ?genus
  ?family
  ?order
  ?class
  ?phylum
  ?kingdom
WHERE {
  VALUES ?species { birds:{species} }
  ?species birds:hasParentTaxon ?genus .
  ?genus birds:hasParentTaxon ?family .
  ?family birds:hasParentTaxon ?order .
  ?order birds:hasParentTaxon ?class .
  ?class birds:hasParentTaxon ?phylum .
  ?phylum birds:hasParentTaxon ?kingdom .
}
```

### `species_profile`

Builds the profile rows for a selected species.

```sparql
SELECT DISTINCT
  ?property
  ?value
WHERE {
  VALUES ?species { birds:{species} }
  {
    BIND("Вид" AS ?property)
    BIND(?species AS ?value)
  }
  UNION {
    ?species birds:foundInRegion ?value .
    BIND("Регион" AS ?property)
  }
  UNION {
    ?species birds:hasIUCNStatus ?value .
    BIND("IUCN статус" AS ?property)
  }
  UNION {
    ?species birds:hasPopulationTrend ?value .
    BIND("Популационна тенденция" AS ?property)
  }
  UNION {
    ?species birds:hasMigratoryBehaviour ?value .
    BIND("Миграционно поведение" AS ?property)
  }
  UNION {
    ?species birds:hasTypicalHabitat ?value .
    BIND("Местообитание" AS ?property)
  }
  UNION {
    ?species birds:hasTypicalDiet ?value .
    BIND("Храна" AS ?property)
  }
  UNION {
    ?species birds:hasBreedingSeason ?value .
    BIND("Размножителен сезон" AS ?property)
  }
  UNION {
    ?species birds:hasTypicalPlumagePattern ?value .
    BIND("Оперение" AS ?property)
  }
  UNION {
    ?species birds:hasBeakMorphology ?value .
    BIND("Клюн" AS ?property)
  }
  UNION {
    ?species birds:hasLegMorphology ?value .
    BIND("Крака" AS ?property)
  }
  UNION {
    ?species birds:hasTailMorphology ?value .
    BIND("Опашка" AS ?property)
  }
  UNION {
    ?species birds:hasWingMorphology ?value .
    BIND("Крила" AS ?property)
  }
  UNION {
    ?species birds:hasParentTaxon ?value .
    BIND("Род" AS ?property)
  }
}
ORDER BY ?property ?value
```
