import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "providers.db"

if not db_path.exists():
    raise FileNotFoundError("Database not found.")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Provider Exclusion List Search")
print("------------------------------")

source = input(
    "Select source (federal/georgia/both): "
).strip().lower()

if not source:
    source = "both"

if source not in ["federal", "georgia", "both"]:
    print("Invalid source.")
    conn.close()
    raise SystemExit

state = input("Enter state (optional): ").strip().upper()
name = input("Enter name (optional): ").strip()
npi = input("Enter NPI (optional): ").strip()

sources = []

if source in ["federal", "both"]:
    sources.append("federal")

if source in ["georgia", "both"]:
    sources.append("georgia")

for current_source in sources:

    conditions = []
    params = []

    if current_source == "federal":
        table = "excluded_providers"
        first_col = "FIRSTNAME"
        last_col = "LASTNAME"
        business_col = "BUSNAME"
        state_col = "STATE"
        npi_col = "NPI"

        select_columns = """
            FIRSTNAME, LASTNAME, BUSNAME,
            CITY, STATE, NPI
        """

    else:
        table = "georgia_exclusions"
        first_col = "first_name"
        last_col = "last_name"
        business_col = "business_name"
        state_col = "state"
        npi_col = "npi"

        select_columns = """
            first_name, last_name, business_name,
            NULL AS city, state, npi
        """

    if state:
        conditions.append(f"{state_col} = ?")
        params.append(state)

    if name:
        conditions.append(
            f"({first_col} LIKE ? OR "
            f"{last_col} LIKE ? OR "
            f"{business_col} LIKE ?)"
        )
        params.extend([f"%{name}%"] * 3)

    if npi:
        conditions.append(f"{npi_col} = ?")
        params.append(npi)

    where_clause = ""

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    cursor.execute(
        f"SELECT COUNT(*) FROM {table}" + where_clause,
        params
    )

    total = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT {select_columns} FROM {table}"
        + where_clause
        + " LIMIT 10",
        params
    )

    results = cursor.fetchall()

    print(f"\nSource: {current_source.upper()}")
    print("Total matching records:", total)
    print("First 10 records:")

    if not results:
        print("No matching records found.")

    for first, last, business, city, state_value, npi_value in results:

        provider_name = f"{first or ''} {last or ''}".strip()
        provider_name = provider_name or business or "Unknown"

        location = state_value or "Unknown"

        if city:
            location = f"{city}, {location}"

        print(
            f"{provider_name} | "
            f"{location} | "
            f"NPI: {npi_value or 'N/A'}"
        )

conn.close()
