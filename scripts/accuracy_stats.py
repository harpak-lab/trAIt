import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Load data
# ----------------------------
df = pd.read_excel("results/cross_verification_results.xlsx")

# Drop species column
df_vals = df.iloc[:, 1:]


# ============================================================
# PART 1 — PER-TRAIT COMPLETENESS (barplot)
# ============================================================
trait_completeness = {}

for col in df_vals.columns:
    col_vals = df_vals[col].values
    missing = (col_vals == "-")
    completeness = 1 - missing.sum() / len(col_vals)
    trait_completeness[col] = completeness

comp_series = pd.Series(trait_completeness)

# ---- Plot ----
plt.figure(figsize=(12, 5))
plt.bar(comp_series.index, comp_series.values)
plt.xticks(rotation=90)
plt.ylim(0, 1)
plt.ylabel("Proportion Found")
plt.title("Trait Extraction Completeness")
plt.tight_layout()
plt.show()


# ============================================================
# PART 2 — OVERALL ACCURACY (single statistic)
# ============================================================

# Flatten everything for accuracy calculation
values = df_vals.values.flatten()

# Numeric detection helper
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

total = len(values)
non_missing = total - missing.sum()

# Weighted correctness
correct = numeric.sum() + 0.5 * overlap.sum()
incorrect = invalid.sum() + 0.5 * overlap.sum()

overall_accuracy = correct / non_missing

print(f"\nOverall accuracy (overlap = 0.5 correct): {overall_accuracy:.2%}")
