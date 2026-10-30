import csv
import sqlite3
from pathlib import Path

project_dir = Path(__file__).parent
csv_path = project_dir / "data" / "UPDATED.csv"
db_path = project_dir / "providers.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    columns = reader.fieldnames

    if not columns:
        raise ValueError("CSV file has no columns.")

    column_names = ", ".join(
        f'"{name}" TEXT' for name in columns
    )

    cursor.execute("DROP TABLE IF EXISTS excluded_providers")

    cursor.execute(
        f"CREATE TABLE excluded_providers ({column_names})"
    )

    placeholders = ", ".join(["?"] * len(columns))

    cursor.executemany(
        f"INSERT INTO excluded_providers VALUES ({placeholders})",
        ([row[name] for name in columns] for row in reader)
    )

conn.commit()

cursor.execute("SELECT COUNT(*) FROM excluded_providers")
count = cursor.fetchone()[0]

print("Database created successfully!")
print("Total records:", count)
print("Database location:", db_path)

conn.close()
