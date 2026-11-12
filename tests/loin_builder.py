"""Construtor de folhas LOIN sintéticas (layout SRU) para testes de robustez."""
from __future__ import annotations

from pathlib import Path

import openpyxl

PHASES = ["Estudo Prévio", "Anteprojeto", "Projeto de Execução"]


def add_sheet(wb, name, obj, entity, *, phases=PHASES, attrs=(), props=(), materials=False,
              classif=(), phase_marks=None, col_offset=0, extra_rows=()):
    """Cria uma folha. ``attrs``: [(nome, marca)]; ``props``: [(nome, pset, marca)];
    ``classif``: [(sistema, tabela, marca)]. Marca aplica-se a todas as fases salvo ``phase_marks``.
    ``col_offset`` desloca as colunas de fase (teste de robustez)."""
    ws = wb.create_sheet(name)
    first = 9 + col_offset  # coluna I (1-based)
    ws.cell(1, 1, "Objetos"); ws.cell(1, 8, obj)
    ws.cell(2, 1, "Ator requerente"); ws.cell(2, 8, "Dono de Obra")
    ws.cell(4, first, "FASE DE PROJETO:")
    for i, p in enumerate(phases):
        ws.cell(5, first + i, p)
    ws.cell(6, 1, "Propósito")
    for i, _ in enumerate(phases):
        ws.cell(6, first + i, f"EIR0{i + 1}")
    ws.cell(7, 1, "Requisitos mínimos de informação geométrica")
    ws.cell(8, 2, "Detalhe")
    ws.cell(13, 1, "Requisitos mínimos de informação alfanumérica")
    r = 14
    ws.cell(r, 2, "Classe IFC")
    for i, _ in enumerate(phases):
        ws.cell(r, first + i, entity)
    r += 1

    def marks(row, m):
        for i, _ in enumerate(phases):
            v = m if phase_marks is None else (m if phase_marks[i] else None)
            if v:
                ws.cell(row, first + i, v)

    if attrs:
        ws.cell(r, 2, "Atributos"); r += 1
        for n, m in attrs:
            ws.cell(r, 3, n); marks(r, m); r += 1
    if props:
        ws.cell(r, 2, "Conjuntos de propriedades"); r += 1
        ws.cell(r, 3, "Propriedade"); ws.cell(r, 8, "Conjunto de propriedades"); r += 1
        for n, ps, m in props:
            ws.cell(r, 3, n); ws.cell(r, 8, ps); marks(r, m); r += 1
    if materials:
        ws.cell(r, 2, "Materiais"); r += 1
        ws.cell(r, 3, "Name"); ws.cell(r, 8, "IfcMaterial"); marks(r, "X"); r += 1
    if classif:
        ws.cell(r, 2, "Classificação"); r += 1
        ws.cell(r, 3, "Sistema"); ws.cell(r, 8, "Tabela"); r += 1
        for s, t, m in classif:
            ws.cell(r, 3, s); ws.cell(r, 8, t); marks(r, m); r += 1
    for row in extra_rows:
        for c, v in row.items():
            ws.cell(r, c, v)
        r += 1
    return ws


def workbook(path: Path, sheets: list[dict]) -> Path:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for s in sheets:
        s = dict(s)
        add_sheet(wb, s.pop("name"), s.pop("obj"), s.pop("entity"), **s)
    wb.save(path)
    return path


WALL = dict(
    name="ARQ-Paredes", obj="Paredes", entity="IfcWall",
    attrs=[("Name", "X"), ("Predifined Type", "X")],
    props=[("FireRating", "Pset_WallCommon", "X"), ("IsExternal", "Pset_WallCommon", "X"),
           ("Lenght", "Qto_WallBaseQuantities", "X")],
    materials=True,
    classif=[("SECClasS", "Elementos/ Funções, Sistemas e Produtos", "X")],
)
