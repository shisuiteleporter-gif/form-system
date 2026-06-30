"""
Servico de integracao com o E-Docs.
Faz a ponte entre as submissoes do formulario e a API do E-Docs.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger("form-system.edocs")


class EDocsService:
    """
    Wrapper para operacoes com o E-Docs.
    Usa o client edocs_api quando as credenciais estao configuradas.
    """

    def __init__(self):
        self._client = None
        self._initialized = False
        self._init_error = None

    def _ensure_client(self):
        """Inicializa o client E-Docs se possivel."""
        if self._initialized:
            return self._client

        self._initialized = True

        if not settings.edocs_configured:
            self._init_error = "E-Docs nao configurado (faltam client_id/client_secret)"
            logger.warning(self._init_error)
            return None

        try:
            from edocs_api import EDocsClient, EDocsConfig

            config = EDocsConfig(
                client_id=settings.edocs_client_id,
                client_secret=settings.edocs_client_secret,
                ambiente=settings.edocs_ambiente,  # type: ignore
                scope=settings.edocs_scope,
            )
            self._client = EDocsClient(config)
            logger.info("Cliente E-Docs inicializado com sucesso.")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"Erro ao inicializar cliente E-Docs: {e}")
            return None

        return self._client

    @property
    def is_available(self) -> bool:
        """Verifica se o E-Docs esta configurado e acessivel."""
        client = self._ensure_client()
        return client is not None

    def get_status(self) -> dict:
        """Retorna status da integracao."""
        client = self._ensure_client()
        if client is None:
            return {
                "configured": False,
                "connected": False,
                "error": self._init_error or "Nao configurado",
            }
        try:
            # Teste simples: consultar patriarcas
            client.agente.listar_patriarcas()
            return {"configured": True, "connected": True, "error": None}
        except Exception as e:
            return {"configured": True, "connected": False, "error": str(e)}

    # ── Operacoes principais ─────────────────────────────────

    def enviar_documento(
        self,
        pdf_path: str | Path,
        id_papel: str,
        id_classe_documental: str,
        resumo: str,
        submitter_info: dict | None = None,
        restricao_acesso: dict | None = None,
    ) -> dict:
        """
        Envia um PDF para o E-Docs: upload + captura.

        Returns:
            dict com resultado da operacao
        """
        client = self._ensure_client()
        if not client:
            return {"success": False, "error": "E-Docs nao disponivel"}

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {"success": False, "error": f"PDF nao encontrado: {pdf_path}"}

        log = []
        resultado = {"success": True}

        try:
            # Passo 1: Upload do arquivo
            logger.info(f"Fazendo upload do arquivo: {pdf_path}")
            tamanho = os.path.getsize(pdf_path)
            upload_data = client.documentos.gerar_url_upload(tamanho)
            client.documentos.enviar_arquivo(upload_data, str(pdf_path))
            id_arquivo = upload_data["idArquivo"]
            log.append({"etapa": "upload", "status": "ok", "id_arquivo": id_arquivo})
            resultado["id_arquivo"] = id_arquivo

            # Passo 2: Captura do documento (assinatura do capturador)
            logger.info(f"Capturando documento com idArquivo: {id_arquivo}")
            captura = client.documentos.enviar_como_servidor(
                id_arquivo=id_arquivo,
                id_papel=id_papel,
                id_classe_documental=id_classe_documental,
                resumo=resumo[:500],
                restricao_acesso=restricao_acesso,
            )

            id_evento = captura.get("idEvento")
            if not id_evento:
                raise RuntimeError(f"Resposta de captura sem idEvento: {captura}")

            log.append({"etapa": "captura", "status": "enfileirado", "id_evento": id_evento})
            resultado["id_evento"] = id_evento

            # Passo 3: Aguardar processamento
            logger.info(f"Aguardando evento {id_evento}...")
            evento = client.aguardar_evento(id_evento, timeout=120)
            log.append({"etapa": "evento", "status": evento.get("status"), "evento": evento})

            id_documento = evento.get("idDocumento")
            if not id_documento:
                raise RuntimeError(f"Evento sem idDocumento: {evento}")

            resultado["id_documento"] = id_documento
            resultado["success"] = True
            log.append({"etapa": "documento_criado", "status": "ok", "id_documento": id_documento})

        except Exception as e:
            logger.error(f"Erro ao enviar documento para E-Docs: {e}")
            resultado["success"] = False
            resultado["error"] = str(e)
            log.append({"etapa": "erro", "status": "erro", "mensagem": str(e)})

        resultado["log"] = log
        return resultado

    def autuar_processo(
        self,
        id_papel_autuador: str,
        id_classe_documental: str,
        resumo: str,
        documentos: list[str] | None = None,
        interessados: list[dict] | None = None,
    ) -> dict:
        """
        Autua um processo no E-Docs com documentos previamente capturados.
        """
        client = self._ensure_client()
        if not client:
            return {"success": False, "error": "E-Docs nao disponivel"}

        log = []
        resultado = {"success": True}

        try:
            id_evento = client.processos.autuar(
                id_papel_autuador=id_papel_autuador,
                id_classe_documental=id_classe_documental,
                resumo=resumo,
                documentos=documentos,
                interessados=interessados,
            )
            log.append({"etapa": "autuar", "status": "enfileirado", "id_evento": id_evento})
            resultado["id_evento"] = id_evento

            evento = client.aguardar_evento(id_evento, timeout=120)
            log.append({"etapa": "evento_processo", "status": evento.get("status")})

            id_processo = evento.get("idProcesso")
            if id_processo:
                resultado["id_processo"] = id_processo
            else:
                resultado["id_processo"] = evento.get("idProcesso")

        except Exception as e:
            logger.error(f"Erro ao autuar processo: {e}")
            resultado["success"] = False
            resultado["error"] = str(e)
            log.append({"etapa": "erro", "status": "erro", "mensagem": str(e)})

        resultado["log"] = log
        return resultado

    def criar_encaminhamento(
        self,
        id_papel_remetente: str,
        destinatarios: list[dict],
        assunto: str,
        mensagem: str,
        documentos: list[str] | None = None,
    ) -> dict:
        """Cria um encaminhamento no E-Docs."""
        client = self._ensure_client()
        if not client:
            return {"success": False, "error": "E-Docs nao disponivel"}

        log = []
        resultado = {"success": True}

        try:
            id_evento = client.encaminhamentos.novo(
                id_papel_remetente=id_papel_remetente,
                destinatarios=destinatarios,
                assunto=assunto,
                mensagem=mensagem,
                documentos=documentos,
            )
            log.append({"etapa": "encaminhamento", "status": "enfileirado", "id_evento": id_evento})
            resultado["id_evento"] = id_evento

            evento = client.aguardar_evento(id_evento, timeout=120)
            log.append({"etapa": "evento_enc", "status": evento.get("status")})
            resultado["id_encaminhamento"] = evento.get("idEncaminhamento")

        except Exception as e:
            logger.error(f"Erro ao criar encaminhamento: {e}")
            resultado["success"] = False
            resultado["error"] = str(e)
            log.append({"etapa": "erro", "status": "erro", "mensagem": str(e)})

        resultado["log"] = log
        return resultado


# Instancia global
edocs_service = EDocsService()
