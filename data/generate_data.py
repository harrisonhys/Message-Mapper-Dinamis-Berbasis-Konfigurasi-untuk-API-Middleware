"""
data/generate_data.py — Generator 500 payload uji transaksi logistik
Menghasilkan data realistis dengan variasi field yang mencerminkan
skenario pengujian S1–S4 pada penelitian.
"""
import json
import random
from datetime import date, timedelta

try:
    from faker import Faker
    fake = Faker("id_ID")
except ImportError:
    print("Install faker: pip install faker")
    raise

random.seed(42)

PROVINCES = [
    "Jl. Sudirman", "Jl. Merdeka", "Jl. Diponegoro", "Jl. Ahmad Yani",
    "Jl. Gatot Subroto", "Jl. Pemuda", "Jl. Veteran", "Jl. Pahlawan",
    "Jl. Raya Bogor", "Jl. HR Rasuna Said",
]

CITIES = [
    "Jakarta", "Bandung", "Surabaya", "Medan", "Semarang",
    "Makassar", "Yogyakarta", "Palembang", "Denpasar", "Balikpapan",
]

ITEMS = [
    "Sepatu Olahraga", "Tas Kulit", "Buku Pelajaran", "Elektronik",
    "Pakaian", "Aksesoris HP", "Peralatan Dapur", "Suplemen",
    "Produk Kecantikan", "Mainan Anak",
]


def random_phone() -> str:
    """80% kemungkinan format 08xxx (valid untuk transform), 20% sudah +62xxx."""
    if random.random() < 0.8:
        return "0" + str(random.randint(811_000_000, 899_999_999))
    else:
        return "62" + str(random.randint(811_000_000, 899_999_999))


def random_date(start_days_ago: int = 365) -> str:
    delta = random.randint(0, start_days_ago)
    d = date.today() - timedelta(days=delta)
    return d.strftime("%Y-%m-%d")


def generate_payload(include_optional: bool = True, n_extra_fields: int = 0) -> dict:
    """
    Generate satu payload transaksi internal.
    
    Parameters
    ----------
    include_optional : bool — sertakan field opsional (item_name, quantity, price, notes)
    n_extra_fields   : int  — tambahan field untuk skenario jumlah field lebih besar
    """
    street_no = random.randint(1, 200)
    city = random.choice(CITIES)
    address = f"{random.choice(PROVINCES)} No. {street_no}, {city}"

    payload = {
        "order_id": f"ORD-{fake.unique.random_int(min=10000, max=99999)}",
        "customer_name": fake.name(),
        "customer_phone": random_phone(),
        "address": address,
        "weight": round(random.uniform(0.1, 50.0), 2),
        "created_at": random_date(),
    }

    if include_optional:
        payload["item_name"] = random.choice(ITEMS)
        payload["quantity"] = random.randint(1, 20)
        payload["price"] = random.randint(10_000, 5_000_000)
        payload["notes"] = fake.sentence(nb_words=6) if random.random() < 0.5 else None

    # Extra fields untuk skenario S3/S4 (20–30 field)
    for i in range(n_extra_fields):
        payload[f"extra_field_{i+1}"] = fake.word()

    return payload


def generate_dataset(
    total: int = 500,
    include_optional: bool = True,
    n_extra_fields: int = 0,
    error_rate: float = 0.08,
) -> list[dict]:
    """
    Generate dataset dengan persentase payload bermasalah untuk simulasi error.
    
    error_rate : float — proporsi payload yang sengaja memiliki field tidak valid
    """
    data = []
    error_count = int(total * error_rate)

    for i in range(total):
        p = generate_payload(include_optional, n_extra_fields)
        # Sisipkan error acak pada error_count pertama
        if i < error_count:
            error_type = random.choice(["missing_required", "wrong_type", "bad_phone"])
            if error_type == "missing_required":
                drop_field = random.choice(["customer_name", "address"])
                p.pop(drop_field, None)
            elif error_type == "wrong_type":
                p["weight"] = "bukan angka"
            elif error_type == "bad_phone":
                p["customer_phone"] = "tidak_valid"
        data.append(p)

    random.shuffle(data)
    return data


def main():
    import os

    out_dir = os.path.dirname(__file__)
    output_path = os.path.join(out_dir, "test_payloads.json")

    print("Generating test datasets...")

    datasets = {
        "S1_100_payloads_10fields": generate_dataset(100, include_optional=False, n_extra_fields=0),
        "S2_300_payloads_15fields": generate_dataset(300, include_optional=True, n_extra_fields=1),
        "S3_500_payloads_20fields": generate_dataset(500, include_optional=True, n_extra_fields=6),
        "S4_500_payloads_30fields": generate_dataset(500, include_optional=True, n_extra_fields=16),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(datasets, f, ensure_ascii=False, indent=2)

    for scenario, payloads in datasets.items():
        print(f"  {scenario}: {len(payloads)} payloads, "
              f"{len(payloads[0])} fields each")

    print(f"\nDataset saved to: {output_path}")


if __name__ == "__main__":
    main()
