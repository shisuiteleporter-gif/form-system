import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import settings
from database import Form, get_session, generate_uuid

logger = logging.getLogger("form-system.forms")
router = APIRouter(prefix="/forms", tags=["Forms"])
templates = Jinja2Templates(directory=str(settings.templates_dir))
templates.env.globals["settings"] = settings


class FormSaveRequest(BaseModel):
    id: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    fields_schema: Any = []
    edocs_config: Any = {}


def _get_edocs_client():
    from services.edocs_service import edocs_service
    try:
        return edocs_service._ensure_client()
    except Exception:
        return None


@router.get("/")
async def list_forms(request: Request):
    session = get_session()
    try:
        forms = session.query(Form).order_by(Form.created_at.desc()).all()
        return templates.TemplateResponse("forms/list.html", {"request": request, "forms": forms})
    except Exception as e:
        logger.error(f"Erro ao listar formularios: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/novo")
async def new_form(request: Request):
    client = _get_edocs_client()
    patriarcas = []
    classes = []
    if client:
        try:
            patriarcas = client.agente.listar_patriarcas()
            if patriarcas:
                planos = client.classificacao.listar_planos_ativos(patriarcas[0]["id"])
                if planos:
                    classes = client.classificacao.listar_classes_ativas(planos[0]["id"])
        except Exception as e:
            logger.warning(f"Nao foi possivel carregar dados do E-Docs: {e}")
    return templates.TemplateResponse(
        "forms/builder.html",
        {"request": request, "form": None, "patriarcas": patriarcas, "classes": classes},
    )


@router.post("/salvar")
async def save_form(body: FormSaveRequest):
    if isinstance(body.fields_schema, str):
        body.fields_schema = json.loads(body.fields_schema)
    if isinstance(body.edocs_config, str):
        body.edocs_config = json.loads(body.edocs_config)

    session = get_session()
    try:
        if body.id:
            form = session.query(Form).filter(Form.id == body.id).first()
            if not form:
                raise HTTPException(status_code=404, detail="Formulario nao encontrado")
            form.name = body.name
            form.slug = body.slug
            form.description = body.description
            form.fields_schema = body.fields_schema
            form.edocs_config = body.edocs_config
        else:
            form = Form(
                name=body.name,
                slug=body.slug,
                description=body.description,
                fields_schema=body.fields_schema,
                edocs_config=body.edocs_config,
            )
            session.add(form)
        session.commit()
        session.refresh(form)
        return {"success": True, "id": form.id}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao salvar formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/{form_id}/editar")
async def edit_form(request: Request, form_id: str):
    session = get_session()
    try:
        form = session.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        client = _get_edocs_client()
        patriarcas = []
        classes = []
        if client:
            try:
                patriarcas = client.agente.listar_patriarcas()
                if patriarcas:
                    planos = client.classificacao.listar_planos_ativos(patriarcas[0]["id"])
                    if planos:
                        classes = client.classificacao.listar_classes_ativas(planos[0]["id"])
            except Exception:
                pass
        return templates.TemplateResponse(
            "forms/builder.html",
            {"request": request, "form": form, "patriarcas": patriarcas, "classes": classes},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao carregar formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/{form_id}")
async def view_form(request: Request, form_id: str):
    session = get_session()
    try:
        form = session.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        return templates.TemplateResponse(
            "forms/view.html",
            {"request": request, "form": form, "fields": form.fields_schema},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao visualizar formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{form_id}/duplicar")
async def duplicate_form(form_id: str):
    session = get_session()
    try:
        original = session.query(Form).filter(Form.id == form_id).first()
        if not original:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        new_slug = f"{original.slug}-copia-{uuid.uuid4().hex[:6]}"
        new_form = Form(
            name=f"{original.name} (Copia)",
            slug=new_slug,
            description=original.description,
            fields_schema=original.fields_schema,
            edocs_config=original.edocs_config,
        )
        session.add(new_form)
        session.commit()
        session.refresh(new_form)
        return {"success": True, "id": new_form.id}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao duplicar formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/{form_id}")
async def delete_form(form_id: str):
    session = get_session()
    try:
        form = session.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        session.delete(form)
        session.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao deletar formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
