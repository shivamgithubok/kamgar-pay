from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from html import escape as escape_xml
from io import BytesIO
from typing import Iterable


@dataclass(frozen=True)
class ExportTable:
    title: str
    headers: list[str]
    rows: list[list[object]]


def format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def sanitize_filename(value: str) -> str:
    allowed = [ch.lower() if ch.isalnum() else "-" for ch in value]
    filename = "".join(allowed).strip("-")
    while "--" in filename:
        filename = filename.replace("--", "-")
    return filename or "report"


def build_export_filename(title: str, file_format: str) -> str:
    extension = "pdf" if file_format == "pdf" else "xls"
    return f"{sanitize_filename(title)}.{extension}"


def export_table(table: ExportTable, file_format: str) -> tuple[bytes, str, str]:
    normalized = file_format.strip().lower()
    if normalized == "pdf":
        return (
            export_pdf(table),
            "application/pdf",
            build_export_filename(table.title, normalized),
        )
    if normalized in {"excel", "xls"}:
        return (
            export_excel_xml(table),
            "application/vnd.ms-excel",
            build_export_filename(table.title, "excel"),
        )
    raise ValueError("Export format must be either pdf or excel")


def export_excel_xml(table: ExportTable) -> bytes:
    rows = [table.headers, *[[format_cell(cell) for cell in row] for row in table.rows]]
    xml_rows = []
    for row in rows:
        cells = "".join(
            f"<Cell><Data ss:Type=\"String\">{escape_xml(format_cell(cell))}</Data></Cell>"
            for cell in row
        )
        xml_rows.append(f"<Row>{cells}</Row>")

    workbook = f"""<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Worksheet ss:Name="{escape_xml(table.title[:31])}">
  <Table>
   {''.join(xml_rows)}
  </Table>
 </Worksheet>
</Workbook>
"""
    return workbook.encode("utf-8")


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_line(value: str, width: int = 115) -> list[str]:
    text = " ".join(value.split())
    if len(text) <= width:
        return [text]

    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        if len(current) + len(word) + 1 <= width:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def table_to_pdf_lines(table: ExportTable) -> list[str]:
    lines = [table.title, ""]
    lines.extend(wrap_line(" | ".join(table.headers)))
    lines.append("-" * 115)
    for row in table.rows:
        text = " | ".join(format_cell(cell) for cell in row)
        lines.extend(wrap_line(text))
    if not table.rows:
        lines.append("No records found.")
    return lines


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def build_pdf_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 9 Tf", "40 800 Td", "12 TL"]
    for line in lines:
        commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def pdf_object(object_id: int, body: bytes) -> bytes:
    return f"{object_id} 0 obj\n".encode("ascii") + body + b"\nendobj\n"


def export_pdf(table: ExportTable) -> bytes:
    lines = table_to_pdf_lines(table)
    pages = list(chunked(lines, 48)) or [[table.title, "", "No records found."]]
    page_object_ids = [4 + index * 2 for index in range(len(pages))]
    content_object_ids = [5 + index * 2 for index in range(len(pages))]
    max_object_id = content_object_ids[-1]

    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            b"<< /Type /Pages /Kids ["
            + b" ".join(f"{page_id} 0 R".encode("ascii") for page_id in page_object_ids)
            + f"] /Count {len(page_object_ids)} >>".encode("ascii")
        ),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }

    for page_id, content_id, page_lines in zip(page_object_ids, content_object_ids, pages):
        stream = build_pdf_stream(page_lines)
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        )

    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0] * (max_object_id + 1)
    for object_id in range(1, max_object_id + 1):
        offsets[object_id] = output.tell()
        output.write(pdf_object(object_id, objects[object_id]))

    xref_offset = output.tell()
    output.write(f"xref\n0 {max_object_id + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for object_id in range(1, max_object_id + 1):
        output.write(f"{offsets[object_id]:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            f"trailer\n<< /Size {max_object_id + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return output.getvalue()
