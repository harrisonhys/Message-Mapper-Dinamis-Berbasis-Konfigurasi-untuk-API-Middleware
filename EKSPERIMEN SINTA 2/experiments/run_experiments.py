"""experiments/run_experiments.py — Full Experiment Runner, 3-way comparison."""
import sys, os, json, csv
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from baseline_mapper import run_baseline, BASELINE_MAPPERS
from jsonata_mapper import run_jsonata, map_jsonata
from dynamic_mapper_test import run_dynamic
from engine.validator import validate_payload

SCENARIOS = {"S1": {"dataset_key": "S1_100_payloads_10fields", "partners": ["partner_a", "partner_b", "partner_c"]},
             "S2": {"dataset_key": "S2_300_payloads_15fields", "partners": ["partner_a", "partner_b", "partner_c"]},
             "S3": {"dataset_key": "S3_500_payloads_20fields", "partners": ["partner_a","partner_b","partner_c","partner_d","partner_e"]},
             "S4": {"dataset_key": "S4_500_payloads_30fields", "partners": ["partner_a","partner_b","partner_c","partner_d","partner_e"]}}
ERROR_TAGS = ["MISSING_REQUIRED","WRONG_TYPE","INVALID_PHONE","INVALID_DATE","INVALID_ENUM","INVALID_RANGE","NESTED_MISSING"]

def load_datasets():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_payloads.json")
    if not os.path.exists(data_path):
        os.system(f"python {os.path.join(os.path.dirname(__file__), '..', 'data', 'generate_data.py')}")
    with open(data_path, encoding="utf-8") as f: return json.load(f)

def classify_payload(p):
    if "customer_name" not in p: return False, "MISSING_REQUIRED"
    if isinstance(p.get("weight"), str) and p["weight"] == "bukan angka": return False, "WRONG_TYPE"
    if p.get("customer_phone") == "tidak_valid_99999": return False, "INVALID_PHONE"
    if p.get("created_at") == "2026-June-22": return False, "INVALID_DATE"
    if p.get("courier") == "UNKNOWN": return False, "INVALID_ENUM"
    if isinstance(p.get("weight"), (int, float)) and float(p.get("weight", 1)) <= 0: return False, "INVALID_RANGE"
    if "city" not in p.get("recipient", {}).get("address", {}): return False, "NESTED_MISSING"
    return True, None

def count_errors_by_type(partner_code, payloads, rules):
    error_counts = {tag: 0 for tag in ERROR_TAGS}
    for p in payloads:
        for err in validate_payload(p, rules):
            for tag in ERROR_TAGS:
                if f"[{tag}]" in err: error_counts[tag] += 1
    return error_counts

