# tremendous-cve 🚀👑

The HUGEST, most TREMENDOUS CVE pages in the history of computing. Probably ever.

Inspired by [bumsrake.de](https://bumsrake.de/), `tremendous-cve` takes a NIST NVD CVE
report (URL or bare CVE ID) and uses the Claude API to generate a satirical
product-launch page for it — hyperbolic campaign rhetoric on top, technically
accurate vulnerability detail underneath.

## How it works

1. `POST /generate` (bearer token) with an NVD URL or CVE ID
2. CVE data is fetched from the [NVD API 2.0](https://nvd.nist.gov/developers/vulnerabilities)
3. Claude writes the satire as structured JSON (default Sonnet, Opus selectable)
4. The page is rendered through Jinja2 templates and cached to disk
5. `GET /cve/{cve_id}` and the index at `/` serve the cached pages publicly

## Development

```sh
uv sync
uv run pytest
uv run ruff check
uv run pylint src/
uv run uvicorn tremendous_cve.main:app --reload
```

## Configuration

| Env var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `GENERATE_TOKEN` | Bearer token required by `POST /generate` |
| `DATA_DIR` | Where rendered pages/metadata are stored (default `/data`) |
| `DEFAULT_MODEL` | Default Claude model alias (default `sonnet`) |

## Disclaimer

The vulnerabilities are real. The merchandise is not. Every generated page links
back to the genuine NVD entry.
