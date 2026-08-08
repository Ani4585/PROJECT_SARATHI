from typing import Dict

class ServiceMeshContext:
    @staticmethod
    def extract_mesh_headers(headers: Dict[str, str]) -> Dict[str, str]:
        mesh_keys = [
            "x-request-id",
            "x-b3-traceid",
            "x-b3-spanid",
            "x-b3-parentspanid",
            "x-b3-sampled",
            "x-ot-span-context"
        ]
        extracted = {}
        for key, val in headers.items():
            k_lower = key.lower()
            if k_lower in mesh_keys:
                extracted[k_lower] = val
        return extracted
