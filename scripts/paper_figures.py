import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from scipy.stats import linregress

# ============================================================
#  ALL DATA
# ============================================================

# MIXED VERTS 
mixed_verts_traits = ["Average life expectancy", "Mating System", "Social Dominance Hierarchy", "Territoriality (Males)", "Age at Maturity", "Group Size Outside of Reproduction", "Migratory behavior", "Habitat Complexity", "Territoriality (Females)", "Group Size During Reproduction", "Group Property", "Activity Pattern", "Number of Offspring Per Reproductive Bout", "Number of Reproductive Bouts Per Year"]
mixed_verts_completeness = [0.791667, 0.583333, 0.583333, 0.583333, 0.583333, 0.500000, 0.500000, 0.500000, 0.500000, 0.50, 0.500000, 0.416667, 0.375000, 0.166667]
mixed_verts_accuracy = [0.789474, 0.714286, 0.714286, 0.785714, 0.714286, 0.750000, 0.750000, 0.750000, 0.750000, 0.68, 0.666667, 0.700000, 0.777778, 0.750000]
mixed_verts_manual_accuracy = [0, .556, .778, .556, 0, .667, .75, 1.0, .429, .714, .714, 1.0, 0, 0]
mixed_verts_overall_completeness = 0.506
mixed_verts_overall_accuracy = 0.741
mixed_verts_overall_manual_accuracy = 0.716

# BIRDS
birds_traits = ["Habitat Type", "Migratory", "Colonial", "Cooperative breeding", "Body mass (g)", "Sociality outside of breeding", "Communal foraging", "Brain mass (g)", "Maximum colony size"]
birds_completeness = [0.949749, 0.914573, 0.678392, 0.608040, 0.597990, 0.512563, 0.457286, 0.381910, 0.306533]
birds_accuracy = [0.624339, 0.634921, 0.546763, 0.496644, 0.672269, 0.573913, 0.578431, 0.565789, 1.000000]
birds_manual_accuracy = [.94, .806, .40, .48, .814, .690, .50, 0, .50]
birds_overall_completeness = 0.601
birds_overall_accuracy = 0.594
birds_overall_manual_accuracy = 0.57

# FROGS
frogs_traits = ["Average Altitude", "Egg Style", "Average Time of Day", "Average Temperature", "Egg Clutch", "Average Rainfall", "Snout-Vent Length Male", "Snout-Vent Length Female", "Average Age at Maturity", "Average Hatch Time", "Average Development Age", "Average Snout-Vent Length Adult"]
frogs_completeness = [0.7, 0.400, 0.38, 0.300, 0.3, 0.245, 0.235, 0.235, 0.23, 0.22, 0.21, 0.180]
case_study_completeness = [0.54000, 0.20000, 0.55000, 0.48500, 0.44500, 0.77500, 0.46500, 0.30500]
frogs_accuracy = [0.35, 0.287500, 0.31, 0.254545, 0.29, 0.239130, 0.368421, 0.416667, 0.24, 0.23, 0.26, 0.125000]
frogs_manual_accuracy = [.50, .926, .875, .625, .833, .833, 1.0, 1.0, .50, 1.0, 0, 1.0]
frogs_case_study_manual_accuracy = [.566265060240964, .983606557377049, 0, .722222222222222, .964285714285714, .90, 1.0, .983333333333333, 0, 0, 0, 1.0]
frogs_overall_completeness = 0.266
frogs_overall_accuracy = 0.287
frogs_overall_manual_accuracy = 0.83963

bar_height = 0.35

# ============================================================
#  FIRST HIT VS CONSENSUS MODEL ACCURACY
# ============================================================

first_hit_accuracy = 0.515
consensus_accuracy = 0.741

models = ["First-Hit Model", "Consensus Model"]
values = [first_hit_accuracy, consensus_accuracy]

n = 23
ses = [np.sqrt(v * (1 - v) / n) for v in values]