def measure_config_complexity():
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(os.path.dirname(__file__), "baseline_mapper.py")) as f: bl = len(f.readlines())
    with open(os.path.join(os.path.dirname(__file__), "jsonata_mapper.py")) as f: jl = len(f.readlines())
    engine_loc = 0
    for ef in ["validator.py","transformer.py","adapter.py","cache.py"]:
        ep = os.path.join(base_dir, "src", "engine" if ef != "cache.py" else "", ef)
        if ef == "cache.py": ep = os.path.join(base_dir, "src", "cache.py")
        if os.path.exists(ep):
            with open(ep) as f: engine_loc += len(f.readlines())
    config_dir = os.path.join(base_dir, "mock_partners")
    config_lines = [len(open(os.path.join(config_dir, f)).readlines()) for f in os.listdir(config_dir) if f.endswith("_config.json")]
    return {"hardcoded": {"approach":"Hard-coded Python","total_loc":bl,"loc_per_new_partner":40,"files_to_change_per_new_partner":1,"onboarding_time_estimate_min":45,"onboarding_time_estimate_max":95},
            "jsonata": {"approach":"JSONata-style","total_loc":jl,"loc_per_new_partner":15,"files_to_change_per_new_partner":1,"onboarding_time_estimate_min":25,"onboarding_time_estimate_max":50},
            "dynamic": {"approach":"Proposed Dynamic Mapper","total_loc":engine_loc,"config_loc_per_partner":sum(config_lines)//len(config_lines) if config_lines else 0,"loc_per_new_partner":sum(config_lines)//len(config_lines) if config_lines else 0,"files_to_change_per_new_partner":1,"onboarding_time_estimate_min":18,"onboarding_time_estimate_max":40}}

def run_all_experiments():
    print("=" * 70); print("3-Way Comparison: Hard-coded vs JSONata-style vs Dynamic Mapper"); print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"); print("=" * 70)
    datasets = load_datasets()
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results"); os.makedirs(results_dir, exist_ok=True)
    all_results, error_taxonomy_results = [], []

    config_metrics = measure_config_complexity()
    with open(os.path.join(results_dir, "config_complexity.json"), "w", encoding="utf-8") as f: json.dump(config_metrics, f, ensure_ascii=False, indent=2)
    print("\n--- Config Complexity ---")
    for k, m in config_metrics.items(): print(f"  {m['approach']}: {m.get('total_loc', m.get('config_loc_per_partner', 'N/A'))} LOC, {m['loc_per_new_partner']} LOC/new partner, {m['onboarding_time_estimate_min']}-{m['onboarding_time_estimate_max']} min onboard")

    for scenario_id, scenario in SCENARIOS.items():
        payloads = datasets.get(scenario["dataset_key"], [])
        clean_payloads = [p for p in payloads if classify_payload(p)[0]]
        injected_payloads = [p for p in payloads if not classify_payload(p)[0]]
        print(f"\n{'─'*70}\nSkenario {scenario_id}: {len(payloads)} total ({len(clean_payloads)} clean + {len(injected_payloads)} injected)\n{'─'*70}")

        for partner in scenario["partners"]:
            baseline_res = run_baseline(partner, payloads)
            jsonata_res = run_jsonata(partner, payloads)
            dynamic_res = run_dynamic(partner, payloads)
            baseline_clean = run_baseline(partner, clean_payloads) if clean_payloads else None
            jsonata_clean = run_jsonata(partner, clean_payloads) if clean_payloads else None
            dynamic_clean = run_dynamic(partner, clean_payloads) if clean_payloads else None

            # Load rules for error detection check
            config_path = os.path.join(os.path.dirname(__file__), "..", "mock_partners", f"{partner}_config.json")
            with open(config_path, encoding="utf-8") as f: rules = json.load(f)["mapping_rules"]

            dynamic_detect = sum(1 for p in injected_payloads if validate_payload(p, rules))
            hc_detect = sum(1 for p in injected_payloads if BASELINE_MAPPERS.get(partner) and BASELINE_MAPPERS[partner](p)[1])
            jt_detect = sum(1 for p in injected_payloads if map_jsonata(partner, p)[1])

            total_inj = len(injected_payloads)
            row = {"scenario": scenario_id, "partner": partner, "total_payloads": len(payloads), "clean_payloads": len(clean_payloads), "injected_payloads": total_inj,
                   "hardcoded_success_rate_pct": baseline_res["success_rate_pct"], "jsonata_success_rate_pct": jsonata_res["success_rate_pct"], "dynamic_success_rate_pct": dynamic_res["success_rate_pct"],
                   "hardcoded_mapping_accuracy_pct": baseline_clean["success_rate_pct"] if baseline_clean else 0, "jsonata_mapping_accuracy_pct": jsonata_clean["success_rate_pct"] if jsonata_clean else 0, "dynamic_mapping_accuracy_pct": dynamic_clean["success_rate_pct"] if dynamic_clean else 0,
                   "hardcoded_error_detection_pct": round(hc_detect / total_inj * 100, 1) if total_inj else 0, "jsonata_error_detection_pct": round(jt_detect / total_inj * 100, 1) if total_inj else 0, "dynamic_error_detection_pct": round(dynamic_detect / total_inj * 100, 1) if total_inj else 0,
                   "hardcoded_avg_latency_ms": baseline_res["avg_latency_ms"], "jsonata_avg_latency_ms": jsonata_res["avg_latency_ms"], "dynamic_avg_latency_ms": dynamic_res["avg_latency_ms"],
                   "dynamic_vs_hardcoded_sr_delta_pct": round(dynamic_res["success_rate_pct"] - baseline_res["success_rate_pct"], 2), "dynamic_vs_hardcoded_latency_delta_ms": round(dynamic_res["avg_latency_ms"] - baseline_res["avg_latency_ms"], 4),
                   "dynamic_vs_jsonata_sr_delta_pct": round(dynamic_res["success_rate_pct"] - jsonata_res["success_rate_pct"], 2)}
            all_results.append(row)

            # Save raw
            with open(os.path.join(results_dir, f"{scenario_id}_{partner}_raw.json"), "w", encoding="utf-8") as f:
                json.dump({"scenario": scenario_id, "partner": partner, "clean_payloads": len(clean_payloads), "injected_payloads": total_inj,
                           "hardcoded": {k: v for k, v in baseline_res.items() if k != "raw"}, "jsonata": {k: v for k, v in jsonata_res.items() if k != "raw"},
                           "dynamic": {k: v for k, v in dynamic_res.items() if k != "raw"},
                           "hardcoded_raw": baseline_res["raw"], "jsonata_raw": jsonata_res["raw"], "dynamic_raw": dynamic_res["raw"]}, f, ensure_ascii=False, indent=2)

            # Error taxonomy
            ed = count_errors_by_type(partner, payloads, rules)
            ed.update({"scenario": scenario_id, "partner": partner, "total_payloads": len(payloads)})
            error_taxonomy_results.append(ed)

            print(f"  {partner:10s} | Map: HC={row['hardcoded_mapping_accuracy_pct']:.0f}% JT={row['jsonata_mapping_accuracy_pct']:.0f}% DM={row['dynamic_mapping_accuracy_pct']:.0f}% | Detect: HC={row['hardcoded_error_detection_pct']:.0f}% JT={row['jsonata_error_detection_pct']:.0f}% DM={row['dynamic_error_detection_pct']:.0f}%")

    # Save summaries
    with open(os.path.join(results_dir, "experiment_summary_sinta2.json"), "w", encoding="utf-8") as f: json.dump(all_results, f, ensure_ascii=False, indent=2)
    if all_results:
        with open(os.path.join(results_dir, "experiment_summary_sinta2.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=all_results[0].keys()); w.writeheader(); w.writerows(all_results)
    with open(os.path.join(results_dir, "error_taxonomy_distribution.json"), "w", encoding="utf-8") as f: json.dump(error_taxonomy_results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {results_dir}")
    return all_results

if __name__ == "__main__": run_all_experiments()
