"""experiments/statistical_analysis.py — Statistical Analysis, 3-way comparison."""
import sys, os, json, csv
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

RESULTS_DIR = Path(__file__).parent.parent / "results"
PLOTS_DIR = RESULTS_DIR / "plots"; PLOTS_DIR.mkdir(parents=True, exist_ok=True)
sns.set_style("whitegrid"); sns.set_palette("Set2")

def cohens_d(x, y):
    diff = np.array(x) - np.array(y); sd = np.std(diff, ddof=1)
    return float(np.mean(diff) / sd) if sd != 0 else 0.0

def interpret_es(d):
    d = abs(d)
    if d < 0.2: return "trivial"
    if d < 0.5: return "small"
    if d < 0.8: return "medium"
    return "large"

def load_raw_latencies(scenario, partner):
    path = RESULTS_DIR / f"{scenario}_{partner}_raw.json"
    if not path.exists(): return [], [], []
    with open(path) as f: data = json.load(f)
    hc = [r["latency_ms"] for r in data.get("hardcoded_raw", [])]
    jt = [r["latency_ms"] for r in data.get("jsonata_raw", [])]
    dm = [r["latency_ms"] for r in data.get("dynamic_raw", [])]
    return hc, jt, dm

def run_paired_test(a, b, la, lb):
    aa, bb = np.array(a), np.array(b); diffs = aa - bb
    _, p_norm = stats.shapiro(diffs[:min(len(diffs), 5000)])
    if p_norm > 0.05: stat, pv, name = stats.ttest_rel(aa, bb); name = "Paired t-test"
    else: stat, pv = stats.wilcoxon(aa, bb, alternative="two-sided"); name = "Wilcoxon signed-rank"
    d = cohens_d(list(aa), list(bb))
    return {"comparison": f"{la} vs {lb}", "test": name, "stat": round(float(stat), 4), "p_value": round(float(pv), 6),
            "significant": bool(pv < 0.05), "normal_diff": bool(p_norm > 0.05),
            f"{la}_mean": round(float(np.mean(aa)), 4), f"{la}_std": round(float(np.std(aa, ddof=1)), 4),
            f"{lb}_mean": round(float(np.mean(bb)), 4), f"{lb}_std": round(float(np.std(bb, ddof=1)), 4),
            "cohens_d": round(d, 4), "effect_size": interpret_es(d)}

def plot_boxplot_3way(hc, jt, dm, title, filename):
    fig, ax = plt.subplots(figsize=(10, 6))
    data = pd.DataFrame({"Hard-coded\n(Baseline)": hc, "JSONata\n(Rule-based)": jt, "Dynamic\nMapper": dm})
    colors = ["#F1948A", "#AED6F1", "#A9DFBF"]
    bp = data.plot(kind="box", ax=ax, patch_artist=True, medianprops=dict(color="#E74C3C", linewidth=2))
    for patch, color in zip(bp.patches, colors): patch.set_facecolor(color)
    ax.set_title(title, fontsize=13, pad=14); ax.set_ylabel("Latency (ms)"); ax.set_xlabel("Mapping Approach")
    plt.tight_layout(); plt.savefig(PLOTS_DIR / filename, dpi=150, bbox_inches="tight"); plt.close()

