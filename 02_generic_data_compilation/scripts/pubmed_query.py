import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import io
import pdfplumber
import pandas as pd
import tiktoken
import time
from openai import RateLimitError

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
PDF_URL = "https://europepmc.org/backend/ptpmcrender.fcgi"

# --- Europe PMC search (metadata only) ---
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


# --- Fetch single PDF lazily ---
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

def extract_trait_from_paper(species: str, trait: str, paper_text: str, trait_desc: str = ""):
    """Ask GPT to extract a single trait from a single paper."""
    encoding = tiktoken.encoding_for_model("gpt-5-nano")
    tokens = encoding.encode(paper_text)
    print(f"      Original paper length: {len(tokens)} tokens")
    max_allowed_tokens = 120000
    if len(tokens) > max_allowed_tokens:
        tokens = tokens[:max_allowed_tokens]
        truncated_text = encoding.decode(tokens) + "... [truncated]"
    else:
        truncated_text = paper_text

    desc_part = f" ({trait_desc})" if trait_desc else ""
    prompt = f"""
    Extract information about the species {species} from the following research paper.
    Focus specifically on the trait: {trait}{desc_part}

    Return only what is asked, in the fewest possible words.
    Do not write full sentences, explanations, or background.
    Output should be just the essential data points (e.g., "10 cm", "desert habitats").
    If no information is found, respond with "N/A".

    Format your response EXACTLY as:
    {trait}: [short fact(s)]

    Research paper:
    {truncated_text}
    """

    print(
    f"""
    Extract information about the species {species} from the following research paper.
    Focus specifically on the trait: {trait}{desc_part}

    Return only the key fact(s), in the fewest possible words.
    Do not write full sentences, explanations, or background.
    Output should be just the essential data points (e.g., "10 cm", "desert habitats").
    If no information is found, respond with "N/A".

    Format your response EXACTLY as:
    {trait}: [short fact(s)]
    """
    )

    for attempt in range(5):  # up to 5 tries
        try:
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful biology research assistant that extracts specific information from scientific papers."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000,
            )
            result = response.choices[0].message.content.strip()
            print(f"GPT response: {result}")
            return result

        except RateLimitError as e:
            wait_time = 60 * (attempt + 1)  # backoff: 60s, 120s, etc.
            print(f"      Rate limit hit (attempt {attempt+1}), waiting {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"      Unexpected error: {e}")
            break  # don’t retry unknown errors

    return f"{trait}: N/A"


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
            return value
    return "N/A"

def process_species_traits(species_list: list, traits_list: list, output_file: str, trait_descriptions: dict = None):
    """
    Main helper method to process species and traits lists through the pipeline.

    Args:
        species_list: List of species names to process
        traits_list: List of traits to search for
        output_file: Name of the output Excel file
        trait_descriptions: Optional dict mapping lowercase trait -> description
    """

    # Create a DataFrame with species and traits
    data = []
    for species in species_list:
        row = [species] + ["N/A"] * len(traits_list)
        data.append(row)
    
    df = pd.DataFrame(data, columns=["Species"] + traits_list)
    results = df.copy()

    # Ensure trait columns are strings to avoid dtype warnings
    for trait in traits_list:
        results[trait] = results[trait].astype(str)

    # Loop through each species and trait
    for idx, row in df.iterrows():
        species = row["Species"]
        print(f"\nProcessing {species}...")

        for trait in traits_list:
            print(f"  Processing trait: {trait}")

            # Get trait description if provided (case-insensitive key)
            trait_desc = ""
            if trait_descriptions:
                trait_desc = trait_descriptions.get(trait, "")

            query = f"{species} AND {trait}"
            pmcids = search_papers(query, max_results=20)

            if not pmcids:
                print(f"    No papers found for {species} {trait}")
                results.at[idx, trait] = "N/A"
                continue

            found_info = False
            for paper_idx, pmcid in enumerate(pmcids[:5]):  # lazy fetch, up to 5
                print(f"    Trying paper {paper_idx + 1}/{min(5, len(pmcids))} for {trait}")
                paper_text = fetch_pdf(pmcid)
                if not paper_text:
                    continue

                try:
                    gpt_output = extract_trait_from_paper(species, trait, paper_text, trait_desc)
                    value = parse_gpt_output(gpt_output, trait)

                    if value != "N/A":
                        results.at[idx, trait] = value
                        found_info = True
                        print(f"    Found information for {trait} in paper {paper_idx + 1}")
                        break
                    else:
                        print(f"    No information found in paper {paper_idx + 1}")
                except Exception as e:
                    print(f"    GPT error for {species} {trait} paper {paper_idx + 1}: {e}")

            if not found_info:
                results.at[idx, trait] = "N/A"
                print(f"    No information found for {trait} after trying {min(5, len(pmcids))} papers")

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, output_file)
    results.to_excel(output_path, index=False)
    print(f"\nResults written to {output_file}")
    return results

