"""
experiments/run_experiments.py — Eksekusi Semua Skenario S1–S4
Membandingkan baseline hard-coded mapping vs dynamic message mapper
dan menyimpan hasil ke folder results/.
"""
import sys
import os
import json
import csv
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from baseline_mapper import run_baseline
from dynamic_mapper_test import run_dynamic

# ------------------------------------------------------------------ #
# Definisi skenario pengujian
# ------------------------------------------------------------------ #
SCENARIOS = {
    "S1": {"dataset_key": "S1_100_payloads_10fields", "partners": ["partner_a", "partner_b", "partner_c"]},
    "S2": {"dataset_key": "S2_300_payloads_15fields", "partners": ["partner_a", "partner_b", "partner_c"]},
    "S3": {"dataset_key": "S3_500_payloads_20fields", "partners": ["partner_a", "partner_b", "partner_c", "partner_d", "partner_e"]},
    "S4": {"dataset_key": "S4_500_payloads_30fields", "partners": ["partner_a", "partner_b", "partner_c", "partner_d", "partner_e"]},
}


def load_datasets() -> dict:
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_payloads.json")
    if not os.path.exists(data_path):
        print("Dataset belum ada. Generating...")
        os.system(f"python {os.path.join(os.path.dirname(__file__), '..', 'data', 'generate_data.py')}")
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


def run_all_experiments():
    print("=" * 70)
    print("EKSPERIMEN: Baseline Hard-coded vs Dynamic Message Mapper")
    print(f"Waktu mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    datasets = load_datasets()
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(results_dir, exist_ok=True)

    all_results = []

    for scenario_id, scenario in SCENARIOS.items():
        dataset_key = scenario["dataset_key"]
        partners = scenario["partners"]
        payloads = datasets.get(dataset_key, [])

        print(f"\n--- Skenario {scenario_id}: {len(payloads)} payloads, {len(partners)} partner(s) ---")

        for partner in partners:
            # Jalankan baseline
            baseline_res = run_baseline(partner, payloads)
            # Jalankan dynamic mapper
            dynamic_res = run_dynamic(partner, payloads)

            row = {
                "scenario": scenario_id,
                "partner": partner,
                "total_payloads": len(payloads),
                # Baseline
                "baseline_success_count": baseline_res["success_count"],
                "baseline_error_count": baseline_res["error_count"],
                "baseline_success_rate_pct": baseline_res["success_rate_pct"],
                "baseline_avg_latency_ms": baseline_res["avg_latency_ms"],
                "baseline_min_latency_ms": baseline_res["min_latency_ms"],
                "baseline_max_latency_ms": baseline_res["max_latency_ms"],
                # Dynamic
                "dynamic_success_count": dynamic_res["success_count"],
                "dynamic_error_count": dynamic_res["error_count"],
                "dynamic_success_rate_pct": dynamic_res["success_rate_pct"],
                "dynamic_avg_latency_ms": dynamic_res["avg_latency_ms"],
                "dynamic_min_latency_ms": dynamic_res["min_latency_ms"],
                "dynamic_max_latency_ms": dynamic_res["max_latency_ms"],
                # Delta
                "success_rate_improvement_pct": round(
                    dynamic_res["success_rate_pct"] - baseline_res["success_rate_pct"], 2
                ),
                "latency_diff_ms": round(
                    dynamic_res["avg_latency_ms"] - baseline_res["avg_latency_ms"], 4
                ),
            }
            all_results.append(row)

            # Simpan raw data per partner per skenario
            raw_path = os.path.join(
                results_dir, f"{scenario_id}_{partner}_raw.json"
            )
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "scenario": scenario_id,
                        "partner": partner,
                        "baseline": {k: v for k, v in baseline_res.items() if k != "raw"},
                        "dynamic": {k: v for k, v in dynamic_res.items() if k != "raw"},
                        "baseline_raw": baseline_res["raw"],
                        "dynamic_raw": dynamic_res["raw"],
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            print(
                f"  {partner}: "
                f"Baseline SR={baseline_res['success_rate_pct']}% "
                f"({baseline_res['avg_latency_ms']:.4f}ms avg) | "
                f"Dynamic SR={dynamic_res['success_rate_pct']}% "
                f"({dynamic_res['avg_latency_ms']:.4f}ms avg)"
            )

    # Simpan ringkasan CSV
    csv_path = os.path.join(results_dir, "experiment_summary.csv")
    if all_results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)

    # Simpan ringkasan JSON
    json_path = os.path.join(results_dir, "experiment_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n\nHasil disimpan di: {results_dir}")
    print(f"  - experiment_summary.csv")
    print(f"  - experiment_summary.json")
    print(f"  - [scenario]_[partner]_raw.json (detail per skenario)")
    print(f"\nSelesai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return all_results


if __name__ == "__main__":
    run_all_experiments()
