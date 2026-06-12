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
ant auth login            # one-time: use your Claude subscription (see CLI auth below)
uv run tremendous-cve generate https://nvd.nist.gov/vuln/detail/CVE-2021-44228 \
  --out /tmp/log4shell.html                       # preview
uv run tremendous-cve generate CVE-2021-44228 \
  --upload --url https://tremendous-cve.int.pgmac.net --token "$TOKEN"
```

## CLI authentication

The CLI calls Claude with a no-args `anthropic.AsyncAnthropic()`, which resolves
credentials from the environment — `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or an
`ant auth login` profile. If you have an API key, just export it and skip `ant`.

`ant` is the **Anthropic CLI** — a separate binary, not bundled with the `anthropic`
Python SDK or Claude Code. The repo's `mise.toml` already pins it (along with `python` and
`uv`), so the simplest path is:

```sh
mise trust && mise install   # installs python, uv, and ant
ant auth login               # browser OAuth; profile under ~/.config/anthropic/
ant auth status              # confirm which credential/workspace won
```

Without mise, install `ant` directly:

```sh
# Linux
VERSION=$(curl -fsSL https://api.github.com/repos/anthropics/anthropic-cli/releases/latest \
  | grep -o '"tag_name": *"v[^"]*"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
curl -fsSL "https://github.com/anthropics/anthropic-cli/releases/download/v${VERSION}/ant_${VERSION}_$(uname -s | tr A-Z a-z)_$(uname -m | sed -e s/x86_64/amd64/ -e s/aarch64/arm64/).tar.gz" \
  | sudo tar -xz -C /usr/local/bin ant

# macOS
brew install anthropics/tap/ant && xattr -d com.apple.quarantine "$(brew --prefix)/bin/ant"

# from source (Go 1.22+)
go install github.com/anthropics/anthropic-cli/cmd/ant@latest
```

Caveats:

- **Subscription OAuth may not grant API (`/v1/messages`) access.** It works for Claude
  Code, but API message calls over a subscription token are gated by the
  `oauth-2025-04-20` beta and aren't guaranteed for every tier. If `generate` returns
  401/403 after a successful `ant auth login`, your subscription lacks API access — use a
  real `ANTHROPIC_API_KEY`, or a Bedrock/Vertex backend, instead.
- **A stale exported `ANTHROPIC_API_KEY` silently overrides the profile.** `ant auth
  status` shows which source won; `unset ANTHROPIC_API_KEY` if a profile login "doesn't
  take."

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
