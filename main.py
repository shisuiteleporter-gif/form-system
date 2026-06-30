import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from database import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("form-system")

app = FastAPI(title="FormSystem - E-Docs")

templates_dir = settings.templates_dir
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))
templates.env.globals["settings"] = settings

static_dir = settings.static_dir
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Banco de dados inicializado")


from routers import edocs, forms, submissions

app.include_router(forms.router)
app.include_router(submissions.router)
app.include_router(edocs.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/forms")
