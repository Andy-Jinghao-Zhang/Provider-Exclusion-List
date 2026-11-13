
import sqlite3
from pathlib import Path
from contextlib import closing
from flask import Flask, request, render_template_string

app = Flask(__name__)

db_path = Path(__file__).parent / "providers.db"

# Database table settings
tables = {
    "federal": {
        "table": "excluded_providers",
        "first": "FIRSTNAME",
        "last": "LASTNAME",
        "business": "BUSNAME",
        "city": "CITY",
        "state": "STATE",
        "npi": "NPI"
    },
    "georgia": {
        "table": "georgia_exclusions",
        "first": "first_name",
        "last": "last_name",
        "business": "business_name",
        "city": "NULL",
        "state": "state",
        "npi": "npi"
    }
}


html = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Provider Exclusion List</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f5f7fa;
            margin: 0;
            padding: 40px 20px;
            color: #253348;
        }

        .container {
            max-width: 1050px;
            margin: auto;
        }

        h1 {
            color: #183b63;
            margin-bottom: 12px;
        }

        h2 {
            margin-top: 0;
            color: #253348;
        }

        .subtitle {
            color: #637083;
            margin-bottom: 25px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px #00000010;
        }

        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .stat {
            flex: 1;
            min-width: 150px;
            background: #edf3fa;
            padding: 18px;
            border-radius: 8px;
        }

        .stat strong {
            display: block;
            font-size: 25px;
            margin-top: 8px;
            color: #253348;
        }

        .source-options {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 10px;
            margin-bottom: 20px;
        }

        .source-option {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #edf3fa;
            padding: 12px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: normal;
        }

        .source-option input {
            width: auto;
            margin: 0;
            accent-color: #23588a;
        }

        .field-label {
            display: block;
            margin-top: 16px;
            font-weight: bold;
        }

        .text-input {
            width: 100%;
            padding: 12px;
            margin-top: 6px;
            border: 1px solid #ccd5df;
            border-radius: 5px;
            font-size: 14px;
            background: white;
            color: #253348;
        }

        .text-input:focus {
            outline: 2px solid #82b0db;
        }

        .buttons {
            display: flex;
            gap: 12px;
            margin-top: 22px;
        }

        button {
            background: #23588a;
            color: white;
            padding: 12px 28px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }

        button:hover {
            background: #17436e;
        }

        .clear-button {
            background: #e8edf2;
            color: #253348;
            padding: 12px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
        }

        .clear-button:hover {
            background: #dbe4ed;
        }

        .table-wrap {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #e0e5eb;
            text-align: left;
            font-size: 14px;
        }

        th {
            background: #edf3fa;
            white-space: nowrap;
        }

        tr:hover {
            background: #f8fafc;
        }

        .note {
            color: #637083;
            font-size: 13px;
            margin-top: 15px;
        }

        .result-section {
            margin-top: 25px;
        }

        .result-count {
            font-size: 20px;
            color: #183b63;
            font-weight: bold;
        }

        .empty {
            color: #637083;
            padding: 15px 0;
        }

        @media (max-width: 600px) {
            body {
                padding: 20px 10px;
            }

            .card {
                padding: 18px;
            }

            .stats {
                flex-direction: column;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <h1>Provider Exclusion List</h1>

    <p class="subtitle">
        Healthcare Provider Exclusion Database
    </p>

    <!-- Database Overview -->

    <div class="card">

        <h2>Database Overview</h2>

        <div class="stats">

            <div class="stat">
                Federal OIG
                <strong>{{ federal_count }}</strong>
            </div>

            <div class="stat">
                Georgia OIG
                <strong>{{ georgia_count }}</strong>
            </div>

            <div class="stat">
                Total Records
                <strong>{{ total_count }}</strong>
            </div>

        </div>

        <p class="note">
            Total records have not been deduplicated
            across data sources.
        </p>

    </div>


    <!-- Search Form -->

    <div class="card">

        <h2>Search Excluded Providers</h2>

        <form method="GET" action="/">

            <input type="hidden" name="search" value="1">

            <label class="field-label">Data Source</label>

            <div class="source-options">

                <label class="source-option">
                    <input
                        type="radio"
                        name="source"
                        value="both"
                        {% if selected_source == "both" %}
                        checked
                        {% endif %}
                    >
                    Both
                </label>

                <label class="source-option">
                    <input
                        type="radio"
                        name="source"
                        value="federal"
                        {% if selected_source == "federal" %}
                        checked
                        {% endif %}
                    >
                    Federal OIG
                </label>

                <label class="source-option">
                    <input
                        type="radio"
                        name="source"
                        value="georgia"
                        {% if selected_source == "georgia" %}
                        checked
                        {% endif %}
                    >
                    Georgia OIG
                </label>

            </div>

            <label class="field-label">State</label>

            <input
                class="text-input"
                type="text"
                name="state"
                value="{{ state }}"
                placeholder="e.g., NY"
                maxlength="2"
            >

            <label class="field-label">Provider Name</label>

            <input
                class="text-input"
                type="text"
                name="name"
                value="{{ name }}"
                placeholder="e.g., Smith"
            >

            <label class="field-label">NPI Number</label>

            <input
                class="text-input"
                type="text"
                name="npi"
                value="{{ npi }}"
                placeholder="Enter NPI"
            >

            <div class="buttons">

                <button type="submit">
                    Search Providers
                </button>

                <a href="/" class="clear-button">
                    Clear Search
                </a>

            </div>

        </form>

    </div>


    <!-- Search Results -->

    {% if searched %}

    <div class="card">

        <h2>Search Results</h2>

        <p>
            Total matching records:
            <span class="result-count">
                {{ matched_count }}
            </span>
        </p>

        {% for section in sections %}

        <div class="result-section">

            <h3>
                {{ section.source }}:
                {{ section.total }} matches
            </h3>

            {% if section.rows %}

            <div class="table-wrap">

                <table>

                    <thead>
                        <tr>
                            <th>Provider Name</th>
                            <th>City</th>
                            <th>State</th>
                            <th>NPI</th>
                        </tr>
                    </thead>

                    <tbody>

                    {% for row in section.rows %}

                        <tr>
                            <td>{{ row.name }}</td>
                            <td>{{ row.city }}</td>
                            <td>{{ row.state }}</td>
                            <td>{{ row.npi }}</td>
                        </tr>

                    {% endfor %}

                    </tbody>

                </table>

            </div>

            {% else %}

                <p class="empty">
                    No matching records found.
                </p>

            {% endif %}

        </div>

        {% endfor %}

        <p class="note">
            Showing up to 10 records per source.
            The total may include records appearing in both lists.
        </p>

        <p class="note">
            This application is for informational purposes.
            Always verify exclusions against the official
            OIG sources before making eligibility decisions.
        </p>

    </div>

    {% endif %}

</div>

</body>
</html>
"""


def search_database(conn, source, state, name, npi):

    config = tables[source]

    table = config["table"]
    first = config["first"]
    last = config["last"]
    business = config["business"]
    city = config["city"]
    state_col = config["state"]
    npi_col = config["npi"]

    conditions = []
    params = []

    if state:
        conditions.append(f"{state_col} = ?")
        params.append(state)

    if name:
        conditions.append(
            f"({first} LIKE ? OR "
            f"{last} LIKE ? OR "
            f"{business} LIKE ?)"
        )
        params.extend([f"%{name}%"] * 3)

    if npi:
        conditions.append(f"{npi_col} = ?")
        params.append(npi)

    where_clause = ""

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # Count matching records
    count = conn.execute(
        f"SELECT COUNT(*) FROM {table}" + where_clause,
        params
    ).fetchone()[0]

    # Get first 10 matching records
    query = f"""
        SELECT
            {first},
            {last},
            {business},
            {city},
            {state_col},
            {npi_col}
        FROM {table}
    """ + where_clause + " LIMIT 10"

    results = conn.execute(query, params).fetchall()

    rows = []

    for first_name, last_name, company, city_value, state_value, npi_value in results:

        provider_name = (
            f"{first_name or ''} {last_name or ''}".strip()
            or company
            or "Unknown"
        )

        npi_text = str(npi_value).strip() if npi_value is not None else ""

        if npi_text in ("", "0"):
            npi_text = "N/A"

        rows.append({
            "name": provider_name,
            "city": city_value or "N/A",
            "state": state_value or "N/A",
            "npi": npi_text
        })

    return {
        "source": source.title() + " OIG",
        "total": f"{count:,}",
        "count": count,
        "rows": rows
    }


@app.route("/")
def home():

    if not db_path.exists():
        return "Database not found. Please create providers.db first.", 500

    selected_source = request.args.get(
        "source", "both"
    ).strip().lower()

    state = request.args.get(
        "state", ""
    ).strip().upper()

    name = request.args.get(
        "name", ""
    ).strip()

    npi = request.args.get(
        "npi", ""
    ).strip()

    searched = request.args.get("search") == "1"

    if selected_source not in ("both", "federal", "georgia"):
        selected_source = "both"

    sections = []
    matched_count = 0

    with closing(sqlite3.connect(db_path)) as conn:

        federal_count = conn.execute(
            "SELECT COUNT(*) FROM excluded_providers"
        ).fetchone()[0]

        georgia_count = conn.execute(
            "SELECT COUNT(*) FROM georgia_exclusions"
        ).fetchone()[0]

        if searched:

            if selected_source == "both":
                selected_tables = ["federal", "georgia"]
            else:
                selected_tables = [selected_source]

            for current_source in selected_tables:

                section = search_database(
                    conn,
                    current_source,
                    state,
                    name,
                    npi
                )

                sections.append(section)

                matched_count += section["count"]

    return render_template_string(
        html,
        federal_count=f"{federal_count:,}",
        georgia_count=f"{georgia_count:,}",
        total_count=f"{federal_count + georgia_count:,}",
        selected_source=selected_source,
        state=state,
        name=name,
        npi=npi,
        searched=searched,
        sections=sections,
        matched_count=f"{matched_count:,}"
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
