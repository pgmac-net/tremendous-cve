import pytest
from fastapi.testclient import TestClient

from tremendous_cve import main
from tremendous_cve.config import Settings

META = {
    "cve_id": "CVE-2021-44228",
    "title": "LOG4SHELL",
    "tagline": "Every JVM.",
    "severity_gag": "11/10",
    "cvss_score": 10.0,
    "severity": "CRITICAL",
    "model": "sonnet",
    "generated_at": "2026-06-13T00:00:00Z",
}
HTML = "<html><body>LOG4SHELL</body></html>"


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = Settings(upload_token="secret-token", data_dir=str(tmp_path))
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    return TestClient(main.create_app())


def _body(**overrides):
    body = {"cve_id": "CVE-2021-44228", "html": HTML, "meta": META}
    body.update(overrides)
    return body


class TestHealth:
    def test_healthz(self, client):
        assert client.get("/healthz").status_code == 200


class TestUploadAuth:
    def test_missing_token_rejected(self, client):
        resp = client.post("/pages", json=_body())
        assert resp.status_code == 401

    def test_wrong_token_rejected(self, client):
        resp = client.post("/pages", json=_body(), headers={"Authorization": "Bearer nope"})
        assert resp.status_code == 401

    def test_bad_cve_id_rejected(self, client):
        resp = client.post(
            "/pages",
            json=_body(cve_id="not a cve"),
            headers={"Authorization": "Bearer secret-token"},
        )
        assert resp.status_code == 422


class TestUploadFlow:
    def test_upload_then_serve_and_index(self, client):
        resp = client.post(
            "/pages",
            json=_body(cve_id="https://nvd.nist.gov/vuln/detail/CVE-2021-44228"),
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
        assert "LOG4SHELL" in index.text

    def test_reupload_overwrites(self, client):
        headers = {"Authorization": "Bearer secret-token"}
        client.post("/pages", json=_body(), headers=headers)
        updated = _body(html="<html>UPDATED</html>")
        client.post("/pages", json=updated, headers=headers)
        assert "UPDATED" in client.get("/cve/CVE-2021-44228").text


class TestServeMissing:
    def test_unknown_cve_404(self, client):
        assert client.get("/cve/CVE-1999-0001").status_code == 404

    def test_bad_cve_path_404(self, client):
        assert client.get("/cve/garbage").status_code == 404
