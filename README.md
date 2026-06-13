# tremendous-cve 🚀👑

The HUGEST, most TREMENDOUS CVE pages in the history of computing. Probably ever.

Inspired by [bumsrake.de](https://bumsrake.de/), this is a [Jekyll](https://jekyllrb.com/)
site of satirical "product launch" pages for real CVEs — bombastic campaign-rally hype on
top, technically accurate vulnerability detail underneath. Published to GitHub Pages at
**https://tremendous-cve.pgmac.net.au**.

## How it works

```
operator → tremendous-cve skill (with a NIST NVD URL)
  → Claude WebFetches the CVE, writes _cves/CVE-XXXX-XXXXX.md in the TREMENDOUS style
  → opens a PR
  → you merge to main
  → GitHub Actions builds the Jekyll site → Pages artifact → deploys
  → https://tremendous-cve.pgmac.net.au/cve/CVE-XXXX-XXXXX/
```

There is no server and no API key. Generation is done **manually** by running the
[Claude Skill](.claude/skills/tremendous-cve/SKILL.md) inside this repo; the operator's own
Claude session does the writing.

## Adding a CVE

Run the `tremendous-cve` skill (Claude Code: ask Claude to use it, or invoke it directly)
and give it a NIST NVD URL or CVE ID:

```
use the tremendous-cve skill on https://nvd.nist.gov/vuln/detail/CVE-2021-44228
```

If you don't supply a URL, the skill prompts for one. It writes `_cves/<CVE-ID>.md`, opens a
PR, and tells you the PR URL. Merge it to publish.

## Repo layout

| Path | Purpose |
|---|---|
| `.claude/skills/tremendous-cve/SKILL.md` | The translator skill (persona + steps) |
| `_cves/*.md` | One satirical page per CVE (front matter + prose) |
| `_layouts/{default,cve,home}.html` | Page chrome, CVE page, catalog |
| `assets/css/style.scss` | The tremendous styling (Comic Sans, gold/red/blue) |
| `index.html` | The satirical product catalog |
| `_config.yml`, `Gemfile`, `CNAME` | Jekyll config, gems, custom domain |
| `.github/workflows/pages.yml` | Build + deploy to GitHub Pages |
| `reference/tremendous-style/` | Original Jinja2 templates + persona prompt (reference) |

## Local preview

```sh
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

## Custom domain

`CNAME` pins `tremendous-cve.pgmac.net.au`. DNS is a Cloudflare `CNAME →
pgmac-net.github.io` record (DNS-only / not proxied, so GitHub Pages can issue its
certificate), managed in the `terraform-cloudflare-config` repo.

## Disclaimer

The vulnerabilities are real and every page links to the official NVD entry. The
merchandise is not real. The satire targets marketing bombast, never victims.
