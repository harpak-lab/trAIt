import os
from dotenv import load_dotenv
import requests
import pandas as pd
import time

load_dotenv()

'''
IUCN Red List takes genus, species and outputs regular string locs (i.e. “Texas”)
Use geonames.xlsx to convert locs to loc codes
CCKP takes loc codes and outputs temp, rainfall
'''

### PART 1: DERIVING LOCATIONS FROM SPECIES ###

TAXA_API_URL = "https://api.iucnredlist.org/api/v4/taxa/scientific_name"
ASSESSMENT_API_URL = "https://api.iucnredlist.org/api/v4/assessment"

API_KEY = os.getenv("IUCN_API_KEY")

# Get the latest assessment ID for a given species
def get_assessment_id(genus, species):
    url = f"{TAXA_API_URL}?genus_name={genus}&species_name={species}"
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    # Get information for genus and species
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assessments = data.get("assessments", []) # Locate assessment id
        if assessments:
            latest_assessment = next((a for a in assessments if a["latest"]), None)
            if latest_assessment:
                return latest_assessment["assessment_id"]
        print(f"No assessments found for {genus} {species}.")
    else:
        print(f"Status code {response.status_code}")
    
    return None

# Fetch full assessment data using an assessment ID
def get_species_assessment(assessment_id):
    url = f"{ASSESSMENT_API_URL}/{assessment_id}"
    headers = {
        "accept": "application/json",
        "Authorization": API_KEY
    }

    # Get species info from assessment id
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Status code {response.status_code}")
        return None

# Get textual location descriptions for a species from the IUCN API
def get_location_info(genus, species):
    assessment_id = get_assessment_id(genus, species)

    if assessment_id:
        assessment_info = get_species_assessment(assessment_id)
        if assessment_info:
            if "locations" in assessment_info:
                # grab location data from species info
                locations = [loc["description"]["en"] for loc in assessment_info["locations"]]
                return locations
            else:
                print("No location data found.")
                return None
    else:
        print(f"Can't get assessment id.")
        return None

### PART 2: DERIVING TEMPERATURE AND RAINFALL FROM LOCATIONS ###

# Match IUCN location names to standardized location codes using geonames.xlsx
def find_location(locations, file_path="01_frog_data_compilation/data/geonames.xlsx"):
    xls = pd.ExcelFile(file_path) # get geonames excel

    countries_df = pd.read_excel(xls, sheet_name="Countries")
    subnationals_df = pd.read_excel(xls, sheet_name="Subnationals")

    region_codes = []
    region_countries = []
    country_codes = []

    # Match subnational entries (e.g., states or provinces)
    for name in locations:
        subnational_match = subnationals_df[subnationals_df["Subnational Name"].str.lower() == name.lower()] # if name in subnationals sheet
        if not subnational_match.empty:
            region_codes.append(subnational_match.iloc[0]["Subnational Code"]) # subnationals code
            region_countries.append(subnational_match.iloc[0]["Country Code"])

    # Match country-level entries (avoid duplicates with subnationals)
    for name in locations:
        country_match = countries_df[countries_df["Name"].str.lower() == name.lower()] # if name in countries sheet
        if not country_match.empty:
            if not country_match.iloc[0]["ISO3 Code"] in region_countries:
                country_codes.append(country_match.iloc[0]["ISO3 Code"]) # country code
    
    return list(region_codes) + list(country_codes)

# Retrieve climate data from World Bank CCKP API for a given location code
def get_data(code):
    url = f"https://cckpapi.worldbank.org/cckp/v1/cmip6-x0.25_climatology_tas,pr_climatology_annual_1995-2014_median_historical_ensemble_all_mean/{code}?_format=json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    elif response.status_code == 429:
        print("Rate limit hit. Waiting before retrying...")
        time.sleep(5)
        return get_data(code)
    else:
        print("Failed to retrieve data. Status code:", response.status_code)
        return None

# Get latest available temperature and rainfall values for all location codes
def temp_and_rainfall(locations):
    all_temps = []
    all_rainfalls = []
    codes = find_location(locations)
    for code in codes:
        if code:
            data = get_data(code)
            if data:
                all_temps.append(float(list(data["data"]["tas"][code].values())[-1])) # get the last value in KV (most recent year as far as I understand)
                all_rainfalls.append(float(list(data["data"]["pr"][code].values())[-1]))
    return all_temps, all_rainfalls

### PART 3: COMBINE PROCESSES TO GET INFO FOR ALL SPECIES ###

if __name__ == "__main__":

    # Load the results spreadsheet
    results_spreadsheet = "01_frog_data_compilation/results/froggy_analysis_results.csv"
    df_ref = pd.read_csv(results_spreadsheet)

    # Add columns for climate statistics
    df_ref["Min Temperature"] = None
    df_ref["Max Temperature"] = None
    df_ref["Mean Temperature"] = None
    df_ref["Std. Dev. Temperature"] = None
    df_ref["Min Rainfall"] = None
    df_ref["Max Rainfall"] = None
    df_ref["Mean Rainfall"] = None
    df_ref["Std. Dev. Rainfall"] = None

    # Process each frog species to extract and calculate climate data
    for i, row in df_ref.iterrows():

        genus, species = row["Name"].split(' ')

        print("Processing {}: {} {}".format(i, genus, species))

        locations = get_location_info(genus, species)
        if locations:
            all_temps, all_rainfalls = temp_and_rainfall(locations)
        else:
            all_temps, all_rainfalls = None, None
        
        # Store calculated temperature stats
        if all_temps:
            df_ref.at[i, "Min Temperature"] = min(all_temps)
            df_ref.at[i, "Max Temperature"] = max(all_temps)
            df_ref.at[i, "Mean Temperature"] = sum(all_temps) / len(all_temps)
            df_ref.at[i, "Std. Dev. Temperature"] = pd.Series(all_temps).std()
        else:
            df_ref.at[i, "Min Temperature"] = '-'
            df_ref.at[i, "Max Temperature"] = '-'
            df_ref.at[i, "Mean Temperature"] = '-'
            df_ref.at[i, "Std. Dev. Temperature"] = '-'

        # Store calculated rainfall stats
        if all_rainfalls:
            df_ref.at[i, "Min Rainfall"] = min(all_rainfalls)
            df_ref.at[i, "Max Rainfall"] = max(all_rainfalls)
            df_ref.at[i, "Mean Rainfall"] = sum(all_rainfalls) / len(all_rainfalls)
            df_ref.at[i, "Std. Dev. Rainfall"] = pd.Series(all_rainfalls).std()
        else:
            df_ref.at[i, "Min Rainfall"] = '-'
            df_ref.at[i, "Max Rainfall"] = '-'
            df_ref.at[i, "Mean Rainfall"] = '-'
            df_ref.at[i, "Std. Dev. Rainfall"] = '-'

    # Overwrite old Excel file with updated climate data
    if os.path.exists("01_frog_data_compilation/results/froggy_analysis_results.csv"):
        os.remove("01_frog_data_compilation/results/froggy_analysis_results.csv")

    df_ref.to_csv("01_frog_data_compilation/results/froggy_analysis_results.csv", index=False)
    print("Written to 01_frog_data_compilation/results/froggy_analysis_results.xlsx")