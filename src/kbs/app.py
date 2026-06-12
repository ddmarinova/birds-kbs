"""Streamlit app for SPARQL question answering over the bird ontology."""

from __future__ import annotations

import base64
import mimetypes
import re
import textwrap
from html import escape
from pathlib import Path

import streamlit as st
from rdflib import Graph, URIRef
from rdflib.exceptions import ParserError
from rdflib.namespace import RDFS
from pyparsing.exceptions import ParseException

from kbs.local_store import BIRDS, load_graph, query_to_sparql_json
from kbs.sparql import (
    BASIC_QUESTIONS,
    CURIOSITY_QUESTIONS,
    DEFAULT_QUERY,
    FILTER_DEFINITIONS,
    QUESTION_LABELS,
    REASONER_CATEGORY_OPTIONS,
    RECOMMENDATION_QUESTIONS,
    SIMILARITY_CRITERIA,
    Option,
    build_question_query,
    build_species_profile_query,
    build_species_filter_query,
    humanize_local_name,
    local_name,
    option_query,
)

REASONER_INFERRED_CATEGORY_OPTIONS = [
    option
    for option in REASONER_CATEGORY_OPTIONS
    if option.local_name
    in {
        "UrbanSpecies",
        "ResidentSpecies",
        "MigratorySpecies",
        "DeciduousForestSpecies",
        "InsectivorousSpecies",
        "ThreatenedSpecies",
    }
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORNER_IMAGE_PATH = PROJECT_ROOT / "images" / "image.png"
FAVICON_PATH = PROJECT_ROOT / "images" / "favicon.png"

COLUMN_LABELS = {
    "beak": "Клюн",
    "behavior": "Поведение",
    "bird": "Птица",
    "class": "Клас",
    "criterion": "Критерий",
    "date": "Дата",
    "differentDiet": "Различна храна",
    "dietCount": "Брой храни",
    "family": "Семейство",
    "genus": "Род",
    "inferredType": "Изведен тип",
    "kingdom": "Царство",
    "legs": "Крака",
    "location": "Локация",
    "morphology": "Морфология",
    "observation": "Наблюдение",
    "observedSeason": "Сезон на наблюдение",
    "observedSpecies": "Наблюдаван вид",
    "order": "Разред",
    "phylum": "Тип",
    "plumage": "Оперение",
    "property": "Свойство",
    "recommendedSpecies": "Препоръчан вид",
    "score": "Оценка",
    "season": "Размножителен сезон",
    "sharedHabitat": "Общо местообитание",
    "sharedValue": "Обща стойност",
    "similarSpecies": "Подобен вид",
    "species": "Вид",
    "status": "IUCN статус",
    "tail": "Опашка",
    "trend": "Популационна тенденция",
    "value": "Стойност",
    "wings": "Крила",
}


def apply_custom_styles() -> None:
    st.markdown(
        """
        <style>
        .stButton > button,
        .stDownloadButton > button {
            background-color: #2F7D5C;
            border-color: #2F7D5C;
            color: #FFFFFF;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: #25674B;
            border-color: #25674B;
            color: #FFFFFF;
        }

        .stButton > button:focus,
        .stDownloadButton > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(47, 125, 92, 0.25);
            color: #FFFFFF;
        }

        .species-image-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }

        .species-image-frame {
            height: 160px;
            background: #FFFFFF;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .species-image-frame img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }

        .profile-summary {
            display: grid;
            gap: 8px;
            margin: 12px 0 16px 0;
        }

        .profile-row {
            background: #FFFFFF;
            border-left: 4px solid #2F7D5C;
            border-radius: 6px;
            padding: 10px 12px;
        }

        .profile-property {
            color: #2F7D5C;
            font-weight: 700;
            margin-right: 6px;
        }

        .corner-image {
            width: 96px;
            height: auto;
            display: block;
            margin-top: -50px;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_corner_image() -> None:
    image_src = image_source_to_src(CORNER_IMAGE_PATH)
    if not image_src:
        return

    st.markdown(
        f'<img class="corner-image" src="{escape(image_src)}" alt="">',
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_graph(infer: bool = True) -> Graph:
    return load_graph(infer=infer)


def run_sparql_query(query: str, infer: bool | None = None) -> dict:
    """Run a SPARQL query against the bundled ontology."""
    graph = get_graph(infer=infer is not False)
    return query_to_sparql_json(graph, query)


def results_to_rows(payload: dict) -> list[dict[str, str]]:
    """Convert SPARQL JSON results into display rows."""
    rows = []

    for binding in payload.get("results", {}).get("bindings", []):
        row = {}
        for key, value in binding.items():
            raw_value = value.get("value", "")
            row[display_column_name(key)] = display_value(raw_value)
        rows.append(row)

    return rows


def display_column_name(name: str) -> str:
    return COLUMN_LABELS.get(name, humanize_local_name(name))


def display_value(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return label_for_uri(value) or humanize_local_name(value)
    return humanize_local_name(value)


def label_for_uri(uri: str) -> str | None:
    labels = list(get_graph().objects(URIRef(uri), RDFS.label))
    bg_labels = [str(label) for label in labels if label.language == "bg"]
    en_labels = [str(label) for label in labels if label.language == "en"]

    if bg_labels:
        return bg_labels[0]
    if en_labels:
        return en_labels[0]
    if labels:
        return str(labels[0])

    return None


def species_image_sources(species: Option) -> list[str | Path]:
    image_values = list(get_graph().objects(URIRef(species.uri), BIRDS.hasImageUrl))
    sources = []

    for value in image_values:
        image_value = str(value)
        if image_value.startswith(("http://", "https://")):
            sources.append(image_value)
        else:
            sources.append(PROJECT_ROOT / image_value)

    return sources


def render_species_images(species: Option) -> None:
    image_sources = species_image_sources(species)
    if not image_sources:
        return

    image_tags = []
    for image_source in image_sources:
        image_src = image_source_to_src(image_source)
        if image_src:
            image_tags.append(
                f'<div class="species-image-frame"><img src="{escape(image_src)}" alt="{escape(species.label)}"></div>'
            )

    if not image_tags:
        return

    st.markdown(
        f"""
        <div class="species-image-grid">
            {''.join(image_tags)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_source_to_src(image_source: str | Path) -> str | None:
    if isinstance(image_source, str):
        return image_source

    if not image_source.exists():
        return None

    mime_type = mimetypes.guess_type(image_source)[0] or "image/jpeg"
    encoded = base64.b64encode(image_source.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@st.cache_data(show_spinner=False)
def load_options(class_name: str) -> list[Option]:
    payload = run_sparql_query(option_query(class_name))
    options = []
    for binding in payload.get("results", {}).get("bindings", []):
        uri = binding["item"]["value"]
        label = (
            label_for_uri(uri)
            or binding.get("label", {}).get("value")
            or humanize_local_name(uri)
        )
        options.append(Option(label=label, uri=uri, local_name=local_name(uri)))
    return options


def display_query_result(
    query: str,
    infer: bool | None = None,
) -> list[dict[str, str]]:
    try:
        payload = run_sparql_query(query, infer=infer)
        rows = results_to_rows(payload)
    except (ParseException, ParserError, ValueError, TypeError) as error:
        st.error(f"SPARQL заявката не може да бъде изпълнена: {error}")
        return []

    if "boolean" in payload:
        st.success(f"ASK резултат: {payload['boolean']}")
        return [{"boolean": str(payload["boolean"])}]
    elif rows:
        st.success(f"Върнати резултати: {len(rows)}")
        st.dataframe(rows, width="stretch", hide_index=True)
        return rows
    else:
        st.error("Заявката е изпълнена успешно, но няма резултати.")
        return [{"result": "Няма резултати"}]


def display_profile_result(query: str) -> list[dict[str, str]]:
    try:
        payload = run_sparql_query(query)
        rows = group_profile_rows(results_to_rows(payload))
    except (ParseException, ParserError, ValueError, TypeError) as error:
        st.error(f"SPARQL заявката не може да бъде изпълнена: {error}")
        return []

    if rows:
        st.success(f"Върнати свойства: {len(rows)}")
        render_profile_summary(rows)
        return rows
    else:
        st.error("Заявката е изпълнена успешно, но няма резултати.")
        return [{"result": "Няма резултати"}]


def group_profile_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[str]] = {}

    for row in rows:
        property_name = row.get("Свойство", "")
        value = row.get("Стойност", "")
        if not property_name or not value:
            continue
        grouped.setdefault(property_name, [])
        if value not in grouped[property_name]:
            grouped[property_name].append(value)

    return [
        {"Свойство": property_name, "Стойност": ", ".join(values)}
        for property_name, values in grouped.items()
    ]


def render_profile_summary(rows: list[dict[str, str]]) -> None:
    items = []
    for row in rows:
        property_name = escape(row["Свойство"])
        value = escape(row["Стойност"])
        items.append(
            f'<div class="profile-row"><span class="profile-property">{property_name}:</span>{value}</div>'
        )

    st.markdown(
        f'<div class="profile-summary">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def query_and_rows_to_svg(query: str, rows: list[dict[str, str]]) -> str:
    query_lines = ["SPARQL заявка", ""] + query.strip().splitlines()
    lines = []
    lines.extend(query_lines)
    lines.extend(["", "", "Резултати", ""])

    headers = list(rows[0])
    lines.append(" | ".join(headers))
    lines.append("-" * min(110, len(lines[-1])))

    for index, row in enumerate(rows, start=1):
        values = " | ".join(row.get(header, "") for header in headers)
        wrapped = textwrap.wrap(f"{index}. {values}", width=120) or [""]
        lines.extend(wrapped)

    width = 1400
    line_height = 24
    padding = 32
    height = max(180, padding * 2 + line_height * len(lines))

    text_lines = []
    for index, line in enumerate(lines):
        y = padding + 18 + index * line_height
        text_lines.append(
            f'<text x="{padding}" y="{y}" font-family="Menlo, Consolas, monospace" font-size="18" fill="#17231C">{escape(line)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" rx="18" fill="#F6F8F4"/>
  <rect x="18" y="18" width="{width - 36}" height="{height - 36}" rx="14" fill="#E7EFE8" stroke="#2F7D5C" stroke-width="2"/>
  {''.join(text_lines)}
</svg>
"""


def render_query_result_export(
    query: str,
    rows: list[dict[str, str]],
    file_name: str,
) -> None:
    if not rows:
        return

    safe_name = safe_file_name(file_name, suffix=".svg")
    st.download_button(
        "Изтегли заявката",
        data=query_and_rows_to_svg(query, rows).encode("utf-8"),
        file_name=safe_name,
        mime="image/svg+xml",
        key=f"query-results-svg-{safe_name}",
    )


def render_reasoner_export(
    query: str,
    with_inference_rows: list[dict[str, str]],
    without_inference_rows: list[dict[str, str]],
    file_name: str,
) -> None:
    rows = reasoner_export_rows(with_inference_rows, without_inference_rows)
    render_query_result_export(query, rows, file_name)


def reasoner_export_rows(
    with_inference_rows: list[dict[str, str]],
    without_inference_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        *add_result_mode("С включени изводи", with_inference_rows),
        *add_result_mode("Без изводи", without_inference_rows),
    ]


def add_result_mode(mode: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return [{"Режим": mode, "Резултат": "Няма резултати"}]

    return [{"Режим": mode, **row} for row in rows]


def safe_file_name(file_name: str, suffix: str) -> str:
    stem = file_name.removesuffix(".svg").removesuffix(".csv")
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-")
    return f"{safe_stem or 'sparql-export'}{suffix}"


def render_query_block(query: str, title: str = "SPARQL заявка") -> None:
    with st.expander(title):
        st.code(query, language="sparql")


def load_filter_options() -> dict[str, list[Option]]:
    options = {}
    for key, (_, class_name, _, _) in FILTER_DEFINITIONS.items():
        options[key] = load_options(class_name)
    return options


def two_column_field_containers(field_count: int):
    containers = []
    full_width_last = field_count % 2 == 1
    paired_count = field_count - int(full_width_last)

    for _ in range(0, paired_count, 2):
        containers.extend(st.columns(2))

    if full_width_last:
        containers.append(st.container())

    return containers


def question_option_count(question: str) -> int:
    if question in {
        "species_by_habitat",
        "species_by_diet",
        "observations_by_location",
        "similar_species",
        "explain_similarity",
        "inferred_category",
        "inverse_reasoner_demo",
        "reasoner_check",
        "location_recommendations",
        "species_location_recommendations",
        "similar_habitat_different_diet",
        "risky_species_by_location",
        "taxonomic_path",
    }:
        return 1

    return 0


def question_field_count(question: str) -> int:
    count = 1 + question_option_count(question)
    if question in {"similar_species", "explain_similarity"}:
        count += 1

    return count


def render_filters() -> None:
    st.subheader("Филтрация на видове")

    try:
        all_options = load_filter_options()
    except (ParserError, ValueError) as error:
        st.error(f"Не мога да заредя филтрите от онтологията: {error}")
        return

    selected_filters = {}
    filter_definitions = list(FILTER_DEFINITIONS.items())
    columns = st.columns(3)

    for index, (key, (label, _, _, _)) in enumerate(filter_definitions):
        with columns[index % len(columns)]:
            selected_filters[key] = st.multiselect(
                label,
                options=all_options[key],
                format_func=lambda option: option.label,
            )

    query = build_species_filter_query(selected_filters)
    rows = display_query_result(query)
    render_query_block(query)
    render_query_result_export(query, rows, "filter-results")


def render_question_group(question_keys: list[str]) -> None:
    group_key = "_".join(question_keys)
    question_key = f"{group_key}_question"
    active_question = st.session_state.get(question_key, question_keys[0])
    if active_question not in question_keys:
        active_question = question_keys[0]

    field_containers = two_column_field_containers(question_field_count(active_question))

    with field_containers[0]:
        question = st.selectbox(
            "Въпрос",
            options=question_keys,
            format_func=lambda key: QUESTION_LABELS[key],
            key=question_key,
        )

    selected = None
    criterion = "combined"
    try:
        if question_option_count(question):
            option_container = field_containers[1]
        else:
            option_container = st.container()

        with option_container:
            if question == "species_by_habitat":
                selected = st.selectbox(
                    "Местообитание",
                    options=load_options("Habitat"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_habitat",
                )
            elif question == "species_by_diet":
                selected = st.selectbox(
                    "Храна",
                    options=load_options("Diet"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_diet",
                )
            elif question == "observations_by_location":
                selected = st.selectbox(
                    "Локация",
                    options=load_options("Location"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_location",
                )
            elif question in {"similar_species", "explain_similarity"}:
                selected = st.selectbox(
                    "Вид",
                    options=load_options("Species"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_species",
                )
            elif question == "inferred_category":
                selected = st.selectbox(
                    "Клас",
                    options=REASONER_CATEGORY_OPTIONS,
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_category",
                )
            elif question in {"inverse_reasoner_demo", "reasoner_check"}:
                selected = st.selectbox(
                    "Вид",
                    options=load_options("Species"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_species",
                )
            elif question == "location_recommendations":
                selected = st.selectbox(
                    "Локация",
                    options=load_options("Location"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_location",
                )
            elif question in {
                "species_location_recommendations",
                "similar_habitat_different_diet",
            }:
                selected = st.selectbox(
                    "Вид",
                    options=load_options("Species"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_species",
                )
            elif question == "risky_species_by_location":
                selected = st.selectbox(
                    "Локация",
                    options=load_options("Location"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_location",
                )
            elif question == "taxonomic_path":
                selected = st.selectbox(
                    "Вид",
                    options=load_options("Species"),
                    format_func=lambda option: option.label,
                    key=f"{group_key}_{question}_species",
                )
    except (ParserError, ValueError) as error:
        st.error(f"Не мога да заредя опциите от онтологията: {error}")
        return

    if question in {"similar_species", "explain_similarity"}:
        with field_containers[2]:
            criterion = st.selectbox(
                "Критерий",
                options=list(SIMILARITY_CRITERIA),
                format_func=lambda key: SIMILARITY_CRITERIA[key][0],
                key=f"{group_key}_{question}_criterion",
            )

    query = build_question_query(question, selected, criterion=criterion)

    if question == "reasoner_check":
        st.markdown("### С включени изводи")
        with_inference_rows = display_query_result(query, infer=True)
        st.markdown("### Без изводи")
        without_inference_rows = display_query_result(query, infer=False)
        render_query_block(query)
        render_reasoner_export(
            query,
            with_inference_rows,
            without_inference_rows,
            f"{question}-reasoner-results",
        )
    else:
        rows = display_query_result(query)
        render_query_block(query)
        render_query_result_export(query, rows, f"{question}-results")


def render_questions() -> None:
    st.subheader("Въпроси")
    render_question_group(BASIC_QUESTIONS + CURIOSITY_QUESTIONS)


def render_recommendations() -> None:
    st.subheader("Препоръки")
    render_question_group(RECOMMENDATION_QUESTIONS)


def render_species_profile() -> None:
    st.subheader("Профил на вид")

    try:
        selected = st.selectbox(
            "Вид",
            options=load_options("Species"),
            format_func=lambda option: option.label,
            key="species_profile_species",
        )
    except (ParserError, ValueError) as error:
        st.error(f"Не мога да заредя видовете от онтологията: {error}")
        return

    render_species_images(selected)

    query = build_species_profile_query(selected)
    rows = display_profile_result(query)
    render_query_block(query)
    render_query_result_export(query, rows, f"{selected.local_name}-profile-results")


def render_reasoner_questions() -> None:
    st.subheader("Логически изводи")

    try:
        species_options = load_options("Species")
    except (ParserError, ValueError) as error:
        st.error(f"Не мога да заредя опциите от онтологията: {error}")
        return

    inference_examples = {
        "observedBird -> hasObservation": "reasoner_check",
        "belongsToSpecies -> isSpeciesOf": "species_inverse_check",
        "Species -> Taxon": "subclass_reasoner_check",
        "BeakMorphology -> Morphology": "morphology_subclass_check",
        "OWL клас -> rdf:type": "category_reasoner_check",
    }

    example_column, resource_column = st.columns(2)
    with example_column:
        selected_example = st.selectbox(
            "Тип логически извод",
            options=list(inference_examples),
            key="reasoner_example",
        )
    with resource_column:
        if selected_example == "BeakMorphology -> Morphology":
            selected_resource = st.selectbox(
                "Морфология за проверка",
                options=load_options("BeakMorphology"),
                format_func=lambda option: option.label,
                key="reasoner_morphology",
            )
        elif selected_example == "OWL клас -> rdf:type":
            selected_resource = st.selectbox(
                "Клас за проверка",
                options=REASONER_INFERRED_CATEGORY_OPTIONS,
                format_func=lambda option: option.label,
                key="reasoner_inferred_category",
            )
        else:
            selected_resource = st.selectbox(
                "Вид за проверка",
                options=species_options,
                format_func=lambda option: option.label,
                key="reasoner_species",
            )

    query = build_question_query(inference_examples[selected_example], selected_resource)

    st.markdown("##### С включени изводи")
    with_inference_rows = display_query_result(query, infer=True)
    st.markdown("##### Без изводи")
    without_inference_rows = display_query_result(query, infer=False)

    render_query_block(query, title="SPARQL заявки")
    render_reasoner_export(
        query,
        with_inference_rows,
        without_inference_rows,
        f"{selected_example}-reasoner-results",
    )


def render_custom_sparql() -> None:
    st.subheader("Свободна SPARQL заявка")
    query = st.text_area("SPARQL", value=DEFAULT_QUERY, height=300)
    if st.button("Изпълни заявката"):
        rows = display_query_result(query)
        render_query_block(query)
        render_query_result_export(query, rows, "custom-sparql-results")


def main() -> None:
    st.set_page_config(
        page_title="Birds KBS",
        page_icon=str(FAVICON_PATH),
        layout="wide",
    )
    apply_custom_styles()
    render_corner_image()
    st.title("Birds KBS")
    st.write("Семантична система за филтрация, препоръки и заявки върху онтология за птиците в България")

    tab_filters, tab_questions, tab_profile, tab_recommendations, tab_reasoner, tab_sparql = st.tabs(
        ["Филтрация", "Въпроси", "Профил на вид", "Препоръки", "Логически изводи", "Свободна заявка"]
    )

    with tab_filters:
        render_filters()
    with tab_questions:
        render_questions()
    with tab_profile:
        render_species_profile()
    with tab_recommendations:
        render_recommendations()
    with tab_reasoner:
        render_reasoner_questions()
    with tab_sparql:
        render_custom_sparql()


if __name__ == "__main__":
    main()
