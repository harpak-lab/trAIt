import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
our_answers_path = os.path.join(base_dir, "results", "uncoded_results_m2_copy.xlsx")
answer_key_path = os.path.join(base_dir, "sample_data", "Answer_Key.csv")
output_path = os.path.join(base_dir, "results", "results_df.xlsx")

our_answers_df = pd.read_excel(our_answers_path)
answer_key_df = pd.read_csv(answer_key_path)

our_answers_df.columns = our_answers_df.columns.str.strip()
answer_key_df.columns = answer_key_df.columns.str.strip()

columns_to_compare = [
    "Social Dominance Hierarchy",
    "Group size(Outside reproductive period)",
    "Age at maturity",
    "Number of offspring per reproductive bout",
    "Number of reproductive bouts/year",
    "Average life expectancy",
    "Migratory behavior",
    "Habitat complexity"
]

results_df = pd.DataFrame(columns=["Scientific name"] + columns_to_compare)

for _, row in our_answers_df.iterrows():
    scientific_name = row["Scientific Name"]
    
    result_row = {"Scientific name": scientific_name}
    
    match = answer_key_df[
        answer_key_df["Scientific name"].str.strip().str.lower() == scientific_name.strip().lower()
    ]
    
    if match.empty:
        continue

    key_row = match.iloc[0]
    
    for col in columns_to_compare:
        our_val = row.get(col, "")
        key_val = key_row.get(col, "")
        
        if pd.isna(our_val) or our_val == "":
            result_row[col] = ""
        else:
            try:
                our_float = float(our_val)
                key_float = float(key_val)
                diff = our_float - key_float

                # for float-based columns, report difference instead of 'invalid'
                if col in [
                    "Age at maturity",
                    "Number of offspring per reproductive bout",
                    "Number of reproductive bouts/year",
                    "Average life expectancy"
                ]:
                    result_row[col] = our_float if our_float == key_float else f"({diff:+.2f})"
                else:
                    result_row[col] = our_float if our_float == key_float else "invalid"

            except ValueError:
                result_row[col] = "invalid"

    results_df = pd.concat([results_df, pd.DataFrame([result_row])], ignore_index=True)

os.makedirs(os.path.join(base_dir, "results"), exist_ok=True)
results_df.to_excel(output_path, index=False)

print(f" Results written to: {output_path}")
