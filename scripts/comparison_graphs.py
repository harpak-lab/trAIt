import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

### OVERALL ACCURACIES ###

average_species_accuracy = {
    "Mixed Vertebrate": 0.632,
    "Bird": 0.703,
    "Frog": 0.202
}

average_trait_accuracy = {
    "Mixed Vertebrate": 0.694,
    "Bird": 0.547,
    "Frog": 0.867
}

overall_accuracy = {
    "Mixed Vertebrate": 0.806,
    "Bird": 0.654,
    "Frog": 0.329
}


### TRAIT ACCURACIES ###

hans_trait_accuracy = {
    "Activity pattern": 0.700,
    "Age at maturity": 0.850,
    "Average life expectancy": 0.820,
    "Group property": 0.650,
    "Group size (During reproduction)": 0.750,
    "Group size (Outside reproduction)": 0.720,
    "Mating System": 0.780,
    "Migratory behavior": 0.700,
    "Number of offspring per reproductive bout": 0.833,
    "Number of reproductive bouts/year": 0.820,
    "Social Dominance Hierarchy": 0.680,
    "Territoriality (Females)": 0.760,
    "Territoriality (Males)": 0.740
}

bird_trait_accuracy = {
    "Body Mass (g)": 0.953,
    "Brain Mass (g)": 0.250,
    "Colonial": 0.250,
    "Communal foraging": 0.438,
    "Cooperative breeding": 0.620,
    "Habitat Type": 0.732,
    "Maximum colony size": 0.600,
    "Migratory": 0.669,
    "Sociality outside of breeding": 0.520
}

frog_trait_accuracy = {
    "Average Rainfall": 1.000,
    "Average SVL Adult": 1.000,
    "Average Temperature": 0.706,
    "Egg Style": 0.000,
    "SVL Female": 1.000,
    "SVL Male": 1.000
}

### SPECIES ACCURACIES ###

hans_species_accuracy = {
    "Anolis carolinensis": 0.700,
    "Cavia porcellus": 0.800,
    "Columba livia": 0.720,
    "Coturnix japonica": 0.750,
    "Fukomys damarensis": 0.680,
    "Pan troglodytes": 0.770,
    "Passer domesticus": 0.700,
    "Pipra filicauda": 0.710,
    "Rattus norvegicus": 0.800,
    "Taeniopygia guttata": 0.900,
}

bird_species_accuracy = {
    "Actitis hypoleucos": 0.286,
    "Aethia psittacula": 0.250,
    "Aethia pusilla": 0.750,
    "Amazona oratrix": 0.600,
    "Anas aucklandica": 0.667,
    # ...
    "Turtur brehmeri": 1.000,
    "Turtur chalcospilos": 1.000,
    "Vanellus albiceps": 0.600,
    "Xanthocephalus xanthocephalus": 0.667,
    "Zenaida macroura": 0.000
}

frog_species_accuracy = {
    "Adenomus kandianus": 0.000,
    "Adenomus kelaartii": None,
    "Allobates brunneus": 0.000,
    "Allobates chalcopis": None,
    "Allobates femoralis": 0.667,
    # ...
    "Leptopelis yaldeni": 0.000,
    "Leptopelis zebra": None,
    "Limnomedusa macroglossa": None,
    "Mannophryne olmonae": 0.000,
    "Trichobatrachus robustus": None
}


# # ============================================================
# #  FIGURE 1 — DATASET-WIDE ACCURACY
# # ============================================================

# plt.figure(figsize=(6,4))
# datasets = list(overall_accuracy.keys())
# values = list(overall_accuracy.values())

# plt.bar(datasets, values, color=["#4C72B0", "#55A868", "#C44E52"])
# plt.ylim(0,1)
# plt.ylabel("Accuracy")
# plt.title("Dataset-wide Accuracy")

# plt.savefig("results/figure1_overall_accuracy.png", dpi=300, bbox_inches="tight")
# plt.close()

# # ============================================================
# #  FIGURE 2 — TRAIT ACCURACIES (3 PANELS)
# # ============================================================

# def plot_trait_accuracy(trait_dict, title, filename):
#     traits = list(trait_dict.keys())
#     values = list(trait_dict.values())

#     plt.figure(figsize=(10,5))
#     plt.bar(traits, values, color="#4C72B0")
#     plt.xticks(rotation=75, ha="right")
#     plt.ylim(0,1)
#     plt.ylabel("Accuracy")
#     plt.title(title)
#     plt.tight_layout()
#     plt.savefig(filename, dpi=300)
#     plt.close()

# plot_trait_accuracy(hans_trait_accuracy, "Hans Trait Accuracy", "results/figure2_hans_trait_accuracy.png")
# plot_trait_accuracy(bird_trait_accuracy, "Bird Trait Accuracy", "results/figure2_bird_trait_accuracy.png")
# plot_trait_accuracy(frog_trait_accuracy, "Frog Trait Accuracy", "results/figure2_frog_trait_accuracy.png")

