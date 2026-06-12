"""FastAPI application: generate and serve satirical CVE pages."""

import secrets
from typing import Literal

import anthropic
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator

from tremendous_cve.config import Settings, get_settings
from tremendous_cve.generator import generate_content
from tremendous_cve.nvd import fetch_cve, parse_cve_id
from tremendous_cve.render import PageStore, render_index, render_page


class GenerateRequest(BaseModel):
    cve: str
    model: Literal["sonnet", "opus"] | None = None
    force: bool = False

    @field_validator("cve")
    @classmethod
    def _valid_cve(cls, value: str) -> str:
        return parse_cve_id(value)


def _anthropic_client(api_key: str) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=api_key)


def _require_token(settings: Settings, authorization: str | None) -> None:
    expected = settings.generate_token
    provided = ""
    if authorization and authorization.startswith("Bearer "):
        provided = authorization.removeprefix("Bearer ")
    if not expected or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


def create_app() -> FastAPI:
    application = FastAPI(title="tremendous-cve")

    def store() -> PageStore:
        return PageStore(get_settings().data_dir)

    @application.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "tremendous"}

    @application.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(render_index(store().list_meta()))

    @application.get("/cve/{cve_id}", response_class=HTMLResponse)
    async def serve(cve_id: str) -> HTMLResponse:
        try:
            normalised = parse_cve_id(cve_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Not a CVE ID") from exc
        html = store().load_html(normalised)
        if html is None:
            raise HTTPException(status_code=404, detail=f"{normalised} not launched yet")
        return HTMLResponse(html)

    @application.post("/generate")
    async def generate(
        request: GenerateRequest,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        settings = get_settings()
        _require_token(settings, authorization)
        cve_id = request.cve
        pages = PageStore(settings.data_dir)

        if pages.exists(cve_id) and not request.force:
            return JSONResponse(
                {"cve_id": cve_id, "url": f"/cve/{cve_id}", "cached": True}
            )

        cve = await fetch_cve(cve_id)
        model = request.model or settings.default_model
        client = _anthropic_client(settings.anthropic_api_key)
        content = await generate_content(cve, model, client=client)
        html = render_page(content, cve)
        pages.save(cve_id, html, content, cve)
        return JSONResponse(
            {"cve_id": cve_id, "url": f"/cve/{cve_id}", "cached": False}
        )

    return application


app = create_app()
