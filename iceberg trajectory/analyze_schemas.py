import pandas as pd
import glob
import os
import numpy as np

files = sorted(glob.glob('data/raw/*.csv'))
print(f"Total CSV files: {len(files)}\n")

# Collect schema info and value ranges
schemas = {}
all_columns = set()
value_ranges = {}

for f in files:
    try:
        df = pd.read_csv(f)
        cols = tuple(sorted(df.columns))
        if cols not in schemas:
            schemas[cols] = []
        schemas[cols].append(os.path.basename(f))
        all_columns.update(df.columns)
        
        # Collect value ranges for numeric columns
        for col in df.columns:
            if col not in value_ranges:
                value_ranges[col] = {'min': float('inf'), 'max': float('-inf'), 'non_null': 0}
            try:
                numeric = pd.to_numeric(df[col], errors='coerce')
                valid = numeric.dropna()
                if len(valid) > 0:
                    value_ranges[col]['min'] = min(value_ranges[col]['min'], valid.min())
                    value_ranges[col]['max'] = max(value_ranges[col]['max'], valid.max())
                    value_ranges[col]['non_null'] += len(valid)
            except:
                pass
    except Exception as e:
        print(f"ERROR reading {os.path.basename(f)}: {e}")

print("=== UNIQUE SCHEMAS FOUND ===\n")
for i, (cols, files_list) in enumerate(sorted(schemas.items(), key=lambda x: -len(x[1])), 1):
    print(f"Schema {i}: {len(files_list)} files")
    print(f"  Columns: {cols}")
    print(f"  Sample files: {', '.join(files_list[:3])}")
    print()

print(f"\n=== ALL COLUMNS ACROSS ALL FILES ===")
print(sorted(all_columns))

print("\n=== VALUE RANGES FOR POTENTIAL COORDINATE COLUMNS ===\n")
for col in ['sass_1', 'sass_2', 'nic_1', 'nic_2', 'nic_3']:
    if col in value_ranges:
        r = value_ranges[col]
        print(f"{col}:")
        print(f"  Min: {r['min']:.4f}" if r['min'] != float('inf') else f"  Min: N/A")
        print(f"  Max: {r['max']:.4f}" if r['max'] != float('-inf') else f"  Max: N/A")
        print(f"  Non-null observations: {r['non_null']}")
        print()

print("\n=== LATITUDE RANGE CHECK ===")
print(f"Valid latitude range: -90 to 90")
for col in ['sass_1', 'nic_1', 'nic_2']:
    if col in value_ranges:
        r = value_ranges[col]
        in_range = r['min'] >= -90 and r['max'] <= 90
        print(f"{col}: {r['min']:.2f} to {r['max']:.2f} - Valid latitude? {in_range}")

print("\n=== LONGITUDE RANGE CHECK ===")
print(f"Valid longitude range: -180 to 180")
for col in ['sass_2', 'nic_1', 'nic_2', 'nic_3']:
    if col in value_ranges:
        r = value_ranges[col]
        in_range = r['min'] >= -180 and r['max'] <= 180
        print(f"{col}: {r['min']:.2f} to {r['max']:.2f} - Valid longitude? {in_range}")
