
import pytest
from fastapi.testclient import TestClient

from tremendous_cve import main
from tremendous_cve.config import Settings
from tremendous_cve.generator import PageContent
from tremendous_cve.nvd import CveData

CONTENT = PageContent(
    title="LOG4SHELL",
    tagline="Every JVM.",
    severity_gag="11/10",
    sections=[],
)
CVE = CveData(
    cve_id="CVE-2021-44228", description="Log4j RCE", cvss_score=10.0, severity="CRITICAL"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = Settings(
        anthropic_api_key="test-key",
        generate_token="secret-token",
        data_dir=str(tmp_path),
        default_model="sonnet",
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    async def fake_fetch(cve_id):
        return CVE.model_copy(update={"cve_id": cve_id})

    async def fake_generate(cve, model, client):
        return CONTENT

    monkeypatch.setattr(main, "fetch_cve", fake_fetch)
    monkeypatch.setattr(main, "generate_content", fake_generate)
    monkeypatch.setattr(main, "_anthropic_client", lambda key: object())
    return TestClient(main.create_app())


class TestHealth:
    def test_healthz(self, client):
        assert client.get("/healthz").status_code == 200


class TestGenerateAuth:
    def test_missing_token_rejected(self, client):
        resp = client.post("/generate", json={"cve": "CVE-2021-44228"})
        assert resp.status_code == 401

    def test_wrong_token_rejected(self, client):
        resp = client.post(
            "/generate",
            json={"cve": "CVE-2021-44228"},
            headers={"Authorization": "Bearer nope"},
        )
        assert resp.status_code == 401

    def test_bad_cve_input_rejected(self, client):
        resp = client.post(
            "/generate",
            json={"cve": "not a cve"},
            headers={"Authorization": "Bearer secret-token"},
        )
        assert resp.status_code == 422


class TestGenerateFlow:
    def test_generate_then_serve(self, client):
        resp = client.post(
            "/generate",
            json={"cve": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"},
            headers={"Authorization": "Bearer secret-token"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["cve_id"] == "CVE-2021-44228"
        assert body["url"] == "/cve/CVE-2021-44228"

        page = client.get("/cve/CVE-2021-44228")
        assert page.status_code == 200
        assert "LOG4SHELL" in page.text

        index = client.get("/")
        assert "CVE-2021-44228" in index.text

    def test_cached_not_regenerated(self, client, monkeypatch):
        headers = {"Authorization": "Bearer secret-token"}
        client.post("/generate", json={"cve": "CVE-2021-44228"}, headers=headers)

        async def boom(cve, model, client):
            raise AssertionError("should not regenerate when cached")

        monkeypatch.setattr(main, "generate_content", boom)
        resp = client.post("/generate", json={"cve": "CVE-2021-44228"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

    def test_force_regenerates(self, client, monkeypatch):
        headers = {"Authorization": "Bearer secret-token"}
        client.post("/generate", json={"cve": "CVE-2021-44228"}, headers=headers)
        resp = client.post(
            "/generate",
            json={"cve": "CVE-2021-44228", "force": True},
            headers=headers,
        )
        assert resp.json()["cached"] is False


class TestServeMissing:
    def test_unknown_cve_404(self, client):
        assert client.get("/cve/CVE-1999-0001").status_code == 404

    def test_bad_cve_path_404(self, client):
        assert client.get("/cve/garbage").status_code == 404
