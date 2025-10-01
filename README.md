# Species Trait Data Compilation

This project automates the retrieval and compilation of species-specific biological trait data by integrating biodiversity APIs with large language models. It is designed to scale from focused case studies to generalized, cross-species analyses.

---

## 1. Frog Analysis

The first phase of this project demonstrates a deep dive into amphibians (frogs) as a proof of concept.  
- Uses multiple APIs to collect ecological and biological information:  
  - AmphibiaWeb: morphology and reproductive traits (snout–vent length, clutch size, egg diameter)  
  - IUCN Red List: elevation ranges and habitat categories  
  - World Bank CCKP: temperature and rainfall statistics  
- Automates retrieval of structured (API) and semi-structured (XML parsed via GPT-4o) data  
- Compiles outputs into a clean CSV/Excel dataset with traits like morphology, reproduction, climate, and altitude  

---

## 2. Generalized Data Pipeline

The system then expands into a general-purpose trait extraction pipeline.  
- Uses Europe PMC / PubMed Central (PMC) to query scientific literature  
- Retrieves PDFs, parses them, and applies LLM-based extraction prompts to pull out traits such as diet, size, habitat, or environmental associations  
- Works for any list of species and any set of traits, driven by an Excel file and trait description mapping  
- Provides a UI for easy use, supporting batch processing across taxa  

---

## How to Use


