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

    # debugging purposes
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

    for attempt in range(5): # up to 5 tries
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
            wait_time = 60 * (attempt + 1) # backoff: 60s, 120s, etc.
            print(f"      Rate limit hit (attempt {attempt+1}), waiting {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"      Unexpected error: {e}")
            break # don’t retry unknown errors

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
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1].strip()
            return value
    return "N/A"

def summarize_answers_with_gpt(species: str, trait: str, answers: list):
    if not answers:
        return f"{trait}: N/A"

    # Build summary prompt
    answers_text = "\n".join(f"- {a}" for a in answers)
    prompt = f"""
You are a biology research assistant summarizing extracted values from multiple papers.

Species: {species}
Trait: {trait}

Here are the values found from different papers:
{answers_text}

Instructions:
- If these values describe the same measurement or concept, reconcile or standardize them into one short answer.
- If they are clearly different but all relevant, list all possible answers separated by commas.
- If all are irrelevant or nonsensical, return "N/A".

Return your result in this exact format:
{trait}: [final concise answer]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a precise scientific summarizer."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Consensus GPT error for {species} {trait}: {e}")
        return f"{trait}: N/A"


def process_species_traits(species_list: list, traits_list: list, output_file: str, trait_descriptions: dict = None):
    """Main helper method to process species and traits lists through the pipeline."""
    start_time = time.time()

    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, output_file)

    all_papers_log = os.path.join(results_dir, "all_papers.txt")
    successful_papers_log = os.path.join(results_dir, "successful_papers.txt")

    # clear previous logs if they exist
    open(all_papers_log, "w").close()
    open(successful_papers_log, "w").close()

    # create a DataFrame with species and traits
    data = []
    for species in species_list:
        row = [species] + ["N/A"] * len(traits_list)
        data.append(row)
    
    df = pd.DataFrame(data, columns=["Species"] + traits_list)
    results = df.copy()

    # ensure trait columns are strings to avoid dtype warnings
    for trait in traits_list:
        results[trait] = results[trait].astype(str)

    # loop through each species and trait
    for idx, row in df.iterrows():
        species = row["Species"]
        print(f"\nProcessing {species}...")

        for trait in traits_list:
            print(f"  Processing trait: {trait}")

            # get trait description if provided (case-insensitive key)
            trait_desc = ""
            if trait_descriptions:
                trait_desc = trait_descriptions.get(trait, "")

            query = f"{species} AND {trait}"
            pmcids = search_papers(query, max_results=20)

            if not pmcids:
                print(f"    No papers found for {species} {trait}")
                results.at[idx, trait] = ""
                continue

            answers = []  # store up to 3 valid extracted answers

            for paper_idx, pmcid in enumerate(pmcids[:20]):  # check up to 20 papers
                print(f"    Trying paper {paper_idx + 1}/{min(20, len(pmcids))} for {trait}")
                paper_text = fetch_pdf(pmcid)
                if not paper_text:
                    continue

                # log every paper where full text was successfully retrieved
                with open(all_papers_log, "a") as f:
                    f.write(f"{species}\t{trait}\t{pmcid}\n")

                try:
                    gpt_output = extract_trait_from_paper(species, trait, paper_text, trait_desc)
                    value = parse_gpt_output(gpt_output, trait)
                    print(f"      Extracted value from paper {paper_idx + 1}: {value}")

                    if value not in ("N/A", "[N/A]", ""):
                        # log successful papers (where GPT extracted a valid answer)
                        with open(successful_papers_log, "a") as f:
                            f.write(f"{species}\t{trait}\t{pmcid}\n")
                        answers.append(value)
                        if len(answers) >= 3:
                            print("      Collected 3 valid answers; stopping paper scan.")
                            break
                except Exception as e:
                    print(f"      GPT error for {species} {trait} paper {paper_idx + 1}: {e}")

            # consensus stage
            if answers:
                print(f"    Collected answers for {trait}: {answers}")
                consensus_output = summarize_answers_with_gpt(species, trait, answers)
                final_value = parse_gpt_output(consensus_output, trait)
                results.at[idx, trait] = final_value
                print(f"    Final consensus for {trait}: {final_value}")
            else:
                results.at[idx, trait] = ""
                print(f"    No valid information found for {trait} after {len(pmcids)} papers")
            
        # save results
        results.to_csv(output_path, index=False)

    print(f"\nResults written to {output_file}")

    # timing
    end_time = time.time()
    total_time = end_time - start_time
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nTotal processing time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")

    return results