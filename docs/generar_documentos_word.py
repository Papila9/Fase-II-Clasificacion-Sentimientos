"""Convierte los dos documentos Markdown de esta carpeta a Word (.docx).

Usa únicamente la biblioteca estándar de Python. Ejecutar desde la raíz:
    python docs/generar_documentos_word.py
"""

from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent
DOCUMENTS = {
    "despliegue-nube.md": "Manual-despliegue-nube.docx",
    "validacion-y-pruebas.md": "Validacion-y-pruebas.docx",
}
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def tag(name: str) -> str:
    return f"{{{W}}}{name}"


def clean_inline(text: str) -> str:
    """Simplifica el marcado en línea conservando el texto y las URL."""
    text = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?<!`)`([^`]+)`(?!`)", r"\1", text)
    return text.replace("  ", " ").strip()


def run(text: str, *, bold: bool = False, italic: bool = False, mono: bool = False) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if mono:
        props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>')
        props.append('<w:color w:val="43536A"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f"<w:r>{rpr}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def paragraph(text: str, style: str = "Normal", *, shaded: bool = False) -> str:
    ppr = f'<w:pStyle w:val="{style}"/>'
    if shaded:
        ppr += '<w:shd w:fill="EAF1F8"/><w:ind w:left="180" w:right="180"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{run(clean_inline(text))}</w:p>"


def table_cell(text: str, *, header: bool) -> str:
    fill = "DCE6F1" if header else "FFFFFF"
    return (
        f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/>'
        f'<w:shd w:fill="{fill}"/></w:tcPr>'
        f'<w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'
        f'{run(clean_inline(text), bold=header)}</w:p></w:tc>'
    )


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    borders = (
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="AAB7C4"/>'
        '<w:left w:val="single" w:sz="4" w:color="AAB7C4"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="AAB7C4"/>'
        '<w:right w:val="single" w:sz="4" w:color="AAB7C4"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="D4DCE5"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="D4DCE5"/></w:tblBorders>'
    )
    output = [
        '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'
        '<w:tblLayout w:type="autofit"/>' + borders + "</w:tblPr>"
    ]
    for index, cells in enumerate(rows):
        output.append("<w:tr>")
        output.extend(table_cell(cell, header=index == 0) for cell in cells)
        output.append("</w:tr>")
    output.append("</w:tbl>")
    return "".join(output)


def convert_markdown(source: str) -> str:
    lines = source.splitlines()
    body: list[str] = []
    in_code = False
    code_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            if in_code:
                body.append(paragraph("\n".join(code_lines), "CodeBlock"))
                code_lines = []
            in_code = not in_code
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if line.startswith("|"):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            body.append(markdown_table(rows))
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            body.append(paragraph(heading.group(2), "Title" if level == 1 else f"Heading{level}"))
        elif line.startswith("> "):
            body.append(paragraph(line[2:], "Quote", shaded=True))
        elif re.match(r"^\s*[-*+]\s+", line):
            body.append(paragraph(re.sub(r"^\s*[-*+]\s+", "• ", line), "ListParagraph"))
        elif re.match(r"^\s*\d+[.)]\s+", line):
            body.append(paragraph(re.sub(r"^\s*(\d+)[.)]\s+", r"\1. ", line), "ListParagraph"))
        elif line.strip() and not re.fullmatch(r"\s*[-*_]{3,}\s*", line):
            body.append(paragraph(line))
        i += 1

    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>""" + "".join(body) + """
<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="540" w:footer="540"/></w:sectPr>
</w:body></w:document>"""
    return document


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="22"/><w:color w:val="263445"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="140" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="240"/></w:pPr><w:rPr><w:b/><w:color w:val="17365D"/><w:sz w:val="34"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr><w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="80"/></w:pPr><w:rPr><w:b/><w:color w:val="365F91"/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:rPr><w:i/><w:color w:val="40566F"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/><w:spacing w:after="80"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:shd w:fill="F1F3F5"/><w:spacing w:before="100" w:after="160"/><w:ind w:left="180"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/><w:color w:val="35465C"/></w:rPr></w:style>
</w:styles>"""


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

PACKAGE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def main() -> None:
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:creator>Proyecto Fase II</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created></cp:coreProperties>"""
    for source_name, output_name in DOCUMENTS.items():
        source = ROOT / source_name
        output = ROOT / output_name
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as package:
            package.writestr("[Content_Types].xml", CONTENT_TYPES)
            package.writestr("_rels/.rels", PACKAGE_RELS)
            package.writestr("word/document.xml", convert_markdown(source.read_text(encoding="utf-8")))
            package.writestr("word/styles.xml", STYLES)
            package.writestr("word/_rels/document.xml.rels", DOC_RELS)
            package.writestr("docProps/core.xml", core)
        print(f"Creado: {output}")


if __name__ == "__main__":
    main()
