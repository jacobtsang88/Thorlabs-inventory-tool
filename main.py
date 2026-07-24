from pathlib import Path
import openpyxl
import sys
import json
from excel_parser import ExcelParser
from plotter import Plotter
from spectrum_parser import SpectrumParser
from storage import Storage
from product_family_2 import Prod_fam_2
from processtxt import txt_to_list

with open("families.json", "r") as file:
    inventoryDict = json.load(file)

from pathlib import Path
import openpyxl


def parse_workbooks(target_dir: Path, query: str | None = None) -> dict:
    workbook_files = sorted(target_dir.glob("*.xlsx"))

    if query:
        query = query.lower()
        workbook_files = [
            path for path in workbook_files if query in path.name.lower()
        ]

    if not workbook_files:
        raise FileNotFoundError(
            f"No matching .xlsx files found in {target_dir}"
        )

    parsed_spectra = {}

    for workbook_path in workbook_files:
        print(f"\nParsing {workbook_path.name}...")

        workbook = openpyxl.load_workbook(
            workbook_path, data_only=True, read_only=True
        )
        workbook_data = {}

        for worksheet in workbook.worksheets:
            print(f"  Processing sheet: {worksheet.title}")

            rows = list(worksheet.iter_rows(values_only=True))
            wavelength_header_row = None

            for row_index, row in enumerate(rows):
                for cell in row:
                    if cell is None:
                        continue
                    if "wavelength" in str(cell).lower():
                        wavelength_header_row = row_index
                        break
                if wavelength_header_row is not None:
                    break

            if wavelength_header_row is None:
                print("  No wavelength header found.")
                continue

            header_row = rows[wavelength_header_row]
            wavelength_columns = []

            for column_index, cell in enumerate(header_row):
                if cell is None:
                    continue
                if "wavelength" in str(cell).lower():
                    wavelength_columns.append(column_index)

            print(f"  Wavelength columns: {wavelength_columns}")

            for wavelength_column in wavelength_columns:
                data_column = wavelength_column + 1

                if data_column >= len(header_row):
                    continue

                wavelength_header = header_row[wavelength_column]
                data_header = header_row[data_column]

                print(f"  Data series: {wavelength_header} -> {data_header}")

                data = {}

                for row in rows[wavelength_header_row + 1 :]:
                    if wavelength_column >= len(row) or data_column >= len(row):
                        continue

                    wavelength = row[wavelength_column]
                    value = row[data_column]

                    if wavelength is None or value is None:
                        continue

                    try:
                        wavelength = float(wavelength)
                        value = float(value)
                    except (ValueError, TypeError):
                        continue

                    data[wavelength] = value

                if data:
                    metric_name = str(data_header)
                    workbook_data[metric_name] = data
                    print(f"  Extracted {len(data)} points")

        parsed_spectra[workbook_path.stem] = workbook_data

    return parsed_spectra


def check_product(product_num):
    pf2 = Prod_fam_2(product_num)
    family_stored = pf2.checkProdFamExists(inventoryDict, product_num)
    #if not stored then find and store before returning.
    if family_stored == None:
        family_found = pf2.find_product_family()
        pf2.store_file(family_found)
        return family_found
    else:
        return family_stored
    

def build_plot_series(
    parsed_spectra: dict,
    center_wavelength: float,
    span: float,
    product_filter: str | None = None,
) -> list[tuple[str, dict]]:
    plot_series = []

    for source_name, spectra in parsed_spectra.items():
        # Filter by product/source name if requested
        if product_filter:
            filter_text = product_filter.lower()
            if filter_text not in source_name.lower():
                continue

        # spectra is directly {metric_name: {wavelength: value}}
        for metric_name, data in spectra.items():
            window = {
                float(wavelength): value
                for wavelength, value in data.items()
                if center_wavelength - span
                <= float(wavelength)
                <= center_wavelength + span
            }
            if window:
                label = f"{source_name} | {metric_name}"
                plot_series.append((label, window))

    return plot_series

def main():
    #target_dir = "/downloads"
    target_dir = (Path(__file__).resolve().parent / "downloads").resolve()
    if len(sys.argv) >1:
        product_name = sys.argv[1]
    else:
        product_name = input("enter product number: ")
    if len(sys.argv) > 2:
        center_wl = float(sys.argv[2])
    else:
        center_wl = float(input("Enter the center wavelength (nm): "))
    
    product_family = check_product(product_name)
    if product_family is None:
        print(f"Could not determine family for "f"{product_name}.")
        return
    span = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

    parsed_spectra = parse_workbooks(target_dir, query=product_family)

    plot_series = build_plot_series(parsed_spectra, center_wl, span, product_filter=product_family)
    if not plot_series:
        print("No data points were found for requested wavelength window.")
        return

    #saves to /home/downloads, change if specific folder needed
    plot_path = Path.home() / "Downloads" / f"plot_{product_name}_at_{center_wl}_for_span_{span}.png"
    Plotter().plot(plot_series, title=f"Spectra around {center_wl} nm", output_path=str(plot_path), show=False)
    print(f"Saved plot to {plot_path}")

    '''
    print("========== PARSED DATA ==========")
    print(json.dumps(parsed_spectra, indent=4))
    '''


if __name__ == "__main__":
    main()