from pathlib import Path
import openpyxl
import re
import sys
import json
from excel_parser import ExcelParser
from plotter import Plotter
from spectrum_parser import SpectrumParser
from storage import Storage
from product_family_2 import Prod_fam_2
from processtxt import txt_to_list
from download_files import FamilyDownloader
from exceptions import FamilyDataUnavailableError, NoSpectralDataError, WavelengthOutOfRangeError

with open("families.json", "r") as file:
    inventoryDict = json.load(file)

from pathlib import Path
import openpyxl

def wavelength_unit_to_nm(header_text: str) -> float:
    """Some Thorlabs raw data sheets (e.g. sapphire, IR components) report
    wavelength in microns instead of nanometers. Return the multiplier
    needed to normalize a value in that column to nm."""
    text = str(header_text)
    if "µm" in text or "μm" in text or re.search(r"\bum\b", text, re.IGNORECASE):
        return 1000.0
    return 1.0


def parse_workbooks(target_dir: Path, query: str | None = None) -> dict:
    workbook_files = sorted(target_dir.glob("*.xlsx"))

    if query:
        query = query.lower()
        workbook_files = [
            path for path in workbook_files if path.stem.lower() == query
        ]

    if not workbook_files:
        raise FileNotFoundError(
            f"No matching .xlsx files found in {target_dir}"
        )

    parsed_spectra = {}

    for workbook_path in workbook_files:
        #print(f"\nParsing {workbook_path.name}...")

        workbook = openpyxl.load_workbook(
            workbook_path, data_only=True, read_only=True
        )
        workbook_data = {}

        for worksheet in workbook.worksheets:
            #print(f"  Processing sheet: {worksheet.title}")

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
                #print("  No wavelength header found.")
                continue

            header_row = rows[wavelength_header_row]
            wavelength_columns = []

            for column_index, cell in enumerate(header_row):
                if cell is None:
                    continue
                if "wavelength" in str(cell).lower():
                    wavelength_columns.append(column_index)

            #print(f"  Wavelength columns: {wavelength_columns}")

            for wavelength_column in wavelength_columns:
                data_column = wavelength_column + 1

                if data_column >= len(header_row):
                    continue

                wavelength_header = header_row[wavelength_column]
                data_header = header_row[data_column]

                #print(f"  Data series: {wavelength_header} -> {data_header}")

                unit_to_nm = wavelength_unit_to_nm(wavelength_header)
                data = {}

                for row in rows[wavelength_header_row + 1 :]:
                    if wavelength_column >= len(row) or data_column >= len(row):
                        continue

                    wavelength = row[wavelength_column]
                    value = row[data_column]

                    if wavelength is None or value is None:
                        continue

                    try:
                        wavelength = float(wavelength) * unit_to_nm
                        value = float(value)
                    except (ValueError, TypeError):
                        continue

                    data[wavelength] = value

                if data:
                    metric_name = str(data_header)
                    workbook_data[metric_name] = data
                    #print(f"  Extracted {len(data)} points")

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


def ensure_family_downloaded(target_dir: Path, family_name: str) -> Path:
    family_dir = target_dir / family_name
    if not family_dir.exists() or not any(family_dir.glob("*.xlsx")):
        FamilyDownloader(json_path="families.json", download_dir=str(target_dir)).download_family(family_name)

    if not any(family_dir.glob("*.xlsx")):
        raise FamilyDataUnavailableError(family_name)

    return family_dir


def list_family_variants(family_dir: Path) -> list[str]:
    return sorted(path.stem for path in family_dir.glob("*.xlsx"))


def choose_variant(variants: list[str], requested: str | None = None) -> str:
    if requested:
        for variant in variants:
            if variant.lower() == requested.lower():
                return variant
        print(f"'{requested}' is not an available coating; ignoring.")

    if len(variants) == 1:
        return variants[0]

    print("Which coating:")
    for i, variant in enumerate(variants, start=1):
        print(f"  {i}. {variant}")

    while True:
        choice = input("Enter a number or name: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(variants):
            return variants[int(choice) - 1]
        for variant in variants:
            if variant.lower() == choice.lower():
                return variant
        print("Not a valid choice, try again.")



def compute_wavelength_ranges(parsed_spectra: dict) -> list[tuple[str, float, float]]:
    """For each parsed metric series, return (label, min_wavelength_nm, max_wavelength_nm)."""
    ranges = []
    for source_name, spectra in parsed_spectra.items():
        for metric_name, data in spectra.items():
            if not data:
                continue
            wavelengths = [float(w) for w in data.keys()]
            label = f"{source_name} | {metric_name}"
            ranges.append((label, min(wavelengths), max(wavelengths)))
    return ranges


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
    requested_variant = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        family_dir = ensure_family_downloaded(target_dir, product_family)
        variants = list_family_variants(family_dir)
        chosen_variant = choose_variant(variants, requested=requested_variant)

        parsed_spectra = parse_workbooks(family_dir, query=chosen_variant)
        if not parsed_spectra[chosen_variant]:
            raise NoSpectralDataError(chosen_variant)

        plot_series = build_plot_series(parsed_spectra, center_wl, span)
        if not plot_series:
            raise WavelengthOutOfRangeError(
                chosen_variant,
                center_wl - span,
                center_wl + span,
                compute_wavelength_ranges(parsed_spectra),
            )
    except FamilyDataUnavailableError as exc:
        print(f"[No data sheet available] {exc}")
        return
    except NoSpectralDataError as exc:
        print(f"[Unrecognized data sheet] {exc}")
        return
    except WavelengthOutOfRangeError as exc:
        print(f"[Wavelength out of range] {exc}")
        return

    #saves to /home/downloads, change if specific folder needed
    plot_path = Path.home() / "Downloads" / f"plot_{product_name}_{chosen_variant}_at_{center_wl}_for_span_{span}.png"
    Plotter().plot(plot_series, title=f"Spectra around {center_wl} nm ({chosen_variant})", output_path=str(plot_path), show=False)
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    main()