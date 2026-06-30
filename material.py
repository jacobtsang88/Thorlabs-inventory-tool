import matplotlib.pyplot as plt
import openpyxl

'''
Requirements:
pip install openpyxl matplotlib
'''

def find_labels(filepath):
    #check row 3 to see whats wavelength, transmission, reflectance, etc.
def plot_transmission(filepath):
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    
    wavelengths = []
    transmissions = []


