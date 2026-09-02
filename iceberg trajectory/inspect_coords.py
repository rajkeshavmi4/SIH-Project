import pandas as pd

# Check sass files (confirmed coordinates)
print("=== SASS FILES (sass_1/sass_2) ===\n")
df_sass = pd.read_csv('data/raw/a01.csv')
print("a01.csv sample:")
print(df_sass.head(10))
print(f"sass_1 (latitude?) min={df_sass['sass_1'].min()}, max={df_sass['sass_1'].max()}")
print(f"sass_2 (longitude?) min={df_sass['sass_2'].min()}, max={df_sass['sass_2'].max()}")

# Check nic files (candidate coordinates)
print("\n\n=== NIC FILES (nic_1/nic_2) ===\n")
df_nic = pd.read_csv('data/raw/a03.csv')
print("a03.csv sample:")
print(df_nic.head(10))
print(f"nic_1 (latitude?) min={df_nic['nic_1'].min()}, max={df_nic['nic_1'].max()}")
print(f"nic_2 (longitude?) min={df_nic['nic_2'].min()}, max={df_nic['nic_2'].max()}")
print(f"nic_3 values: {df_nic['nic_3'].unique()}")

# Check what other sensor columns look like
print("\n\n=== OTHER SENSOR COLUMNS ===\n")
df_other = pd.read_csv('data/raw/a34a.csv')
print("a34a.csv (qscat only) sample:")
print(df_other.head())
print(f"Columns: {df_other.columns.tolist()}")
print(f"qscat_1 range: {df_other['qscat_1'].min():.2f} to {df_other['qscat_1'].max():.2f}")
print(f"qscat_2 range: {df_other['qscat_2'].min():.2f} to {df_other['qscat_2'].max():.2f}")
print(f"qscat_3 range: {df_other['qscat_3'].min():.2f} to {df_other['qscat_3'].max():.2f}")
