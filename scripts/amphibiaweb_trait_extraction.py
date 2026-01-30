# Simplified orchestrator: reads species from XLSX, fetches AmphibiaWeb sources,
# uses GPT to extract 5 specific traits, and writes CSV.

import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from trait_utils import get_amphibiaweb_xml

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # one level up from /scripts
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "..", ".env"))  # load .env from module root

INPUT_XLSX = os.path.join(BASE_DIR, "data", "Froggy_Spreadsheet.xlsx")
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "amphibiaweb_traits.csv")

# Trait descriptions for GPT prompts
TRAIT_DESCRIPTIONS = {
    "Egg Style": "return one of (aquatic, terrestrial, live-bearing).",
    "Egg Clutch": "average size of the egg clutch, return a whole number.",
    "Snout-Vent Length Male": "average Snout–Vent Length of males, return a number in millimeters (without units).",
    "Snout-Vent Length Female": "average Snout–Vent Length of females, return a number in millimeters (without units).",
    "Average Snout-Vent Length Adult": "average Snout–Vent Length of adults, return a number in millimeters (without units).",
}

# ------------------------------ GPT Helpers ------------------------------

def _gpt_extract_trait(species: str, trait: str, description: str, xml_text: str) -> str:
    """Extract a single trait using GPT with the specified template."""
    if not xml_text:
        return "N/A"

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
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract concise biological traits from noisy text."},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=1000,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            # silent backoff to keep minimal output
            pass
    return f"{trait}: N/A"


def _strip_after_colon(result: str) -> str:
    """Return the value after 'trait:' or 'N/A'."""
    if not isinstance(result, str):
        return "N/A"
    parts = result.split(":", 1)
    val = parts[1].strip() if len(parts) > 1 else result.strip()
    return val if val else "N/A"


# -------------------------- AmphibiaWeb extraction ------------------------

def extract_amphibiaweb_traits_simple(species: str, xml_text: str) -> dict:
    """Extract 5 traits from AmphibiaWeb XML using GPT."""
    out = {
        "Egg Style": "N/A",
        "Egg Clutch": "N/A",
        "Snout-Vent Length Male": "N/A",
        "Snout-Vent Length Female": "N/A",
        "Average Snout-Vent Length Adult": "N/A",
    }
    
    if not xml_text:
        return out

    # Extract each trait with its description
    for trait, description in TRAIT_DESCRIPTIONS.items():
        result = _gpt_extract_trait(species, trait, description, xml_text)
        out[trait] = _strip_after_colon(result)

    return out


# ------------------------------ Main Pipeline -----------------------------

def run_pipeline(input_xlsx: str = INPUT_XLSX,
                 output_csv: str = OUTPUT_CSV):
    """Read species from Excel, extract AmphibiaWeb traits, write to CSV."""
    
    # Read the Excel file - single sheet with "Species" column
    df_src = pd.read_excel(input_xlsx)
    
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
        
        # Extract traits
        traits = extract_amphibiaweb_traits_simple(species_key, xml)
        record.update(traits)

        results.append(record)

    # Write results to CSV
    df_output = pd.DataFrame(results)
    df_output.to_csv(output_csv, index=False)
    print(f"Wrote results to {output_csv}")


if __name__ == "__main__":
    run_pipeline()