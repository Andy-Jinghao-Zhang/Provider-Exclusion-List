import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "providers.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

state = input("Enter a state (e.g., NY): ").strip().upper()

if state:
    cursor.execute(
        "SELECT COUNT(*) FROM excluded_providers WHERE STATE = ?",
        (state,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT FIRSTNAME, LASTNAME, BUSNAME, CITY, STATE, NPI
        FROM excluded_providers
        WHERE STATE = ?
        LIMIT 10
        """,
        (state,)
    )

    results = cursor.fetchall()

    print(f"\nTotal records in {state}: {total}")
    print("\nFirst 10 records:")

    for first, last, business, city, state, npi in results:
        name = f"{first} {last}".strip() or business
        print(f"{name} | {city}, {state} | NPI: {npi}")
else:
    print("Please enter a state.")

conn.close()
