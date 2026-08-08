"""Distance metrics and vector math utilities."""
from enum import Enum
import numpy as np

class DistanceMetric(str, Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"

def compute_similarity(v1: np.ndarray, v2: np.ndarray, metric: DistanceMetric) -> float:
    v1 = np.asarray(v1, dtype=np.float32)
    v2 = np.asarray(v2, dtype=np.float32)
    if metric == DistanceMetric.COSINE:
        norm1 = float(np.linalg.norm(v1))
        norm2 = float(np.linalg.norm(v2))
        return float(np.dot(v1, v2) / (norm1 * norm2)) if norm1 > 0 and norm2 > 0 else 0.0
    elif metric == DistanceMetric.DOT_PRODUCT:
        return float(np.dot(v1, v2))
    elif metric == DistanceMetric.EUCLIDEAN:
        return float(1.0 / (1.0 + float(np.linalg.norm(v1 - v2))))
    elif metric == DistanceMetric.MANHATTAN:
        return float(1.0 / (1.0 + float(np.sum(np.abs(v1 - v2)))))
    else:
        raise ValueError(f"Unsupported metric: {metric}")
