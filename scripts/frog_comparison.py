import pandas as pd
import re
import numpy as np

'''
# STEP 1: CLEAN UP FROG ANSWER KEY
df = pd.read_excel("sample_data/frog_answer_key.xlsx")

rename_map = {
    "Name": "Species",
    "SVL Male (mm)": "SVL Male",
    "SVL Female (mm)": "SVL Female",
    "Avg SVL Adult (mm)": "Average SVL Adult",
    "Mean Temperature": "Average Temperature",
    "Mean Rainfall": "Average Rainfall",
}
df = df.rename(columns=rename_map)

cols_to_drop = [
    "+/- SVL Male (mm)", "+/- SVL Female (mm)", "+/- SVL Adult (mm)",
    "+/- Egg Diameter (mm)", "Avg Egg Diameter (mm)", 
    "Std. Dev. Temperature", "Std. Dev. Rainfall",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16"
]
df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")

df = df.head(200)

df.to_csv("sample_data/new_frog_answer_key.csv", index=False)
'''

'''
# STEP 2: CLEAN UP FROG OUTPUT RESULTS
df = pd.read_csv("results/frog_output_results.csv")

cols_to_drop = [
    "Average Hatch Time",
    "Average Development Time",
    "Average Time of Day",
    "Average Age at Maturity"
]
df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")

cols_to_clean = [c for c in df.columns if c not in ["Species", "Egg Style"]]
def extract_number(value):
    if pd.isna(value):
        return value
    if isinstance(value, (int, float)):
        return value
    value = str(value)
    # Find number pattern, e.g. 12, 12.5, 0.87
    match = re.search(r"-?\d+\.?\d*", value)
    if match:
        num = match.group()
        # convert automatically: if integer-like, make int; else float
        return float(num) if "." in num else int(num)
    return value
for col in cols_to_clean:
    df[col] = df[col].apply(extract_number)

# Egg Style aquatic 0, terrestrial 1
def encode_egg_style(value):
    if pd.isna(value) or str(value).strip() == "":
        return ""
    v = str(value).strip().lower()
    if v == "aquatic":
        return 0
    if v == "terrestrial":
        return 1
    return value # shouldn't get here

if "Egg Style" in df.columns:
    df["Egg Style"] = df["Egg Style"].apply(encode_egg_style)

df.to_csv("results/new_frog_output_results.csv", index=False)
'''

# STEP 3: ACTUAL COMPARISON