# Convert to percentages
values_pct = [v * 100 for v in values]
ses_pct = [se * 100 for se in ses]

x_pos = [0, 0.7]

plt.figure(figsize=(3.5,4))
plt.bar(
    x_pos,
    values_pct,
    width=0.3,
    yerr=ses_pct,
    capsize=6,
    color=["#F589C4", "#DB4497"]
)

plt.xticks(x_pos, models)
plt.xlim(-0.4, 1.1)
plt.ylim(0, 100)
plt.ylabel("Exact Text Match (%)")

for i, v in zip(x_pos, values_pct):
    plt.text(i, v + ses_pct[x_pos.index(i)] + 2, f"{v:.1f}%", ha='center', fontsize=10)

plt.tight_layout()
plt.savefig("figures/figure5_model_comparison.png", dpi=300)
plt.close()

# ============================================================
#  MAIN ACCURACY FIGURE
# ============================================================

import textwrap

def wrap_labels(labels, width=25):
    """Wrap long labels to multiple lines"""
    return ['\n'.join(textwrap.wrap(label, width)) for label in labels]

fontsize_f9 = 45  # controls ALL non-tick/trait text in figure 9 (titles, labels, scatter text, suptitle)
fontsize_ticks = 19
fontsize_legend = 25 #UNNEEDED

f5_completeness = "#72B173"
f5_automated_accuracy = "#C490CF"
f5_manual_accuracy = "#90529C"

def automated_manual_accuracy(ax, traits, completeness, accuracy, manual_accuracy, overall_stats, title, x_min=0):
    overall_comp, overall_acc, overall_manual = overall_stats

    completeness_pct = [c * 100 for c in completeness]
    accuracy_pct = [a * 100 for a in accuracy]
    manual_accuracy_pct = [m * 100 for m in manual_accuracy]

    spacing = 1.3
    y_pos = np.arange(len(traits)) * spacing

    ax.barh(y_pos - bar_height_manual - gap, completeness_pct, bar_height_manual,
            color=f5_completeness, label="Completeness (% Species)")
    ax.barh(y_pos, accuracy_pct, bar_height_manual,
            color=f5_automated_accuracy, label="Exact Text Match Accuracy (% out of Complete Entries)")
    ax.barh(y_pos + bar_height_manual + gap, manual_accuracy_pct, bar_height_manual,
            color=f5_manual_accuracy, label="Domain Expert Evaluated Accuracy (% out of Complete Entries)")

    ax.set_yticks(y_pos)
    wrapped_labels = wrap_labels(traits, width=22)

    ax.set_yticklabels(wrapped_labels)

    n = len(traits)
    ax.set_xlim(x_min, 100)
    ax.set_ylim(-spacing * 0.5, (n - 1) * spacing + spacing * 0.5)

    ax.xaxis.tick_bottom()
    ax.xaxis.set_label_position('bottom')
    ax.set_xlabel("Percentage (%)", fontsize=fontsize_f9, labelpad=10)
    ax.set_title(title, fontsize=fontsize_f9, pad=20)
    ax.tick_params(axis='both', which='major', labelsize=fontsize_ticks)
    ax.invert_yaxis()

n_mixed = len(mixed_verts_traits) 
n_birds = len(birds_traits) 
n_frogs = len(frogs_traits) 
n_max = max(n_mixed, n_birds, n_frogs)

spacing = 1.3
bar_height_manual = 0.25
bar_unit = 0.45
gap = 0.10

# ── All layout values in absolute inches ──────────────────────────────────────
scatter_h_in    = 5.0   # height of scatter axes
bottom_margin   = 2   # inches below scatter (for x-axis label)
mid_gap         = 2.5   # inches between scatter top and bars bottom
top_height      = n_max * bar_unit * spacing   # height of tallest bar panel
top_pad         = 4   # inches above bar charts for the suptitle

scatter_bot_in  = bottom_margin
bars_bot_in     = scatter_bot_in + scatter_h_in + mid_gap
fig_height      = bars_bot_in + top_height + top_pad
# ──────────────────────────────────────────────────────────────────────────────

