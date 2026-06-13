# tremendous-cve

Satirical CVE page generator in the style of [bumsrake.de](https://bumsrake.de/). A Jekyll
site of parody "product launch" pages for real CVEs, published to GitHub Pages at
**https://tremendous-cve.pgmac.net.au**.

## Architecture (Claude Skill → Jekyll → GitHub Pages)

There is no running application and no API key. Translation is performed **manually** by an
operator running a Claude Skill inside this repo; the operator's own Claude session writes
the page. The repo is a static Jekyll site that GitHub Actions builds and deploys to Pages.

```
operator runs the tremendous-cve skill (with a NIST NVD URL)
  → Claude: WebFetch NVD CVE data -> write _cves/CVE-XXXX-XXXXX.md (front matter + prose)
  → git branch + PR
  → operator merges to main
  → GitHub Actions (pages.yml): jekyll build -> Pages artifact -> deploy-pages
  → https://tremendous-cve.pgmac.net.au/cve/CVE-XXXX-XXXXX/
```

Why this shape: the operator has no Anthropic API key (subscription OAuth doesn't reliably
grant `/v1/messages`), so a programmatic generator isn't viable. A skill run in an
already-authenticated Claude session sidesteps that entirely, and a static site removes all
hosting/secret concerns.

## The skill (`.claude/skills/tremendous-cve/SKILL.md`)

Steps Claude follows:

1. Take a NIST NVD URL / CVE ID from the invocation; **if none, prompt the operator**.
2. Resolve the CVE ID (`CVE-\d{4}-\d{4,}`, uppercased).
3. WebFetch the CVE data — NVD API 2.0
   (`https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<id>`), falling back to the
   detail page: description, CVSS score/vector/severity, CWE(s), references, published date.
4. Write the satire in the TREMENDOUS persona (bombast over accurate mechanism; punch at
   bombast, not victims).
5. Create `_cves/<CVE-ID>.md` (front matter + markdown body).
6. Branch, commit, push, open a PR with `gh`; report the PR URL.

The persona is descended from `reference/tremendous-style/prompt.md`.

## Page format

Front matter carries metadata and the structured gags; the body is prose. The `cve` layout
renders the chrome:

```yaml
---
layout: cve
cve_id: CVE-2021-44228
title: "LOG4SHELL"
tagline: "Every JVM on Earth. Tremendous reach."
severity_gag: "11/10 PERFECT SCORE"
cvss_score: 10.0
severity: CRITICAL
cvss_vector: "CVSS:3.1/..."
cwe: ["CWE-502"]
published: "2021-12-10"
nvd_url: "https://nvd.nist.gov/vuln/detail/CVE-2021-44228"
references: ["https://logging.apache.org/log4j/2.x/security.html"]
faq:
  - { q: "Is this real?", a: "Unfortunately, yes." }
merch:
  - { item: "JNDI Lookup Tee", price: "$44.22", status: "SOLD OUT" }
---
## 🚀 WHAT WE'RE LAUNCHING
...prose...
```

`_layouts/cve.html` renders: banner (title + tagline), severity-gag box, the prose body, a
facts table (CVSS/vector/CWE/published + NVD link), FAQ, merch, and the "satire but the vuln
is real" footer. `index.html` (`home` layout) loops `site.cves` as the product catalog.

## Styling

`assets/css/style.scss` — Comic Sans, gold `#FFD700` / red `#DC143C` / blue `#003F7F`, dashed
gold borders, rotated severity box, merch table. A direct port of the original Jinja2
templates kept in `reference/tremendous-style/`.

## Build & deploy (`.github/workflows/pages.yml`)

GitHub-hosted (`ubuntu-latest`), triggered on push to `main` (and `workflow_dispatch`):

- **build:** `actions/configure-pages` → `actions/jekyll-build-pages` → `actions/upload-pages-artifact`
- **deploy:** `actions/deploy-pages` into the `github-pages` environment

One-time: enable Pages with build type `workflow`
(`gh api repos/pgmac-net/tremendous-cve/pages -X POST -f build_type=workflow`).

## Custom domain

- `CNAME` file: `tremendous-cve.pgmac.net.au`.
- DNS: a Cloudflare `cloudflare_dns_record` (provider v5) `CNAME tremendous-cve →
  pgmac-net.github.io`, **DNS-only / not proxied** so GitHub Pages can issue its Let's
  Encrypt certificate. Managed in `terraform-cloudflare-config`.

## Local preview

```sh
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

## Disclaimer

The vulnerabilities are real and every page links to the official NVD entry. The
merchandise is not real. The satire targets marketing bombast, never victims.