def to_float(x):
    """Extract numeric value from any string; return np.nan if none."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()

    # find integer or float
    m = re.search(r"-?\d+\.?\d*", s)
    if m:
        num = m.group()
        return float(num)
    return np.nan

key = pd.read_csv("sample_data/new_frog_answer_key.csv")
out = pd.read_csv("results/new_frog_output_results.csv")

numeric_cols_key = [
    "SVL Male","SVL Female","Average SVL Adult",
    "Min Egg Clutch","Max Egg Clutch",
    "Min Temperature","Max Temperature","Average Temperature",
    "Min Rainfall","Max Rainfall","Average Rainfall",
    "Min Altitude","Max Altitude"
]

numeric_cols_out = [
    "SVL Male","SVL Female","Average SVL Adult",
    "Egg Clutch","Average Temperature",
    "Average Rainfall","Average Altitude"
]

# Convert all numeric columns in both spreadsheets
for col in numeric_cols_key:
    key[col] = key[col].apply(to_float)

for col in numeric_cols_out:
    out[col] = out[col].apply(to_float)

comparison = pd.DataFrame()
comparison["Species"] = out["Species"]

def format_diff(correct, predicted):
    """Return (+X) or (-X) depending on difference."""
    try:
        diff = correct - predicted
    except:
        print(f"Error computing difference: correct={correct}, predicted={predicted}")
    if diff > 0:
        return f"(+{diff})"
    else:
        return f"({diff})"  # negative already has "-"

def safe_val(x):
    """Return np.nan if value is missing or empty string."""
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if s == "": return np.nan
    return x


# 1. Direct comparison numeric (SVL Male / SVL Female / Average SVL Adult)
for col in ["SVL Male", "SVL Female", "Average SVL Adult"]:
    result_vals = []
    for i in range(len(out)):
        correct = safe_val(key.loc[i, col])
        predicted = safe_val(out.loc[i, col])

        if pd.isna(correct) or pd.isna(predicted):
            result_vals.append("")    # blank if either missing
        elif correct == predicted:
            result_vals.append(predicted)
        else:
            result_vals.append(format_diff(correct, predicted))
    comparison[col] = result_vals

# 2. Egg Style (discrete)
egg_style_vals = []
for i in range(len(out)):
    correct = safe_val(key.loc[i, "Egg Style"])
    predicted = safe_val(out.loc[i, "Egg Style"])
    # blank if either is missing
    if pd.isna(correct) or pd.isna(predicted):
        egg_style_vals.append("")
        continue
    # convert both to int (so 1 and 1.0 become identical)
    try:
        correct_int = int(correct)
        predicted_int = int(predicted)
    except:
        egg_style_vals.append("invalid")
        continue
    # now compare
    if correct_int == predicted_int:
        egg_style_vals.append(correct_int)   # or predicted_int, same now
    else:
        egg_style_vals.append("invalid")
comparison["Egg Style"] = egg_style_vals

# 3. Egg Clutch — check if inside min/max range
egg_clutch_vals = []
for i in range(len(out)):
    predicted = safe_val(out.loc[i, "Egg Clutch"])
    min_val = safe_val(key.loc[i, "Min Egg Clutch"])
    max_val = safe_val(key.loc[i, "Max Egg Clutch"])
    if pd.isna(predicted) or pd.isna(min_val) or pd.isna(max_val):
        egg_clutch_vals.append("")
        continue
    if min_val <= predicted <= max_val:
        egg_clutch_vals.append(predicted)
    else:
        # compute distance from nearest boundary
        if predicted < min_val:
            diff = min_val - predicted
            egg_clutch_vals.append(f"(-{diff})")
        else:
            diff = predicted - max_val
            egg_clutch_vals.append(f"(+{diff})")
comparison["Egg Clutch"] = egg_clutch_vals

# 4. Average Altitude — compare to Min/Max Altitude
avg_alt_vals = []
for i in range(len(out)):
    predicted = safe_val(out.loc[i, "Average Altitude"])
    min_val = safe_val(key.loc[i, "Min Altitude"])
    max_val = safe_val(key.loc[i, "Max Altitude"])
    if pd.isna(predicted) or pd.isna(min_val) or pd.isna(max_val):
        avg_alt_vals.append("")
        continue
    if min_val <= predicted <= max_val:
        avg_alt_vals.append(predicted)
    else:
        if predicted < min_val:
            diff = min_val - predicted
            avg_alt_vals.append(f"(-{diff})")
        else:
            diff = predicted - max_val
            avg_alt_vals.append(f"(+{diff})")
comparison["Average Altitude"] = avg_alt_vals

# 5. Average Temperature — hybrid logic
avg_temp_vals = []
for i in range(len(out)):
    predicted = safe_val(out.loc[i, "Average Temperature"])
    correct_avg = safe_val(key.loc[i, "Average Temperature"])
    min_val = safe_val(key.loc[i, "Min Temperature"])
    max_val = safe_val(key.loc[i, "Max Temperature"])
    if pd.isna(predicted) or pd.isna(correct_avg):
        avg_temp_vals.append("")
        continue
    if predicted == correct_avg:
        avg_temp_vals.append(predicted)
    else:
        if min_val <= predicted <= max_val:
            avg_temp_vals.append(predicted)
        else:
            if predicted < min_val:
                diff = min_val - predicted
                avg_temp_vals.append(f"(-{diff})")
            else:
                diff = predicted - max_val
                avg_temp_vals.append(f"(+{diff})")
comparison["Average Temperature"] = avg_temp_vals

# 6. Average Rainfall — same hybrid logic as temperature
avg_rain_vals = []
for i in range(len(out)):
    predicted = safe_val(out.loc[i, "Average Rainfall"])
    correct_avg = safe_val(key.loc[i, "Average Rainfall"])
    min_val = safe_val(key.loc[i, "Min Rainfall"])
    max_val = safe_val(key.loc[i, "Max Rainfall"])
    if pd.isna(predicted) or pd.isna(correct_avg):
        avg_rain_vals.append("")
        continue
    if predicted == correct_avg:
        avg_rain_vals.append(predicted)
    else:
        if min_val <= predicted <= max_val:
            avg_rain_vals.append(predicted)
        else:
            if predicted < min_val:
                diff = min_val - predicted
                avg_rain_vals.append(f"(-{diff})")
            else:
                diff = predicted - max_val
                avg_rain_vals.append(f"(+{diff})")
comparison["Average Rainfall"] = avg_rain_vals

comparison.to_csv("results/frog_comparison_results.csv", index=False)
