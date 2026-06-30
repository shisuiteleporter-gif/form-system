"""
Servico de geracao de PDF a partir dos dados do formulario.
Usa ReportLab para criar documentos com layout profissional.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import settings

# Tenta registrar fontes com suporte a acentos
_FONTS_REGISTERED = False

def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    try:
        # Tenta fontes comuns do Windows com suporte a PT-BR
        font_dirs = [
            "C:/Windows/Fonts",
            "/usr/share/fonts",
            "/usr/local/share/fonts",
        ]
        for fd in font_dirs:
            if os.path.exists(fd):
                for fname in ["arial.ttf", "arialbd.ttf", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]:
                    fpath = os.path.join(fd, fname)
                    if os.path.exists(fpath):
                        pdfmetrics.registerFont(TTFont(fname.replace(".ttf", ""), fpath))
        _FONTS_REGISTERED = True
    except Exception:
        pass


class PDFGenerator:
    """Gera PDFs estilizados a partir de dados de formulario."""

    MARGIN_LEFT = 25 * mm
    MARGIN_RIGHT = 25 * mm
    MARGIN_TOP = 20 * mm
    MARGIN_BOTTOM = 20 * mm

    def __init__(self):
        _register_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Configura estilos personalizados."""
        font_name = "arial" if "arial" in [pdfmetrics.getRegisteredFontNames()] else "Helvetica"
        font_bold = "arialbd" if "arialbd" in [pdfmetrics.getRegisteredFontNames()] else "Helvetica-Bold"

        self.styles.add(ParagraphStyle(
            "HeaderTitle", parent=self.styles["Heading1"],
            fontName=font_name, fontSize=20, leading=24,
            spaceAfter=6, alignment=TA_CENTER,
            textColor=colors.HexColor("#1a237e"),
        ))
        self.styles.add(ParagraphStyle(
            "HeaderSub", parent=self.styles["Normal"],
            fontName=font_name, fontSize=10, leading=14,
            spaceAfter=20, alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
        ))
        self.styles.add(ParagraphStyle(
            "SectionTitle", parent=self.styles["Heading2"],
            fontName=font_bold, fontSize=13, leading=16,
            spaceBefore=14, spaceAfter=8,
            textColor=colors.HexColor("#1a237e"),
            borderWidth=0, borderPadding=0,
        ))
        self.styles.add(ParagraphStyle(
            "FieldLabel", parent=self.styles["Normal"],
            fontName=font_bold, fontSize=9, leading=11,
            textColor=colors.HexColor("#444444"),
            spaceBefore=6, spaceAfter=1,
        ))
        self.styles.add(ParagraphStyle(
            "FieldValue", parent=self.styles["Normal"],
            fontName=font_name, fontSize=11, leading=15,
            textColor=colors.HexColor("#000000"),
            spaceBefore=0, spaceAfter=8,
            leftIndent=4,
        ))
        self.styles.add(ParagraphStyle(
            "Footer", parent=self.styles["Normal"],
            fontName=font_name, fontSize=7, leading=9,
            textColor=colors.HexColor("#999999"),
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "Protocolo", parent=self.styles["Normal"],
            fontName=font_bold, fontSize=14, leading=18,
            alignment=TA_CENTER, spaceBefore=6, spaceAfter=4,
            textColor=colors.HexColor("#c62828"),
        ))
        self.styles.add(ParagraphStyle(
            "InfoLabel", parent=self.styles["Normal"],
            fontName=font_bold, fontSize=9, leading=11,
            textColor=colors.HexColor("#555555"),
            spaceBefore=2, spaceAfter=1,
        ))
        self.styles.add(ParagraphStyle(
            "InfoValue", parent=self.styles["Normal"],
            fontName=font_name, fontSize=10, leading=14,
            textColor=colors.HexColor("#000000"),
            spaceBefore=0, spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            "ResumoField", parent=self.styles["Normal"],
            fontName=font_name, fontSize=11, leading=15,
            textColor=colors.HexColor("#000000"),
            spaceBefore=2, spaceAfter=6,
            alignment=TA_JUSTIFY,
        ))

    def _field_value_text(self, field_def: dict, value: Any) -> str:
        """Formata o valor do campo para exibicao no PDF."""
        if value is None or value == "":
            return "<i>(nao preenchido)</i>"

        field_type = field_def.get("type", "text")

        if field_type == "checkbox" and isinstance(value, list):
            return "; ".join(str(v) for v in value)
        elif field_type == "select" and isinstance(value, dict):
            return value.get("label", str(value.get("value", "")))
        elif field_type == "radio" and isinstance(value, dict):
            return value.get("label", str(value.get("value", "")))
        elif field_type == "file":
            return f"[Arquivo: {value}]"
        elif field_type == "date":
            try:
                d = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return d.strftime("%d/%m/%Y")
            except (ValueError, AttributeError):
                return str(value)
        elif field_type == "cpf":
            v = str(value).zfill(11)
            return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
        elif field_type == "cnpj":
            v = str(value).zfill(14)
            return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
        elif field_type == "currency":
            try:
                return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (ValueError, TypeError):
                return str(value)

        return str(value)

    def generate(
        self,
        form_name: str,
        form_description: str,
        fields_schema: list[dict],
        submission_data: dict,
        protocol: str,
        submitter_info: dict | None = None,
        output_path: str | Path | None = None,
    ) -> bytes | str:
        """
        Gera o PDF do formulario preenchido.

        Args:
            form_name: Nome do formulario
            form_description: Descricao
            fields_schema: Schema dos campos
            submission_data: Dados preenchidos {field_id: value}
            protocol: Numero de protocolo da submissao
            submitter_info: Dict com name, email, cpf
            output_path: Caminho para salvar (se None, retorna bytes)

        Returns:
            bytes do PDF ou string do caminho do arquivo
        """
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                leftMargin=self.MARGIN_LEFT,
                rightMargin=self.MARGIN_RIGHT,
                topMargin=self.MARGIN_TOP,
                bottomMargin=self.MARGIN_BOTTOM,
                title=f"{form_name} - {protocol}",
                author="Sistema de Formularios E-Docs",
            )
        else:
            from io import BytesIO
            buf = BytesIO()
            doc = SimpleDocTemplate(
                buf, pagesize=A4,
                leftMargin=self.MARGIN_LEFT, rightMargin=self.MARGIN_RIGHT,
                topMargin=self.MARGIN_TOP, bottomMargin=self.MARGIN_BOTTOM,
            )

        elements = []

        # ── Cabecalho ──
        elements.append(Paragraph(form_name, self.styles["HeaderTitle"]))
        if form_description:
            elements.append(Paragraph(form_description, self.styles["HeaderSub"]))

        # Linha horizontal
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#1a237e"),
            spaceAfter=12, spaceBefore=4,
        ))

        # ── Protocolo e metadados ──
        elements.append(Paragraph(f"Protocolo: {protocol}", self.styles["Protocolo"]))
        elements.append(Spacer(1, 4))

        now_str = datetime.now().strftime("%d/%m/%Y as %H:%M")
        elements.append(Paragraph(
            f"Gerado em: {now_str}",
            self.styles["HeaderSub"]
        ))
        elements.append(Spacer(1, 8))

        # ── Dados do Submissor ──
        if submitter_info:
            elements.append(Paragraph("Dados do Submissor", self.styles["SectionTitle"]))
            info_data = []
            if submitter_info.get("name"):
                info_data.append([Paragraph("Nome:", self.styles["InfoLabel"]),
                                  Paragraph(submitter_info["name"], self.styles["InfoValue"])])
            if submitter_info.get("email"):
                info_data.append([Paragraph("E-mail:", self.styles["InfoLabel"]),
                                  Paragraph(submitter_info["email"], self.styles["InfoValue"])])
            if submitter_info.get("cpf"):
                info_data.append([Paragraph("CPF:", self.styles["InfoLabel"]),
                                  Paragraph(submitter_info["cpf"], self.styles["InfoValue"])])
            if info_data:
                info_table = Table(info_data, colWidths=[50*mm, 120*mm])
                info_table.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]))
                elements.append(info_table)
                elements.append(Spacer(1, 6))

        # ── Campos do Formulario ──
        elements.append(Paragraph("Dados do Formulario", self.styles["SectionTitle"]))
        elements.append(Spacer(1, 4))

        # Agrupar campos por secao (se houver)
        sections: dict[str, list] = {"__default__": []}
        for field in fields_schema:
            section = field.get("section", "__default__")
            if section not in sections:
                sections[section] = []
            sections[section].append(field)

        ordered_fields = []
        for section_name, section_fields in sections.items():
            if section_name != "__default__":
                ordered_fields.append(("__section__", section_name))
            for f in section_fields:
                ordered_fields.append(("__field__", f))

        # Ordenar por sort_order
        def _get_sort(item):
            if item[0] == "__section__":
                return -1
            return item[1].get("sort_order", 999)

        ordered_fields.sort(key=_get_sort)

        for item_type, item_data in ordered_fields:
            if item_type == "__section__":
                elements.append(Paragraph(item_data, self.styles["SectionTitle"]))
                continue

            field = item_data
            field_id = field.get("id", "")
            field_label = field.get("label", "Campo sem nome")
            field_type = field.get("type", "text")
            value = submission_data.get(field_id)

            # Pular campos de tipo "file" (nao podemos incluir o arquivo no PDF)
            if field_type == "file":
                continue

            elements.append(Paragraph(field_label, self.styles["FieldLabel"]))
            text_value = self._field_value_text(field, value)
            elements.append(Paragraph(text_value, self.styles["FieldValue"]))

        # ── Rodape ──
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4))
        elements.append(Paragraph(
            f"Documento gerado eletronicamente pelo Sistema de Formularios E-Docs em {now_str}."
            f"<br/>Protocolo: {protocol}",
            self.styles["Footer"],
        ))

        doc.build(elements)

        if output_path:
            return str(output_path)
        return buf.getvalue()


# Instancia global
pdf_generator = PDFGenerator()
