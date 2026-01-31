# Simplified orchestrator: reads species from CSV, fetches AmphibiaWeb sources,
# uses GPT to extract 5 specific traits, and writes CSV.

import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from trait_utils import (
    get_amphibiaweb_xml,
    get_iucn_assessment,
    extract_location_names,
    get_cckp_raw_json,  # NEW - we'll create this
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # one level up from /scripts
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "..", ".env"))  # load .env from module root

INPUT_CSV = os.path.join(BASE_DIR, "data", "frog_case_study_species.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "amphibiaweb_traits.csv")

# Trait descriptions for GPT prompts
TRAIT_DESCRIPTIONS = {
    "Egg Style": "return one of (aquatic, terrestrial, live-bearing).",
    "Egg Clutch": "average size of the egg clutch, return a whole number.",
    "Snout-Vent Length Male": "average Snout-Vent Length of males, return a number in millimeters (without units).",
    "Snout-Vent Length Female": "average Snout-Vent Length of females, return a number in millimeters (without units).",
    "Average Snout-Vent Length Adult": "average Snout-Vent Length of adults, return a number in millimeters (without units).",
    "Average Temperature": "return a number in celsius (without units).",
    "Average Rainfall": "return a number in millimeters (without units).",
    "Average Altitude": "return a number in meters (without units).",
}

# ------------------------------ GPT Helpers ------------------------------

def _gpt_extract_trait(species: str, trait: str, description: str, xml_text: str) -> str:
    """Extract a single trait using GPT with the specified template."""
    if not xml_text:
        return ""

    prompt = f"""Extract information about the species {species} from the following research paper.
    Focus specifically on the trait: {trait}: {description}

    Return only the key fact(s), in the fewest possible words.
    Do not write full sentences, explanations, or background.
    Output should be just the essential data points (e.g., "10", "desert habitats").
    If no information is found, respond with "N/A".

    Format your response EXACTLY as:
    {trait}: [short fact(s)]

    Text:
    {xml_text}
    """.strip()

    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You extract concise biological traits from noisy text."},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=1000,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            print("exception: ", e)
            # silent backoff to keep minimal output
            pass
    return f"{trait}: "


def _strip_after_colon(result: str) -> str:
    """Return the value after 'trait:' or ''."""
    if not isinstance(result, str):
        return ""
    parts = result.split(":", 1)
    val = parts[1].strip() if len(parts) > 1 else result.strip()
    return val if val else ""


# -------------------------- extraction ------------------------

def extract_all_traits(species: str, xml_text: str, iucn_json: dict, cckp_json: dict) -> dict:
    """Extract 8 traits from AmphibiaWeb XML, IUCN JSON, and CCKP JSON using GPT."""
    out = {
        "Egg Style": "",
        "Egg Clutch": "",
        "Snout-Vent Length Male": "",
        "Snout-Vent Length Female": "",
        "Average Snout-Vent Length Adult": "",
        "Average Altitude": "",
        "Average Temperature": "",
        "Average Rainfall": "",
    }
    
    # Extract AmphibiaWeb traits
    if xml_text:
        for trait in ["Egg Style", "Egg Clutch", "Snout-Vent Length Male", 
                      "Snout-Vent Length Female", "Average Snout-Vent Length Adult"]:
            print(f"Processing trait: {trait}")
            result = _gpt_extract_trait(species, trait, TRAIT_DESCRIPTIONS[trait], xml_text)
            out[trait] = _strip_after_colon(result)
    
    # Extract IUCN altitude trait
    if iucn_json:
        print("Processing trait: Average Altitude")
        iucn_text = str(iucn_json)  # Convert JSON to string for GPT
        result = _gpt_extract_trait(species, "Average Altitude", 
                                    TRAIT_DESCRIPTIONS["Average Altitude"], iucn_text)
        out["Average Altitude"] = _strip_after_colon(result)
    
    # Extract CCKP climate traits
    if cckp_json:
        cckp_text = str(cckp_json)  # Convert JSON to string for GPT
        
        print("Processing trait: Average Temperature")
        result = _gpt_extract_trait(species, "Average Temperature", 
                                    TRAIT_DESCRIPTIONS["Average Temperature"], cckp_text)
        out["Average Temperature"] = _strip_after_colon(result)
        
        print("Processing trait: Average Rainfall")
        result = _gpt_extract_trait(species, "Average Rainfall", 
                                    TRAIT_DESCRIPTIONS["Average Rainfall"], cckp_text)
        out["Average Rainfall"] = _strip_after_colon(result)

    return out


# ------------------------------ Main Pipeline -----------------------------

def run_pipeline(input_csv: str = INPUT_CSV,
                 output_csv: str = OUTPUT_CSV):
    """Read species from Excel, extract AmphibiaWeb traits, write to CSV."""
    
    # read csv file
    df_src = pd.read_csv(input_csv)
    
    if "Species" not in df_src.columns:
        raise ValueError("Expected 'Species' column in input Excel file.")

    results = []
    
    for _, row in df_src.iterrows():
        name = str(row["Species"]).strip()
        parts = name.split()
        
        if len(parts) < 2:
            continue
            
        genus, species = parts[0], parts[1]
        species_key = f"{genus} {species}"

        print(f"Processing species: {species_key}")

        record = {"Species": species_key}

        # Fetch AmphibiaWeb XML
        xml = get_amphibiaweb_xml(genus, species)

        # Fetch IUCN JSON
        iucn_json = get_iucn_assessment(genus, species)

        # Fetch CCKP JSON (need locations from IUCN first)
        cckp_json = None
        if iucn_json:
            locations = extract_location_names(iucn_json)
            if locations:
                cckp_json = get_cckp_raw_json(locations)

        # Extract all traits
        traits = extract_all_traits(species_key, xml, iucn_json, cckp_json)
        record.update(traits)

        results.append(record)

        # Auto-save every 10 species
        if len(results) % 10 == 0:
            df_output = pd.DataFrame(results)
            df_output.to_csv(output_csv, index=False)
            print(f"Auto-saved {len(results)} species to {output_csv}")

    # Write results to CSV
    df_output = pd.DataFrame(results)
    df_output.to_csv(output_csv, index=False)
    print(f"Wrote results to {output_csv}")


if __name__ == "__main__":
    run_pipeline()