import csv
from pathlib import Path

file_path = Path(__file__).parent / "data" / "UPDATED.csv"

with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    print("Column names:")
    print(reader.fieldnames)

    count = 0

    for row in reader:
        count += 1

        if count <= 5:
            print(row)

    print("\nTotal records:", count)
