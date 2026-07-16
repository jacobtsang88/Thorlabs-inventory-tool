import sys
from pathlib import Path

from excel_parser import ExcelParser
from plotter import Plotter
from spectrum_parser import SpectrumParser
from storage import Storage
from product_family_2 import Prod_fam_2
from processtxt import txt_to_list

def main():
    print("poop")
    '''
    download list of products and their respective families into a local .json file
    '''
    fart = txt_to_list().convert()
    pf = Prod_fam_2()
    pf.store_file_2("downloads", fart)




if __name__ == "__main__":
    main()
