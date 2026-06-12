"""Jinja2 rendering and on-disk page storage."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from tremendous_cve.generator import PageContent
from tremendous_cve.nvd import CveData

_env = Environment(
    loader=PackageLoader("tremendous_cve", "styles/tremendous"),
    autoescape=select_autoescape(["html", "j2"]),
)


def render_page(content: PageContent, cve: CveData) -> str:
    """Render a generated CVE page through the tremendous style template."""
    template = _env.get_template("page.html.j2")
    return template.render(
        content=content,
        cve=cve,
        nvd_url=f"https://nvd.nist.gov/vuln/detail/{cve.cve_id}",
    )


def render_index(metas: list[dict[str, Any]]) -> str:
    """Render the index page listing all generated CVE pages."""
    template = _env.get_template("index.html.j2")
    return template.render(metas=metas)


class PageStore:
    """Stores rendered HTML pages and their metadata under a data directory."""

    def __init__(self, data_dir: str | Path):
        self.pages_dir = Path(data_dir) / "pages"
        self.meta_dir = Path(data_dir) / "meta"
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def save(self, cve_id: str, html: str, content: PageContent, cve: CveData) -> None:
        (self.pages_dir / f"{cve_id}.html").write_text(html)
        meta = {
            "cve_id": cve_id,
            "title": content.title,
            "tagline": content.tagline,
            "severity_gag": content.severity_gag,
            "cvss_score": cve.cvss_score,
            "severity": cve.severity,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        (self.meta_dir / f"{cve_id}.json").write_text(json.dumps(meta))

    def exists(self, cve_id: str) -> bool:
        return (self.pages_dir / f"{cve_id}.html").exists()

    def load_html(self, cve_id: str) -> str | None:
        path = self.pages_dir / f"{cve_id}.html"
        return path.read_text() if path.exists() else None

    def list_meta(self) -> list[dict[str, Any]]:
        metas = [json.loads(path.read_text()) for path in self.meta_dir.glob("CVE-*.json")]
        return sorted(metas, key=lambda meta: meta["generated_at"], reverse=True)
