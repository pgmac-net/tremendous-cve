from tremendous_cve.generator import FaqItem, MerchItem, PageContent, Section
from tremendous_cve.nvd import CveData
from tremendous_cve.render import PageStore, build_meta, render_index, render_page

CVE = CveData(
    cve_id="CVE-2026-45257",
    description="A kernel bug.",
    published="2026-05-01T10:00:00.000",
    cvss_score=8.8,
    severity="HIGH",
    cvss_vector="CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H",
    cwe_ids=["CWE-787"],
    affected=["cpe:2.3:o:freebsd:freebsd:13.0:*:*:*:*:*:*:*"],
    references=["https://example.com/advisory"],
)

CONTENT = PageContent(
    title="THE MOST TREMENDOUS KERNEL BUG",
    tagline="Nobody writes page caches like we do. Nobody.",
    severity_gag="14/10 OFF THE CHARTS",
    sections=[
        Section(
            heading="🚀 WHAT WE'RE LAUNCHING",
            body="The greatest write primitive.\n\nEveryone is talking about it.",
            code="root@freebsd # whoami",
        ),
        Section(heading="🔥 THE TECHNOLOGY", body="It uses sendfile. Bigly."),
    ],
    faq=[FaqItem(question="Is this real?", answer="Unfortunately, yes.")],
    merch=[MerchItem(item="Kernel Panic Mug", price="$13.37", status="SOLD OUT")],
)


class TestRenderPage:
    def test_contains_content_and_chrome(self):
        html = render_page(CONTENT, CVE)
        assert "THE MOST TREMENDOUS KERNEL BUG" in html
        assert "14/10 OFF THE CHARTS" in html
        assert "Comic Sans MS" in html
        assert "Kernel Panic Mug" in html
        assert "Is this real?" in html
        # footer must link to the real NVD entry
        assert "https://nvd.nist.gov/vuln/detail/CVE-2026-45257" in html

    def test_html_in_llm_output_escaped(self):
        evil = CONTENT.model_copy(
            update={"title": "<script>alert(1)</script>"}
        )
        html = render_page(evil, CVE)
        assert "<script>alert(1)</script>" not in html

    def test_section_code_block_rendered(self):
        html = render_page(CONTENT, CVE)
        assert "root@freebsd # whoami" in html


def meta_for(cve_id, generated_at=""):
    meta = build_meta(cve_id, CONTENT, CVE, "sonnet")
    return meta.model_copy(update={"generated_at": generated_at})


class TestBuildMeta:
    def test_fields_from_content_and_cve(self):
        meta = build_meta("CVE-2026-45257", CONTENT, CVE, "opus")
        assert meta.cve_id == "CVE-2026-45257"
        assert meta.title == CONTENT.title
        assert meta.severity_gag == CONTENT.severity_gag
        assert meta.cvss_score == 8.8
        assert meta.severity == "HIGH"
        assert meta.model == "opus"
        assert meta.generated_at  # populated at build time


class TestPageStore:
    def test_save_load_roundtrip(self, tmp_path):
        store = PageStore(tmp_path)
        store.save("CVE-2026-45257", "<html>page</html>", meta_for("CVE-2026-45257"))
        assert store.load_html("CVE-2026-45257") == "<html>page</html>"

    def test_save_fills_generated_at_when_blank(self, tmp_path):
        store = PageStore(tmp_path)
        store.save("CVE-2026-45257", "<html>x</html>", meta_for("CVE-2026-45257"))
        assert store.list_meta()[0]["generated_at"]

    def test_load_missing_returns_none(self, tmp_path):
        store = PageStore(tmp_path)
        assert store.load_html("CVE-1999-0001") is None

    def test_list_meta_newest_first(self, tmp_path):
        store = PageStore(tmp_path)
        store.save(
            "CVE-1999-0001", "<html>old</html>", meta_for("CVE-1999-0001", "2020-01-01T00:00:00Z")
        )
        store.save(
            "CVE-2026-45257", "<html>new</html>", meta_for("CVE-2026-45257", "2026-01-01T00:00:00Z")
        )
        metas = store.list_meta()
        assert len(metas) == 2
        assert metas[0]["cve_id"] == "CVE-2026-45257"
        assert metas[0]["title"] == CONTENT.title
        assert metas[0]["cvss_score"] == 8.8

    def test_exists(self, tmp_path):
        store = PageStore(tmp_path)
        assert not store.exists("CVE-2026-45257")
        store.save("CVE-2026-45257", "<html>x</html>", meta_for("CVE-2026-45257"))
        assert store.exists("CVE-2026-45257")


class TestRenderIndex:
    def test_lists_generated_pages(self, tmp_path):
        store = PageStore(tmp_path)
        store.save("CVE-2026-45257", "<html>x</html>", meta_for("CVE-2026-45257"))
        html = render_index(store.list_meta())
        assert "CVE-2026-45257" in html
        assert "THE MOST TREMENDOUS KERNEL BUG" in html
        assert "/cve/CVE-2026-45257" in html
