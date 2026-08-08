"""
Master Privacy Manager for Sarathi.
"""
from typing import Dict, Any, List, Optional
from sarathi.privacy.dp_engine import DifferentialPrivacyEngine, PrivacyBudgetTracker
from sarathi.privacy.federated import FederatedAggregator

class PrivacyManager:
    def __init__(self, max_epsilon: float = 10.0):
        self.budget_tracker = PrivacyBudgetTracker(max_epsilon=max_epsilon)
        self.dp_engine = DifferentialPrivacyEngine(budget_tracker=self.budget_tracker)
        self.aggregator = FederatedAggregator()

    def anonymize_vector(self, vector: List[float], epsilon: float = 0.5) -> List[float]:
        return self.dp_engine.add_laplace_noise(vector=vector, epsilon=epsilon)
