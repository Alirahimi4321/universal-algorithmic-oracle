"""Notebook 03: Fusion Analysis - Test multi-system fusion with sample entropy packets."""
import sys
import os
import hashlib
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.symbolic.registry import register_all, get_system, list_systems


def make_entropy_packet(seed: int = 42) -> dict:
    h = hashlib.sha256(str(seed).encode()).hexdigest()
    numeric = [int(h[i:i+2], 16) / 255.0 for i in range(0, min(32, len(h)), 2)]
    return {
        "text": f"oracle_query_{seed}",
        "seed": seed,
        "sha_stream": h,
        "numeric_vector": numeric,
        "bit_stream": list(h),
    }


def main():
    register_all()
    print("=" * 70)
    print("  FUSION ANALYSIS - Multi-System Integration")
    print("=" * 70)

    ep = make_entropy_packet(42)
    print(f"\nEntropy packet: seed={ep['seed']}, numeric={len(ep['numeric_vector'])} values")

    systems_to_test = [
        "gematria", "iching", "geomancy", "numerology",
        "tarot", "hebrew_gematria", "english_gematria",
    ]

    print(f"\nTesting {len(systems_to_test)} systems individually...")
    results = {}
    for sys_id in systems_to_test:
        wrapper = get_system(sys_id)
        if wrapper is None:
            print(f"  {sys_id}: NOT AVAILABLE")
            continue
        t0 = time.time()
        try:
            result = wrapper.compute(ep)
            elapsed = time.time() - t0
            if hasattr(result, 'numeric_projection'):
                nums = result.numeric_projection
                sym = result.symbolic_state
            else:
                nums = result.get("numeric_projection", [])
                sym = result.get("symbolic_state", {})
            results[sys_id] = {"numeric": nums, "symbolic": sym}
            print(f"  {sys_id:25s}: {len(nums):3d} numeric values, {elapsed:.3f}s")
        except Exception as e:
            print(f"  {sys_id:25s}: ERROR - {e}")

    print(f"\nFusing results with weighted average...")
    all_avgs = []
    for sys_id, res in results.items():
        nums = res["numeric"]
        if nums:
            avg = sum(nums) / len(nums)
            all_avgs.append((sys_id, avg))
            print(f"  {sys_id:25s}: avg={avg:.4f}, count={len(nums)}")
    if all_avgs:
        overall_avg = sum(a for _, a in all_avgs) / len(all_avgs)
        print(f"\n  Overall fused average: {overall_avg:.4f}")
        print(f"  Individual averages: {[f'{a:.4f}' for _, a in all_avgs]}")

    print("\n--- Cross-system comparison ---")
    for sys_id, res in results.items():
        nums = res["numeric"]
        if nums:
            mean = sum(nums) / len(nums)
            std = (sum((x - mean) ** 2 for x in nums) / len(nums)) ** 0.5 if len(nums) > 1 else 0
            print(f"  {sys_id:25s}: mean={mean:.4f}, std={std:.4f}, range=[{min(nums):.3f}, {max(nums):.3f}]")


if __name__ == "__main__":
    main()
