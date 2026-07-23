# excel_parser.py
from pathlib import Path
import pandas as pd

class ExcelParser:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def parse(self, sheet_name=0):
        """
        Parses optical Excel data files.
        Dynamically finds header rows and cleans surrounding empty data.
        """
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        
        # Remove completely empty rows/columns
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        
        # Identify the header row index using keyword matching
        header_row_idx = None
        for idx, row in df.iterrows():
            if row.astype(str).str.contains('Wavelength|Reflectance|Transmission|Divergence', case=False).any():
                header_row_idx = idx
                break
                
        if header_row_idx is not None:
            df.columns = df.loc[header_row_idx]
            df = df.loc[header_row_idx + 1:].reset_index(drop=True)
            
        # Clean unnamed/NaN columns
        df = df.loc[:, df.columns.notna()]
        
        # Coerce column values to numeric floats
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna()


'''import openpyxl
class ExcelParser:

    def __init__(self, filename):
        self.filename = filename


    def load(self):

        wb = openpyxl.load_workbook(
            self.filename,
            data_only=True
        )

        ws = wb.active

        self.expand_merged_cells(ws)

        return ws


    def expand_merged_cells(self, ws):

        for merged in list(ws.merged_cells.ranges):
            value = ws.cell(merged.min_row, merged.min_col).value
            ws.unmerge_cells(merged.coord)

            for row in range(merged.min_row, merged.max_row + 1):
                for col in range(merged.min_col, merged.max_col + 1):
                    ws.cell(row, col).value = value


    def find_header_row(self, ws):

        for row in range(1, ws.max_row+1):

            values = [
                str(ws.cell(row,c).value)
                for c in range(1,ws.max_column+1)
                if ws.cell(row,c).value
            ]

            text = " ".join(values).lower()


            if "wavelength" in text:
                return row


        raise Exception(
            "No wavelength header found"
        )'''