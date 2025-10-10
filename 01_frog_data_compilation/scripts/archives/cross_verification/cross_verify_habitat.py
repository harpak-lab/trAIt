import pandas as pd

# File paths
reference_path = '01_frog_data_compilation/data/Reference_Froggy_Spreadsheet.xlsx'
analysis_path = '01_frog_data_compilation/results/froggy_analysis_results.csv'
cross_verification_path = '01_frog_data_compilation/results/cross_verification_results.csv'

# Habitat columns to check (IUCN top-level codes)
columns_to_check = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '13', '14', '15', '16']

# Load reference, analysis, and cross-verification dataframes
df_reference = pd.read_excel(reference_path, dtype=str)
df_analysis = pd.read_csv(analysis_path, dtype=str)
df_cross = pd.read_csv(cross_verification_path, dtype=str)

# Use species name as index for fast lookup
df_reference.set_index('Name', inplace=True)
df_analysis.set_index('Name', inplace=True)

# Compare individual habitat column values between reference and analysis
def compare_values(name, col):
    val_ref = df_reference.at[name, int(col)] if name in df_reference.index and int(col) in df_reference.columns else "-" # stores it as nums not str
    val_analysis = df_analysis.at[name, col] if name in df_analysis.index and col in df_analysis.columns else "-"

    val_ref = val_ref.strip() if isinstance(val_ref, str) else "-"
    val_analysis = val_analysis.strip() if isinstance(val_analysis, str) else "-"

    # Handle missing or empty values
    if val_ref == "-" or val_ref == "" or val_analysis == "-" or val_analysis == "":
        print("BREH")
        return "-"
    elif val_ref == val_analysis:
        return val_ref
    else:
        return "invalid"

# Apply comparison to each species for each habitat code
for col in columns_to_check:
    df_cross[col] = df_cross['Name'].apply(lambda name: compare_values(name, col))

# Save updated cross-verification file with habitat comparisons
df_cross.to_csv(cross_verification_path, index=False)
