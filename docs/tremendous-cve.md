# tremendous-cve

Satirical CVE page generator. Takes a NIST NVD CVE report (URL or bare CVE ID) and uses
the Claude API to produce a parody "product launch" page in the style of
[bumsrake.de](https://bumsrake.de/) — hyperbolic campaign rhetoric on top, technically
accurate vulnerability detail underneath.

## Architecture

```
POST /generate ──> parse CVE ID ──> NVD API 2.0 ──> Claude (JSON) ──> Jinja2 ──> /data
GET  /cve/{id} ──> serve cached HTML from /data
GET  /          ──> index of generated pages
```

The model returns **structured JSON** (title, tagline, sections, severity gag, FAQ, merch),
never raw HTML — keeping layout consistent and avoiding injection. All output is
auto-escaped by Jinja2. Every page footer links back to the genuine NVD entry with a
"this is satire but the vuln is real" disclaimer.

### Modules (`src/tremendous_cve/`)

| Module | Responsibility |
|---|---|
| `nvd.py` | CVE ID parsing (URL or bare ID) + NVD API 2.0 client with 403/429 retry |
| `generator.py` | `PageContent` schema, prompt assembly, Claude call, JSON validation |
| `render.py` | Jinja2 rendering + `PageStore` (HTML + metadata on disk) |
| `main.py` | FastAPI routes and bearer-token auth |
| `config.py` | Env-var settings |
| `styles/tremendous/` | Persona prompt + base/page/index templates |

The `styles/` package is structured so additional personas can be added later as a
`style` parameter.

## Routes

| Route | Auth | Behaviour |
|---|---|---|
| `GET /` | public | Index listing generated pages |
| `GET /cve/{cve_id}` | public | Serve cached page; 404 (in style) if not generated |
| `POST /generate` | Bearer token | `{"cve": "<url or id>", "model": "sonnet"\|"opus", "force": false}` |
| `GET /healthz` | public | Liveness/readiness |

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `GENERATE_TOKEN` | — | Bearer token required by `POST /generate` |
| `DATA_DIR` | `/data` | Storage for rendered pages + metadata |
| `DEFAULT_MODEL` | `sonnet` | Default model alias (`sonnet` → Sonnet 4.6, `opus` → Opus 4.8) |

## Local development

```sh
uv sync
uv run pytest
uv run ruff check
uv run pylint src/
ANTHROPIC_API_KEY=... GENERATE_TOKEN=dev DATA_DIR=./data \
  uv run uvicorn tremendous_cve.main:app --reload
curl -X POST localhost:8000/generate \
  -H "Authorization: Bearer dev" \
  -d '{"cve":"https://nvd.nist.gov/vuln/detail/CVE-2021-44228"}'
```

## Deployment

- **Image:** built in GitHub Actions (`.github/workflows/docker.yml`) via the pvek8s
  remote BuildKit endpoint, pushed to `macro.int.pgmac.net:5000/pg-tremendous-cve`.
- **Chart:** `chart/` — Deployment (1 replica, `Recreate` strategy because of RWO PVC),
  Service, Ingress, PVC (~1Gi), wired to an out-of-band Secret.
- **ArgoCD:** copy `deploy/argocd-application.yaml` into the pgk8s app-of-apps repo.
- **Secret:** create with `kubectl create secret generic tremendous-cve` (see
  `deploy/secret.example.yaml`).

### Public exposure

The app enforces bearer auth on `/generate` regardless of network exposure. To make the
read paths (`/`, `/cve/*`) public, add an ingress rule for the chosen hostname to the
"sab" Cloudflare tunnel in `terraform-cloudflare-config` (PGM-249).

## Disclaimer

The vulnerabilities are real and every page links to the official NVD entry. The
merchandise is not real. The satire is aimed at marketing bombast, never at victims.
