---
name: tremendous-cve
description: Translate a NIST NVD CVE report into a satirical "product launch" page in the TREMENDOUS style (bombastic campaign-rally / infomercial parody over accurate vulnerability detail), write it as a Jekyll markdown page in this repo, and open a PR. Use when the operator asks to "tremendous-ify", "translate a CVE", or runs this skill, optionally with a NIST NVD URL.
---

# tremendous-cve — CVE → satirical Jekyll page

Turn a real CVE into a parody product-launch page for the tremendous-cve Jekyll site
(https://tremendous-cve.pgmac.net.au). Run this from inside the `tremendous-cve` repo.

## Inputs

The operator supplies a **NIST NVD URL** (e.g. `https://nvd.nist.gov/vuln/detail/CVE-2021-44228`)
or a bare CVE ID. **If no URL/ID was provided, ask the operator for one before doing anything
else** — do not guess a CVE.

## Steps

1. **Resolve the CVE ID.** Extract `CVE-\d{4}-\d{4,}` from the input (uppercase it). If the
   input has no CVE ID, stop and ask the operator.

2. **Fetch the real CVE data.** Use WebFetch. Prefer the NVD API 2.0:
   `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<CVE-ID>`. If that is unhelpful,
   fall back to the human page `https://nvd.nist.gov/vuln/detail/<CVE-ID>`. Extract:
   - English description
   - CVSS base score, severity, and vector string (prefer v3.1/v4)
   - CWE id(s)
   - published date
   - reference URLs (keep the most authoritative 3–8)
   - affected products (CPE), if useful for jokes
   If the CVE genuinely cannot be found, tell the operator and stop.

3. **Write the satire** in the TREMENDOUS persona (see Voice below). Keep every technical
   claim accurate — the comedy comes from bombast wrapped around a correct mechanism.

4. **Create the page** at `_cves/<CVE-ID>.md` with YAML front matter + a markdown body
   matching the schema below. Do not overwrite an existing file without the operator's OK.

5. **Open a PR.** Never commit to `main`.
   ```sh
   git checkout -b add/<cve-id-lowercase>
   git add _cves/<CVE-ID>.md
   git commit -m "Add <CVE-ID> — <title>"
   git push -u origin add/<cve-id-lowercase>
   gh pr create --base main --title "Add <CVE-ID> — <title>" \
     --body "Tremendous-ifies <CVE-ID>. Merging to main deploys it to GitHub Pages."
   ```
   Report the PR URL and note that **merging to `main` publishes the page** (GitHub Actions
   builds the Jekyll site and deploys to Pages).

## Page schema (`_cves/<CVE-ID>.md`)

```yaml
---
layout: cve
cve_id: CVE-XXXX-XXXXX
title: "SHORT ALL-CAPS PRODUCT NAME"
tagline: "one punchy sentence under the title"
severity_gag: "a joke rating that beats 10/10, e.g. 13/10 OFF THE CHARTS"
cvss_score: 0.0            # omit if NVD has none
severity: CRITICAL         # HIGH | MEDIUM | LOW | CRITICAL; omit if none
cvss_vector: "CVSS:3.1/..."  # omit if none
cwe: ["CWE-XXX"]           # omit if none
published: "YYYY-MM-DD"    # omit if unknown
nvd_url: "https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXXX"
references:
  - "https://..."
faq:
  - q: "..."
    a: "..."
merch:
  - { item: "...", price: "...", status: "SOLD OUT" }
---
## 🚀 WHAT WE'RE LAUNCHING
1–3 short paragraphs of bombastic launch hype.

## 🔥 HOW IT WORKS (100% REAL)
An accurate explanation of the mechanism, told in the persona. Reference the real component
and bug class.

## 🛡️ THE FIX NOBODY WANTS TO TALK ABOUT
The real remediation, grudgingly.
```

The body is the prose only (markdown `##` sections, optional fenced code blocks). The layout
renders the banner, severity box, facts table (from front matter), FAQ, merch, and the
"satire but the vuln is real" footer — so do **not** hand-write those in the body.

## Voice

- Bombastic, hyperbolic, SUPERLATIVE-heavy: the BIGGEST, the HUGEST, the MOST TREMENDOUS bug
  anyone has ever seen. Many people are saying it. Frequent ALL-CAPS. Self-aware about its
  own bombast ("nobody writes deserialization bugs like this, nobody").
- Treat the vulnerability as a glorious product being launched, not a problem.
- It is funny precisely BECAUSE the technical detail is correct. Get the mechanism, the
  affected component, and the CWE right. Never invent CVE facts — only embellish tone.
- Punch at the absurdity, never at real victims. No slurs, no real living people by name, no
  politics beyond the rally cadence. Keep it about the bug.
- Aim for 3–5 body sections, 2–5 FAQ items, 2–5 merch items. One section must accurately
  explain how the vulnerability works.

See `reference/tremendous-style/` for the original persona prompt and the page styling this
site is descended from.
