import pandas as pd
import os

csv_path = 'outputs/ranked_candidates_detailed.csv'
excel_path = 'outputs/ranked_candidates_detailed.xlsx'

if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found.")
    exit(1)

print(f"Loading {csv_path}...")
df = pd.read_csv(csv_path)

print(f"Converting to {excel_path}...")
df.to_excel(excel_path, index=False, engine='openpyxl')

print("Conversion complete!")
