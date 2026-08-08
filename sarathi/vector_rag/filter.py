"""Metadata filtering engine."""
from typing import Dict, Any, Optional, List

class MetadataFilter:
    @staticmethod
    def matches(filter_spec: Optional[Dict[str, Any]], metadata: Dict[str, Any]) -> bool:
        if not filter_spec: return True
        for key, val in filter_spec.items():
            if key == "$and":
                if not isinstance(val, list) or not all(MetadataFilter.matches(c, metadata) for c in val): return False
            elif key == "$or":
                if not isinstance(val, list) or not any(MetadataFilter.matches(c, metadata) for c in val): return False
            elif key == "$not":
                if MetadataFilter.matches(val, metadata): return False
            else:
                meta_val = metadata.get(key)
                if isinstance(val, dict):
                    for op, target in val.items():
                        if op == "$eq" and meta_val != target: return False
                        elif op == "$ne" and meta_val == target: return False
                        elif op == "$gt" and (meta_val is None or meta_val <= target): return False
                        elif op == "$gte" and (meta_val is None or meta_val < target): return False
                        elif op == "$lt" and (meta_val is None or meta_val >= target): return False
                        elif op == "$lte" and (meta_val is None or meta_val > target): return False
                        elif op == "$in" and meta_val not in target: return False
                        elif op == "$contains" and target not in meta_val: return False
                elif meta_val != val: return False
        return True
