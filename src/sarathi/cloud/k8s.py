from typing import Dict, Any

class SarathiCRDGenerator:
    @staticmethod
    def generate_crd_spec(service_name: str, image: str, replicas: int = 2) -> Dict[str, Any]:
        return {
            "apiVersion": "sarathi.io/v1alpha1",
            "kind": "SarathiApp",
            "metadata": {"name": service_name},
            "spec": {
                "replicas": replicas,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": service_name,
                                "image": image,
                                "ports": [{"containerPort": 8000}],
                                "livenessProbe": {
                                    "httpGet": {"path": "/health/liveness", "port": 8000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 10
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/health/readiness", "port": 8000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5
                                }
                            }
                        ]
                    }
                }
            }
        }
