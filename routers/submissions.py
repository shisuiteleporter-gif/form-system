import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import settings
from database import Form, Submission, SubmissionStatus, get_session, generate_uuid
from services.edocs_service import edocs_service
from services.pdf_generator import pdf_generator

logger = logging.getLogger("form-system.submissions")
router = APIRouter(prefix="/submissions", tags=["Submissions"])
templates = Jinja2Templates(directory=str(settings.templates_dir))
templates.env.globals["settings"] = settings


class SubmitRequest(BaseModel):
    data: dict = {}
    submitter_name: Optional[str] = None
    submitter_email: Optional[str] = None
    submitter_cpf: Optional[str] = None


@router.get("/")
async def list_submissions(
    request: Request,
    form_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    session = get_session()
    try:
        query = session.query(Submission).join(Form)
        if form_id:
            query = query.filter(Submission.form_id == form_id)
        if status:
            query = query.filter(Submission.status == status)
        total = query.count()
        submissions = (
            query.order_by(Submission.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        total_pages = max(1, (total + per_page - 1) // per_page)
        return templates.TemplateResponse(
            "submissions/list.html",
            {
                "request": request,
                "submissions": submissions,
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "form_id": form_id,
                "status": status,
            },
        )
    except Exception as e:
        logger.error(f"Erro ao listar submissoes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{form_id}/submit")
async def submit_form(form_id: str, body: SubmitRequest):
    session = get_session()
    try:
        form = session.query(Form).filter(Form.id == form_id).first()
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        if not form.is_active:
            raise HTTPException(status_code=400, detail="Formulario inativo")

        protocol = f"FORMS-{datetime.now():%Y%m%d}-{str(uuid.uuid4())[:8].upper()}"

        submission = Submission(
            form_id=form.id,
            data=body.data,
            submitter_name=body.submitter_name,
            submitter_email=body.submitter_email,
            submitter_cpf=body.submitter_cpf,
            status=SubmissionStatus.SUBMITTED,
            protocol=protocol,
            submitted_at=datetime.now(),
        )
        session.add(submission)
        session.commit()
        session.refresh(submission)

        try:
            pdf_filename = f"{submission.id}.pdf"
            pdf_path = settings.pdf_path / pdf_filename
            submitter_info = {
                "name": body.submitter_name,
                "email": body.submitter_email,
                "cpf": body.submitter_cpf,
            }
            pdf_generator.generate(
                form_name=form.name,
                form_description=form.description or "",
                fields_schema=form.fields_schema,
                submission_data=body.data,
                protocol=protocol,
                submitter_info=submitter_info,
                output_path=pdf_path,
            )
            submission.pdf_path = str(pdf_path)
            submission.status = SubmissionStatus.PDF_GENERATED
            session.commit()

            edocs_config = form.edocs_config or {}
            if edocs_config.get("auto_submit"):
                _send_to_edocs(session, submission, form)

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            submission.status = SubmissionStatus.ERROR
            submission.error_message = f"Erro ao gerar PDF: {str(e)}"
            session.commit()

        return {"success": True, "id": submission.id, "protocol": protocol}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao submeter formulario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


def _send_to_edocs(session, submission, form):
    try:
        submission.status = SubmissionStatus.PROCESSING
        session.commit()

        edocs_config = form.edocs_config or {}
        doc_config = edocs_config.get("document", {})

        if not submission.pdf_path or not Path(submission.pdf_path).exists():
            raise RuntimeError("PDF nao encontrado para envio ao E-Docs")

        result = edocs_service.enviar_documento(
            pdf_path=submission.pdf_path,
            id_papel=doc_config.get("id_papel", ""),
            id_classe_documental=doc_config.get("classe_documental_id", ""),
            resumo=f"{form.name} - {submission.protocol}",
            submitter_info={
                "name": submission.submitter_name,
                "email": submission.submitter_email,
                "cpf": submission.submitter_cpf,
            },
            restricao_acesso=doc_config.get("restricao_acesso"),
        )

        submission.edocs_log = (submission.edocs_log or []) + result.get("log", [])

        if not result.get("success"):
            raise RuntimeError(result.get("error", "Erro desconhecido no E-Docs"))

        submission.edocs_id_arquivo = result.get("id_arquivo")
        submission.edocs_id_documento = result.get("id_documento")
        submission.edocs_id_evento = result.get("id_evento")
        submission.status = SubmissionStatus.SENT_TO_EDOCS

        process_config = edocs_config.get("process", {})
        if process_config.get("autuar") and submission.edocs_id_documento:
            assunto = process_config.get(
                "assunto_template", f"Formulario: {form.name}"
            ).replace("{{ form_name }}", form.name)
            proc_result = edocs_service.autuar_processo(
                id_papel_autuador=process_config.get(
                    "id_papel_autuador", doc_config.get("id_papel", "")
                ),
                id_classe_documental=process_config.get("classe_documental_id", ""),
                resumo=assunto,
                documentos=[submission.edocs_id_documento],
                interessados=None,
            )
            submission.edocs_log = (submission.edocs_log or []) + proc_result.get("log", [])
            if proc_result.get("success"):
                submission.edocs_id_processo = proc_result.get("id_processo")
                submission.status = SubmissionStatus.COMPLETED
            else:
                submission.edocs_error = proc_result.get("error")
                submission.status = SubmissionStatus.ERROR
                logger.error(f"Erro ao autuar processo: {proc_result.get('error')}")
        else:
            submission.status = SubmissionStatus.COMPLETED

        session.commit()

    except Exception as e:
        logger.error(f"Erro ao enviar para E-Docs: {e}")
        submission.status = SubmissionStatus.ERROR
        submission.edocs_error = str(e)
        submission.edocs_log = (submission.edocs_log or []) + [
            {"etapa": "envio_edocs", "status": "erro", "mensagem": str(e)}
        ]
        session.commit()


@router.get("/{submission_id}")
async def view_submission(request: Request, submission_id: str):
    session = get_session()
    try:
        submission = session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submissao nao encontrada")
        return templates.TemplateResponse(
            "submissions/detail.html",
            {"request": request, "submission": submission},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao carregar submissao: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.get("/{submission_id}/pdf")
async def download_pdf(submission_id: str):
    session = get_session()
    try:
        submission = session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submissao nao encontrada")
        if not submission.pdf_path or not Path(submission.pdf_path).exists():
            raise HTTPException(status_code=404, detail="PDF nao encontrado")
        return FileResponse(
            submission.pdf_path,
            media_type="application/pdf",
            filename=f"{submission.protocol or submission.id}.pdf",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao baixar PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{submission_id}/enviar-edocs")
async def send_to_edocs(submission_id: str):
    session = get_session()
    try:
        submission = session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submissao nao encontrada")
        form = submission.form
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        _send_to_edocs(session, submission, form)
        return {"success": True, "status": submission.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar para E-Docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.post("/{submission_id}/reenviar")
async def resend_to_edocs(submission_id: str):
    session = get_session()
    try:
        submission = session.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submissao nao encontrada")
        form = submission.form
        if not form:
            raise HTTPException(status_code=404, detail="Formulario nao encontrado")
        submission.edocs_error = None
        submission.status = SubmissionStatus.PDF_GENERATED
        session.commit()
        _send_to_edocs(session, submission, form)
        return {"success": True, "status": submission.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reenviar para E-Docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