fig2 = plt.figure(figsize=(27, fig_height))

def make_ax(fig, left, width, n_traits):
    panel_h_in = n_traits * bar_unit * spacing
    bot_in = bars_bot_in + (top_height - panel_h_in)
    return fig.add_axes([left, bot_in / fig_height, width, panel_h_in / fig_height])

ax_m1 = make_ax(fig2, 0.17, 0.15, n_mixed)
ax_m2 = make_ax(fig2, 0.47, 0.15, n_birds)
ax_m3 = make_ax(fig2, 0.77, 0.15, n_frogs)
ax_scatter = fig2.add_axes([0.1, scatter_bot_in / fig_height, 0.85, scatter_h_in / fig_height])

automated_manual_accuracy(ax_m1, mixed_verts_traits, mixed_verts_completeness, mixed_verts_accuracy, mixed_verts_manual_accuracy, 
                          (mixed_verts_overall_completeness, mixed_verts_overall_accuracy, mixed_verts_overall_manual_accuracy), 
                          "B. Mixed Vertebrates\n(23 Species)", x_min=0)
ax_m1.set_facecolor('none')

automated_manual_accuracy(ax_m2, birds_traits, birds_completeness, birds_accuracy, birds_manual_accuracy, 
                          (birds_overall_completeness, birds_overall_accuracy, birds_overall_manual_accuracy), 
                          "C. Birds\n(146 Species)", x_min=0)
ax_m2.set_facecolor('none')

automated_manual_accuracy(ax_m3, frogs_traits, frogs_completeness, frogs_accuracy, frogs_manual_accuracy, 
                          (frogs_overall_completeness, frogs_overall_accuracy, frogs_overall_manual_accuracy), 
                          "D. Frogs\n(200 Species)", x_min=0)
ax_m3.set_facecolor('none')

color_mixed_verts = "#E3993D"
color_birds = "#855050"
color_frogs = "#1E5A8E"
mixed_scatter_comp = [c * 100 for c in mixed_verts_completeness]
mixed_scatter_manual = [m * 100 for m in mixed_verts_manual_accuracy]
birds_scatter_comp = [c * 100 for c in birds_completeness]
birds_scatter_manual = [m * 100 for m in birds_manual_accuracy]
frogs_scatter_comp = [c * 100 for c in frogs_completeness]
frogs_scatter_manual = [m * 100 for m in frogs_manual_accuracy]

all_comp = mixed_scatter_comp + birds_scatter_comp + frogs_scatter_comp
all_manual = mixed_scatter_manual + birds_scatter_manual + frogs_scatter_manual
slope, intercept, r_value, p_value, std_err = linregress(all_comp, all_manual)

ax_scatter.set_title(f"E. Completeness does not Correlate with Accuracy", fontsize=fontsize_f9)

ax_scatter.scatter(mixed_scatter_comp, mixed_scatter_manual, 
                   color=color_mixed_verts, s=250, alpha=0.7, 
                   marker='o')
ax_scatter.scatter(birds_scatter_comp, birds_scatter_manual, 
                   color=color_birds, s=250, alpha=0.7, 
                   marker='o')
ax_scatter.scatter(frogs_scatter_comp, frogs_scatter_manual, 
                   color=color_frogs, s=250, alpha=0.7, 
                   marker='o')

line_x = np.array([20, 105])
line_y = slope * line_x + intercept
ax_scatter.plot(line_x, line_y, color='black', linestyle='--', linewidth=2)

ax_scatter.text(31, 83, 'Frogs',
                color=color_frogs, fontsize=fontsize_f9,
                fontweight='bold', va='center')

ax_scatter.text(51, 100, 'Mixed Vertebrates',
                color=color_mixed_verts, fontsize=fontsize_f9,
                fontweight='bold', va='center')

ax_scatter.text(92, 80, 'Birds',
                color=color_birds, fontsize=fontsize_f9,
                fontweight='bold', va='center')

