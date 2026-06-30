import logging

from fastapi import APIRouter, HTTPException

from services.edocs_service import edocs_service

logger = logging.getLogger("form-system.edocs")
router = APIRouter(prefix="/edocs", tags=["E-Docs"])


def _get_client():
    client = edocs_service._ensure_client()
    if not client:
        raise HTTPException(status_code=503, detail="E-Docs nao disponivel")
    return client


@router.get("/status")
async def check_status():
    try:
        return edocs_service.get_status()
    except Exception as e:
        logger.error(f"Erro ao verificar status do E-Docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patriarcas")
async def list_patriarcas():
    try:
        client = _get_client()
        data = client.agente.listar_patriarcas()
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar patriarcas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patriarca_id}/organizacoes")
async def list_orgaos(patriarca_id: str):
    try:
        client = _get_client()
        data = client.agente.listar_organizacoes(patriarca_id)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar orgaos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/setores/{orgao_id}")
async def list_setores(orgao_id: str):
    try:
        client = _get_client()
        data = client.agente.listar_setores(orgao_id)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar setores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/planos/{patriarca_id}")
async def list_planos(patriarca_id: str):
    try:
        client = _get_client()
        data = client.classificacao.listar_planos_ativos(patriarca_id)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar planos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classes/{plano_id}")
async def list_classes_documentais(plano_id: str):
    try:
        client = _get_client()
        data = client.classificacao.listar_classes_ativas(plano_id)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar classes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papeis")
async def list_papeis():
    try:
        client = _get_client()
        data = client.consultas.papeis_usuario()
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar papeis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/caixas/{caixa_id}/papeis")
async def list_papeis_por_caixa(caixa_id: str):
    try:
        client = _get_client()
        data = client.consultas.papeis_para_encaminhamento(caixa_id)
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar papeis da caixa: {e}")
        raise HTTPException(status_code=500, detail=str(e))
