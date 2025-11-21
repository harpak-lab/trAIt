import pandas as pd

# df = pd.read_excel("sample_data/bird_answer_key_og.xlsx")
# df = df.rename(columns={"SpeciesName": "Species"})
# df["Species"] = df["Species"].str.replace("_", " ")
# cols_to_drop = [
#     "Avian Order",
#     "Family.name",
#     "Family",
#     "Common name",
#     "Completeness_Rating",
#     "logBrainMass",
#     "logBodyMass",
#     "Brain Sample Size"
# ]
# df = df.drop(columns=cols_to_drop, errors="ignore")
# rename_map = {
#     "Colonial?": "Colonial",
#     "Communal foraging?": "Communal foraging",
#     "Cooperative breeding?": "Cooperative breeding",
#     "Habitat_Type": "Habitat Type"
# }
# df = df.rename(columns=rename_map)
# df_sample = df.sample(n=200, random_state=42)

# output_path = "sample_data/bird_answer_key_new.csv"
# df_sample.to_csv(output_path, index=False)






df = pd.read_csv("sample_data/bird_answer_key_new.csv")
for i in range(1, df.shape[0]):
    for j in range(1, df.shape[1]):
        df.iat[i, j] = ''
df.to_csv('sample_data/bird_species.csv', index=False)
