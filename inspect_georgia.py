from pathlib import Path
from openpyxl import load_workbook

data_dir = Path(__file__).parent / "data"

excel_files = list(data_dir.glob("*.xlsx"))

if not excel_files:
    print("No Georgia Excel file found.")
else:
    file_path = excel_files[0]

    print("File:", file_path.name)

    workbook = load_workbook(
        file_path,
        read_only=True,
        data_only=True
    )

    print("Worksheets:", workbook.sheetnames)

    for sheet in workbook.worksheets:
        print("\nSheet:", sheet.title)
        print("Total rows:", sheet.max_row)
        print("Total columns:", sheet.max_column)

        print("\nFirst 15 rows:")

        for row in sheet.iter_rows(
            min_row=1,
            max_row=min(15, sheet.max_row),
            values_only=True
        ):
            print(row[:15])

    workbook.close()
