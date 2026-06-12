"""Claude-powered satire generation: content schema and API client."""

import json
import re
from importlib import resources
from typing import Any

from pydantic import BaseModel, ValidationError

from tremendous_cve.nvd import CveData

MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}
MAX_TOKENS = 6000


class Section(BaseModel):
    heading: str
    body: str
    code: str | None = None


class FaqItem(BaseModel):
    question: str
    answer: str


class MerchItem(BaseModel):
    item: str
    price: str
    status: str = "SOLD OUT"


class PageContent(BaseModel):
    title: str
    tagline: str
    severity_gag: str
    sections: list[Section]
    faq: list[FaqItem] = []
    merch: list[MerchItem] = []


def resolve_model(alias: str) -> str:
    """Map a short model alias (sonnet/opus) to a full model ID."""
    try:
        return MODEL_ALIASES[alias]
    except KeyError as exc:
        raise ValueError(f"Unknown model alias: {alias!r}") from exc


def _system_prompt() -> str:
    return (
        resources.files("tremendous_cve.styles.tremendous")
        .joinpath("prompt.md")
        .read_text(encoding="utf-8")
    )


def build_prompt(cve: CveData) -> str:
    """Build the user prompt describing the CVE facts for the model."""
    lines = [
        f"CVE: {cve.cve_id}",
        f"Description: {cve.description}",
    ]
    if cve.cvss_score is not None:
        lines.append(f"CVSS base score: {cve.cvss_score} ({cve.severity})")
    if cve.cvss_vector:
        lines.append(f"CVSS vector: {cve.cvss_vector}")
    if cve.cwe_ids:
        lines.append(f"Weakness types: {', '.join(cve.cwe_ids)}")
    if cve.affected:
        lines.append(f"Affected products: {', '.join(cve.affected[:8])}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc


async def generate_content(cve: CveData, model: str, client: Any) -> PageContent:
    """Call Claude to produce satirical page content for a CVE."""
    response = await client.messages.create(
        model=resolve_model(model),
        max_tokens=MAX_TOKENS,
        system=_system_prompt(),
        messages=[{"role": "user", "content": build_prompt(cve)}],
    )
    raw = "".join(block.text for block in response.content if hasattr(block, "text"))
    data = _extract_json(raw)
    try:
        return PageContent.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Model JSON did not match the page schema: {exc}") from exc
