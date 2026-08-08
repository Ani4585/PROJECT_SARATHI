import pytest
from sarathi.cloud import K8sProbeHandler, SarathiCRDGenerator, ServiceMeshContext

def test_k8s_probes_status_codes():
    handler = K8sProbeHandler()

    l_res = handler.liveness_probe()
    assert l_res.status_code == 200
    assert l_res.status == "UP"

    r_res = handler.readiness_probe()
    assert r_res.status_code == 200
    assert r_res.status == "UP"

    handler.is_ready = False
    r_res_unready = handler.readiness_probe()
    assert r_res_unready.status_code == 503
    assert r_res_unready.status == "DOWN"

def test_sarathi_crd_generator():
    crd = SarathiCRDGenerator.generate_crd_spec("order_service", "sarathi/order_service:v1.2.0", replicas=3)
    assert crd["kind"] == "SarathiApp"
    assert crd["spec"]["replicas"] == 3
    assert crd["metadata"]["name"] == "order_service"

def test_service_mesh_header_extraction():
    headers = {
        "User-Agent": "Envoy/1.24",
        "X-Request-Id": "req_12345",
        "X-B3-TraceId": "4bf92f3577b34da6a3ce929d0e0e4736",
        "X-B3-SpanId": "00f067aa0ba902b7"
    }
    extracted = ServiceMeshContext.extract_mesh_headers(headers)
    assert extracted["x-request-id"] == "req_12345"
    assert extracted["x-b3-traceid"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert "user-agent" not in extracted
