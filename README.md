# Species Trait Data Compilation

This project automates the retrieval and compilation of species-specific biological trait data by integrating biodiversity APIs with large language models.

## Frog Analysis

- Uses multiple APIs to collect ecological and biological information:  
  - AmphibiaWeb: morphology and reproductive traits (snout–vent length, clutch size, egg diameter)  
  - IUCN Red List: elevation ranges and habitat categories  
  - World Bank CCKP: temperature and rainfall statistics  
- Automates retrieval of structured (API) and semi-structured (XML parsed via GPT-4o) data  
- Compiles outputs into a clean CSV/Excel dataset with traits like morphology, reproduction, climate, and altitude  
