import os
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import tiktoken
import time
from openai import RateLimitError
from utils import get_iucn_assessment, search_papers, fetch_pdf, parse_llm_output

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-nano")


def extract_trait_from_paper(species: str, trait: str, paper_text: str, trait_desc: str = ""):
    """Ask LLM to extract a single trait from a single paper."""
    # Use generic encoding to avoid crashing on unknown model names from other providers
    encoding = tiktoken.get_encoding("cl100k_base") 
    tokens = encoding.encode(paper_text)
    max_allowed_tokens = 120000
    if len(tokens) > max_allowed_tokens:
        tokens = tokens[:max_allowed_tokens]
        truncated_text = encoding.decode(tokens) + "... [truncated]"
    else:
        truncated_text = paper_text

    desc_part = f" ({trait_desc})" if trait_desc else ""
    prompt = f"""
    Extract information about the WILD species {species} from the following research paper.
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

    for attempt in range(5): # up to 5 tries
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful biology research assistant that extracts specific information from scientific papers."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000,
            )
            result = response.choices[0].message.content.strip()
            return result

        except RateLimitError as e:
            wait_time = 60 * (attempt + 1) # backoff: 60s, 120s, etc.
            print(f"      Rate limit hit (attempt {attempt+1}), waiting {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"      Unexpected error: {e}")
            break # don’t retry unknown errors

    return f"{trait}: N/A"

def summarize_answers_with_llm(species: str, trait: str, answers: list):
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
- If these values describe the same measurement or concept:
  - If they are numerical and share the same unit, calculate the mean and uncertainty (half the range). Return as: "<mean> +/- <uncertainty> <unit>"
  - Otherwise, reconcile them into one short answer.
- If they are clearly different but all relevant, list all possible answers separated by commas.
- If all are irrelevant or nonsensical, return "N/A".

Return your result in this exact format:
{trait}: [final concise answer]
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise scientific summarizer."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=2000,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Consensus LLM error for {species} {trait}: {e}")
        return f"{trait}: N/A"


def process_species_traits(species_list: list, traits_list: list, output_file: str, trait_descriptions: dict = None, progress_callback=None):
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

    total_steps = len(species_list) * len(traits_list)
    steps_done = 0

    # loop through each species and trait
    for idx, row in df.iterrows():
        species = row["Species"]
        print(f"\nProcessing {species}...")

        # grab iucn
        genus, sp = species.split(" ", 1) if " " in species else (species, "")
        iucn_data = get_iucn_assessment(genus, sp)

        for trait in traits_list:
            print(f"  Processing trait: {trait}")

            # get trait description if provided (case-insensitive key)
            trait_desc = ""
            if trait_descriptions:
                trait_desc = trait_descriptions.get(trait, "")

            # IUCN + LLM PIPELINE
            if iucn_data:
                try:
                    iucn_prompt = f"""
                    Extract the value of the trait "{trait}" for the species {species}
                    from the following IUCN Red List JSON data.
                    {trait}: {trait_desc}

                    If the JSON does not contain the information, respond with "N/A".
                    Return your answer exactly as:
                    {trait}: [short fact(s)]

                    JSON:
                    {iucn_data}
                    """

                    response = client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that extracts factual data from structured JSON."},
                            {"role": "user", "content": iucn_prompt}
                        ],
                        max_completion_tokens=2000,
                    )
                    llm_output = response.choices[0].message.content.strip()
                    value = parse_llm_output(llm_output, trait)
                    if value not in ("N/A", "[N/A]", ""):
                        results.at[idx, trait] = value
                        continue  # skip to next trait
                except Exception as e:
                    print(f"    IUCN LLM extraction failed for {trait}: {e}")
            
            # PUBMED API + LLM PIPELINE
            query = f"wild {species} AND {trait}"
            pmcids = search_papers(query, max_results=20)

            if not pmcids:
                print(f"    No papers found for {species} {trait}")
                results.at[idx, trait] = ""
                continue

            answers = []  # store up to 3 valid extracted answers

            for paper_idx, pmcid in enumerate(pmcids[:20]):  # check up to 20 papers
                # print(f"    Trying paper {paper_idx + 1}/{min(20, len(pmcids))} for {trait}")
                paper_text = fetch_pdf(pmcid)
                if not paper_text:
                    continue

                # log every paper where full text was successfully retrieved
                with open(all_papers_log, "a") as f:
                    f.write(f"{species}\t{trait}\t{pmcid}\n")

                try:
                    llm_output = extract_trait_from_paper(species, trait, paper_text, trait_desc)
                    value = parse_llm_output(llm_output, trait)
                    # print(f"      Extracted value from paper {paper_idx + 1}: {value}")

                    if value not in ("N/A", "[N/A]", ""):
                        # log successful papers (where LLM extracted a valid answer)
                        with open(successful_papers_log, "a") as f:
                            f.write(f"{species}\t{trait}\t{pmcid}\n")
                        answers.append(value)
                        if len(answers) >= 3:
                            break
                except Exception as e:
                    print(f"      LLM error for {species} {trait} paper {paper_idx + 1}: {e}")

            # consensus stage
            if answers:
                consensus_output = summarize_answers_with_llm(species, trait, answers)
                final_value = parse_llm_output(consensus_output, trait)
                results.at[idx, trait] = final_value
            else:
                results.at[idx, trait] = ""

            # save results and notify GUI after each trait
            results.to_csv(output_path, index=False)
            steps_done += 1
            if progress_callback:
                progress_callback(steps_done, total_steps)

    print(f"\nResults written to {output_file}")

    # timing
    end_time = time.time()
    total_time = end_time - start_time
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)
    # print(f"\nTotal processing time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")

    return results

def sanity_check(species_list: list, traits_list: list):
    import statistics
    trait_stats = {}
    # species_counts[species] = list of paper counts, one per trait
    species_counts = {species: [] for species in species_list}

    for trait in traits_list:
        print("Checking trait:", trait)

        for species in species_list:
            print("  Species:", species)
            query = f"wild {species} AND {trait}"
            pmcids = search_papers(query, max_results=20)
            count = len(pmcids)
            species_counts[species].append(count)

        counts = [species_counts[s][-1] for s in species_list]  # counts for this trait
        if counts:
            mean_count = sum(counts) / len(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0.0
        else:
            mean_count = 0.0
            std_dev = 0.0

        trait_stats[trait] = {"mean": mean_count, "std_dev": std_dev}

    # compute per-species stats (average across traits)
    species_stats = {}
    for species, counts in species_counts.items():
        if counts:
            mean_count = sum(counts) / len(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0.0
        else:
            mean_count = 0.0
            std_dev = 0.0
        species_stats[species] = {"mean": mean_count, "std_dev": std_dev}
    
    # Write full results to log file
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)
    log_path = os.path.join(results_dir, "literature_availability_results.txt")
    with open(log_path, "w") as f:
        f.write("Sources Found Per Trait:\n")
        for trait, stats in trait_stats.items():
            f.write(f"{trait}: {stats['mean']:.1f} +- {stats['std_dev']:.1f} papers\n")
        f.write("\nSources Found Per Species:\n")
        for species, stats in species_stats.items():
            f.write(f"{species}: {stats['mean']:.1f} +- {stats['std_dev']:.1f} papers\n")

    return trait_stats, species_stats