ax_scatter.xaxis.tick_bottom()
ax_scatter.xaxis.set_label_position('bottom')
ax_scatter.set_xlabel('Completeness (%)', fontsize=fontsize_f9, labelpad=20)
ax_scatter.set_ylabel('Domain Expert-Evaluated\nAccuracy (%)', fontsize=fontsize_f9, labelpad=20)
ax_scatter.set_xlim(20, 105)
ax_scatter.set_ylim(-5, 105)
ax_scatter.grid(True, alpha=0.3)
ax_scatter.tick_params(axis='both', which='major', labelsize=fontsize_ticks)
ax_scatter.text(.995, 0.25, f"Linear Fit ($R^2={r_value**2:.2f}$, $p={p_value:.3f}$)",
                transform=ax_scatter.transAxes,
                ha='right', va='bottom', fontsize=fontsize_f9,
                color='black')

fig2.suptitle("trAIt's Performance Varies Considerably and Depends on\nOpen Access Data Availability", fontsize=fontsize_f9, y=0.99)

handles, labels = ax_m1.get_legend_handles_labels()

plt.savefig("figures/figure9_trait_completeness_combined_manual.png", dpi=300)
plt.close()

fig_legend = plt.figure(figsize=(8, 3))
ax_legend = fig_legend.add_subplot(111)
ax_legend.axis('off')

legend = ax_legend.legend(handles, labels, loc='center', 
                         fontsize=fontsize_legend, frameon=True, 
                         facecolor='white', framealpha=1, ncol=1)

plt.tight_layout()
plt.savefig("figures/figure9_legend.png", dpi=300, bbox_inches='tight')
plt.close()

#  PIE CHART FIGURE

pie_datasets = [
    ("Mixed Vertebrates\n(23 Species,\n14 Traits)", mixed_verts_overall_completeness, mixed_verts_overall_accuracy, mixed_verts_overall_manual_accuracy),
    ("Birds\n(146 Species,\n9 Traits)",             birds_overall_completeness,        birds_overall_accuracy,        birds_overall_manual_accuracy),
    ("Frogs\n(200 Species,\n12 Traits)",            frogs_overall_completeness,        frogs_overall_accuracy,        frogs_overall_manual_accuracy),
]

pie_metric_labels = ["Completeness (% Species)", "Exact Text Match Accuracy\n(% out of Complete Entries)", "Domain Expert Evaluated Accuracy\n(% out of Complete Entries)"]
pie_colors_ordered = [f5_completeness, f5_automated_accuracy, f5_manual_accuracy]

fontsize_pie9 = 60  # controls ALL text in the figure 9 pie chart

# ── All layout values in absolute inches ──────────────────────────────────────
pie_left_margin  = 4.0   # room for metric row labels on the left
pie_right_margin = 2   # right padding
pie_top_pad      = 3   # room above top row for suptitle
pie_col_header   = 3.5   # extra space above each top-row cell for dataset name
pie_bot_margin   = 0.4   # bottom padding
pie_cell_w       = 2.8   # width of each pie cell
pie_cell_h       = 2.8   # height of each pie cell
pie_col_gap      = 5   # horizontal gap between columns
pie_row_gap      = 1.5   # vertical gap between rows

pie_fig_w = 27
pie_fig_h = pie_bot_margin  + 3 * pie_cell_h + 2 * pie_row_gap + pie_col_header + pie_top_pad
# ──────────────────────────────────────────────────────────────────────────────

fig_pie = plt.figure(figsize=(pie_fig_w, pie_fig_h), facecolor='white')

def make_pie_ax(row, col):
    left_in = pie_left_margin + col * (pie_cell_w + pie_col_gap)
    bot_in  = pie_bot_margin  + (2 - row) * (pie_cell_h + pie_row_gap)
    ax = fig_pie.add_axes(
        [left_in / pie_fig_w, bot_in / pie_fig_h,
         pie_cell_w / pie_fig_w, pie_cell_h / pie_fig_h],
        facecolor='white'
    )
    ax.patch.set_facecolor('white')
    return ax

