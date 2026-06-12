# tremendous-cve

Satirical CVE page generator. Takes a NIST NVD CVE report (URL or bare CVE ID) and uses
the Claude API to produce a parody "product launch" page in the style of
[bumsrake.de](https://bumsrake.de/) — hyperbolic campaign rhetoric on top, technically
accurate vulnerability detail underneath.

## Architecture (split: local CLI + serve-only web app)

Generation runs **locally**, where the operator is authenticated to Claude. The web app
holds no Claude credentials — it only stores and serves uploaded pages. This keeps a
short-lived subscription token (or any API key) out of the cluster entirely.

```
LOCAL (authenticated to Claude):
  tremendous-cve generate <CVE>
    → NVD API 2.0 fetch → Claude (structured JSON) → Jinja2 render → HTML
    → --out (preview)  and/or  --upload → POST /pages

CLUSTER (no Claude credentials):
  GET /              index of uploaded pages
  GET /cve/{cve_id}  serve a stored page
  POST /pages        bearer-token upload (HTML + meta)
  GET /healthz       liveness/readiness
```

The model returns **structured JSON** (title, tagline, sections, severity gag, FAQ, merch),
never raw HTML — keeping layout consistent and avoiding injection. Output is auto-escaped
by Jinja2. Every page footer links the genuine NVD entry with a "satire but real vuln"
disclaimer.

### Modules (`src/tremendous_cve/`)

| Module | Responsibility | Used by |
|---|---|---|
| `nvd.py` | CVE ID parsing + NVD API 2.0 client (403/429 retry) | CLI |
| `generator.py` | `PageContent` schema, prompt, Claude JSON call, validation | CLI |
| `render.py` | Jinja2 rendering, `PageMeta`/`build_meta`, on-disk `PageStore` | CLI + web |
| `cli.py` | `tremendous-cve generate` — fetch → generate → render → upload | CLI |
| `main.py` | FastAPI store-and-serve routes + bearer auth | web |
| `config.py` | Web app env settings (`UPLOAD_TOKEN`, `DATA_DIR`) | web |
| `styles/tremendous/` | Persona prompt + base/page/index templates | CLI + web |

The `styles/` package is structured so additional personas can be added later.

## CLI

```sh
ant auth login   # one-time; uses your Claude subscription
tremendous-cve generate <CVE-or-NVD-URL> [--model sonnet|opus] [--out PATH] \
    [--upload --url <base> --token <token>]
```

The Claude client is constructed with no arguments, so the SDK resolves
`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or an `ant auth login` profile from the
environment. `--upload` reads `--url`/`--token` or `TREMENDOUS_CVE_URL`/`TREMENDOUS_CVE_TOKEN`.

## Web app routes

| Route | Auth | Behaviour |
|---|---|---|
| `GET /` | public | Index listing uploaded pages |
| `GET /cve/{cve_id}` | public | Serve a stored page; 404 (in style) if absent |
| `POST /pages` | Bearer token | `{cve_id, html, meta}` — store an uploaded page |
| `GET /healthz` | public | Liveness/readiness |

## Configuration

### Web app

| Env var | Default | Purpose |
|---|---|---|
| `UPLOAD_TOKEN` | — | Bearer token required by `POST /pages` |
| `DATA_DIR` | `/data` | Storage for uploaded pages + metadata |

### CLI

| Env var / flag | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` / `ant auth login` | Claude auth (resolved by the SDK) |
| `--url` / `TREMENDOUS_CVE_URL` | Web app base URL for `--upload` |
| `--token` / `TREMENDOUS_CVE_TOKEN` | Upload bearer token (matches `UPLOAD_TOKEN`) |
| `--model` / `TREMENDOUS_CVE_MODEL` | Claude model alias (default `sonnet`) |

## Deployment

- **Image:** built in GitHub Actions (`.github/workflows/docker.yml`) via the pvek8s
  remote BuildKit endpoint, pushed to `macro.int.pgmac.net:5000/pg-tremendous-cve`.
  One image; the CLI is run locally, not in-cluster.
- **Chart:** `chart/` — Deployment (1 replica, `Recreate` strategy because of RWO PVC),
  Service, Ingress, PVC (~1Gi), wired to an out-of-band Secret holding only `UPLOAD_TOKEN`.
- **ArgoCD:** copy `deploy/argocd-application.yaml` into the pgk8s app-of-apps repo.
- **Secret:** `kubectl create secret generic tremendous-cve --from-literal=UPLOAD_TOKEN=...`
  (see `deploy/secret.example.yaml`).

### Public exposure

`POST /pages` enforces bearer auth regardless of network exposure. To make the read paths
(`/`, `/cve/*`) public, add an ingress rule for the chosen hostname to the "sab" Cloudflare
tunnel in `terraform-cloudflare-config` (PGM-249).

## Disclaimer

The vulnerabilities are real and every page links to the official NVD entry. The
merchandise is not real. The satire is aimed at marketing bombast, never at victims.
