import json

import httpx
import pytest
import respx

from tremendous_cve.nvd import NVD_API_URL, fetch_cve, parse_cve_id


class TestParseCveId:
    def test_bare_cve_id(self):
        assert parse_cve_id("CVE-2026-45257") == "CVE-2026-45257"

    def test_lowercase_normalised(self):
        assert parse_cve_id("cve-2026-45257") == "CVE-2026-45257"

    def test_nvd_url(self):
        url = "https://nvd.nist.gov/vuln/detail/CVE-2026-45257"
        assert parse_cve_id(url) == "CVE-2026-45257"

    def test_nvd_url_with_query(self):
        url = "https://nvd.nist.gov/vuln/detail/CVE-2021-44228?vulnSource=mend"
        assert parse_cve_id(url) == "CVE-2021-44228"

    def test_short_sequence_number(self):
        assert parse_cve_id("CVE-1999-0001") == "CVE-1999-0001"

    def test_long_sequence_number(self):
        assert parse_cve_id("CVE-2024-1234567") == "CVE-2024-1234567"

    def test_surrounding_whitespace(self):
        assert parse_cve_id("  CVE-2026-45257\n") == "CVE-2026-45257"

    def test_garbage_rejected(self):
        with pytest.raises(ValueError):
            parse_cve_id("not a cve at all")

    def test_empty_rejected(self):
        with pytest.raises(ValueError):
            parse_cve_id("")

    def test_truncated_id_rejected(self):
        with pytest.raises(ValueError):
            parse_cve_id("CVE-2026")


NVD_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2026-45257",
                "published": "2026-05-01T10:00:00.000",
                "descriptions": [
                    {"lang": "en", "value": "A kernel bug in FreeBSD ktls allows writes."},
                    {"lang": "es", "value": "Un error del kernel."},
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "cvssData": {
                                "baseScore": 8.8,
                                "baseSeverity": "HIGH",
                                "vectorString": "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H",
                            }
                        }
                    ]
                },
                "weaknesses": [
                    {"description": [{"lang": "en", "value": "CWE-787"}]}
                ],
                "references": [
                    {"url": "https://www.freebsd.org/security/advisories/FreeBSD-SA-26:26.ktls.asc"}
                ],
                "configurations": [
                    {
                        "nodes": [
                            {
                                "cpeMatch": [
                                    {"criteria": "cpe:2.3:o:freebsd:freebsd:13.0:*:*:*:*:*:*:*"}
                                ]
                            }
                        ]
                    }
                ],
            }
        }
    ]
}


class TestFetchCve:
    @respx.mock
    async def test_parses_cve_data(self):
        respx.get(NVD_API_URL, params={"cveId": "CVE-2026-45257"}).respond(
            200, json=NVD_RESPONSE
        )
        cve = await fetch_cve("CVE-2026-45257")
        assert cve.cve_id == "CVE-2026-45257"
        assert cve.description == "A kernel bug in FreeBSD ktls allows writes."
        assert cve.cvss_score == 8.8
        assert cve.severity == "HIGH"
        assert cve.cvss_vector.startswith("CVSS:3.1/")
        assert cve.cwe_ids == ["CWE-787"]
        assert "freebsd" in cve.affected[0]
        assert cve.references[0].endswith(".asc")
        assert cve.published == "2026-05-01T10:00:00.000"

    @respx.mock
    async def test_unknown_cve_raises(self):
        respx.get(NVD_API_URL).respond(200, json={"vulnerabilities": []})
        with pytest.raises(LookupError):
            await fetch_cve("CVE-1900-99999")

    @respx.mock
    async def test_retries_on_429(self):
        route = respx.get(NVD_API_URL)
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(200, json=NVD_RESPONSE),
        ]
        cve = await fetch_cve("CVE-2026-45257", retry_delay=0)
        assert cve.cve_id == "CVE-2026-45257"

    @respx.mock
    async def test_missing_metrics_tolerated(self):
        stripped = json.loads(json.dumps(NVD_RESPONSE))
        stripped["vulnerabilities"][0]["cve"].pop("metrics")
        stripped["vulnerabilities"][0]["cve"].pop("weaknesses")
        stripped["vulnerabilities"][0]["cve"].pop("configurations")
        respx.get(NVD_API_URL).respond(200, json=stripped)
        cve = await fetch_cve("CVE-2026-45257")
        assert cve.cvss_score is None
        assert cve.severity is None
        assert cve.cwe_ids == []
        assert cve.affected == []
