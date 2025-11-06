# data_checker.py
'''
Script zum Analysieren der Datenqualität von Dateien.
Funktion:

'''
import os
import pandas as pd

# Variablen und Konstanten
CONSOLE_OUTPUT_LINE = "_"*100

# relativer Pfad vom Script zu den Datenordnern
script_dir = os.path.dirname(os.path.abspath(__file__))
data_sets_folder_path = os.path.join(script_dir, "../../data_sets")
euda_sets_path = os.path.join(data_sets_folder_path, "EUDA_Wastewater_analysis_and_drugs")

# Datei als DataFrame einlesen
file_name = "ww2025-all-data.csv" 
df = pd.read_csv(os.path.join(euda_sets_path, "ww2025-all-data.csv"))




print(CONSOLE_OUTPUT_LINE, "\n\nStarte Datencheck")
print(df.describe())
# Fehlende Werte
print("\nAnzahl fehlender Werte pro Spalte:")
print(df.isnull().sum())
print(df.isnull().sum())
# Erste Zeilen (visuelle Kontrolle)
print("\nErste Zeilen:")
print(df.head())