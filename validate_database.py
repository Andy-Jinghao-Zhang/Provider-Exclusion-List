import sqlite3
import json
from pathlib import Path

project_dir = Path(__file__).parent
db_path = project_dir / "providers.db"
report_path = project_dir / "validation_report.json"

if not db_path.exists():
    raise FileNotFoundError("Database not found.")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check database integrity
cursor.execute("PRAGMA integrity_check")
integrity = cursor.fetchone()[0]

print("Database integrity:", integrity)

# Check both tables
tables = {
    "Federal": {
        "table": "excluded_providers",
        "first": "FIRSTNAME",
        "last": "LASTNAME",
        "business": "BUSNAME",
        "state": "STATE",
        "npi": "NPI"
    },
    "Georgia": {
        "table": "georgia_exclusions",
        "first": "first_name",
        "last": "last_name",
        "business": "business_name",
        "state": "state",
        "npi": "npi"
    }
}

report = {
    "database": "providers.db",
    "integrity": integrity,
    "sources": {}
}

for source, fields in tables.items():

    table = fields["table"]

    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type = 'table' AND name = ?",
        (table,)
    )

    if cursor.fetchone() is None:
        raise ValueError(f"Missing table: {table}")

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total = cursor.fetchone()[0]

    # Records without an individual or business name
    cursor.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE TRIM(COALESCE({fields['first']}, '')) = ''
        AND TRIM(COALESCE({fields['last']}, '')) = ''
        AND TRIM(COALESCE({fields['business']}, '')) = ''
    """)

    missing_name = cursor.fetchone()[0]

    # Records without a state
    cursor.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE TRIM(COALESCE({fields['state']}, '')) = ''
    """)

    missing_state = cursor.fetchone()[0]

    # Records without a usable NPI value
    cursor.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE TRIM(COALESCE({fields['npi']}, '')) IN ('', '0')
    """)

    missing_npi = cursor.fetchone()[0]

    report["sources"][source] = {
        "total_records": total,
        "missing_names": missing_name,
        "missing_states": missing_state,
        "missing_npi": missing_npi
    }

    print(f"\nSource: {source}")
    print("Total records:", total)
    print("Missing names:", missing_name)
    print("Missing states:", missing_state)
    print("Missing NPI:", missing_npi)

conn.close()

report["total_records"] = sum(
    data["total_records"]
    for data in report["sources"].values()
)

report["passed"] = integrity == "ok" and all(
    data["total_records"] > 0
    for data in report["sources"].values()
)

with open(report_path, "w") as file:
    json.dump(report, file, indent=4)

print("\nCombined records:", report["total_records"])
print("Basic validation passed:", report["passed"])
print("Validation report saved:", report_path)
