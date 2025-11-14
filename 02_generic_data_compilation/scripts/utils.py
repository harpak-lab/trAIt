import os
import requests
import io
import pdfplumber
from dotenv import load_dotenv
load_dotenv()

IUCN_API_KEY = os.getenv("IUCN_API_KEY")
TAXA_API_URL = "https://api.iucnredlist.org/api/v4/taxa/scientific_name"
ASSESSMENT_API_URL = "https://api.iucnredlist.org/api/v4/assessment"
BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
PDF_URL = "https://europepmc.org/backend/ptpmcrender.fcgi"

def _iucn_headers():
    return {"Authorization": IUCN_API_KEY or "", "accept": "application/json"}

def get_iucn_assessment_id(genus: str, species: str) -> str | None:
    """Get latest assessment_id for species, else None."""
    url = f"{TAXA_API_URL}?genus_name={genus}&species_name={species}"
    try:
        r = requests.get(url, headers=_iucn_headers(), timeout=30)
        print(r)
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

def search_papers(query: str, max_results: int = 20):
    """Search Europe PMC and return a list of PMCIDs (metadata only)."""
    search_url = f"{BASE_URL}/search"
    params = {"query": query, "resultType": "core", "format": "json", "pageSize": max_results}
    try:
        resp = requests.get(search_url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"      EuropePMC error: {e}")
        return []

    data = resp.json()
    if "resultList" not in data or "result" not in data["resultList"]:
        return []

    pmcids = [article.get("pmcid") for article in data["resultList"]["result"] if article.get("pmcid")]
    return pmcids


def fetch_pdf(pmcid: str):
    """Download and parse a single PDF by PMCID."""
    pdf_url = f"{PDF_URL}?accid={pmcid}&blobtype=pdf"
    try:
        pdf_resp = requests.get(pdf_url, timeout=30)
        if pdf_resp.status_code == 200 and pdf_resp.headers.get("Content-Type") == "application/pdf":
            with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            if text.strip():
                print(f"     Retrieved PDF {pmcid}")
                return text
    except Exception as e:
        print(f"      Failed to fetch/parse PDF {pmcid}: {e}")
    return None

def parse_gpt_output(gpt_output, trait):
    """Parse GPT output to extract information for a single trait."""
    lines = gpt_output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        base_patterns = [f"{trait.lower()}:", f"*{trait.lower()}*:", f"**{trait.lower()}**:"]
        possible_patterns = base_patterns + [f"- {p}" for p in base_patterns]
        if line.lower().startswith(tuple(possible_patterns)):
            value = line.split(":", 1)[1].strip() if ":" in line else ""
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1].strip()
            return value
    return "N/A"