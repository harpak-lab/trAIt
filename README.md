# trAIt: Species-by-Trait Data Retrieval using Large Language Models

trAIt is a publicly-available software for the retrieval of species characteristics from scientific literature catalogued in the Europe PubMed Central (PubMed) database. Using a large language model (LLM), trAIt retrieves papers, synthesizes their content using a consensus-based model, and outputs a species-by-characteristic table.

---

## Overview

trAIt:
- Queries the PubMed open-access API to retrieve scientific papers for each species-trait pair
- Uses a configurable LLM chatbot to extract trait values from each paper
- Applies a consensus mechanism to reconcile results from multiple papers
- Outputs trait values in a structured CSV file

trAIt works for any list of species and any set of traits, with a graphical user interface that allows users to upload input files and run trAIt without writing code.

---

## Prerequisites

- **Python 3.10 or higher** — this tool uses Python features that are not available in earlier versions. You can check your version with:

  ```bash
  python3 --version
  ```

  If you need to upgrade, download the latest Python from [python.org](https://www.python.org/downloads/).

---

## How to Use

1. Clone the repository:

   ```bash
   git clone https://github.com/harpak-lab/trAIt.git
   cd trAIt
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure API Keys:

   trAIt requires API keys for IUCN Red List (optional, for supplementary structured data) and an LLM chatbot provider.

   **IUCN Red List API (Optional)**
   
   Go to https://api.iucnredlist.org/ and create an account to generate a new API key.

   **LLM Chatbot API**
   
   Sign up or login at https://platform.openai.com/ to get an API key. Alternatively, you can use any OpenAI-compatible provider.

   **Add keys to a .env file in the project root (same folder as requirements.txt).**

   ```bash
   IUCN_API_KEY=your_iucn_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Configure Model (Defaults to gpt-5-nano if not set)
   LLM_MODEL=gpt-4o
   
   # Optional: Use a different provider (e.g., DeepSeek, OpenRouter, Localhost)
   # OPENAI_BASE_URL=https://api.deepseek.com/v1
   ```

   *Note: You can use any OpenAI-compatible provider (DeepSeek, OpenRouter, vLLM, Ollama) by setting the `OPENAI_BASE_URL` and `LLM_MODEL` variables.*

4. Make sure you're on the main branch and inside the correct directory:

   ```bash
   git checkout main
   cd scripts
   ```

5. Run the GUI script:

   ```bash
   python3 trAIt.py
   ```

6. In the popup window:
   - Upload your spreadsheet (CSV or Excel): first column = species names, remaining columns = traits of interest
   - Upload your trait descriptions text file: UTF-8 encoded; each line in the format **trait: description**

7. Review trait quality assessment:
   - trAIt will display the mean and standard deviation of papers pulled for each trait, across species
   - Proceed with extraction or revise your trait names based on these results

8. Start extraction:
   - Click **Proceed with Extraction**
   - trAIt will query the PubMed API, retrieve papers, and extract trait information
   - Results will be saved to: trAIt/results/

---

## Input Requirements

**Spreadsheet File (CSV or Excel):**
- First column: species names (e.g., "Mus musculus")
- Subsequent columns: trait names (e.g., "Body Size", "Habitat", "Diet")

**Trait Descriptions File (plain text, UTF-8):**
- Each line should contain: trait_name: description
- For categorical traits, include all possible category labels in the description
- Example: "Mating System: The structure of social and sexual interactions of reproduction. Options are Monogamous, Polygynous, Polyandrous, Polygamous, and Promiscuous."

---

## Output

trAIt generates three files in the results directory:

1. **output_results.csv**: A species-by-trait table with extracted values
2. **all_papers.txt**: Log of all papers retrieved for each species-trait pair
3. **successful_papers.txt**: Log of papers where trAIt extracted non-missing trait values
