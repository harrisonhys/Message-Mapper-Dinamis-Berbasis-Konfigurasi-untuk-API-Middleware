"""
experiments/statistical_analysis.py — Analisis Statistik Hasil Eksperimen
Sesuai panduan penelitian Sinta 4:
  - Uji normalitas Shapiro-Wilk
  - Paired t-test (jika normal) / Wilcoxon signed-rank (jika tidak normal)
  - Effect size (Cohen's d)
  - Summary statistics (mean, std, min, max)
  - Visualisasi boxplot dan bar chart

Jalankan setelah run_experiments.py selesai.
"""
import sys
import os
import json
import csv
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

RESULTS_DIR = Path(__file__).parent.parent / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ #
# Utility
# ------------------------------------------------------------------ #
def cohens_d(x: list, y: list) -> float:
    """Effect size Cohen's d untuk paired samples."""
    diff = np.array(x) - np.array(y)
    return float(np.mean(diff) / np.std(diff, ddof=1)) if np.std(diff, ddof=1) != 0 else 0.0


def interpret_effect_size(d: float) -> str:
    d = abs(d)
    if d < 0.2:
        return "trivial"
    if d < 0.5:
        return "small"
    if d < 0.8:
        return "medium"
    return "large"


def load_raw_latencies(scenario: str, partner: str) -> tuple[list, list]:
    """Load raw latency lists dari file JSON per skenario."""
    path = RESULTS_DIR / f"{scenario}_{partner}_raw.json"
    if not path.exists():
        return [], []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    baseline = [r["latency_ms"] for r in data.get("baseline_raw", [])]
    dynamic = [r["latency_ms"] for r in data.get("dynamic_raw", [])]
    return baseline, dynamic


def run_statistical_tests(baseline: list, dynamic: list, label: str) -> dict:
    b = np.array(baseline)
    d = np.array(dynamic)

    # Shapiro-Wilk normalitas
    _, p_norm_b = stats.shapiro(b[:min(len(b), 5000)])
    _, p_norm_d = stats.shapiro(d[:min(len(d), 5000)])
    is_normal = p_norm_b > 0.05 and p_norm_d > 0.05

    if is_normal:
        stat, p_value = stats.ttest_rel(b, d)
        test_name = "Paired t-test"
    else:
        stat, p_value = stats.wilcoxon(b, d, alternative="two-sided")
        test_name = "Wilcoxon signed-rank"

    d_effect = cohens_d(list(b), list(d))

    return {
        "label": label,
        "test": test_name,
        "stat": round(float(stat), 4),
        "p_value": round(float(p_value), 6),
        "significant": bool(p_value < 0.05),
        "baseline_normal": bool(p_norm_b > 0.05),
        "dynamic_normal": bool(p_norm_d > 0.05),
        "baseline_mean": round(float(np.mean(b)), 4),
        "baseline_std": round(float(np.std(b, ddof=1)), 4),
        "baseline_min": round(float(np.min(b)), 4),
        "baseline_max": round(float(np.max(b)), 4),
        "dynamic_mean": round(float(np.mean(d)), 4),
        "dynamic_std": round(float(np.std(d, ddof=1)), 4),
        "dynamic_min": round(float(np.min(d)), 4),
        "dynamic_max": round(float(np.max(d)), 4),
        "cohens_d": round(d_effect, 4),
        "effect_size": interpret_effect_size(d_effect),
    }


def plot_boxplot(baseline: list, dynamic: list, title: str, filename: str):
    fig, ax = plt.subplots(figsize=(8, 5))
    data = pd.DataFrame({
        "Hard-coded (Baseline)": baseline,
        "Dynamic Mapper": dynamic,
    })
    data.plot(kind="box", ax=ax, patch_artist=True,
              boxprops=dict(facecolor="#AED6F1"),
              medianprops=dict(color="red", linewidth=2))
    ax.set_title(title, fontsize=12, pad=12)
    ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("Pendekatan Mapping")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=150)
    plt.close()


def plot_success_rate_bar(df: pd.DataFrame, filename: str):
    """Bar chart perbandingan success rate per partner per skenario."""
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df))
    width = 0.35
    ax.bar(x - width / 2, df["baseline_success_rate_pct"], width, label="Hard-coded (Baseline)", color="#AED6F1")
    ax.bar(x + width / 2, df["dynamic_success_rate_pct"], width, label="Dynamic Mapper", color="#A9DFBF")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.scenario}\n{r.partner}" for r in df.itertuples()], rotation=30, ha="right")
    ax.set_ylabel("Success Rate (%)")
    ax.set_title("Perbandingan Success Rate: Baseline vs Dynamic Mapper", fontsize=12)
    ax.legend()
    ax.set_ylim(80, 102)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=150)
    plt.close()


def main():
    summary_path = RESULTS_DIR / "experiment_summary.json"
    if not summary_path.exists():
        print(f"ERROR: {summary_path} tidak ditemukan.")
        print("Jalankan terlebih dahulu: python experiments/run_experiments.py")
        return

    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)

    df = pd.DataFrame(summary)
    print("=" * 70)
    print("ANALISIS STATISTIK — Dynamic Message Mapper vs Baseline")
    print("=" * 70)

    stat_results = []

    for _, row in df.iterrows():
        scenario = row["scenario"]
        partner = row["partner"]
        baseline_latencies, dynamic_latencies = load_raw_latencies(scenario, partner)

        if not baseline_latencies or not dynamic_latencies:
            print(f"  Lewati {scenario}/{partner}: data mentah tidak ditemukan.")
            continue

        label = f"{scenario} - {partner}"
        result = run_statistical_tests(baseline_latencies, dynamic_latencies, label)
        stat_results.append(result)

        print(f"\n{label}")
        print(f"  Uji: {result['test']}, stat={result['stat']}, p={result['p_value']}")
        print(f"  Signifikan: {result['significant']} (α=0.05)")
        print(f"  Baseline: mean={result['baseline_mean']}ms ± {result['baseline_std']}ms")
        print(f"  Dynamic : mean={result['dynamic_mean']}ms ± {result['dynamic_std']}ms")
        print(f"  Effect size (Cohen's d): {result['cohens_d']} ({result['effect_size']})")

        # Plot boxplot
        plot_boxplot(
            baseline_latencies,
            dynamic_latencies,
            f"Distribusi Latency — {label}",
            f"boxplot_{scenario}_{partner}.png",
        )

    # Simpan hasil uji statistik
    stat_path = RESULTS_DIR / "statistical_results.json"
    with open(stat_path, "w", encoding="utf-8") as f:
        json.dump(stat_results, f, ensure_ascii=False, indent=2)

    stat_csv_path = RESULTS_DIR / "statistical_results.csv"
    if stat_results:
        with open(stat_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=stat_results[0].keys())
            writer.writeheader()
            writer.writerows(stat_results)

    # Bar chart success rate
    plot_success_rate_bar(df, "success_rate_comparison.png")

    # Tabel ringkasan per skenario
    print("\n" + "=" * 70)
    print("RINGKASAN SUCCESS RATE PER SKENARIO")
    print("=" * 70)
    scenario_agg = df.groupby("scenario").agg(
        avg_baseline_sr=("baseline_success_rate_pct", "mean"),
        avg_dynamic_sr=("dynamic_success_rate_pct", "mean"),
        improvement=("success_rate_improvement_pct", "mean"),
    ).reset_index()
    print(scenario_agg.to_string(index=False))

    print(f"\nPlot disimpan di: {PLOTS_DIR}")
    print(f"Hasil statistik: {stat_path}")


if __name__ == "__main__":
    main()