# # ============================================================
# #  FIGURE 3 — SPECIES ACCURACIES (3 PANELS, SORTED)
# # ============================================================

# def plot_species_accuracy(species_dict, title, filename):
#     # Convert None → 0 at plotting time (safety guarantee)
#     clean_dict = {k: (0 if v is None else v) for k, v in species_dict.items()}

#     # Sort by accuracy
#     species_sorted = sorted(clean_dict.items(), key=lambda x: x[1])

#     names = [x[0] for x in species_sorted]
#     values = [x[1] for x in species_sorted]

#     plt.figure(figsize=(10,6))
#     plt.bar(names, values, color="#55A868")
#     plt.xticks(rotation=75, ha="right")
#     plt.ylim(0,1)
#     plt.ylabel("Accuracy")
#     plt.title(title)
#     plt.tight_layout()
#     plt.savefig(filename, dpi=300)
#     plt.close()

# plot_species_accuracy(hans_species_accuracy, "Hans Species Accuracy", "results/figure3_hans_species_accuracy.png")
# plot_species_accuracy(bird_species_accuracy, "Bird Species Accuracy", "results/figure3_bird_species_accuracy.png")
# plot_species_accuracy(frog_species_accuracy, "Frog Species Accuracy", "results/figure3_frog_species_accuracy.png")

# # ============================================================
# #  FIGURE 4 — COMPARISON OF ALL SUMMARY ACCURACIES
# # ============================================================

# datasets = ["Mixed Vertebrate", "Bird", "Frog"]

# dataset_values = [overall_accuracy[d] for d in datasets]
# species_values = [average_species_accuracy[d] for d in datasets]
# trait_values = [average_trait_accuracy[d] for d in datasets]

# x = np.arange(len(datasets))
# width = 0.25

# plt.figure(figsize=(8,6))

# plt.bar(x - width, dataset_values, width, label="Dataset-wide", color="#4C72B0")
# plt.bar(x, species_values, width, label="Avg Species-wide", color="#55A868")
# plt.bar(x + width, trait_values, width, label="Avg Trait-wide", color="#C44E52")

# plt.xticks(x, datasets)
# plt.ylim(0, 1)
# plt.ylabel("Accuracy")
# plt.title("Comparison of Summary Accuracy Metrics Across Datasets")
# plt.legend()

# plt.tight_layout()
# plt.savefig("results/figure4_summary_accuracy.png", dpi=300)
# plt.close()

# ============================================================
#  FIGURE 5 — OG MODEL VS CONSENSUS MODEL ACCURACY
# ============================================================

# first_hit_accuracy = 0.484
# consensus_accuracy = 0.632

# models = ["First-Hit Model", "Consensus Model"]
# values = [first_hit_accuracy, consensus_accuracy]

# plt.figure(figsize=(6,5))
# plt.bar(models, values, color=["#C44E52", "#4C72B0"])
# plt.ylim(0,0.8)
# plt.ylabel("Accuracy")
# plt.title("Comparison of Model Accuracy: First-Hit vs Consensus")

# for i, v in enumerate(values):
#     plt.text(i, v + 0.02, f"{v:.3f}", ha='center', fontsize=10)

# plt.tight_layout()
# plt.savefig("results/figure5_model_comparison.png", dpi=300)
# plt.close()

# ============================================================
#  FIGURE 6 — MISSINGNESS HEATMAPS
# ============================================================
# hans_df = pd.read_csv("results/hans_output_results.csv")
# bird_df = pd.read_csv("results/bird_output_results.csv")
# frog_df = pd.read_csv("results/frog_output_results.csv")

# datasets = {
#     "Mixed Vertebrate": (hans_df, "results/figure6_missingness_hans.png"),
#     "Bird": (bird_df, "results/figure6_missingness_bird.png"),
#     "Frog": (frog_df, "results/figure6_missingness_frog.png")
# }

# def plot_trait_foundness(df, dataset_name, title, filename):
#     trait_cols = df.columns[1:]
#     found_percentages = {}

#     for trait in trait_cols:
#         col = df[trait]

#         missing_mask = col.isna() | (col.astype(str).str.strip() == "")
#         missing_percent = missing_mask.mean()

#         found_percent = 1 - missing_percent
#         found_percentages[trait] = found_percent

#     traits_sorted = sorted(found_percentages, key=lambda x: found_percentages[x], reverse=True)
#     values_sorted = [found_percentages[t] for t in traits_sorted]

#     plt.figure(figsize=(10, 6))
#     plt.bar(traits_sorted, values_sorted, color="#55A868")  # green = positive
#     plt.xticks(rotation=75, ha="right")
#     plt.ylim(0, 1)
#     plt.ylabel("Proportion Found")
#     plt.title(title)

#     plt.tight_layout()
#     plt.savefig(filename, dpi=300)
#     plt.close()

# for dataset_name, (df, filename) in datasets.items():
#     plot_trait_foundness(
#         df,
#         dataset_name,
#         f"Trait Extraction Completeness — {dataset_name} Dataset",
#         filename
#     )
