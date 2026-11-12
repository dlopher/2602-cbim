"""Grelha da folha LOIN → modelo intermédio (``LoinSheet`` com ``Block``s).

Gramática esperada (colunas 0-based):
  A (0)  rótulos de cabeçalho: Objetos / Ator ... / Propósito / Requisitos mínimos ...
  B (1)  secções: Classe IFC, Atributos, Conjuntos de propriedades, Materiais, Classificação, ...
  C (2)  item (atributo, propriedade, sistema de classificação)
  D (3)  sub-item (atributos dentro de "Referências")
  H (7)  Pset / tabela de classificação / valor do objeto
  I+ (8…) uma coluna por fase de projeto com a marca (X ou valor)

O parser NÃO consulta o esquema IFC: guarda os nomes tal como estão (limpos) e a
normalização contra o esquema acontece em ``normalize.py``.
"""
from __future__ import annotations

import re

from .model import AttrReq, Block, ClassReq, Issue, LoinSheet, MaterialReq, PropReq
from .readers import Sheet
from .textutil import clean, compact, load_config, norm

COL_SECTION, COL_ITEM, COL_SUB, COL_GROUP, COL_FIRST_PHASE = 1, 2, 3, 7, 8


def _cfg():
    return load_config("aliases.yaml")


def _startswith_any(text: str, options: list[str]) -> str | None:
    t = norm(text)
    for o in sorted(options, key=len, reverse=True):
        if t == o or t.startswith(o + " ") or t.startswith(o):
            return o
    return None


def section_of(text: str | None) -> str | None:
    if not text:
        return None
    t = norm(text)
    for key, opts in _cfg()["sections"].items():
        for o in opts:
            if t == o or t.startswith(o):
                return key
    return None


def _is_required_mark(v: str | None) -> bool:
    return v is not None and norm(v) in [norm(m) for m in _cfg()["required_marks"]]


def find_phases(sheet: Sheet) -> dict[int, str]:
    """Devolve {coluna: nome da fase}."""
    labels = _cfg()["phase_label"]
    for r, row in enumerate(sheet.rows[:30]):
        for c, v in enumerate(row):
            if v and _startswith_any(v, labels) and len(norm(v)) < 60:
                same = {i: clean(x) for i, x in enumerate(row) if i > c and x and clean(x)}
                if same:
                    return same
                nxt = sheet.rows[r + 1] if r + 1 < len(sheet.rows) else []
                below = {i: clean(x) for i, x in enumerate(nxt) if i >= COL_FIRST_PHASE and x and clean(x)}
                if below:
                    return below
    return {}


def select_phase(phases: dict[int, str], wanted: str | None) -> tuple[int | None, str | None]:
    """Escolhe a coluna da fase. Devolve (coluna, erro)."""
    if not phases:
        return None, "não foi encontrada a linha de fases (FASE DE PROJETO)"
    if wanted:
        for c, n in phases.items():
            if norm(n) == norm(wanted):
                return c, None
        for c, n in phases.items():
            if norm(wanted) in norm(n):
                return c, None
        return None, f"fase '{wanted}' não existe (disponíveis: {', '.join(phases.values())})"
    if len(phases) == 1:
        return next(iter(phases)), None
    return None, f"a folha tem várias fases ({', '.join(phases.values())}); indique --phase"


_DOTTED = re.compile(r"^(Ifc[A-Za-z0-9]+)\.([A-Za-z0-9_]+)$")
_CLASS_IN_TEXT = re.compile(r"^classe ifc\s+(ifc[a-z0-9]+)$", re.I)