axes_pie = np.array([[make_pie_ax(row, col) for col in range(3)] for row in range(3)])

for col, (dataset_name, comp, acc, man_acc) in enumerate(pie_datasets):
    dataset_vals = [comp, acc, man_acc]
    for row, (metric_label, val, color) in enumerate(zip(pie_metric_labels, dataset_vals, pie_colors_ordered)):
        ax = axes_pie[row, col]
        remainder_color = 'white' if row == 0 else f5_completeness
        ax.pie(
            [val, 1 - val],
            colors=[color, remainder_color],
            startangle=90,
            counterclock=False,
            wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
        )
        outline_color = 'black' if row == 0 else remainder_color
        from matplotlib.patches import Circle as _Circle
        ax.add_patch(_Circle((0, 0), 1.0, fill=False, edgecolor=outline_color, linewidth=3.5,
                              transform=ax.transData, zorder=10))
        ax.set_title(f"{val*100:.1f}%", fontsize=fontsize_pie9, pad=4)
        if row == 0:
            ax.text(0.5, 1.35, dataset_name, ha='center', va='bottom',
                    fontsize=fontsize_pie9, transform=ax.transAxes)
    for row, (metric_label, color) in enumerate(zip(pie_metric_labels, pie_colors_ordered)):
        axes_pie[row, 0].text(-1.4, 0.5, metric_label, ha='right', va='center',
                               fontsize=fontsize_pie9, transform=axes_pie[row, 0].transAxes,
                               fontweight='bold', color=color)

fig_pie.suptitle("A. Average Performance Across Traits", fontsize=fontsize_pie9,
                 y=(pie_fig_h - pie_top_pad * 0.3) / pie_fig_h)
plt.savefig("figures/figure9_pies.png", dpi=300, bbox_inches='tight')
plt.close()


# ============================================================
#  CASE STUDY FIGURE
# ============================================================

fontsize_title = 20
fontsize_label = 20
fontsize_ticks = 17
fontsize_legend = 17

f6_completeness_1 = "#72B173"
f6_completeness_2 = "#2C792D"  
f6_manual_accuracy_1 = "#C490CF"
f6_manual_accuracy_2 = "#90529C" 

def manual_case_study_accuracy(ax, traits, completeness, manual_accuracy, case_study_completeness, case_study_manual_accuracy, title, x_min=0):
    completeness_pct = [c * 100 for c in completeness]
    manual_accuracy_pct = [m * 100 for m in manual_accuracy]
    case_study_completeness_pct = [cs * 100 for cs in case_study_completeness]
    case_study_manual_accuracy_pct = [cs * 100 for cs in case_study_manual_accuracy]

    y_pos = np.arange(len(traits)) * spacing_cs
    bar_height = 0.1
    gap = 0.05
    ax.barh(y_pos - 1.5 * bar_height - 1.5 * gap, completeness_pct, bar_height,
            color=f6_completeness_1, label="PubMed Completeness (% Species)")
    ax.barh(y_pos - 0.5 * bar_height - 0.5 * gap, case_study_completeness_pct, bar_height,
            color=f6_completeness_2, label="AmphibiaWeb Completeness (% Species)")

    ax.barh(y_pos + 0.5 * bar_height + 0.5 * gap, manual_accuracy_pct, bar_height,
            color=f6_manual_accuracy_1, label="PubMed Exact Text Match Accuracy (% out of Complete Entries)")
    ax.barh(y_pos + 1.5 * bar_height + 1.5 * gap, case_study_manual_accuracy_pct, bar_height,
            color=f6_manual_accuracy_2, label="AmphibiaWeb Exact Text Match Accuracy (% out of Complete Entries)")

    n = len(traits)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(traits)
    ax.set_ylim(-spacing_cs * 0.5, (n - 1) * spacing_cs + spacing_cs * 0.5)

    ax.set_xlim(x_min, 100)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_xlabel("Percentage (%)", fontsize=fontsize_f10, labelpad=8)
    ax.set_title(title, fontsize=fontsize_f10, pad=30)
    ax.tick_params(axis='both', which='major', labelsize=fontsize_ticks)
    ax.invert_yaxis()

