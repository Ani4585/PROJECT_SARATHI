"""
Federated Learning Parameter Aggregator (FedAvg).
"""
import numpy as np
from typing import List, Dict, Any

class FederatedAggregator:
    @staticmethod
    def aggregate_fedavg(client_weights: List[Dict[str, List[float]]], client_samples: List[int]) -> Dict[str, List[float]]:
        if not client_weights or not client_samples or len(client_weights) != len(client_samples):
            raise ValueError("Mismatched client weights and sample counts.")

        total_samples = sum(client_samples)
        if total_samples == 0:
            raise ValueError("Total sample count cannot be zero.")

        aggregated: Dict[str, np.ndarray] = {}

        for weights, num_samples in zip(client_weights, client_samples):
            weight_factor = num_samples / total_samples
            for param_key, param_val in weights.items():
                arr = np.asarray(param_val, dtype=np.float32) * weight_factor
                if param_key not in aggregated:
                    aggregated[param_key] = arr
                else:
                    aggregated[param_key] += arr

        return {k: v.tolist() for k, v in aggregated.items()}
