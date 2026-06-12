"""NVD CVE ID parsing and API client."""

import asyncio
import re
from typing import Any

import httpx
from pydantic import BaseModel

CVE_ID_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAX_ATTEMPTS = 4


def parse_cve_id(text: str) -> str:
    """Extract a CVE ID from a bare ID or an NVD URL. Raises ValueError if none found."""
    match = CVE_ID_PATTERN.search(text)
    if not match:
        raise ValueError(f"No CVE ID found in input: {text!r}")
    return match.group(0).upper()


class CveData(BaseModel):
    cve_id: str
    description: str
    published: str | None = None
    cvss_score: float | None = None
    severity: str | None = None
    cvss_vector: str | None = None
    cwe_ids: list[str] = []
    affected: list[str] = []
    references: list[str] = []


def _english_description(cve: dict[str, Any]) -> str:
    for desc in cve.get("descriptions", []):
        if desc.get("lang") == "en":
            return desc["value"]
    return ""


def _cvss(cve: dict[str, Any]) -> dict[str, Any]:
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if entries:
            return entries[0].get("cvssData", {})
    return {}


def _cwe_ids(cve: dict[str, Any]) -> list[str]:
    found: list[str] = []
    for weakness in cve.get("weaknesses", []):
        for desc in weakness.get("description", []):
            value = desc.get("value", "")
            if value.startswith("CWE-") and value not in found:
                found.append(value)
    return found


def _affected(cve: dict[str, Any]) -> list[str]:
    criteria: list[str] = []
    for config in cve.get("configurations", []):
        for node in config.get("nodes", []):
            for match in node.get("cpeMatch", []):
                value = match.get("criteria")
                if value and value not in criteria:
                    criteria.append(value)
    return criteria


def _parse_cve(cve: dict[str, Any]) -> CveData:
    cvss = _cvss(cve)
    return CveData(
        cve_id=cve["id"],
        description=_english_description(cve),
        published=cve.get("published"),
        cvss_score=cvss.get("baseScore"),
        severity=cvss.get("baseSeverity"),
        cvss_vector=cvss.get("vectorString"),
        cwe_ids=_cwe_ids(cve),
        affected=_affected(cve),
        references=[ref["url"] for ref in cve.get("references", []) if "url" in ref],
    )


async def fetch_cve(cve_id: str, retry_delay: float = 6.0) -> CveData:
    """Fetch CVE details from the NVD API 2.0, retrying on rate limits."""
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(MAX_ATTEMPTS):
            response = await client.get(NVD_API_URL, params={"cveId": cve_id})
            if response.status_code in (403, 429) and attempt < MAX_ATTEMPTS - 1:
                await asyncio.sleep(retry_delay)
                continue
            response.raise_for_status()
            break
        vulnerabilities = response.json().get("vulnerabilities", [])
        if not vulnerabilities:
            raise LookupError(f"{cve_id} not found in NVD")
        return _parse_cve(vulnerabilities[0]["cve"])
