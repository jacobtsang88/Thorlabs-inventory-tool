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
    part_num = input("enter part num: ")
    family_name = Prod_fam_2(part_num).find_product_family()
    #downloads in current dir, downloads folder. change later to abs path, or argv.
    Prod_fam_2(part_num).store_file("downloads", family_name)
    '''
    print(txt_to_list().convert())




if __name__ == "__main__":
    main()
