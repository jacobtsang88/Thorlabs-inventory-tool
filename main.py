import sys
from pathlib import Path

from excel_parser import ExcelParser
from plotter import Plotter
from spectrum_parser import SpectrumParser
from storage import Storage
from product_family_2 import Prod_fam_2

'''
this prog has 4 stages:
parse the excel file given (excel_parser.py), 
extract the data (spectrum_parser.py), 
save it to a json file (storage.py), 
and plot the data (plotter.py)
'''

def parse_workbooks(target_dir: Path, query: str | None = None) -> dict:
    workbook_files = sorted(target_dir.glob("*.xlsx"))

    if query:
        query = query.lower()
        workbook_files = [
            path for path in workbook_files
            if query in path.name.lower()
        ]

    if not workbook_files:
        raise FileNotFoundError(f"No matching .xlsx files found in {target_dir}")

    parsed_spectra = {}

    for workbook_path in workbook_files:
        print(f"Parsing {workbook_path.name}...")
        excel_parser = ExcelParser(str(workbook_path))
        ws = excel_parser.load()

        spectrum_parser = SpectrumParser()
        spectra = spectrum_parser.parse(ws)
        parsed_spectra[workbook_path.stem] = spectra

    return parsed_spectra


def build_plot_series(parsed_spectra: dict, center_wavelength: float, span: float, product_filter: str | None = None) -> list[tuple[str, dict]]:
    plot_series = []

    for source_name, spectra in parsed_spectra.items():
        for product_name, metrics in spectra.items():
            if product_filter:
                filter_text = product_filter.lower()
                if filter_text not in source_name.lower() and filter_text not in product_name.lower():
                    continue

            for metric_name, data in metrics.items():
                window = {
                    float(wavelength): value
                    for wavelength, value in data.items()
                    if center_wavelength - span <= float(wavelength) <= center_wavelength + span
                }
                if window:
                    label = f"{source_name} | {product_name} | {metric_name}"
                    plot_series.append((label, window))

    return plot_series


def main():
    #arg 1 is target dir
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).resolve()
    else:
        target_dir = (Path(__file__).resolve().parent / "downloads" / "Inventory").resolve()

    if not target_dir.is_dir():
        print(f"ERROR: {target_dir} is not a valid directory.")
        sys.exit(1)

    product_filter = sys.argv[2]

    #arg 3 is center wl, dont need to input right away.
    if len(sys.argv) > 3:
        center_wavelength = float(sys.argv[3])
    else:
        center_wavelength = float(input("Enter the center wavelength (nm): "))
    #arg 4 is span, but optional.
    span = float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
    
    

    print(f"Scanning {target_dir} for .xlsx files...")
    parsed_spectra = parse_workbooks(target_dir, query=product_filter)

    output_json = target_dir / "parsed_spectra.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    Storage().save(parsed_spectra, str(output_json))
    print(f"Saved parsed spectra to {output_json}")

    plot_series = build_plot_series(parsed_spectra, center_wavelength, span, product_filter=product_filter)
    if not plot_series:
        print("No data points were found for requested wavelength window.")
        return

    #saves to /home/downloads, change if specific folder needed
    plot_path = Path.home() / "Downloads" / f"plot_{product_filter}_at_{center_wavelength}_for_span_{span}.png"
    Plotter().plot(plot_series, title=f"Spectra around {center_wavelength} nm", output_path=str(plot_path), show=False)
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    main()
