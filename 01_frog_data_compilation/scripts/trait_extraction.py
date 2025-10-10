# Main orchestrator: reads species from XLSX, fetches sources via trait_utils,
# uses gpt-5-nano to extract AmphibiaWeb traits, computes stats, and writes CSV.

import os
import pandas as pd
from statistics import mean, pstdev
from dotenv import load_dotenv
from openai import OpenAI

from trait_utils import (
    get_amphibiaweb_xml,
    get_iucn_assessment,
    extract_altitude_from_iucn,
    extract_habitat_codes_top_level,
    extract_location_names,
    collect_climate_arrays,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # one level up from /scripts
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "..", ".env")) # load .env from module root

INPUT_XLSX = os.path.join(BASE_DIR, "data", "Froggy_Spreadsheet.xlsx")
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "frog_traits_master.csv")
GEONAMES_XLSX = os.path.join(BASE_DIR, "data", "geonames.xlsx")
INPUT_SHEET = "All Frogs"

# ------------------------------ GPT Helpers ------------------------------

def _gpt_extract(species: str, trait: str, text: str, trait_desc: str = "") -> str:
    if not text:
        return f"{trait}: N/A"

    desc_part = f" ({trait_desc})" if trait_desc else ""

    prompt = f"""
    Extract information about the species {species} from the following text.
    Focus specifically on the trait: {trait}{desc_part}

    Return only what is asked, in the fewest possible words.
    Do not write full sentences or explanations.
    If no information is found, respond with "N/A".

    Format EXACTLY as:
    {trait}: [short fact(s)]

    Text:
    {text}
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
        except Exception:
            # silent backoff to keep minimal output
            pass
    return f"{trait}: N/A"

def _strip_after_colon(label: str, result: str) -> str:
    """Return the value after 'label:' or 'N/A'."""
    if not isinstance(result, str):
        return "N/A"
    parts = result.split(":", 1)
    val = parts[1].strip() if len(parts) > 1 else result.strip()
    return val if val else "N/A"

def _split_avg_uncert(value: str) -> tuple[str, str]:
    """
    Expect 'avg +- uncert'. If not present or malformed, return ('-', '-').
    Accepts variations like '+/-' or '+ -'.
    """
    if not isinstance(value, str):
        return "-", "-"
    normalized = value.replace("±", "+-").replace("+/-", "+-").replace("+ -", "+-")
    if "+-" not in normalized:
        return "-", "-"
    try:
        avg, uncert = normalized.split("+-", 1)
        return avg.strip(), uncert.strip()
    except Exception:
        return "-", "-"

# -------------------------- AmphibiaWeb extraction ------------------------

def extract_amphibiaweb_traits(species: str, xml_text: str) -> dict:
    """Extract SVL (male/female/avg), clutch min/max, egg diameter (avg/±), and egg style+confidence."""
    out = {
        "SVL Male (mm)": "-",
        "+/- SVL Male (mm)": "-",
        "SVL Female (mm)": "-",
        "+/- SVL Female (mm)": "-",
        "Avg SVL Adult (mm)": "-",
        "+/- SVL Adult (mm)": "-",
        "Min Egg Clutch": "-",
        "Max Egg Clutch": "-",
        "Avg Egg Diameter (mm)": "-",
        "+/- Egg Diameter (mm)": "-",
        "Egg Style": "-",
        "Egg Style Confidence": "-",
    }
    if not xml_text:
        return out

    # SVLs & Egg diameter expect "avg +- uncert"
    male = _strip_after_colon("Male SVL", _gpt_extract(species, "Male SVL (mm)", xml_text,
                                                       "Return 'avg +- uncert' in mm; if single value, use 'avg +- 0'"))
    female = _strip_after_colon("Female SVL", _gpt_extract(species, "Female SVL (mm)", xml_text,
                                                           "Return 'avg +- uncert' in mm; if single value, use 'avg +- 0'"))
    avg_svl = _strip_after_colon("Avg SVL", _gpt_extract(species, "Average SVL (mm)", xml_text,
                                                         "If male/female ranges present, compute overall average and half-range"))
    egg_diam = _strip_after_colon("Egg Diameter", _gpt_extract(species, "Egg Diameter (mm)", xml_text,
                                                                "Return 'avg +- uncert' in mm; if single value, use 'avg +- 0'"))
    min_clutch = _strip_after_colon("Min Egg Clutch", _gpt_extract(species, "Minimum clutch size", xml_text,
                                                                   "Lower value of eggs per clutch range; if single value, that value; integer if possible"))
    max_clutch = _strip_after_colon("Max Egg Clutch", _gpt_extract(species, "Maximum clutch size", xml_text,
                                                                   "Upper value of eggs per clutch range; if single value, that value; integer if possible"))

    m_avg, m_unc = _split_avg_uncert(male)
    f_avg, f_unc = _split_avg_uncert(female)
    a_avg, a_unc = _split_avg_uncert(avg_svl)
    e_avg, e_unc = _split_avg_uncert(egg_diam)

    out["SVL Male (mm)"] = m_avg if m_avg != "-" else "-"
    out["+/- SVL Male (mm)"] = m_unc if m_unc != "-" else "-"
    out["SVL Female (mm)"] = f_avg if f_avg != "-" else "-"
    out["+/- SVL Female (mm)"] = f_unc if f_unc != "-" else "-"
    out["Avg SVL Adult (mm)"] = a_avg if a_avg != "-" else "-"
    out["+/- SVL Adult (mm)"] = a_unc if a_unc != "-" else "-"
    out["Avg Egg Diameter (mm)"] = e_avg if e_avg != "-" else "-"
    out["+/- Egg Diameter (mm)"] = e_unc if e_unc != "-" else "-"
    out["Min Egg Clutch"] = min_clutch if min_clutch and min_clutch.upper() != "N/A" else "-"
    out["Max Egg Clutch"] = max_clutch if max_clutch and max_clutch.upper() != "N/A" else "-"

    # Egg style (0 aquatic, 1 terrestrial, 2 live-bearing) + confidence 0-100
    style_resp = _gpt_extract(
        species,
        "Reproductive style",
        xml_text,
        ("Respond with '0,confidence' for aquatic; '1,confidence' for terrestrial; "
         "'2,confidence' for live-bearing. Confidence 0-100. No words, just two numbers.")
    )
    val = _strip_after_colon("Reproductive style", style_resp)
    if "," in val:
        style, conf = [s.strip() for s in val.split(",", 1)]
        out["Egg Style"] = style if style else "-"
        out["Egg Style Confidence"] = conf if conf else "-"
    else:
        out["Egg Style"] = "-"
        out["Egg Style Confidence"] = "-"

    return out


# ------------------------------ Main Pipeline -----------------------------

def _safe_stats(arr: list[float]) -> tuple[str, str, str, str]:
    if not arr:
        return "-", "-", "-", "-"
    if len(arr) == 1:
        x = arr[0]
        return f"{x:.3f}", f"{x:.3f}", f"{x:.3f}", "0"
    mn = f"{min(arr):.3f}"
    mx = f"{max(arr):.3f}"
    mu = f"{mean(arr):.3f}"
    sd = f"{pstdev(arr):.3f}"  # population std dev to be stable for small n
    return mn, mx, mu, sd

def run_pipeline(input_xlsx: str = INPUT_XLSX,
                 input_sheet: str = INPUT_SHEET,
                 output_csv: str = OUTPUT_CSV,
                 geonames_xlsx: str = GEONAMES_XLSX):
    xls = pd.ExcelFile(input_xlsx)
    if input_sheet not in xls.sheet_names:
        raise ValueError(f"Sheet '{input_sheet}' not found in {input_xlsx}")
    df_src = xls.parse(input_sheet, header=1)  # preserves your previous indexing
    if "Name" not in df_src.columns:
        raise ValueError("Expected 'Name' column in input sheet.")

    results = []
    for _, row in df_src.iterrows():
        name = str(row["Name"]).strip()
        parts = name.split()
        if len(parts) < 2:
            continue
        genus, species = parts[0], parts[1]
        species_key = f"{genus} {species}"

        print(f"Processing species: {species_key}")

        record = {"Name": species_key}

        # AmphibiaWeb
        xml = get_amphibiaweb_xml(genus, species)
        record.update(extract_amphibiaweb_traits(species_key, xml))

        # IUCN (altitude, habitats, locations)
        iucn_json = get_iucn_assessment(genus, species)
        min_alt, max_alt = extract_altitude_from_iucn(iucn_json) if iucn_json else ("-", "-")
        record["Min Altitude"] = min_alt
        record["Max Altitude"] = max_alt

        # Habitat one-hot (1..16)
        for c in map(str, range(1, 17)):
            record[c] = 0
        if iucn_json:
            tops = set(extract_habitat_codes_top_level(iucn_json))
            for c in tops:
                if c in record:
                    record[c] = 1

        # CCKP (temperature/rainfall stats) via IUCN locations
        temps, rains = [], []
        if iucn_json:
            locs = extract_location_names(iucn_json)
            if locs:
                temps, rains = collect_climate_arrays(locs, geonames_file=geonames_xlsx)

        t_min, t_max, t_mean, t_sd = _safe_stats(temps)
        r_min, r_max, r_mean, r_sd = _safe_stats(rains)
        record["Min Temperature"] = t_min
        record["Max Temperature"] = t_max
        record["Mean Temperature"] = t_mean
        record["Std. Dev. Temperature"] = t_sd
        record["Min Rainfall"] = r_min
        record["Max Rainfall"] = r_max
        record["Mean Rainfall"] = r_mean
        record["Std. Dev. Rainfall"] = r_sd

        results.append(record)

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print("Wrote results to", output_csv)


if __name__ == "__main__":
    run_pipeline()
