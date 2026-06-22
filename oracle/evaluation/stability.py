"""Response stability evaluation - measures robustness to input perturbation."""
import hashlib


def evaluate_stability(chromosome, oracle_func, entropy_packet: dict, num_perturbations: int = 5) -> float:
    """Evaluate response stability by perturbing input and checking output consistency."""
    try:
        original_result = oracle_func(chromosome, entropy_packet)
        original_np = original_result.get("numeric_projection", [])
        if not original_np:
            return 0.0

        stable_count = 0
        for i in range(num_perturbations):
            perturbed = dict(entropy_packet)
            perturbed["seed"] = entropy_packet.get("seed", 0) + i + 1
            perturbed_result = oracle_func(chromosome, perturbed)
            perturbed_np = perturbed_result.get("numeric_projection", [])

            if not perturbed_np:
                continue

            max_len = max(len(original_np), len(perturbed_np))
            orig = original_np + [0] * (max_len - len(original_np))
            pert = perturbed_np + [0] * (max_len - len(perturbed_np))

            diff = sum(abs(a - b) for a, b in zip(orig, pert)) / max_len
            similarity = 1.0 / (1.0 + diff)

            if similarity > 0.5:
                stable_count += 1

        return stable_count / num_perturbations if num_perturbations > 0 else 0.0
    except Exception:
        return 0.0
