"""Tests for entropy encoder and related modules."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_entropy_encoder():
    from oracle.entropy.encoder import EntropyEncoder
    encoder = EntropyEncoder()
    packet = encoder.encode("test question")
    assert packet.seed > 0
    assert len(packet.bit_stream) > 0
    assert len(packet.numeric_vector) > 0
    print("[PASS] test_entropy_encoder")

def test_calendar_entropy():
    from oracle.entropy.calendar_entropy import generate_calendar_entropy
    result = generate_calendar_entropy()
    assert "gregorian" in result
    assert "jalali" in result
    assert "hijri" in result
    assert "numeric_signature" in result
    print("[PASS] test_calendar_entropy")

def test_symbolic_matrix():
    from oracle.entropy.symbolic_matrix import generate_symbolic_matrix, matrix_to_features
    matrix = generate_symbolic_matrix(42, (4, 4))
    assert len(matrix) == 4
    assert len(matrix[0]) == 4
    features = matrix_to_features(matrix)
    assert "mean" in features
    assert "entropy" in features
    print("[PASS] test_symbolic_matrix")

if __name__ == "__main__":
    test_entropy_encoder()
    test_calendar_entropy()
    test_symbolic_matrix()
    print("=== ALL ENTROPY TESTS PASSED ===")
