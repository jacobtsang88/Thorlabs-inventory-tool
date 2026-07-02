import sys
from pathlib import Path

from excel_parser import ExcelParser


def main():
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path.cwd()

    if not target_dir.is_dir():
        print(f"ERROR: {target_dir} is not a valid directory.")
        sys.exit(1)

    workbook_files = sorted(target_dir.glob("*.xlsx"))

    if not workbook_files:
        print(f"No .xlsx files found in {target_dir}")
        return

    print(f"Testing ExcelParser against {len(workbook_files)} workbook(s) in {target_dir}:")

    for workbook_path in workbook_files:
        print(f"\n- {workbook_path.name}")
        try:
            parser = ExcelParser(str(workbook_path))
            ws = parser.load()
            header_row = parser.find_header_row(ws)
            headers = [ws.cell(header_row, col).value for col in range(1, ws.max_column + 1)]
            print(f"  Loaded successfully")
            print(f"  Header row: {header_row}")
            print(f"  Headers: {headers}")
        except Exception as exc:
            print(f"  ERROR: {exc}")


if __name__ == "__main__":
    main()
