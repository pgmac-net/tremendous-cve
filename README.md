# tremendous-cve 🚀👑

The HUGEST, most TREMENDOUS CVE pages in the history of computing. Probably ever.

Inspired by [bumsrake.de](https://bumsrake.de/), `tremendous-cve` takes a NIST NVD CVE
report (URL or bare CVE ID) and uses the Claude API to generate a satirical
product-launch page for it — hyperbolic campaign rhetoric on top, technically
accurate vulnerability detail underneath.

## How it works

Generation runs **locally** (where you're authenticated to Claude); the web app only
stores and serves what you upload — no Claude credentials in the cluster.

1. `tremendous-cve generate <CVE-or-NVD-URL>` fetches CVE data from the
   [NVD API 2.0](https://nvd.nist.gov/developers/vulnerabilities)
2. Claude writes the satire as structured JSON (default Sonnet, `--model opus` selectable)
3. The CLI renders the page through Jinja2 templates
4. `--out PATH` previews locally; `--upload` POSTs the HTML + metadata to the web app
5. The web app serves uploaded pages at `GET /cve/{cve_id}` and lists them at `/`

```sh
ant auth login            # one-time: use your Claude subscription
uv run tremendous-cve generate https://nvd.nist.gov/vuln/detail/CVE-2021-44228 \
  --out /tmp/log4shell.html                       # preview
uv run tremendous-cve generate CVE-2021-44228 \
  --upload --url https://tremendous-cve.int.pgmac.net --token "$TOKEN"
```

## Development

```sh
uv sync
uv run pytest
uv run ruff check
uv run pylint src/
uv run uvicorn tremendous_cve.main:app --reload    # the serve-only web app
```

## Configuration

### Web app (cluster)

| Env var | Purpose |
|---|---|
| `UPLOAD_TOKEN` | Bearer token required by `POST /pages` |
| `DATA_DIR` | Where uploaded pages/metadata are stored (default `/data`) |

### CLI (local)

| Env var / flag | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` / `ant auth login` | Claude auth (resolved by the SDK) |
| `--url` / `TREMENDOUS_CVE_URL` | Web app base URL for `--upload` |
| `--token` / `TREMENDOUS_CVE_TOKEN` | Upload bearer token (matches `UPLOAD_TOKEN`) |
| `--model` / `TREMENDOUS_CVE_MODEL` | Claude model alias (default `sonnet`) |

## Disclaimer

The vulnerabilities are real. The merchandise is not. Every generated page links
back to the genuine NVD entry.
