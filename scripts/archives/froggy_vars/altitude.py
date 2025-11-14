import os
import pandas as pd
from dotenv import load_dotenv
from temp_and_rainfall import get_assessment_id, get_species_assessment

load_dotenv()

# Load frog results spreadsheet into DataFrame
results_spreadsheet = "01_frog_data_compilation/results/froggy_analysis_results.csv"
df_ref = pd.read_csv(results_spreadsheet)

# Add new columns for altitude limits
df_ref["Min Altitude"] = None
df_ref["Max Altitude"] = None

# Loop through each species and extract altitude from IUCN data
for i, row in df_ref.iterrows():
    genus, species = row["Name"].split(' ')

    print(f"Processing {i}: {genus} {species}")

    assessment_id = get_assessment_id(genus, species)
    if assessment_id:
        species_info = get_species_assessment(assessment_id)
        if species_info:
            supplementary_info = species_info.get("supplementary_info", {})
            min_altitude = supplementary_info.get("lower_elevation_limit", None)
            max_altitude = supplementary_info.get("upper_elevation_limit", None)
        else:
            min_altitude, max_altitude = None, None
    else:
        min_altitude, max_altitude = None, None

    # Store altitude values or dash if missing
    df_ref.at[i, "Min Altitude"] = min_altitude if min_altitude is not None else "-"
    df_ref.at[i, "Max Altitude"] = max_altitude if max_altitude is not None else "-"

# Overwrite existing file with updated altitude data
if os.path.exists("01_frog_data_compilation/results/froggy_analysis_results.csv"):
    os.remove("01_frog_data_compilation/results/froggy_analysis_results.csv")

df_ref.to_csv("01_frog_data_compilation/results/froggy_analysis_results.csv", index=False)
print("Updated file saved to 01_frog_data_compilation/results/froggy_analysis_results.xlsx")