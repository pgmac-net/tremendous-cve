"""Local CLI: fetch a CVE, generate the satire with Claude, render, upload.

Run where you are authenticated to Claude (``ant auth login`` or
``ANTHROPIC_API_KEY``). The web app never calls Claude — it only serves
pages this CLI uploads.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import anthropic
import httpx

from tremendous_cve.generator import generate_content
from tremendous_cve.nvd import fetch_cve, parse_cve_id
from tremendous_cve.render import build_meta, render_page

DEFAULT_MODEL = os.environ.get("TREMENDOUS_CVE_MODEL", "sonnet")


def _anthropic_client() -> anthropic.AsyncAnthropic:
    # No args: resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an
    # `ant auth login` subscription profile from the environment.
    return anthropic.AsyncAnthropic()


def _upload(url: str, token: str, cve_id: str, html: str, meta) -> None:
    response = httpx.post(
        f"{url.rstrip('/')}/pages",
        headers={"Authorization": f"Bearer {token}"},
        json={"cve_id": cve_id, "html": html, "meta": meta.model_dump()},
        timeout=30,
    )
    response.raise_for_status()


async def _generate(cve_id: str, model: str) -> tuple[str, object]:
    cve = await fetch_cve(cve_id)
    content = await generate_content(cve, model, client=_anthropic_client())
    html = render_page(content, cve)
    meta = build_meta(cve_id, content, cve, model)
    return html, meta


def _run_generate(args: argparse.Namespace) -> int:
    try:
        cve_id = parse_cve_id(args.cve)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.upload:
        url = args.url or os.environ.get("TREMENDOUS_CVE_URL")
        token = args.token or os.environ.get("TREMENDOUS_CVE_TOKEN")
        if not url or not token:
            print(
                "error: --upload needs --url/--token (or TREMENDOUS_CVE_URL/_TOKEN)",
                file=sys.stderr,
            )
            return 2

    html, meta = asyncio.run(_generate(cve_id, args.model))

    if args.out:
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"wrote {args.out}")

    if args.upload:
        _upload(args.url or os.environ["TREMENDOUS_CVE_URL"],
                args.token or os.environ["TREMENDOUS_CVE_TOKEN"],
                cve_id, html, meta)
        print(f"uploaded {cve_id}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tremendous-cve", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate a satirical page for a CVE")
    gen.add_argument("cve", help="CVE ID or NVD URL")
    gen.add_argument("--model", default=DEFAULT_MODEL, choices=["sonnet", "opus"])
    gen.add_argument("--out", help="write rendered HTML to this path")
    gen.add_argument("--upload", action="store_true", help="upload to the web app")
    gen.add_argument("--url", help="web app base URL (or TREMENDOUS_CVE_URL)")
    gen.add_argument("--token", help="upload bearer token (or TREMENDOUS_CVE_TOKEN)")
    gen.set_defaults(func=_run_generate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