def plot_success_rate_bar_3way(df, filename):
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(df)); w = 0.25
    ax.bar(x - w, df["hardcoded_success_rate_pct"], w, label="Hard-coded (Baseline)", color="#F1948A", edgecolor="white")
    ax.bar(x, df["jsonata_success_rate_pct"], w, label="JSONata (Rule-based)", color="#AED6F1", edgecolor="white")
    ax.bar(x + w, df["dynamic_success_rate_pct"], w, label="Dynamic Mapper (Proposed)", color="#A9DFBF", edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels([f"{r.scenario}\n{r.partner}" for r in df.itertuples()], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Success Rate (%)"); ax.set_title("3-Way Success Rate Comparison", fontsize=14)
    ax.legend(loc="lower right"); ax.set_ylim(75, 105); plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=150, bbox_inches="tight"); plt.close()

def plot_latency_comparison(df, filename):
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(df)); w = 0.25
    ax.bar(x - w, df["hardcoded_avg_latency_ms"], w, label="Hard-coded", color="#F1948A", edgecolor="white")
    ax.bar(x, df["jsonata_avg_latency_ms"], w, label="JSONata", color="#AED6F1", edgecolor="white")
    ax.bar(x + w, df["dynamic_avg_latency_ms"], w, label="Dynamic Mapper", color="#A9DFBF", edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels([f"{r.scenario}\n{r.partner}" for r in df.itertuples()], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Average Latency (ms)"); ax.set_title("3-Way Latency Comparison", fontsize=14)
    ax.legend(); plt.tight_layout(); plt.savefig(PLOTS_DIR / filename, dpi=150, bbox_inches="tight"); plt.close()

def plot_error_heatmap(error_data, filename):
    df = pd.DataFrame(error_data)
    hd = df.groupby("partner")[["MISSING_REQUIRED","WRONG_TYPE","INVALID_PHONE","INVALID_DATE","INVALID_ENUM","INVALID_RANGE","NESTED_MISSING"]].sum()
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(hd, annot=True, fmt="d", cmap="YlOrRd", ax=ax, cbar_kws={"label": "Error Count"})
    ax.set_title("Error Taxonomy Distribution by Partner", fontsize=14); ax.set_ylabel("Partner"); ax.set_xlabel("Error Type")
    plt.tight_layout(); plt.savefig(PLOTS_DIR / filename, dpi=150, bbox_inches="tight"); plt.close()

def main():
    sp = RESULTS_DIR / "experiment_summary_sinta2.json"
    if not sp.exists(): print(f"ERROR: {sp} not found. Run experiments first."); return
    with open(sp) as f: summary = json.load(f)
    df = pd.DataFrame(summary)
    print("=" * 70); print("STATISTICAL ANALYSIS — 3-Way Comparison"); print("=" * 70)
    all_stats = []
    for _, row in df.iterrows():
        scenario, partner = row["scenario"], row["partner"]
        hc, jt, dm = load_raw_latencies(scenario, partner)
        if not hc or not jt or not dm: print(f"  Skip {scenario}/{partner}: raw data missing"); continue
        label = f"{scenario} - {partner}"
        for (a, b, la, lb) in [(dm, hc, "dynamic", "hardcoded"), (dm, jt, "dynamic", "jsonata"), (jt, hc, "jsonata", "hardcoded")]:
            r = run_paired_test(a, b, la, lb); r["label"] = f"{label} ({la} vs {lb})"; all_stats.append(r)
            print(f"  {label} {la} vs {lb}: {r['test']}, p={r['p_value']}, d={r['cohens_d']} ({r['effect_size']})")
        plot_boxplot_3way(hc, jt, dm, f"Latency Distribution - {label}", f"boxplot_3way_{scenario}_{partner}.png")

    with open(RESULTS_DIR / "statistical_results_sinta2.json", "w") as f: json.dump(all_stats, f, ensure_ascii=False, indent=2)
    if all_stats:
        with open(RESULTS_DIR / "statistical_results_sinta2.csv", "w", newline="") as f:
            csv_fields = ["label","comparison","test","stat","p_value","significant","normal_diff","cohens_d","effect_size"]
            w = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore"); w.writeheader(); w.writerows(all_stats)

    plot_success_rate_bar_3way(df, "success_rate_3way.png")
    plot_latency_comparison(df, "latency_3way.png")

    ep = RESULTS_DIR / "error_taxonomy_distribution.json"
    if ep.exists():
        with open(ep) as f: plot_error_heatmap(json.load(f), "error_taxonomy_heatmap.png")

    sig = sum(1 for r in all_stats if r["significant"])
    print(f"\nSignificant: {sig}/{len(all_stats)} ({sig/len(all_stats)*100:.1f}%)" if all_stats else "")
    print(f"Plots: {PLOTS_DIR}")

if __name__ == "__main__": main()