def parse_sheet(sheet: Sheet, phase: str | None, issues: list[Issue]) -> LoinSheet:
    cfg = _cfg()
    ls = LoinSheet(name=sheet.name)
    sname = clean(sheet.name) or sheet.name

    def issue(level, code, msg, row=None, item=None, suggestion=None):
        issues.append(Issue(level, code, sname, msg, row=(row + 1) if row is not None else None,
                            item=item, suggestion=suggestion))

    if norm(sheet.name) in cfg["ignore_sheets"]:
        ls.ignored, ls.ignored_reason = True, "folha de índice/observações"
        issue("info", "sheet-ignored", "Folha ignorada (índice/observações).")
        return ls

    # --- cabeçalho -------------------------------------------------------
    alpha_row = None
    for r, row in enumerate(sheet.rows):
        a = row[0] if row else None
        if a and norm(a) in cfg["object_labels"] and ls.object_name is None:
            ls.object_name = clean(sheet.cell(r, COL_GROUP)) or clean(next((x for x in row[1:] if x), None))
        if a and _startswith_any(a, cfg["alphanumeric_start"]):
            alpha_row = r
            break
    if alpha_row is None:
        ls.ignored, ls.ignored_reason = True, "sem secção 'Requisitos mínimos de informação alfanumérica'"
        issue("info", "sheet-ignored", "Folha ignorada: não tem secção alfanumérica.")
        return ls

    ls.phases = find_phases(sheet)
    col, err = select_phase(ls.phases, phase)
    if col is None:
        issue("blocker", "phase", f"Fase não determinada: {err}.")
        ls.ignored, ls.ignored_reason = True, err
        return ls
    ls.phase_col = col
    for r in range(alpha_row):
        lab = norm(sheet.cell(r, 0))
        val = clean(sheet.cell(r, col))
        if lab in ("referencias eir", "eir") and val:
            ls.purpose = val
        elif lab in ("proposito",) and val and ls.purpose is None:
            ls.purpose = val

    def mark(r: int) -> str | None:
        return clean(sheet.cell(r, col))

    # --- corpo -----------------------------------------------------------
    main = Block(sheet=sname, entity=None, object_name=ls.object_name)
    blocks = [main]
    derived: dict[str, Block] = {}         # entidade → bloco derivado (atributos "IfcX.Attr")
    current = main
    section = None
    in_refs_attrs = False

    for r in range(alpha_row + 1, len(sheet.rows)):
        row = sheet.rows[r]
        if not any(row):
            continue
        b, c, d, h = (clean(sheet.cell(r, i)) for i in (COL_SECTION, COL_ITEM, COL_SUB, COL_GROUP))
        m = mark(r)

        if b:
            sec = section_of(b)
            if sec is None:
                if m:
                    issue("warning", "unknown-row", f"Linha com marca '{m}' numa secção desconhecida: '{b}'.", r, b)
                else:
                    ls.notes.append(b)
                continue
            section = sec
            in_refs_attrs = False
            if sec == "classe_ifc":
                ent = m or clean(next((x for x in row[COL_FIRST_PHASE:] if x), None))
                if not ent:
                    mm = re.match(r"^classe ifc\s+(\S+)$", b, re.I)
                    ent = mm.group(1) if mm else None
                if ent:
                    current.entity, current.entity_row = ent, r + 1
            elif sec == "referencias":
                current = Block(sheet=sname, entity=None, object_name=ls.object_name, suffix="Referências")
                blocks.append(current)
            elif sec == "nota":
                section = "nota"
            continue

        item = c or d
        if not item:
            continue

        if section == "nota" or section is None:
            if m:
                issue("warning", "unknown-row", f"Linha com marca '{m}' fora de qualquer secção.", r, item)
            ls.notes.append(item)
            continue

        # "Classe IFC" dentro de uma secção (Referências, ou layout irregular)
        if c and norm(c).startswith("classe ifc"):
            mm = _CLASS_IN_TEXT.match(norm(c))
            ent = None
            if mm:
                ent = c.split()[-1]
            elif m and not _is_required_mark(m):
                ent = m
            elif h:
                ent = h
            if ent:
                if current.entity and current.entity.lower() != ent.lower() and section != "referencias":
                    issue("warning", "layout", f"Entidade declarada duas vezes ('{current.entity}' e '{ent}').", r, c)
                if not current.entity or section == "referencias":
                    current.entity, current.entity_row = ent, r + 1
                if section != "referencias":
                    issue("warning", "layout", f"'Classe IFC' encontrada fora da posição habitual (coluna C); usada a entidade {ent}.", r, c)
            continue
        if c and norm(c) == "atributos" and section == "referencias":
            in_refs_attrs = True
            continue
        if c and norm(c) in cfg["section_headers"]:
            continue

        if not m:
            # linha sem marca na fase escolhida: não é exigida (ou é nota/link de referência)
            continue

        if section in ("atributos", "georef", "referencias", "classe_ifc"):
            target = current
            name = item
            dm = _DOTTED.match(item.replace(" ", ""))
            if dm:
                ent, name = dm.group(1), dm.group(2)
                key = ent.lower()
                if key not in derived:
                    derived[key] = Block(sheet=sname, entity=ent, object_name=ls.object_name, suffix=ent,
                                         entity_row=r + 1)
                    blocks.append(derived[key])
                target = derived[key]
            value = None if _is_required_mark(m) else m
            target.attrs.append(AttrReq(name=name, value=value, row=r + 1, raw=item))
        elif section == "propriedades":
            if not h:
                issue("blocker", "prop-no-pset",
                      f"Propriedade '{item}' marcada sem conjunto de propriedades (coluna H vazia).", r, item,
                      "Indique pset/nome em decisions.yaml (rows) ou marque skip.")
                current.props.append(PropReq(pset="", name=item, row=r + 1, raw=item))
                continue
            value = None if _is_required_mark(m) else m
            current.props.append(PropReq(pset=h, name=item, value=value, row=r + 1, raw=item))
        elif section == "materiais":
            value = None if _is_required_mark(m) else m
            current.materials.append(MaterialReq(value=value, row=r + 1))
        elif section == "classificacao":
            if not h:
                issue("blocker", "class-no-table", f"Sistema de classificação '{item}' sem tabela (coluna H).", r, item)
                continue
            current.classes.append(ClassReq(system=item, prefixes=[], row=r + 1, raw=h))

    if main.entity is None:
        default = cfg["object_entity_defaults"].get(norm(ls.object_name)) if ls.object_name else None
        if default:
            main.entity = default
            issue("info", "entity-default", f"Folha sem 'Classe IFC'; entidade deduzida do objeto: {default}.")
    for blk in blocks:
        if blk.suffix == "Referências" and blk.entity is None:
            blk.entity = cfg["references_default_entity"]

    ls.blocks = [blk for blk in blocks if not (blk is not main and blk.is_empty())]
    if main.entity is None and not main.is_empty():
        issue("blocker", "no-entity", "Folha sem 'Classe IFC' — não é possível saber a entidade.")
    if main.is_empty() and main.entity and len(ls.blocks) > 1:
        # bloco principal sem requisitos próprios mas com derivados (ex.: Projeto só com georreferenciação)
        pass
    return ls


def sheet_key(name: str) -> str:
    return compact(name)