exclude_traits = ["Average Age at Maturity", "Average Hatch Time", "Average Development Age", "Average Time of Day"]
filtered_indices = [i for i, trait in enumerate(frogs_traits) if trait not in exclude_traits]

filtered_traits = [frogs_traits[i] for i in filtered_indices]
filtered_completeness = [frogs_completeness[i] for i in filtered_indices]
filtered_manual_accuracy = [frogs_manual_accuracy[i] for i in filtered_indices]
filtered_case_study_manual_accuracy = [frogs_case_study_manual_accuracy[i] for i in filtered_indices]

spacing_cs = 0.7  # vertical spacing between trait groups in figure 10 bar chart
fontsize_f10 = 25  # controls ALL non-tick/trait text in figure 10 bar chart (title, xlabel, suptitle)

fig3 = plt.figure(figsize=(12, 12))
gs3 = fig3.add_gridspec(1, 1)

ax_cs = fig3.add_subplot(gs3[0, 0])
filtered_traits = ['Average Altitude', 'Egg Style', 'Average Temperature', 'Egg Clutch', 'Snout-Vent\nLength Male', 'Snout-Vent\nLength Female', 'Average Rainfall', 'Average Snout-Vent\nLength Adult']
filtered_completeness = [0.7, 0.400, 0.300, 0.3, 0.235, 0.235, 0.245, 0.180]
filtered_manual_accuracy = [.50, .926, .625, .833, 1.0, 1.0, .833, 1.0]
filtered_case_study_manual_accuracy = [.566265060240964, .983606557377049, .722222222222222, .964285714285714, 1.0, .983333333333333, .90, 1.0]
manual_case_study_accuracy(ax_cs, filtered_traits, filtered_completeness, filtered_manual_accuracy,
                           case_study_completeness, filtered_case_study_manual_accuracy,
                           "B. Frogs (200 Species, 12 Traits)", x_min=15)
ax_cs.set_facecolor('none')

fig3.suptitle("trAIt Extraction from Domain-Specific Data Sources\nOutperformed PubMed", fontsize=fontsize_f10)

plt.subplots_adjust(left=0.25)
plt.tight_layout(rect=[0, 0.02, 1, 0.90])

plt.savefig("figures/figure10_trait_completeness_combined_case_study.png", dpi=300)
plt.close()


# ============================================================
#  PIE CHART FIGURE FOR FIGURE 10
# ============================================================

pubmed_completeness = 0.266
pubmed_manual_accuracy = 0.83963
amphibiaweb_completeness = 0.47063
amphiabiaweb_manual_accuracy = 0.88996

f10_pie_data = [
    ("PubMed",           pubmed_completeness,            pubmed_manual_accuracy),
    ("AmphibiaWeb",      amphibiaweb_completeness,       amphiabiaweb_manual_accuracy),
]

f10_pie_colors = [
    [f6_completeness_1,    f6_completeness_2   ],
    [f6_manual_accuracy_1, f6_manual_accuracy_2],
]

fontsize_pie10 = 40  # controls ALL text in the figure 10 pie chart

# ── All layout values in absolute inches ──────────────────────────────────────
f10_left_margin  = 1.0   # no row labels — just edge padding
f10_right_margin = 1.0   # right padding
f10_top_pad      = 2.0   # room above top row for suptitle
f10_col_header   = 3.5   # extra headroom above top-row cells for 3-line column headers
f10_bot_margin   = 0.4   # bottom padding
f10_cell_w       = 3.0   # width of each pie cell
f10_cell_h       = 3.0   # height of each pie cell
f10_col_gap      = 9.0   # horizontal gap between columns
f10_row_gap      = 0.5   # vertical gap between rows

