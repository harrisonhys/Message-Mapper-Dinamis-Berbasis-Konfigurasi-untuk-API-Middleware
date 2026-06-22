"""data/generate_data.py — Enhanced Test Data Generator (7 error types)."""
import json, random
from datetime import date, timedelta
from faker import Faker
fake = Faker("id_ID")
random.seed(42); Faker.seed(42)

PROVINCES = ["Jl. Sudirman", "Jl. Merdeka", "Jl. Diponegoro", "Jl. Ahmad Yani", "Jl. Gatot Subroto", "Jl. Pemuda", "Jl. Veteran", "Jl. Pahlawan", "Jl. Raya Bogor", "Jl. HR Rasuna Said"]
CITIES = ["Jakarta", "Bandung", "Surabaya", "Medan", "Semarang", "Makassar", "Yogyakarta", "Palembang", "Denpasar", "Balikpapan"]
ITEMS = ["Sepatu Olahraga", "Tas Kulit", "Buku Pelajaran", "Elektronik", "Pakaian", "Aksesoris HP", "Peralatan Dapur", "Suplemen", "Produk Kecantikan", "Mainan Anak"]
VALID_COURIERS = ["jne", "pos", "tiki", "jnt", "sicepat", "anteraja", "lion_parcel"]
RECIPIENT_CITIES = [{"region": "Jawa", "city": "Jakarta Selatan", "postal": "12950"}, {"region": "Jawa", "city": "Bandung", "postal": "40262"}, {"region": "Jawa", "city": "Surabaya", "postal": "60265"}, {"region": "Sumatera", "city": "Medan", "postal": "20219"}, {"region": "Jawa", "city": "Semarang", "postal": "50241"}, {"region": "Sulawesi", "city": "Makassar", "postal": "90111"}]

def random_phone():
    if random.random() < 0.8: return "0" + str(random.randint(811_000_000, 899_999_999))
    else: return "62" + str(random.randint(811_000_000, 899_999_999))

def random_date(start_days_ago=365):
    d = date.today() - timedelta(days=random.randint(0, start_days_ago))
    return d.strftime("%Y-%m-%d")

def generate_payload(include_optional=True, n_extra_fields=0):
    street_no = random.randint(1, 200); city = random.choice(CITIES)
    address = f"{random.choice(PROVINCES)} No. {street_no}, {city}"
    recipient = random.choice(RECIPIENT_CITIES)
    payload = {"order_id": f"ORD-{fake.unique.random_int(min=10000, max=99999)}", "customer_name": fake.name(),
               "customer_phone": random_phone(), "address": address, "weight": round(random.uniform(0.1, 50.0), 2),
               "created_at": random_date(), "courier": random.choice(VALID_COURIERS),
               "recipient": {"name": fake.name(), "phone": random_phone(),
                              "address": {"street": f"{random.choice(PROVINCES)} No. {random.randint(1,200)}", "city": recipient["city"], "region": recipient["region"], "postal_code": recipient["postal"]}}}
    if include_optional:
        payload["item_name"] = random.choice(ITEMS); payload["quantity"] = random.randint(1, 20)
        payload["price"] = random.randint(10_000, 5_000_000)
        payload["notes"] = fake.sentence(nb_words=6) if random.random() < 0.5 else None
    for i in range(n_extra_fields): payload[f"extra_field_{i+1}"] = fake.word()
    return payload

def inject_missing_required(p): p2 = json.loads(json.dumps(p)); p2.pop("customer_name", None); return p2
def inject_wrong_type(p): p2 = json.loads(json.dumps(p)); p2["weight"] = "bukan angka"; return p2
def inject_invalid_phone(p): p2 = json.loads(json.dumps(p)); p2["customer_phone"] = "tidak_valid_99999"; return p2
def inject_invalid_date(p): p2 = json.loads(json.dumps(p)); p2["created_at"] = "2026-June-22"; return p2
def inject_invalid_enum(p): p2 = json.loads(json.dumps(p)); p2["courier"] = "UNKNOWN"; return p2
def inject_invalid_range(p): p2 = json.loads(json.dumps(p)); p2["weight"] = random.choice([0, -0.5, -1.2]); return p2
def inject_nested_missing(p):
    p2 = json.loads(json.dumps(p))
    if "recipient" in p2 and "address" in p2.get("recipient", {}): p2["recipient"]["address"].pop("city", None)
    return p2

ERROR_INJECTORS = {"MISSING_REQUIRED": inject_missing_required, "WRONG_TYPE": inject_wrong_type, "INVALID_PHONE": inject_invalid_phone, "INVALID_DATE": inject_invalid_date, "INVALID_ENUM": inject_invalid_enum, "INVALID_RANGE": inject_invalid_range, "NESTED_MISSING": inject_nested_missing}

def generate_dataset(total=500, include_optional=True, n_extra_fields=0, error_rate=0.10):
    error_types = list(ERROR_INJECTORS.keys()); errors_per_type = max(1, int(total * error_rate) // len(error_types))
    normal_count = total - (errors_per_type * len(error_types))
    data = [generate_payload(include_optional, n_extra_fields) for _ in range(normal_count)]
    for error_type in error_types:
        injector = ERROR_INJECTORS[error_type]
        for _ in range(errors_per_type): data.append(injector(generate_payload(include_optional, n_extra_fields)))
    while len(data) < total: data.append(generate_payload(include_optional, n_extra_fields))
    data = data[:total]; random.shuffle(data); return data

def main():
    import os; out_dir = os.path.dirname(__file__); output_path = os.path.join(out_dir, "test_payloads.json")
    print("Generating Enhanced Test Datasets (7 error types)...")
    datasets = {"S1_100_payloads_10fields": generate_dataset(100, False, 0, 0.10),
                "S2_300_payloads_15fields": generate_dataset(300, True, 1, 0.10),
                "S3_500_payloads_20fields": generate_dataset(500, True, 6, 0.12),
                "S4_500_payloads_30fields": generate_dataset(500, True, 16, 0.12)}
    with open(output_path, "w", encoding="utf-8") as f: json.dump(datasets, f, ensure_ascii=False, indent=2)
    for s, pl in datasets.items(): print(f"  {s}: {len(pl)} payloads, {len(pl[0])} fields")
    print(f"Saved to {output_path}")

if __name__ == "__main__": main()
