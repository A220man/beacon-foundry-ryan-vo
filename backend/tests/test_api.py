import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.core.security import generate_demo_token
from app.core.config import settings

@pytest.fixture
def app_instance():
    return create_app()

@pytest.mark.asyncio
async def test_health_check(app_instance):
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "beacon-foundry"
        assert data["version"] == "1.0.0"

@pytest.mark.asyncio
async def test_auth_config(app_instance):
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get("/api/auth/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["keycloak_realm"] == "beacon-realm"
        assert data["keycloak_client_id"] == "beacon-client"

@pytest.mark.asyncio
async def test_demo_login_and_token_exchange(app_instance):
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post("/api/auth/demo-login")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "flight-analyst"
        assert "viewer" in data["roles"]

@pytest.mark.asyncio
async def test_unauthenticated_rejection(app_instance):
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get("/api/v1/agc/programs")
        assert resp.status_code == 401
        assert "Missing Authorization" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_token_rejection(app_instance):
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/agc/programs",
            headers={"Authorization": "Bearer invalid-dummy-token"}
        )
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_role_based_access_denial(app_instance):
    # Issue token with only 'viewer' role
    viewer_token = generate_demo_token("user-viewer", "viewer-only", ["viewer"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        # Operator endpoint should reject viewer
        resp = await client.post(
            "/api/v1/agc/proof",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"transcription_text": "CA TIME1"}
        )
        assert resp.status_code == 403
        assert "Insufficient permissions" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_authenticated_programs_flow(app_instance):
    token = generate_demo_token("user-viewer", "viewer", ["viewer"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/agc/programs",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        programs = resp.json()["programs"]
        assert len(programs) >= 2
        prog_id = programs[0]["id"]

        detail_resp = await client.get(
            f"/api/v1/agc/programs/{prog_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert "instructions" in detail
        assert detail["source_lines_count"] > 0

@pytest.mark.asyncio
async def test_program_not_found(app_instance):
    token = generate_demo_token("user-viewer", "viewer", ["viewer"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/agc/programs/non-existent-program-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 404

@pytest.mark.asyncio
async def test_proof_execution_endpoint(app_instance):
    op_token = generate_demo_token("user-op", "operator", ["operator"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agc/proof",
            headers={"Authorization": f"Bearer {op_token}"},
            json={"transcription_text": "CA TIME1\nTC CHECKTIM\nCCS WAITEXIT"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PASSED"
        assert data["quality_score"] == 1.0
        assert len(data["discrepancies"]) == 0

@pytest.mark.asyncio
async def test_proof_discrepancy_detection(app_instance):
    op_token = generate_demo_token("user-op", "operator", ["operator"])
    corrupted = "CA TIME1\nTX_ILLEGAL CHECKTIM\nTS"
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agc/proof",
            headers={"Authorization": f"Bearer {op_token}"},
            json={"transcription_text": corrupted}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "DISCREPANCIES_DETECTED"
        assert len(data["discrepancies"]) >= 2

@pytest.mark.asyncio
async def test_trajectory_simulation_nominal(app_instance):
    op_token = generate_demo_token("user-op", "operator", ["operator"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trajectory/simulate",
            headers={"Authorization": f"Bearer {op_token}"},
            json={"burn_program": "P63_BRAKING", "duration_s": 25, "simulate_thruster_failure": False}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["anomaly_detected"] is False
        assert len(data["trajectory"]) == 25
        assert data["delta_v_total"] > 0

@pytest.mark.asyncio
async def test_trajectory_simulation_failure_injection(app_instance):
    op_token = generate_demo_token("user-op", "operator", ["operator"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trajectory/simulate",
            headers={"Authorization": f"Bearer {op_token}"},
            json={"burn_program": "P63_BRAKING", "duration_s": 30, "simulate_thruster_failure": True}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["anomaly_detected"] is True
        assert any(t["anomaly_flag"] for t in data["trajectory"])

@pytest.mark.asyncio
async def test_ml_benchmark_evaluation(app_instance):
    token = generate_demo_token("user-viewer", "viewer", ["viewer"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/evaluation/benchmark",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_samples"] == 40
        assert data["embedding_metrics"]["f1_score"] > 0.8
        assert data["baseline_metrics"]["f1_score"] > 0.7

@pytest.mark.asyncio
async def test_opt_in_advisory_offline_fallback(app_instance):
    op_token = generate_demo_token("user-op", "operator", ["operator"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/advisory/explain",
            headers={"Authorization": f"Bearer {op_token}"},
            json={
                "context_type": "PROOFING_DISCREPANCY",
                "details": {"line": 12, "opcode": "TX_ILLEGAL"},
                "user_query": "Explain opcode error"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "offline-deterministic"
        assert "advisory-offline" in data["confidence_assessment"]

@pytest.mark.asyncio
async def test_audit_log_query(app_instance):
    admin_token = generate_demo_token("user-admin", "admin", ["admin"])
    async with AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
