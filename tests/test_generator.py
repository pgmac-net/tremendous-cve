import json

import pytest

from tremendous_cve.generator import (
    MODEL_ALIASES,
    PageContent,
    build_prompt,
    generate_content,
    resolve_model,
)
from tremendous_cve.nvd import CveData

CVE = CveData(
    cve_id="CVE-2021-44228",
    description="JNDI features in Log4j allow remote code execution.",
    cvss_score=10.0,
    severity="CRITICAL",
    cwe_ids=["CWE-502"],
)

CONTENT_JSON = json.dumps(
    {
        "title": "LOG4SHELL: THE PEOPLE'S RCE",
        "tagline": "Every JVM. Tremendous reach.",
        "severity_gag": "11/10 PERFECT SCORE, MANY SAY HIGHER",
        "sections": [{"heading": "🚀 LAUNCH", "body": "The biggest logging event ever."}],
        "faq": [{"question": "Real?", "answer": "Yes."}],
        "merch": [{"item": "JNDI Lookup Tee", "price": "$44.22", "status": "SOLD OUT"}],
    }
)


class StubMessages:
    def __init__(self, text):
        self.text = text
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)

        class Block:
            def __init__(self, text):
                self.text = text

        class Response:
            def __init__(self, text):
                self.content = [Block(text)]

        return Response(self.text)


class StubClient:
    def __init__(self, text):
        self.messages = StubMessages(text)


class TestResolveModel:
    def test_aliases(self):
        assert resolve_model("sonnet") == MODEL_ALIASES["sonnet"]
        assert resolve_model("opus") == MODEL_ALIASES["opus"]

    def test_unknown_rejected(self):
        with pytest.raises(ValueError):
            resolve_model("gpt-7")


class TestBuildPrompt:
    def test_includes_cve_facts(self):
        prompt = build_prompt(CVE)
        assert "CVE-2021-44228" in prompt
        assert "JNDI" in prompt
        assert "10.0" in prompt


class TestGenerateContent:
    async def test_parses_json_response(self):
        client = StubClient(CONTENT_JSON)
        content = await generate_content(CVE, "sonnet", client=client)
        assert isinstance(content, PageContent)
        assert content.title == "LOG4SHELL: THE PEOPLE'S RCE"
        assert client.messages.calls[0]["model"] == MODEL_ALIASES["sonnet"]

    async def test_strips_markdown_fences(self):
        client = StubClient(f"```json\n{CONTENT_JSON}\n```")
        content = await generate_content(CVE, "sonnet", client=client)
        assert content.severity_gag.startswith("11/10")

    async def test_invalid_json_raises(self):
        client = StubClient("I refuse to answer in JSON")
        with pytest.raises(ValueError):
            await generate_content(CVE, "sonnet", client=client)
