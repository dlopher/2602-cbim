"""Leitura de folhas LOIN (.xlsx / .ods) para uma grelha normalizada.

Cada folha é devolvida como ``Sheet(name, rows)`` em que ``rows`` é uma lista de
linhas e cada linha uma lista de ``str | None`` (índice 0 = coluna A). Células
mescladas ficam apenas com o valor na célula superior-esquerda (comportamento
igual em xlsx e ods). Os valores são convertidos para texto; espaços e quebras
de linha NÃO são removidos aqui (isso é responsabilidade do parser).
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

MAX_COLS = 40  # as folhas LOIN nunca passam da coluna ~L; corta repetições ODS enormes
MAX_ROWS = 2000


@dataclass
class Sheet:
    name: str
    rows: list[list[str | None]] = field(default_factory=list)

    def cell(self, r: int, c: int) -> str | None:
        if r < len(self.rows) and c < len(self.rows[r]):
            return self.rows[r][c]
        return None


def _to_text(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v)
    return s if s.strip() != "" else None


def _trim_row(cells: list) -> list:
    while cells and cells[-1] is None:
        cells.pop()
    return cells


def read_xlsx(path: Path) -> list[Sheet]:
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    sheets = []
    for ws in wb.worksheets:
        rows = []
        for row in ws.iter_rows(max_col=MAX_COLS, max_row=MAX_ROWS, values_only=True):
            rows.append(_trim_row([_to_text(v) for v in row]))
        sheets.append(Sheet(ws.title, rows))
    return sheets


_T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
_X = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def _ods_cell_text(cell) -> str | None:
    paras = []
    for p in cell.iter(_X + "p"):
        parts = []
        def walk(el):
            if el.text:
                parts.append(el.text)
            for ch in el:
                if ch.tag == _X + "s":
                    parts.append(" " * int(ch.get(_X + "c", "1")))
                elif ch.tag == _X + "line-break":
                    parts.append("\n")
                elif ch.tag == _X + "tab":
                    parts.append("\t")
                else:
                    walk(ch)
                if ch.tail:
                    parts.append(ch.tail)
        walk(p)
        paras.append("".join(parts))
    return _to_text("\n".join(paras)) if paras else None


def read_ods(path: Path) -> list[Sheet]:
    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    sheets = []
    for table in root.iter(_T + "table"):
        rows: list[list[str | None]] = []
        for row in table.iter(_T + "table-row"):
            cells: list[str | None] = []
            for c in row:
                if c.tag not in (_T + "table-cell", _T + "covered-table-cell"):
                    continue
                rep = int(c.get(_T + "number-columns-repeated", "1"))
                txt = _ods_cell_text(c) if c.tag == _T + "table-cell" else None
                n = min(rep, max(0, MAX_COLS - len(cells)))
                cells.extend([txt] * n)
            cells = _trim_row(cells)
            rrep = int(row.get(_T + "number-rows-repeated", "1"))
            for _ in range(min(rrep, max(0, MAX_ROWS - len(rows)))):
                rows.append(list(cells))
        while rows and not rows[-1]:
            rows.pop()
        sheets.append(Sheet(table.get(_T + "name"), rows))
    return sheets


def read_workbook(path: str | Path) -> list[Sheet]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return read_xlsx(path)
    if ext == ".ods":
        return read_ods(path)
    raise ValueError(f"Formato não suportado: {path.suffix} (use .xlsx ou .ods)")
