"""
Differential Privacy Engine (Gaussian/Laplace Noise & Privacy Budget Tracker).
"""
import math
import random
from typing import List, Dict, Any, Optional

class PrivacyBudgetExhaustedError(Exception):
    """Raised when the epsilon/delta privacy budget is depleted."""
    pass

class PrivacyBudgetTracker:
    def __init__(self, max_epsilon: float = 10.0, max_delta: float = 1e-5):
        self.max_epsilon = max_epsilon
        self.max_delta = max_delta
        self.consumed_epsilon = 0.0
        self.consumed_delta = 0.0

    def consume(self, epsilon: float, delta: float = 0.0):
        if self.consumed_epsilon + epsilon > self.max_epsilon:
            raise PrivacyBudgetExhaustedError(
                f"Privacy budget exceeded: requested {epsilon:.2f}, remaining {self.max_epsilon - self.consumed_epsilon:.2f}"
            )
        self.consumed_epsilon += epsilon
        self.consumed_delta += delta

    def remaining_budget(self) -> Dict[str, float]:
        return {
            "remaining_epsilon": max(0.0, self.max_epsilon - self.consumed_epsilon),
            "remaining_delta": max(0.0, self.max_delta - self.consumed_delta)
        }

class DifferentialPrivacyEngine:
    def __init__(self, budget_tracker: Optional[PrivacyBudgetTracker] = None):
        self.tracker = budget_tracker or PrivacyBudgetTracker()

    def add_laplace_noise(self, vector: List[float], epsilon: float, sensitivity: float = 1.0) -> List[float]:
        self.tracker.consume(epsilon=epsilon)
        scale = sensitivity / epsilon
        noisy_vec = []
        for x in vector:
            u = random.uniform(-0.49, 0.49)
            sgn = 1.0 if u >= 0 else -1.0
            noise = -scale * sgn * math.log(1.0 - 2.0 * abs(u))
            noisy_vec.append(x + noise)
        return noisy_vec

    def add_gaussian_noise(self, vector: List[float], epsilon: float, delta: float = 1e-5, sensitivity: float = 1.0) -> List[float]:
        self.tracker.consume(epsilon=epsilon, delta=delta)
        sigma = (sensitivity * math.sqrt(2 * math.log(1.25 / delta))) / epsilon
        return [x + random.gauss(0, sigma) for x in vector]
