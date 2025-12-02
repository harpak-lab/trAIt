import pandas as pd
import numpy as np
import re

ANSWER_KEY = "sample_data/frog_answer_key_new.csv"
MODEL_OUTPUT = "results/new_frog_output_results.csv"

NUMERIC_TRAITS = [
    "SVL Male",
    "SVL Female",
    "Average SVL Adult",
    "Egg Clutch",
    "Average Temperature",
    "Average Rainfall",
    "Average Altitude"
]

CATEGORICAL_TRAITS = [
    "Egg Style"
]

Z_THRESHOLD = 1.5

ans = pd.read_csv(ANSWER_KEY)
pred = pd.read_csv(MODEL_OUTPUT)

ans.columns = ans.columns.str.strip()
pred.columns = pred.columns.str.strip()

df = ans.merge(pred, on="Species", how="inner", suffixes=("_true", "_pred"))

def parse_numeric(value):
    if pd.isna(value):
        return np.nan

    text = str(value)

    # Extract all numbers
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", text)
    if not nums:
        return np.nan

    nums = [float(n) for n in nums]
    return np.mean(nums)

def categorical_correct(true, pred):
    true = str(true).strip().lower()
    pred = str(pred).strip().lower()

    if true in ["nan", "", "n/a"] or pred in ["nan", "", "n/a"]:
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

common_traits = []
for trait in NUMERIC_TRAITS + CATEGORICAL_TRAITS:
    if f"{trait}_true" in df.columns and f"{trait}_pred" in df.columns:
        common_traits.append(trait)

rows = []

for _, row in df.iterrows():
    species = row["Species"]

    for trait in common_traits:
        true_val = row[f"{trait}_true"]
        pred_val = row[f"{trait}_pred"]

        if trait in NUMERIC_TRAITS:
            correct = numeric_correct(true_val, pred_val, trait)
        else:
            correct = categorical_correct(true_val, pred_val)

        rows.append({
            "Species": species,
            "Trait": trait,
            "True": true_val,
            "Pred": pred_val,
            "Correct": correct
        })

results_df = pd.DataFrame(rows)

dataset_accuracy = results_df["Correct"].mean()
species_accuracy = results_df.groupby("Species")["Correct"].mean()
trait_accuracy = results_df.groupby("Trait")["Correct"].mean()

avg_species_accuracy = species_accuracy.mean()
avg_trait_accuracy = trait_accuracy.mean()

print(f"Average species-wide accuracy: {avg_species_accuracy:.3f}")
print(f"Average trait-wide accuracy: {avg_trait_accuracy:.3f}\n")

print("\n=== FROG DATASET ACCURACY ===")
print(f"Dataset-wide accuracy: {dataset_accuracy:.3f}\n")

print("=== Species-specific accuracy ===")
print(species_accuracy, "\n")

print("=== Trait-specific accuracy ===")
print(trait_accuracy, "\n")