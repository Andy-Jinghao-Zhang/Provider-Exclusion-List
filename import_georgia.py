import sqlite3
from pathlib import Path
from openpyxl import load_workbook

project_dir = Path(__file__).parent
data_dir = project_dir / "data"
db_path = project_dir / "providers.db"

excel_files = [
    file for file in data_dir.glob("*.xlsx")
    if not file.name.startswith("~$")
]

if len(excel_files) != 1:
    raise ValueError("Expected exactly one Georgia Excel file.")

if not db_path.exists():
    raise FileNotFoundError("providers.db was not found.")

excel_path = excel_files[0]

workbook = load_workbook(
    excel_path,
    read_only=True,
    data_only=True
)

sheet = workbook["Sheet1"]

# Read the column names from row 3
header = next(sheet.iter_rows(
    min_row=3,
    max_row=3,
    max_col=9,
    values_only=True
))

def normalize(name):
    return "".join(
        char for char in str(name).upper()
        if char.isalnum()
    )

columns = {
    normalize(name): i
    for i, name in enumerate(header)
    if name is not None
}


required = [
    "LAST NAME",
    "FIRST NAME",
    "MIDDLE NAME",
    "BUSINESS NAME",
    "GENERAL",
    "STATE",
    "SANC DATE",
    "NPI"
]

if not all(normalize(name) in columns for name in required):
    workbook.close()
    raise ValueError("Georgia Excel columns do not match.")

def clean(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()

records = []

for row in sheet.iter_rows(
    min_row=4,
    max_col=9,
    values_only=True
):
    values = [
    clean(row[columns[normalize(name)]])
    for name in required
]

    last, first, middle, business, general, state, date, npi = values

    # Skip blank rows, headers and unrelated text
    if not (last or first or business):
        continue

    if last.upper() == "LAST NAME":
        continue

    if not (state or date):
        continue

    records.append(tuple(values))

workbook.close()

if not records:
    raise ValueError("No valid Georgia records were found.")

conn = sqlite3.connect(db_path)

try:
    with conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS georgia_exclusions (
                last_name TEXT,
                first_name TEXT,
                middle_name TEXT,
                business_name TEXT,
                general TEXT,
                state TEXT,
                sanction_date TEXT,
                npi TEXT
            )
        """)

        # Replace only the Georgia records
        cursor.execute("DELETE FROM georgia_exclusions")

        cursor.executemany("""
            INSERT INTO georgia_exclusions
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_georgia_state
            ON georgia_exclusions(state)
        """)

    georgia_count = conn.execute(
        "SELECT COUNT(*) FROM georgia_exclusions"
    ).fetchone()[0]

    federal_count = conn.execute(
        "SELECT COUNT(*) FROM excluded_providers"
    ).fetchone()[0]

    print("Georgia database imported successfully!")
    print("Georgia records:", georgia_count)
    print("Federal records:", federal_count)
    print("Database:", db_path)

finally:
    conn.close()
