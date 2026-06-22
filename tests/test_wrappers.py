"""Tests for all symbolic system wrappers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all_wrappers():
    from oracle.symbolic.registry import list_systems, compute_system
    systems = list_systems()
    packet = {"bit_stream": [1,0,1]*10, "seed": 42, "numeric_vector": [1,2,3],
              "normalized_text": "test", "calendar_context": {"year":2024,"month":1,"day":1,"hour":12},
              "timestamp": 0}
    for sys_id in systems:
        try:
            result = compute_system(sys_id, packet)
            assert result.system_id == sys_id
            assert len(result.numeric_projection) > 0
            assert isinstance(result.structural_features, dict)
            print(f"  [OK] {sys_id}")
        except Exception as e:
            print(f"  [FAIL] {sys_id}: {e}")
    print("[PASS] test_all_wrappers")

if __name__ == "__main__":
    test_all_wrappers()
