import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "providers.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

state = input("Enter a state (optional): ").strip().upper()
name = input("Enter a provider name (optional): ").strip()

conditions = []
params = []

if state:
    conditions.append("STATE = ?")
    params.append(state)

if name:
    conditions.append(
        "(FIRSTNAME LIKE ? OR LASTNAME LIKE ? OR BUSNAME LIKE ?)"
    )
    params.extend([f"%{name}%"] * 3)

if conditions:
    where_clause = " WHERE " + " AND ".join(conditions)

    cursor.execute(
        "SELECT COUNT(*) FROM excluded_providers" + where_clause,
        params
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT FIRSTNAME, LASTNAME, BUSNAME, CITY, STATE, NPI
        FROM excluded_providers
        """
        + where_clause + " LIMIT 10",
        params
    )

    results = cursor.fetchall()

    print("\nTotal matching records:", total)
    print("\nFirst 10 records:")

    for first, last, business, city, state, npi in results:
        provider_name = f"{first or ''} {last or ''}".strip()
        provider_name = provider_name or business

        print(f"{provider_name} | {city}, {state} | NPI: {npi}")

else:
    print("Please enter a state or provider name.")

conn.close()
