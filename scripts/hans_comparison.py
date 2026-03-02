import pandas as pd
import numpy as np
import re

ANSWER_KEY = "sample_data/hans_answer_key.csv"
MODEL_OUTPUT = "results/hans_output_results.csv"

NUMERIC_TRAITS = [
    "Age at maturity",
    "Number of offspring per reproductive bout",
    "Number of reproductive bouts/year",
    "Average life expectancy"
]

# some columns have slightly different names in output, map them
OUTPUT_RENAME = {
    "Territoriality (males)": "Territoriality(Males)",
    "Territoriality (females)": "Territoriality(Females)",
    "Group Size During Reproduction": "Group size(During reproductive period)",
    "Group Size Outside of Reproduction": "Group size(Outside reproductive period)",
    "# offspring/reproductive bout": "Number of offspring per reproductive bout",
    "# reproductive bouts/year": "Number of reproductive bouts/year",
    "Avg. life expectancy": "Average life expectancy",
    "Group Property": "Group property",
    "Age at Maturity": "Age at maturity",
    "Activity Pattern": "Activity pattern",
}

Z_THRESHOLD = 1.5 # numeric correctness threshold

ans = pd.read_csv(ANSWER_KEY)
pred = pd.read_csv(MODEL_OUTPUT)

pred = pred.rename(columns=OUTPUT_RENAME)

ans.columns = ans.columns.str.strip()
pred.columns = pred.columns.str.strip()

df = ans.merge(pred, left_on="Scientific name", right_on="Species", how="inner",
               suffixes=("_true", "_pred"))

def parse_numeric(value):
    """
    Converts:
      - single numbers ("3.2")
      - ranges ("0.11–0.21" or "0.14-0.22")
      - messy strings with multiple numbers ("0.3 years, 0.12 years")
    into a single float (mean of all numbers found).
    """
    if pd.isna(value):
        return np.nan

    text = str(value)

    # find all numbers in the string
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", text)
    if not nums:
        return np.nan

    nums = [float(n) for n in nums]
    return np.mean(nums)

def is_complete(pred_val):
    """A prediction counts as complete if the model returned a non-empty, non-NA answer."""
    text = str(pred_val).strip().lower()
    return text not in ["nan", "", "n/a", "unknown", "none"]

def categorical_correct(true, pred):
    true = str(true).strip().lower()
    pred = str(pred).strip().lower()

    if true in ["na", "nan", "", "n/a"] or pred in ["na", "nan", "", "n/a"]:
        return np.nan

    return int(true == pred)

def numeric_correct(true, pred, trait):
    true_val = parse_numeric(true)
    pred_val = parse_numeric(pred)

    if np.isnan(true_val) or np.isnan(pred_val):
        return np.nan

    sd = ans[trait].apply(parse_numeric).std()

    if pd.isna(sd) or sd == 0:
        return np.nan

    z = abs(pred_val - true_val) / sd
    return int(z <= Z_THRESHOLD)

# main eval pipeline

trait_columns = [
    col for col in ans.columns
    if col not in ["Scientific name", "Class", "Order", "Family", "Common Name"]
]

# drop traits that are not present in BOTH true and pred
trait_columns = [
    t for t in trait_columns
    if f"{t}_true" in df.columns and f"{t}_pred" in df.columns
]

rows = []

for _, row in df.iterrows():
    species = row["Scientific name"]

    for trait in trait_columns:
        true_val = row[f"{trait}_true"]

        pred_col = f"{trait}_pred"
        if pred_col not in df.columns:
            correct = np.nan
            pred_val = None
        else:
            pred_val = row[pred_col]

            if trait in NUMERIC_TRAITS:
                correct = numeric_correct(true_val, pred_val, trait)
            else:
                correct = categorical_correct(true_val, pred_val)

        rows.append({
            "Species": species,
            "Trait": trait,
            "True": true_val,
            "Pred": pred_val,
            "Correct": correct,
            "Complete": int(is_complete(pred_val))
        })

results_df = pd.DataFrame(rows)

dataset_accuracy     = results_df["Correct"].mean()
species_accuracy     = results_df.groupby("Species")["Correct"].mean()
trait_accuracy       = results_df.groupby("Trait")["Correct"].mean()

dataset_completeness = results_df["Complete"].mean()
trait_completeness   = results_df.groupby("Trait")["Complete"].mean()

print("\n=== HANS DATASET ACCURACY ===")
print(f"Dataset-wide accuracy:     {dataset_accuracy:.3f}")
print(f"Dataset-wide completeness: {dataset_completeness:.3f}\n")

print("=== Trait-specific accuracy ===")
print(trait_accuracy, "\n")

print("=== Trait-specific completeness ===")
print(trait_completeness, "\n")