import pandas as pd
import os
import sys

def main():
    # Attempt to locate the file
    possible_paths = [
        "results/frog_case_study_results.csv",
        "/Users/srivi/Desktop/UT/4 Senior/Harpak lab/Data-Compilation-Model/results/frog_case_study_results.csv"
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
            
    if not file_path:
        print("Error: Could not find 'results/frog_case_study_results.csv'")
        sys.exit(1)
        
    print(f"Reading from: {file_path}")
    
    # Load the data
    # We treat empty strings and specific markers like '[N/A]' as NaN (missing)
    # Based on file inspection, empty fields between commas are standard CSV empty cells
    try:
        df = pd.read_csv(file_path, na_values=['[N/A]', 'N/A', 'NA', ''])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    total_species = len(df)
    print(f"Total Species: {total_species}")
    print("-" * 60)
    print(f"{'Trait':<35} | {'Count':<5} | {'Completeness':<10}")
    print("-" * 60)

    # Calculate completeness for each column
    for col in df.columns:
        # Skip the identifier column 'Species' usually, but user said "for each trait"
        # We'll assume everything else is a trait.
        if col.lower() == "species":
            continue
            
        # Count non-NaN values
        non_blank_count = df[col].count()
        
        # Calculate proportion
        proportion = non_blank_count / total_species
        
        print(f"{col:<35} | {non_blank_count:<5} | {proportion:.5f}")

if __name__ == "__main__":
    main()
