'''
From IUCN: Preferred Habitat (IUCN Habitat Categories) and one preferred habitat if available
'''

import os
import pandas as pd
from temp_and_rainfall import get_assessment_id, get_species_assessment

# Extract top-level habitat codes
def habitat_codes(json_data):
    if "habitats" not in json_data:
        return []

    codes = set()
    for habitat in json_data["habitats"]:
        code = habitat.get("code")
        if code and isinstance(code, str) and "_" in code:
            top_level = code.split("_")[0]
            codes.add(top_level)

    return list(codes)

# Load frog dataset
df = pd.read_csv("01_frog_data_compilation/results/froggy_analysis_results.csv")

# Initialize habitat columns 1–16 with zeros (one-hot style encoding)
for i in range(1, 17):
    df[str(i)] = 0

# Process each species row to extract and encode IUCN habitat categories
for index, row in df.iterrows():

    name_parts = row["Name"].strip().split()
    if len(name_parts) < 2:
        continue

    print("Processing {}: {}".format(index, row["Name"]))

    genus, species = name_parts[0], name_parts[1]

    codes = []

    assessment_id = get_assessment_id(genus, species)

    if assessment_id:
        assessment_info = get_species_assessment(assessment_id)

        if assessment_info:
            codes = habitat_codes(assessment_info)

    # Mark presence of each top-level habitat code with 1
    for code in codes:
        if code in df.columns:
            df.at[index, code] = 1

# Overwrite old Excel file with updated habitat columns
if os.path.exists("01_frog_data_compilation/results/froggy_analysis_results.csv"):
    os.remove("01_frog_data_compilation/results/froggy_analysis_results.csv")

df.to_csv("01_frog_data_compilation/results/froggy_analysis_results.csv", index=False)
