import json

import httpx
import pytest
import respx

from tremendous_cve import cli
from tremendous_cve.generator import PageContent, Section
from tremendous_cve.nvd import CveData

CVE = CveData(
    cve_id="CVE-2021-44228",
    description="Log4j JNDI RCE",
    cvss_score=10.0,
    severity="CRITICAL",
)
CONTENT = PageContent(
    title="LOG4SHELL",
    tagline="Every JVM.",
    severity_gag="11/10",
    sections=[Section(heading="🚀", body="Big.")],
)


@pytest.fixture
def patched(monkeypatch):
    async def fake_fetch(cve_id):
        return CVE.model_copy(update={"cve_id": cve_id})

    async def fake_generate(cve, model, client):
        return CONTENT

    monkeypatch.setattr(cli, "fetch_cve", fake_fetch)
    monkeypatch.setattr(cli, "generate_content", fake_generate)
    monkeypatch.setattr(cli, "_anthropic_client", lambda: object())


class TestArgParsing:
    def test_accepts_nvd_url(self, patched, tmp_path):
        out = tmp_path / "page.html"
        rc = cli.main(
            ["generate", "https://nvd.nist.gov/vuln/detail/CVE-2021-44228", "--out", str(out)]
        )
        assert rc == 0
        assert "LOG4SHELL" in out.read_text()

    def test_rejects_garbage_cve(self, patched, capsys):
        rc = cli.main(["generate", "not-a-cve", "--out", "/dev/null"])
        assert rc != 0


class TestOutput:
    def test_out_writes_rendered_html(self, patched, tmp_path):
        out = tmp_path / "log4shell.html"
        cli.main(["generate", "CVE-2021-44228", "--out", str(out)])
        html = out.read_text()
        assert "LOG4SHELL" in html
        assert "nvd.nist.gov/vuln/detail/CVE-2021-44228" in html


class TestUpload:
    @respx.mock
    def test_upload_posts_expected_body(self, patched):
        route = respx.post("https://cve.example.com/pages").mock(
            return_value=httpx.Response(200, json={"cve_id": "CVE-2021-44228", "url": "/cve/x"})
        )
        rc = cli.main(
            [
                "generate",
                "CVE-2021-44228",
                "--upload",
                "--url",
                "https://cve.example.com",
                "--token",
                "secret",
            ]
        )
        assert rc == 0
        assert route.called
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer secret"
        body = json.loads(request.content)
        assert body["cve_id"] == "CVE-2021-44228"
        assert "LOG4SHELL" in body["html"]
        assert body["meta"]["title"] == "LOG4SHELL"
        assert body["meta"]["model"] == "sonnet"

    @respx.mock
    def test_model_flag_plumbed_through(self, patched):
        route = respx.post("https://cve.example.com/pages").mock(
            return_value=httpx.Response(200, json={"cve_id": "x", "url": "/cve/x"})
        )
        cli.main(
            [
                "generate",
                "CVE-2021-44228",
                "--upload",
                "--model",
                "opus",
                "--url",
                "https://cve.example.com",
                "--token",
                "secret",
            ]
        )
        body = json.loads(route.calls[0].request.content)
        assert body["meta"]["model"] == "opus"

    def test_upload_without_token_errors(self, patched, capsys):
        rc = cli.main(["generate", "CVE-2021-44228", "--upload", "--url", "https://x.example.com"])
        assert rc != 0
