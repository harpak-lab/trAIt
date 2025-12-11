import pandas as pd
import numpy as np

df = pd.read_excel("results/cross_verification_results.xlsx")

df_values = df.iloc[:, 1:]

total_cells = df_values.size

values = df_values.values.flatten()

missing_mask = values == "-"
invalid_mask = values == "invalid"
overlap_mask = values == "overlap"

def is_numeric(x):
    try:
        float(x)
        return True
    except:
        return False

numeric_mask = np.array([is_numeric(v) for v in values])

missing_count = missing_mask.sum()
invalid_count = invalid_mask.sum()
overlap_count = overlap_mask.sum()
numeric_count = numeric_mask.sum()

non_missing_count = total_cells - missing_count

correct_count = numeric_count + overlap_count

accuracy = correct_count / non_missing_count if non_missing_count > 0 else 0.0

percent_missing = missing_count / total_cells

print(f"Total cells: {total_cells}")
print(f"Missing cells: {missing_count} ({percent_missing:.2%})")
print(f"Non-missing cells: {non_missing_count}")

print(f"\nCorrect (numeric or 'overlap'): {correct_count}")
print(f"Incorrect ('invalid'): {invalid_count}")

print(f"\nAccuracy (among non-missing): {accuracy:.2%}")