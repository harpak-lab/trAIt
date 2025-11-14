# Species Trait Data Compilation

This project automates the retrieval and compilation of species-specific biological trait data by integrating biodiversity APIs with large language models. It is designed to scale from focused case studies to generalized, cross-species analyses.

---

## Generalized Data Pipeline

The system demonstrates a general-purpose trait extraction pipeline.  
- Uses Europe PMC / PubMed Central (PMC) to query scientific literature  
- Retrieves PDFs, parses them, and applies LLM-based extraction prompts to pull out traits such as diet, size, habitat, or environmental associations  
- Works for any list of species and any set of traits, driven by an Excel file and trait description mapping  
- Provides a UI for easy use, supporting batch processing across taxa  

---

## How to Use

1. Clone the repository (if not already done):

   ```bash
   git clone https://github.com/harpak-lab/Data-Compilation-Model.git
   cd Data-Compilation-Model
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure API Keys:

   This project requires API keys for IUCN Red List and OpenAI GPT to retrieve species traits and run extraction.

   **IUCN Red List API**
   
   Go to https://api.iucnredlist.org/ and create an account to generate a new API key.

   **OpenAI GPT**
   
   Sign up or login at https://platform.openai.com/ to get an API key.

   **Add keys to a .env file in the project root (same folder as requirements.txt).**

   ```bash
   IUCN_API_KEY=your_iucn_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Make sure you're on the main branch and inside the correct directory:

   ```bash
   git checkout main
   cd scripts
   ```

5. Run the GUI script:

   ```bash
   python3 gui.py
   ```

6. In the popup window:
   - Upload your Excel file: first column = species, remaining columns = traits.
   - Upload your trait descriptions text file: UTF-8 encoded; each line in the format **trait: description**.

7. Start extraction:
   - Click **Start Data Extraction**.
   - The system will query APIs, fetch papers, and extract trait data.
   - Results will be saved to:
   Data-Compilation-Model/02_generic_data_compilation/results/

