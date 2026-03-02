import pandas as pd
import numpy as np
import re

ANSWER_KEY_PATH = "sample_data/bird_answer_key.csv"
MODEL_OUTPUT_PATH = "results/bird_output_results.csv"

NUMERIC_TRAITS = [
    "Body Mass (g)",
    "Brain Mass (g)",
    "Maximum colony size"
]

Z_THRESHOLD = 1.5 # model output is correct if within 1.5 SDs of true value

answer = pd.read_csv(ANSWER_KEY_PATH)
pred = pd.read_csv(MODEL_OUTPUT_PATH)

pred.columns = pred.columns.str.strip()
answer.columns = answer.columns.str.strip()

df = answer.merge(pred, on="Species", suffixes=("_true", "_pred"))

def parse_numeric(value):
    if pd.isna(value):
        return np.nan
    text = str(value).lower().strip()
    if text in ["unknown", "na", "n/a"]:
        return np.nan
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", text)
    if not nums:
        return np.nan
    nums = [float(n) for n in nums]
    return np.mean(nums)

def is_complete(pred_val):
    """A prediction counts as complete if the model returned a non-empty, non-NA answer."""
    text = str(pred_val).strip().lower()
    return text not in ["nan", "", "n/a", "unknown"]

def categorical_correct(true, pred):
    true = str(true).strip().lower()
    pred = str(pred).strip().lower()

    if true in ["nan", "", "n/a"] or pred in ["nan", "", "n/a"]:
        return np.nan # cannot score missing values

    return int(true == pred)

def numeric_correct(true, pred, col):
    true_val = parse_numeric(true)
    pred_val = parse_numeric(pred)

    if np.isnan(true_val) or np.isnan(pred_val):
        return np.nan

    sd = answer[col].apply(parse_numeric).std()

    if pd.isna(sd) or sd == 0:
        return np.nan

    z = abs(pred_val - true_val) / sd
    return int(z <= Z_THRESHOLD)

# evaluate each trait prediction

results = []

trait_cols = [col for col in answer.columns if col != "Species"]

for _, row in df.iterrows():
    species = row["Species"]

    for trait in trait_cols:
        true_val = row[f"{trait}_true"]
        pred_val = row[f"{trait}_pred"]

        if trait in NUMERIC_TRAITS:
            correct = numeric_correct(true_val, pred_val, trait)
        else:
            correct = categorical_correct(true_val, pred_val)

        results.append({
            "Species": species,
            "Trait": trait,
            "Correct": correct,
            "Complete": int(is_complete(pred_val))
        })

results_df = pd.DataFrame(results)

dataset_accuracy    = results_df["Correct"].mean()
species_accuracy    = results_df.groupby("Species")["Correct"].mean()
trait_accuracy      = results_df.groupby("Trait")["Correct"].mean()

dataset_completeness = results_df["Complete"].mean()
trait_completeness   = results_df.groupby("Trait")["Complete"].mean()

print("\n=== BIRD DATASET ACCURACY ===")
print(f"Dataset-wide accuracy:     {dataset_accuracy:.3f}")
print(f"Dataset-wide completeness: {dataset_completeness:.3f}\n")

print("=== Trait-specific accuracy ===")
print(trait_accuracy, "\n")

print("=== Trait-specific completeness ===")
print(trait_completeness, "\n")