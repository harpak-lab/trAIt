import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load Excel file
df = pd.read_excel("results/cross_verification_results.xlsx")

# Drop species column
df_vals = df.iloc[:, 1:]

# -----------------------------------------------------------
# REMOVE numeric-only trait columns (e.g., "1", "2", ..., "16")
# -----------------------------------------------------------
df_vals = df_vals[[col for col in df_vals.columns if not col.strip().isdigit()]]

# ===========================================================
# PART 1 — PER-TRAIT COMPLETENESS GRAPH
# ===========================================================
trait_completeness = {}

for col in df_vals.columns:
    vals = df_vals[col].values
    missing = (vals == "-")
    completeness = 1 - missing.sum() / len(vals)
    trait_completeness[col] = completeness

comp_series = pd.Series(trait_completeness)

# ---- Plot ----
plt.figure(figsize=(14, 5))
plt.bar(comp_series.index, comp_series.values, color="seagreen")
plt.xticks(rotation=60, ha="right")
plt.ylim(0, 1)
plt.ylabel("Proportion Found")
plt.title("Trait Extraction Completeness — Frog Dataset")
plt.tight_layout()
plt.show()

# ===========================================================
# PART 2 — OVERALL MISSINGNESS + OVERALL ACCURACY
# ===========================================================
# Flatten values
values = df_vals.values.flatten()

def is_numeric(x):
    try:
        float(x)
        return True
    except:
        return False

# Masks
missing = (values == "-")
invalid = (values == "invalid")
overlap = (values == "overlap")
numeric = np.array([is_numeric(v) for v in values])

total_cells = len(values)
non_missing = total_cells - missing.sum()

# ---- Missingness ----
overall_missingness = missing.sum() / total_cells

# ---- Weighted Accuracy ----
correct = numeric.sum() + 0.5 * overlap.sum()
overall_accuracy = correct / non_missing if non_missing > 0 else np.nan

# ---- PRINT RESULTS ----
print("\n================ SUMMARY ================\n")
print(f"Overall missingness: {overall_missingness:.2%}")
print(f"Overall accuracy (overlap = 0.5 correct): {overall_accuracy:.2%}")
print("\n=========================================\n")


