"""FastAPI application: store and serve satirical CVE pages.

Generation happens in the CLI (tremendous_cve.cli); this app only accepts
uploaded pages and serves them. No Claude dependency, no API key.
"""

import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator

from tremendous_cve.config import Settings, get_settings
from tremendous_cve.nvd import parse_cve_id
from tremendous_cve.render import PageMeta, PageStore, render_index


class UploadRequest(BaseModel):
    cve_id: str
    html: str
    meta: PageMeta

    @field_validator("cve_id")
    @classmethod
    def _valid_cve(cls, value: str) -> str:
        return parse_cve_id(value)


def _require_token(settings: Settings, authorization: str | None) -> None:
    expected = settings.upload_token
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

    @application.post("/pages")
    async def upload(
        request: UploadRequest,
        authorization: str | None = Header(default=None),
    ) -> JSONResponse:
        settings = get_settings()
        _require_token(settings, authorization)
        cve_id = request.cve_id
        PageStore(settings.data_dir).save(cve_id, request.html, request.meta)
        return JSONResponse({"cve_id": cve_id, "url": f"/cve/{cve_id}"})

    return application


app = create_app()
