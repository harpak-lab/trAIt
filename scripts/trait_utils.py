# Utilities for all external data access (AmphibiaWeb, IUCN, CCKP) and helpers.

import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ----------------------------- AmphibiaWeb -----------------------------

def get_amphibiaweb_xml(genus: str, species: str) -> str | None:
    """Return AmphibiaWeb XML text for a given species, or None if not found."""
    url = f"https://amphibiaweb.org/cgi/amphib_ws?where-genus={genus}&where-species={species}&src=amphibiaweb"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml-xml")
        if soup.find("error"):
            return None
        return r.text
    except requests.RequestException:
        return None


# -------------------------------- IUCN --------------------------------

IUCN_API_KEY = os.getenv("IUCN_API_KEY")
TAXA_API_URL = "https://api.iucnredlist.org/api/v4/taxa/scientific_name"
ASSESSMENT_API_URL = "https://api.iucnredlist.org/api/v4/assessment"

def _iucn_headers():
    return {"Authorization": IUCN_API_KEY or "", "accept": "application/json"}

def get_iucn_assessment_id(genus: str, species: str) -> str | None:
    """Get latest assessment_id for species, else None."""
    url = f"{TAXA_API_URL}?genus_name={genus}&species_name={species}"
    try:
        r = requests.get(url, headers=_iucn_headers(), timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        assessments = data.get("assessments", [])
        latest = next((a for a in assessments if a.get("latest")), None)
        return latest.get("assessment_id") if latest else None
    except requests.RequestException:
        return None

def get_iucn_assessment(genus: str, species: str) -> dict | None:
    """Get full IUCN assessment JSON for species, else None."""
    aid = get_iucn_assessment_id(genus, species)
    if not aid:
        return None
    try:
        r = requests.get(f"{ASSESSMENT_API_URL}/{aid}", headers=_iucn_headers(), timeout=30)
        return r.json() if r.status_code == 200 else None
    except requests.RequestException:
        return None

def extract_altitude_from_iucn(assessment: dict) -> tuple[str, str]:
    """Return (min_altitude, max_altitude) as strings or '-'."""
    info = assessment.get("supplementary_info", {}) if assessment else {}
    lo = info.get("lower_elevation_limit")
    hi = info.get("upper_elevation_limit")
    return (str(lo) if lo is not None else "-", str(hi) if hi is not None else "-")

def extract_habitat_codes_top_level(assessment: dict) -> list[str]:
    """Return unique top-level habitat codes ['1'..'16'] present."""
    codes = set()
    for h in assessment.get("habitats", []) if assessment else []:
        code = h.get("code")
        if isinstance(code, str) and "_" in code:
            codes.add(code.split("_")[0])
    return sorted(codes, key=lambda x: int(x))

def extract_location_names(assessment: dict) -> list[str]:
    """Return list of location names (strings) from IUCN assessment."""
    out = []
    for loc in assessment.get("locations", []) if assessment else []:
        desc = (loc.get("description") or {}).get("en")
        if isinstance(desc, str) and desc.strip():
            out.append(desc.strip())
    return out


# ------------------------------ CCKP + Geo -----------------------------

# geonames.xlsx should have sheets: 
# # "Countries" with columns ["Name","ISO3 Code"],
# # "Subnationals" with columns ["Subnational Name","Subnational Code","Country Code"].

def find_location_codes(location_names: list[str],
                        geonames_file: str = "data/geonames.xlsx") -> list[str]:
    """Map location display names to codes expected by CCKP (subnational first, then country)."""
    try:
        xls = pd.ExcelFile(geonames_file)
        countries_df = pd.read_excel(xls, sheet_name="Countries")
        subs_df = pd.read_excel(xls, sheet_name="Subnationals")
    except Exception:
        return []

    region_codes, region_countries, country_codes = [], set(), []

    for name in location_names:
        m = subs_df[subs_df["Subnational Name"].str.lower() == name.lower()]
        if not m.empty:
            region_codes.append(str(m.iloc[0]["Subnational Code"]))
            region_countries.add(str(m.iloc[0]["Country Code"]))

    for name in location_names:
        m = countries_df[countries_df["Name"].str.lower() == name.lower()]
        if not m.empty:
            iso3 = str(m.iloc[0]["ISO3 Code"])
            if iso3 not in region_countries:
                country_codes.append(iso3)

    return list(dict.fromkeys(region_codes + country_codes))  # unique, preserve order

def _cckp_get(code: str, max_retries: int = 3, backoff_s: int = 5) -> dict | None:
    url = (
        "https://cckpapi.worldbank.org/cckp/v1/"
        "cmip6-x0.25_climatology_tas,pr_climatology_annual_1995-2014_median_historical_ensemble_all_mean/"
        f"{code}?_format=json"
    )
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(backoff_s * (attempt + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(backoff_s * (attempt + 1))
    return None

def get_cckp_latest_values(code: str) -> tuple[float | None, float | None]:
    """Return (latest_temp_C, latest_rain_mm) for a code, or (None, None)."""
    data = _cckp_get(code)
    if not data or "data" not in data:
        return None, None
    try:
        tas_dict = data["data"]["tas"][code]
        pr_dict = data["data"]["pr"][code]
        # last chronological entry
        temp = float(list(tas_dict.values())[-1])
        rain = float(list(pr_dict.values())[-1])
        return temp, rain
    except Exception:
        return None, None

def collect_climate_arrays(location_names: list[str],
                           geonames_file: str = "data/geonames.xlsx") -> tuple[list[float], list[float]]:
    """Return arrays of temps and rains across all mapped codes."""
    temps, rains = [], []
    for code in find_location_codes(location_names, geonames_file):
        t, r = get_cckp_latest_values(code)
        if t is not None:
            temps.append(t)
        if r is not None:
            rains.append(r)
    return temps, rains

def get_cckp_raw_json(location_names: list[str], 
                      geonames_file: str = None) -> dict | None:
    """Return combined raw CCKP JSON for all location codes."""
    if geonames_file is None:
        geonames_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "geonames.xlsx")
    
    codes = find_location_codes(location_names, geonames_file)
    if not codes:
        return None
    
    combined_data = {"data": {"tas": {}, "pr": {}}}
    
    for code in codes:
        data = _cckp_get(code)
        if data and "data" in data:
            if "tas" in data["data"]:
                combined_data["data"]["tas"].update(data["data"]["tas"])
            if "pr" in data["data"]:
                combined_data["data"]["pr"].update(data["data"]["pr"])
    
    return combined_data if combined_data["data"]["tas"] or combined_data["data"]["pr"] else None