import pandas as pd
from froggy_vars.temp_and_rainfall import get_location_info

# Load our rainfall output and reference (ground truth) spreadsheet
df_ours = pd.read_csv("01_frog_data_compilation/results/temp_and_rainfall.csv")
df_big = pd.read_excel("01_frog_data_compilation/data/Reference_Froggy_Spreadsheet.xlsx")

missing_data_locs = []
loc_diffs = {}

# Analyze discrepancies and missing values per location
for i, row in df_ours.iterrows():
    try:
        genus, species = row["Name"].split(' ')
        print("Processing {}: {} {}".format(i, genus, species))
    
        locations = get_location_info(genus, species)
        if locations:

            # If rainfall is missing for a species, mark all associated locations
            if row["Min Rainfall"] == "-": # if one's missing, they all are
                for loc in locations:
                    if loc not in missing_data_locs:
                        missing_data_locs.append(loc)
                continue
            
            # Compare mean temperature against reference dataset
            big_mean_temp = df_big.loc[df_big["Name"] == row["Name"]]["Mean Temperature"].values[0]
            our_mean_temp = row["Mean Temperature"]

            if not big_mean_temp or not our_mean_temp: # if either is missing, skip
                continue

            diff = abs(big_mean_temp - our_mean_temp)

            if diff == 0:
                continue

            # Track the largest discrepancy per location
            for loc in locations:
                if loc in loc_diffs:
                    if diff > loc_diffs[loc]:
                        loc_diffs[loc] = diff
                else:
                    loc_diffs[loc] = diff
    
    except Exception as e:
        print(f"Error processing row {i}: {e}")
        continue

# Output discrepancy and missing-data summaries
print("Locations with discrepancies in mean rainfall: ")
print(loc_diffs)

print("Locations with missing rainfall data: ")
print(missing_data_locs)