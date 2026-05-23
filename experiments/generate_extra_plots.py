"""
generate_extra_plots.py — Plot tambahan untuk memperkaya paper Sinta 4.

Menghasilkan:
  1. grouped_bar_latency_all.png  — Grouped bar latency semua skenario
  2. success_rate_heatmap.png     — Heatmap SR setiap kombinasi skenario-partner
  3. overhead_ratio.png           — Rasio overhead dynamic/baseline per skenario
  4. error_detection_rate.png     — Error detection: baseline vs dynamic (Partner D)
  5. latency_cdf.png              — CDF distribusi latency S3 5 partner
  6. latency_trend.png            — Tren latency rata-rata vs jumlah payload
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "..", "results")
PLOT_DIR = os.path.join(RESULTS, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

# ------------------------------------------------------------------ #
# Load summary data
# ------------------------------------------------------------------ #
df = pd.read_csv(os.path.join(RESULTS, "experiment_summary.csv"))

PARTNER_LABELS = {
    "partner_a": "Partner A",
    "partner_b": "Partner B",
    "partner_c": "Partner C",
    "partner_d": "Partner D",
    "partner_e": "Partner E",
}

COLORS = {
    "baseline": "#4C72B0",
    "dynamic":  "#DD8452",
}

# ------------------------------------------------------------------ #
# 1. Grouped Bar — Latency semua skenario per partner (mean)
# ------------------------------------------------------------------ #
print("Generating 1: grouped_bar_latency_all.png ...")
scenarios = ["S1", "S2", "S3", "S4"]
partners_s3 = ["partner_a", "partner_b", "partner_c", "partner_d", "partner_e"]
partners_s1 = ["partner_a", "partner_b", "partner_c"]

fig, axes = plt.subplots(2, 2, figsize=(14, 9))
axes = axes.flatten()

for ax, sc in zip(axes, scenarios):
    sdf = df[df["scenario"] == sc].copy()
    sdf["partner_label"] = sdf["partner"].map(PARTNER_LABELS)
    x = np.arange(len(sdf))
    width = 0.35
    ax.bar(x - width/2, sdf["baseline_avg_latency_ms"] * 1000,
           width, label="Baseline", color=COLORS["baseline"], alpha=0.85)
    ax.bar(x + width/2, sdf["dynamic_avg_latency_ms"] * 1000,
           width, label="Dynamic", color=COLORS["dynamic"], alpha=0.85)
    ax.set_title(f"Skenario {sc}", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(sdf["partner_label"], fontsize=9)
    ax.set_ylabel("Latency Rata-rata (µs)", fontsize=9)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.4)

fig.suptitle("Perbandingan Latency Rata-rata per Skenario dan Partner\n"
             "(satuan: mikro-detik/µs = ms × 1000)", fontsize=11, y=1.01)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "grouped_bar_latency_all.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

# ------------------------------------------------------------------ #
# 2. Heatmap — Success Rate
# ------------------------------------------------------------------ #
print("Generating 2: success_rate_heatmap.png ...")
pivot_baseline = df.pivot_table(index="scenario", columns="partner",
                                 values="baseline_success_rate_pct")
pivot_dynamic  = df.pivot_table(index="scenario", columns="partner",
                                 values="dynamic_success_rate_pct")

# reorder cols
col_order = ["partner_a", "partner_b", "partner_c", "partner_d", "partner_e"]
pivot_baseline = pivot_baseline.reindex(columns=[c for c in col_order if c in pivot_baseline.columns])
pivot_dynamic  = pivot_dynamic.reindex(columns=[c for c in col_order if c in pivot_dynamic.columns])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))

def draw_heatmap(ax, data, title, cmap="YlGn"):
    im = ax.imshow(data.values, cmap=cmap, vmin=88, vmax=100, aspect="auto")
    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels([PARTNER_LABELS.get(c, c) for c in data.columns], fontsize=9)
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(data.index, fontsize=9)
    for i in range(len(data.index)):
        for j in range(len(data.columns)):
            val = data.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                        fontsize=10, fontweight="bold",
                        color="white" if val < 93 else "black")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=8)

draw_heatmap(ax1, pivot_baseline, "Baseline Hard-coded SR (%)", cmap="Blues")
draw_heatmap(ax2, pivot_dynamic,  "Dynamic Mapper SR (%)",      cmap="Greens")

fig.suptitle("Heatmap Success Rate — Baseline vs Dynamic Mapper\n"
             "(NaN = partner tidak digunakan pada skenario tersebut)", fontsize=10, y=1.04)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "success_rate_heatmap.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

# ------------------------------------------------------------------ #
# 3. Overhead Ratio (dynamic / baseline)
# ------------------------------------------------------------------ #
print("Generating 3: overhead_ratio.png ...")
df_ratio = df.copy()
df_ratio["ratio"] = df_ratio["dynamic_avg_latency_ms"] / df_ratio["baseline_avg_latency_ms"]
df_ratio["label"] = df_ratio["scenario"] + "\n" + df_ratio["partner"].map(PARTNER_LABELS)

fig, ax = plt.subplots(figsize=(14, 5))
colors_bar = ["#e74c3c" if r > 4 else "#e67e22" if r > 2 else "#2ecc71"
               for r in df_ratio["ratio"]]
x = np.arange(len(df_ratio))
bars = ax.bar(x, df_ratio["ratio"], color=colors_bar, alpha=0.85, edgecolor="white")
ax.axhline(1.0, color="black", linewidth=1, linestyle="--", label="Rasio = 1 (setara)")
ax.axhline(4.0, color="red",   linewidth=0.8, linestyle=":", alpha=0.6, label="Ambang 4×")
ax.set_xticks(x)
ax.set_xticklabels(df_ratio["label"], fontsize=7.5, rotation=30, ha="right")
ax.set_ylabel("Rasio Latency (Dynamic / Baseline)", fontsize=10)
ax.set_title("Rasio Overhead Latency Dynamic Mapper terhadap Baseline\n"
             "(nilai 1.0 = setara; <4× = dapat diterima)", fontsize=10, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.4)
for bar, val in zip(bars, df_ratio["ratio"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f"{val:.1f}×", ha="center", va="bottom", fontsize=7.5)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "overhead_ratio.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

# ------------------------------------------------------------------ #
# 4. Error Detection Rate — Baseline vs Dynamic (Partner D)
# ------------------------------------------------------------------ #
print("Generating 4: error_detection_rate.png ...")
partner_d = df[df["partner"] == "partner_d"].copy()

fig, ax = plt.subplots(figsize=(7, 4.5))
scenarios_d = partner_d["scenario"].tolist()
x = np.arange(len(scenarios_d))
w = 0.35

ax.bar(x - w/2, partner_d["baseline_success_rate_pct"], w,
       label="Baseline SR (%)", color=COLORS["baseline"], alpha=0.85)
ax.bar(x + w/2, partner_d["dynamic_success_rate_pct"], w,
       label="Dynamic SR (%)", color=COLORS["dynamic"], alpha=0.85)

# annotate selisih
for i, (b, d_val) in enumerate(zip(partner_d["baseline_success_rate_pct"],
                                    partner_d["dynamic_success_rate_pct"])):
    diff = d_val - b
    y_pos = min(b, d_val) - 1.5
    ax.annotate(f"Δ{diff:.1f}%", xy=(x[i], y_pos),
                ha="center", fontsize=9, color="#c0392b", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(scenarios_d, fontsize=10)
ax.set_ylim(85, 100)
ax.set_ylabel("Success Rate (%)", fontsize=10)
ax.set_xlabel("Skenario", fontsize=10)
ax.set_title("Perbedaan Success Rate pada Partner D\n"
             "(Dynamic mapper mendeteksi error format lebih ketat)", fontsize=10, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "error_detection_rate.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

# ------------------------------------------------------------------ #
# 5. CDF latency distribusi S3 per partner
# ------------------------------------------------------------------ #
print("Generating 5: latency_cdf.png ...")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, approach, label_str in [
        (axes[0], "baseline", "Baseline Hard-coded"),
        (axes[1], "dynamic",  "Dynamic Mapper")]:
    for partner in ["partner_a", "partner_b", "partner_c", "partner_d", "partner_e"]:
        raw_path = os.path.join(RESULTS, f"S3_{partner}_raw.json")
        if not os.path.exists(raw_path):
            continue
        with open(raw_path) as f:
            raw = json.load(f)
        # raw is a dict with keys: scenario, partner, baseline, dynamic, baseline_raw, dynamic_raw
        key = "baseline_raw" if approach == "baseline" else "dynamic_raw"
        raw_list = raw.get(key, [])
        latencies = [r["latency_ms"] for r in raw_list if r.get("latency_ms") is not None]
        if not latencies:
            continue
        lat = np.sort(latencies)
        cdf = np.arange(1, len(lat)+1) / len(lat)
        ax.plot(lat * 1000, cdf, label=PARTNER_LABELS[partner], linewidth=1.5)
    ax.set_xlabel("Latency (µs)", fontsize=9)
    ax.set_ylabel("CDF", fontsize=9)
    ax.set_title(label_str, fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_xlim(left=0)

fig.suptitle("CDF Distribusi Latency Skenario S3 (500 payload, 5 partner)",
             fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "latency_cdf.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

# ------------------------------------------------------------------ #
# 6. Latency trend vs payload count (Partner A, semua skenario)
# ------------------------------------------------------------------ #
print("Generating 6: latency_trend.png ...")
trend_data = {
    "S1": 100, "S2": 300, "S3": 500, "S4": 500
}

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, approach, color in [
        (axes[0], "baseline_avg_latency_ms", COLORS["baseline"]),
        (axes[1], "dynamic_avg_latency_ms",  COLORS["dynamic"])]:
    for partner in ["partner_a", "partner_b", "partner_c"]:
        sub = []
        for sc in ["S1", "S2", "S3", "S4"]:
            row = df[(df["scenario"] == sc) & (df["partner"] == partner)]
            if len(row) > 0:
                sub.append((trend_data[sc], row[approach].values[0] * 1000))
        if sub:
            xs, ys = zip(*sub)
            axes[0 if approach.startswith("baseline") else 1].plot(
                xs, ys, marker="o", label=PARTNER_LABELS[partner], linewidth=1.8)

for ax, title in zip(axes, ["Baseline Hard-coded", "Dynamic Mapper"]):
    ax.set_xlabel("Jumlah Payload", fontsize=9)
    ax.set_ylabel("Latency Rata-rata (µs)", fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_xticks([100, 300, 500])

fig.suptitle("Tren Latency terhadap Peningkatan Volume Payload (Partner A–C)",
             fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "latency_trend.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  DONE")

print("\n✓ Semua plot tambahan tersimpan di:", PLOT_DIR)
