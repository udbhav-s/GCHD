# =============================================================================
# brief.py — Turns one region's exposure figures into a readable summary.
# No Earth Engine and no Dash import, so the content rules can be tested
# directly.
# =============================================================================
#
# Two rules govern everything here.
#
# A figure never travels without the condition that produced it. "36,414
# children" means nothing on its own; "36,414 children where 2024 brought 30 or
# more days above 35 °C" can be checked and argued with.
#
# Absent is not zero. A hazard with no data in a region is reported as having no
# data. Writing 0 would put it beside regions the hazard genuinely misses.

from config import (
    ACCESS_OFF,
    DURATION_HAZARDS,
    HAZARD_INFO,
    HAZARD_TOPICS,
    UNDER_FIVE_LABEL,
    baseline_label,
    clean_access,
    clean_durations,
    clean_frequency,
    clean_period,
)

NOT_AVAILABLE = "no data"

TOPIC_BY_HAZARD = {
    name: topic for topic, names in HAZARD_TOPICS.items() for name in names
}
HAZARD_BY_TOPIC = {topic: names[0] for topic, names in HAZARD_TOPICS.items()}


def _safe_int(value):
    return int(round(value or 0))


def conditions(view):
    """The settings the figures were produced under, in plain words."""
    view = view or {}
    durations = clean_durations(view.get("durations"))
    period = clean_period(view.get("period"))
    frequency = clean_frequency(view.get("frequency"))
    access = view.get("access", ACCESS_OFF)

    lines = []
    for hazard in DURATION_HAZARDS:
        topic = TOPIC_BY_HAZARD.get(hazard["name"], hazard["name"])
        minimum = durations[hazard["name"]]
        unit = hazard["duration_unit"]
        lasted = "any" if minimum <= 1 else f"{minimum} or more"
        lines.append(f"{topic}: counted where it lasted {lasted} {unit}")

    if period == "typical":
        windows = ", ".join(
            f"{TOPIC_BY_HAZARD.get(h['name'], h['name'])} {baseline_label(h)}"
            for h in DURATION_HAZARDS
        )
        lines.append(
            f"Counted across a typical year, needing {frequency} or more "
            f"qualifying years in every ten ({windows})"
        )
    else:
        lines.append("Counted for the single year 2024, which was the warmest on record")

    if access != ACCESS_OFF:
        lines.append(
            f"Care treated as out of reach beyond {clean_access(access)} minutes "
            "of motorised travel"
        )
    return lines


def ranked_hazards(result):
    """Hazards worst first, with the ones carrying no data kept separate.

    Sorting puts the largest exposure at the top, which is the order someone
    deciding where to look wants. Regions a hazard does not cover are listed
    after, unranked, rather than sorted to the bottom as if they were zero.
    """
    total = _safe_int(result.get("total_population"))
    ranked, unavailable = [], []

    for topic in HAZARD_TOPICS:
        covered = (result.get("cov_" + _safe_key(topic)) or 0) > 0
        if not covered:
            unavailable.append(topic)
            continue
        exposed = _safe_int(result.get(topic))
        ranked.append(
            {
                "topic": topic,
                "children": exposed,
                "share": (exposed / total * 100) if total else None,
                "under_five": _safe_int(result.get("u5_" + topic)),
                "beyond_care": _safe_int(result.get("far_" + topic)),
            }
        )

    ranked.sort(key=lambda row: row["children"], reverse=True)
    return ranked, unavailable


def _safe_key(topic):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "_", topic)


def what_is_missing(view):
    """What this brief cannot tell you. Stated every time, not on request."""
    view = view or {}
    gaps = [
        "Vulnerability here is age alone. Poverty, health, housing, disability "
        "and displacement are all absent.",
        "Travel time says whether care can be reached, not whether it has beds, "
        "staff, or anyone who treats children.",
        "Hazard severity is not measured. A day one degree over the threshold "
        "counts the same as a day ten degrees over.",
        "Population is from 2020 and hazard layers from 2024 or earlier, so the "
        "two describe different moments.",
    ]
    if clean_period(view.get("period")) == "observed":
        gaps.append(
            "These are single-year figures. They say what happened in 2024, not "
            "how likely it is to happen again."
        )
    if view.get("access", ACCESS_OFF) == ACCESS_OFF:
        gaps.append("Access to care was not counted in these figures.")
    return gaps


def sources(result):
    """Every input behind the figures, with its date."""
    used = ["population_worldpop_2020"]
    used += [HAZARD_BY_TOPIC[t] for t in HAZARD_TOPICS if t in HAZARD_BY_TOPIC]
    from config import ACCESS_LAYER, UNDER_FIVE_LAYER

    used.append(UNDER_FIVE_LAYER)
    if (result.get("_view") or {}).get("access", ACCESS_OFF) != ACCESS_OFF:
        used.append(ACCESS_LAYER)

    listed = []
    for name in used:
        info = HAZARD_INFO.get(name)
        if not info:
            continue
        listed.append(
            {
                "layer": name,
                "source": info.get("source", NOT_AVAILABLE),
                "as_of": info.get("availability", NOT_AVAILABLE),
                "resolution": info.get("native_resolution", NOT_AVAILABLE),
                "known_gaps": info.get("known_gaps", ""),
            }
        )
    return listed


