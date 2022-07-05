from bevy import Context
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncEngine

from soc.apps.admin_app import admin_app
from soc.apps.api import api_app
from soc.apps.auth import auth_app
from soc.config.models.site import SiteSettings
from soc.context import create_app, create_context, inject
from soc.templates.jinja import Jinja2
from soc.templates.response import TemplateResponse

site = create_app()
site.mount("/v1/", api_app)
site.mount("/admin/", admin_app)
site.mount("/auth/", auth_app)
site.mount("/static", StaticFiles(directory="static"), name="static")


@site.on_event("startup")
async def on_start():
    context: Context = site.dependency_overrides.get(create_context, create_context)()
    settings = context.get(SiteSettings) or context.create(
        SiteSettings, add_to_context=True
    )
    if settings.dev:
        database = context.get(AsyncEngine)
        if not database:
            context.create(AsyncEngine)


@site.get("/", response_class=TemplateResponse)
async def index():
    return "index.html"


@site.get("/logout", response_class=HTMLResponse)
async def logout(template: Jinja2 = inject(Jinja2)):
    response = HTMLResponse(template("logout.html"))
    response.delete_cookie("sessionid")
    return response