f10_fig_w = f10_left_margin + 2 * f10_cell_w + 1 * f10_col_gap + f10_right_margin
f10_fig_h = f10_bot_margin  + 2 * f10_cell_h + 1 * f10_row_gap + f10_col_header + f10_top_pad
# ──────────────────────────────────────────────────────────────────────────────

fig_pie10 = plt.figure(figsize=(f10_fig_w, f10_fig_h), facecolor='white')

def make_pie10_ax(row, col):
    left_in = f10_left_margin + col * (f10_cell_w + f10_col_gap)
    bot_in  = f10_bot_margin  + (1 - row) * (f10_cell_h + f10_row_gap)
    ax = fig_pie10.add_axes(
        [left_in / f10_fig_w, bot_in / f10_fig_h,
         f10_cell_w / f10_fig_w, f10_cell_h / f10_fig_h],
        facecolor='white'
    )
    ax.patch.set_facecolor('white')
    return ax

axes_pie10 = np.array([[make_pie10_ax(row, col) for col in range(2)] for row in range(2)])

for col, (source_name, comp, acc) in enumerate(f10_pie_data):
    source_vals = [comp, acc]
    for row, val in enumerate(source_vals):
        color = f10_pie_colors[row][col]
        ax = axes_pie10[row, col]
        remainder_color = 'white' if row == 0 else f10_pie_colors[0][col]
        ax.pie(
            [val, 1 - val],
            colors=[color, remainder_color],
            startangle=90,
            counterclock=False,
            wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'}
        )
        outline_color = 'black' if row == 0 else remainder_color
        ax.add_patch(_Circle((0, 0), 1.0, fill=False, edgecolor=outline_color, linewidth=3.5,
                              transform=ax.transData, zorder=10))
        ax.set_title(f"{val*100:.1f}%", fontsize=fontsize_pie10, pad=4)

from matplotlib.offsetbox import TextArea, HPacker, VPacker, AnnotationBbox

def _ta(text, color, fs=fontsize_pie10, bold=False):
    return TextArea(text, textprops=dict(color=color, fontsize=fs,
                                        fontweight='bold' if bold else 'normal',
                                        ha='center'))

col_source_names = ["PubMed", "AmphibiaWeb"]
col_comp_colors  = [f6_completeness_1, f6_completeness_2]
col_acc_colors   = [f6_manual_accuracy_1, f6_manual_accuracy_2]

for col, (src_name, comp_color, acc_color) in enumerate(zip(col_source_names, col_comp_colors, col_acc_colors)):
    ax_top = axes_pie10[0, col]

    line_src = HPacker(children=[
        _ta(src_name, 'black', bold=True),
    ], pad=0, sep=0, align='baseline')
    line_comp = HPacker(children=[
        _ta("Completeness (% Species)", comp_color, bold=True),
    ], pad=0, sep=0, align='baseline')
    line_acc = HPacker(children=[
        _ta("Domain Expert Evaluated Accuracy \n(% Out of Complete Entries)", acc_color, bold=True),
    ], pad=0, sep=0, align='baseline')

    col_pack = VPacker(children=[line_src, line_comp, line_acc], pad=0, sep=6, align='center')
    col_ab = AnnotationBbox(col_pack, (0.5, 1.3), xycoords=ax_top.transAxes,
                            box_alignment=(0.5, 0.0), frameon=False, clip_on=False)
    ax_top.add_artist(col_ab)

pie10_center_x = (f10_left_margin + f10_cell_w + f10_col_gap / 2) / f10_fig_w
fig_pie10.suptitle("A. Average Performance Across Traits",
                   fontsize=fontsize_pie10,
                   x=pie10_center_x, ha='center',
                   y=(f10_fig_h - f10_top_pad * 0.3) / f10_fig_h)
plt.savefig("figures/figure10_pies.png", dpi=300, bbox_inches='tight')
plt.close()