def build(result, region_name, admin_level, case_studies=None):
    """Everything the brief shows, as plain data."""
    if not result:
        return None

    view = result.get("_view") or {}
    total = _safe_int(result.get("total_population"))
    under_five = _safe_int(result.get("total_under_five"))
    ranked, unavailable = ranked_hazards(result)

    return {
        "region": region_name or "Unnamed region",
        "admin_level": admin_level or NOT_AVAILABLE,
        "children": total,
        "under_five": under_five,
        "under_five_share": (under_five / total * 100) if total else None,
        "beyond_care": (
            _safe_int(result.get("beyond_care"))
            if "beyond_care" in result
            else None
        ),
        "hazards": ranked,
        "no_data_hazards": unavailable,
        "conditions": conditions(view),
        "missing": what_is_missing(view),
        "sources": sources(result),
        "case_studies": list(case_studies or [])[:5],
    }


def format_number(value):
    """Thousands separated, and absent stated rather than drawn as zero."""
    if value is None:
        return NOT_AVAILABLE
    return f"{value:,}"


def format_share(value):
    if value is None:
        return NOT_AVAILABLE
    return f"{value:.1f}%"


def to_html(data):
    """A standalone page the browser can print to PDF.

    Plain HTML rather than a PDF library: it adds no dependency, and a brief
    that opens in a tab gets read more often than one that downloads.
    """
    if not data:
        return "<p>No region selected.</p>"

    def esc(text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    rows = []
    for row in data["hazards"]:
        far = (
            f"<td>{format_number(row['beyond_care'])}</td>"
            if data["beyond_care"] is not None
            else "<td>—</td>"
        )
        rows.append(
            f"<tr><td>{esc(row['topic'])}</td>"
            f"<td>{format_number(row['children'])}</td>"
            f"<td>{format_share(row['share'])}</td>"
            f"<td>{format_number(row['under_five'])}</td>{far}</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="5">No hazard data covers this region.</td></tr>')

    no_data = (
        "<p class='gap'>No data for: "
        + ", ".join(esc(t) for t in data["no_data_hazards"])
        + ". These are not zero — the layers do not reach here.</p>"
        if data["no_data_hazards"]
        else ""
    )

    studies = "".join(
        f"<li>{esc(s.get('title') or s.get('id'))}</li>" for s in data["case_studies"]
    )
    studies_block = (
        f"<h2>Interventions recorded nearby</h2><ul>{studies}</ul>" if studies else ""
    )

    source_rows = "".join(
        f"<tr><td>{esc(s['source'])}</td><td>{esc(s['as_of'])}</td>"
        f"<td>{esc(s['resolution'])}</td></tr>"
        for s in data["sources"]
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{esc(data['region'])} — child hazard and exposure brief</title>
<style>
 body {{ font: 13px/1.55 Georgia, serif; color: #1a1a2e; max-width: 46em;
         margin: 2.5em auto; padding: 0 1.5em; }}
 h1 {{ font-size: 1.5em; margin-bottom: 0.1em; }}
 .sub {{ color: #555; margin-top: 0; }}
 h2 {{ font-size: 1em; margin-top: 1.8em; border-bottom: 1px solid #ddd;
       padding-bottom: 0.2em; }}
 table {{ border-collapse: collapse; width: 100%; margin-top: 0.6em; }}
 th, td {{ text-align: left; padding: 4px 8px; border-bottom: 1px solid #eee; }}
 th {{ font-size: 0.85em; color: #555; font-weight: normal; }}
 td:nth-child(n+2), th:nth-child(n+2) {{ text-align: right; }}
 ul {{ padding-left: 1.2em; }}
 li {{ margin-bottom: 0.3em; }}
 .gap {{ color: #555; font-style: italic; }}
 .caveat {{ background: #f7f7f9; padding: 0.9em 1.1em; border-left: 3px solid #1CABE2; }}
 footer {{ margin-top: 2.5em; font-size: 0.8em; color: #666; }}
 @media print {{ body {{ margin: 0; }} h2 {{ page-break-after: avoid; }} }}
</style></head><body>
<h1>{esc(data['region'])}</h1>
<p class="sub">Child hazard and exposure brief · {esc(data['admin_level'])}</p>

<div class="caveat">
<strong>This is a screening aid, not a risk assessment.</strong> It pairs hazard
layers with where children live. It does not measure how badly a hazard would
hurt them.
</div>

<h2>Children</h2>
<p>{format_number(data['children'])} children under 18, of whom
{format_number(data['under_five'])} ({format_share(data['under_five_share'])}) are
{esc(UNDER_FIVE_LABEL)}.
{"" if data['beyond_care'] is None else
 f"{format_number(data['beyond_care'])} live beyond the travel time set below."}</p>

<h2>Hazards, worst first</h2>
<table>
<tr><th>Hazard</th><th>Children exposed</th><th>Share</th><th>Under 5</th>
<th>Far from care</th></tr>
{''.join(rows)}
</table>
{no_data}

<h2>How these figures were counted</h2>
<ul>{''.join(f'<li>{esc(line)}</li>' for line in data['conditions'])}</ul>

<h2>What this cannot tell you</h2>
<ul>{''.join(f'<li>{esc(line)}</li>' for line in data['missing'])}</ul>
{studies_block}

<h2>Sources</h2>
<table><tr><th>Source</th><th>Data as of</th><th>Resolution</th></tr>
{source_rows}</table>

<footer>Global Child Hazard Database, public-data build. Boundaries: UNICEF
GeoRepo (CC BY 4.0).</footer>
</body></html>"""
