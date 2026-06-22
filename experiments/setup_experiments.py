"""Experiment setup with sample data for prospective testing of the Oracle."""
import sys
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all, list_systems, get_system


EXPERIMENT_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(EXPERIMENT_DIR, exist_ok=True)


def generate_entropy_packet(seed: int = 42) -> dict:
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    numeric = [int(h[i:i+2], 16) / 255.0 for i in range(0, min(32, len(h)), 2)]
    return {
        "text": f"experiment_query_{seed}",
        "seed": seed,
        "sha_stream": h,
        "numeric_vector": numeric,
        "bit_stream": list(h),
        "timestamp": datetime.now().isoformat(),
    }


def create_baseline_dataset(n_samples: int = 50) -> list[dict]:
    print(f"Creating baseline dataset with {n_samples} samples...")
    dataset = []
    for i in range(n_samples):
        ep = generate_entropy_packet(seed=i * 7 + 13)
        sample = {
            "id": i,
            "entropy_packet": ep,
            "systems_tested": [],
            "results": {},
            "timestamp": datetime.now().isoformat(),
        }
        for sys_id in ["gematria", "iching", "geomancy", "numerology", "tarot"]:
            wrapper = get_system(sys_id)
            if wrapper:
                try:
                    result = wrapper.compute(ep)
                    if hasattr(result, 'numeric_projection'):
                        nums = result.numeric_projection
                        sym = result.symbolic_state
                    else:
                        nums = result.get("numeric_projection", [])
                        sym = result.get("symbolic_state", {})
                    sample["systems_tested"].append(sys_id)
                    sample["results"][sys_id] = {
                        "numeric": nums[:10],
                        "symbolic_keys": list(sym.keys())[:5] if isinstance(sym, dict) else [],
                    }
                except Exception as e:
                    sample["results"][sys_id] = {"error": str(e)}
        dataset.append(sample)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{n_samples} samples created")
    return dataset


def create_time_series_dataset(n_days: int = 30) -> list[dict]:
    print(f"Creating time series dataset with {n_days} days...")
    dataset = []
    base_date = datetime(2025, 1, 1)
    for i in range(n_days):
        day = base_date + timedelta(days=i)
        seed = int(day.strftime("%Y%m%d"))
        ep = generate_entropy_packet(seed=seed)
        ep["date"] = day.isoformat()
        sample = {
            "day": i + 1,
            "date": day.isoformat(),
            "entropy_packet": ep,
            "daily_readings": {},
        }
        for sys_id in ["gematria", "iching", "numerology"]:
            wrapper = get_system(sys_id)
            if wrapper:
                try:
                    result = wrapper.compute(ep)
                    if hasattr(result, 'numeric_projection'):
                        nums = result.numeric_projection
                    else:
                        nums = result.get("numeric_projection", [])
                    sample["daily_readings"][sys_id] = {
                        "primary_value": nums[0] if nums else 0,
                        "value_count": len(nums),
                    }
                except Exception:
                    sample["daily_readings"][sys_id] = {"primary_value": 0, "value_count": 0}
        dataset.append(sample)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{n_days} days created")
    return dataset


def main():
    register_all()
    print("=" * 70)
    print("  EXPERIMENT SETUP - Sample Data for Prospective Testing")
    print("=" * 70)

    print(f"\nRegistered systems: {len(list_systems())}")

    dataset = create_baseline_dataset(50)
    filepath = os.path.join(EXPERIMENT_DIR, "baseline_dataset.json")
    with open(filepath, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"\nBaseline dataset saved to {filepath}")

    ts_dataset = create_time_series_dataset(30)
    filepath = os.path.join(EXPERIMENT_DIR, "timeseries_dataset.json")
    with open(filepath, "w") as f:
        json.dump(ts_dataset, f, indent=2)
    print(f"Time series dataset saved to {filepath}")

    metadata = {
        "created_at": datetime.now().isoformat(),
        "baseline_samples": len(dataset),
        "timeseries_days": len(ts_dataset),
        "systems_used": list(set(s for d in dataset for s in d.get("systems_tested", []))),
        "total_systems": len(list_systems()),
    }
    filepath = os.path.join(EXPERIMENT_DIR, "metadata.json")
    with open(filepath, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {filepath}")

    print("\n--- Dataset Summary ---")
    print(f"  Baseline samples: {len(dataset)}")
    print(f"  Time series days: {len(ts_dataset)}")
    print(f"  Systems tested: {metadata['systems_used']}")
    print(f"\n  Sample baseline entry:")
    if dataset:
        s = dataset[0]
        print(f"    ID: {s['id']}")
        print(f"    Systems: {s['systems_tested']}")
        for sys_id, res in s['results'].items():
            if 'numeric' in res:
                print(f"    {sys_id}: {len(res['numeric'])} values")

    print(f"\nExperiments directory: {EXPERIMENT_DIR}")
    print("Setup complete!")


if __name__ == "__main__":
    main()
