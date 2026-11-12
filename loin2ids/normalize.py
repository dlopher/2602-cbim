"""Normalização determinística dos blocos contra o esquema IFC e as decisões.

Corrige nomes (gralhas, maiúsculas, espaços) quando a correspondência é única,
resolve dataTypes, expande tabelas de classificação e regista cada correção ou
ambiguidade como ``Issue``.
"""
from __future__ import annotations

import re

from . import schema as S
from .decisions import Decisions
from .model import AttrReq, ApplicabilityFilter, Block, ClassReq, Issue, PropReq
from .textutil import compact, load_config, norm, resolve_name


def _issue(issues, level, code, blk: Block, msg, row=None, item=None, suggestion=None):
    issues.append(Issue(level, code, blk.sheet, msg, row=row, item=item, suggestion=suggestion))


def _report_fix(issues, blk, kind, raw, fixed, method, row):
    if method in ("exact",) or raw == fixed:
        return
    level = "warning" if method == "fuzzy" else "info"
    _issue(issues, level, f"fix-{kind}", blk, f"{kind} '{raw}' corrigido para '{fixed}' ({method}).", row, raw)


def normalize_block(blk: Block, version: str, dec: Decisions, issues: list[Issue]) -> None:
    sd = dec.sheet(blk.sheet)
    if sd.get("skip"):
        blk.skip = True
        if blk.suffix is None:
            _issue(issues, "info", "sheet-skipped", blk,
                   f"Folha omitida por decisão: {sd.get('reason', '(sem motivo)')}")
        return
    if blk.suffix is None and sd.get("entity"):
        blk.entity = sd["entity"]

    # --- entidade ---------------------------------------------------------
    if not blk.entity:
        blk.skip = True
        return
    ent = S.entity(version, blk.entity.strip())
    if ent is None:
        cand, method, close = resolve_name(blk.entity.strip(), list(S.entity_names(version)), max_dist=2)
        if cand:
            _report_fix(issues, blk, "entidade", blk.entity, cand, method, blk.entity_row)
            ent = cand
        else:
            _issue(issues, "blocker", "entity-unknown", blk,
                   f"Entidade '{blk.entity}' não existe em {version}.", blk.entity_row, blk.entity,
                   f"Candidatas: {', '.join(close)}" if close else None)
            blk.skip = True
            return
    blk.entity = ent

    # --- atributos --------------------------------------------------------
    attr_names = list(S.entity_attributes(version, ent))
    seen = set()
    attrs = []
    for a in blk.attrs:
        rd = dec.row(blk.sheet, a.raw)
        if rd is not None and rd.get("skip"):
            continue
        raw = (rd or {}).get("name") or a.name
        # "Predifined Type IfcCoveringType" → remove o tipo IFC no fim
        txt = re.sub(r"\s+Ifc[A-Za-z0-9]+$", "", raw.strip())
        alias = (load_config("aliases.yaml").get("attribute_aliases") or {}).get(norm(txt))
        if alias and alias in attr_names:
            cand, method, close = alias, "alias", []
        else:
            cand, method, close = resolve_name(txt, attr_names)
        if cand is None:
            _issue(issues, "blocker", "attr-unknown", blk,
                   f"Atributo '{raw}' não existe em {ent}.", a.row, a.raw,
                   f"Candidatos: {', '.join(close)}" if close else None)
            continue
        _report_fix(issues, blk, "atributo", a.name, cand, method, a.row)
        a.name = cand
        if a.value is not None and cand == "PredefinedType":
            allowed = S.predefined_type_values(version, ent)
            vals = [v.strip().upper() for v in re.split(r"[,;/]", a.value) if v.strip()]
            bad = [v for v in vals if allowed and v not in allowed]
            if bad:
                _issue(issues, "blocker", "predefined-unknown", blk,
                       f"PredefinedType {bad} não existe em {ent} (válidos: {', '.join(allowed)}).", a.row, a.value)
                continue
            blk.filters.append(ApplicabilityFilter("PredefinedType", values=vals))
            a.value = None  # o valor vai para a aplicabilidade; o requisito fica só de existência
        if cand in seen:
            continue
        seen.add(cand)
        attrs.append(a)
    blk.attrs = attrs

    pt = sd.get("predefined_type") if blk.suffix is None else None
    if pt:
        vals = [pt] if isinstance(pt, str) else list(pt)
        blk.filters = [f for f in blk.filters if f.attribute != "PredefinedType"]
        blk.filters.append(ApplicabilityFilter("PredefinedType", values=[v.upper() for v in vals]))
    for f in (sd.get("applicability") or []) if blk.suffix is None else []:
        blk.filters.append(ApplicabilityFilter(f["attribute"], values=f.get("values"), pattern=f.get("pattern")))

    # --- propriedades -----------------------------------------------------
    pnames = list(S.pset_names(version))
    seen = set()
    props = []
    for p in blk.props:
        rd = dec.row(blk.sheet, p.raw)
        if rd is not None:
            if rd.get("skip"):
                continue
            p.pset = rd.get("pset", p.pset)
            p.name = rd.get("name", p.name)
            if rd.get("data_type"):
                p.data_type = rd["data_type"]
        if not p.pset:
            continue  # já reportado como blocker pelo parser (prop-no-pset)
        if rd is not None and rd.get("pset"):
            # decisão explícita: retira o blocker do parser
            issues[:] = [i for i in issues if not (i.code == "prop-no-pset" and i.sheet == blk.sheet
                                                   and compact(i.item) == compact(p.raw))]
        if not _resolve_prop(blk, p, version, pnames, dec, issues):
            continue
        key = (p.pset, p.name)
        if key in seen:
            continue
        seen.add(key)
        props.append(p)
    blk.props = props
    # remove blockers prop-no-pset para linhas omitidas por decisão
    issues[:] = [i for i in issues if not (i.code == "prop-no-pset" and i.sheet == blk.sheet
                                           and (dec.row(blk.sheet, i.item) or {}).get("skip"))]

    # --- classificação ----------------------------------------------------
    blk.classes = _expand_classes(blk, dec, issues)

    # --- materiais --------------------------------------------------------
    if len(blk.materials) > 1:
        vals = {m.value for m in blk.materials}
        blk.materials = [blk.materials[0]] if len(vals) == 1 else blk.materials


def _resolve_prop(blk: Block, p: PropReq, version: str, pnames: list[str], dec: Decisions,
                  issues: list[Issue]) -> bool:
    raw_pset, raw_name = p.pset, p.name
    pdec = dec.pset(p.pset)
    if S.is_standard_pset(p.pset) and S.pset(version, p.pset) is None and pdec is None:
        cand, method, close = resolve_name(p.pset, pnames)
        if cand and method != "ambiguous":
            _report_fix(issues, blk, "pset", p.pset, cand, method, p.row)
            p.pset = cand
        else:
            _issue(issues, "blocker", "pset-unknown", blk,
                   f"Conjunto '{p.pset}' (propriedade '{p.name}') não existe em {version}.", p.row, p.pset,
                   (f"Candidatos: {', '.join(close)}. " if close else "")
                   + "Corrija a folha ou aceite-o em decisions.yaml (psets).")
            return False
    pdec = dec.pset(p.pset)
    if S.is_standard_pset(p.pset) and S.pset(version, p.pset) is not None:
        known = S.pset_properties(version, p.pset)
        cand, method, close = resolve_name(p.name, list(known))
        if cand is None:
            if pdec and pdec.get("accept"):
                p.data_type = p.data_type or (pdec.get("properties") or {}).get(p.name) or pdec.get("data_type")
                return True
            _issue(issues, "blocker", "prop-unknown", blk,
                   f"Propriedade '{p.name}' não existe em {p.pset} ({version}).", p.row, p.name,
                   f"Candidatos: {', '.join(close)}" if close else None)
            return False
        _report_fix(issues, blk, "propriedade", raw_name, cand, method, p.row)
        p.name = cand
        p.data_type = p.data_type or known[cand]
        return True
    # Pset não normalizado (ou normalizado inexistente mas aceite)
    if pdec is not None:
        p.data_type = p.data_type or (pdec.get("properties") or {}).get(p.name) or pdec.get("data_type")
        return True
    _issue(issues, "warning", "pset-custom", blk,
           f"Conjunto não normalizado '{raw_pset}': propriedade '{p.name}' sem dataType.", p.row, raw_pset,
           "Confirme em decisions.yaml (psets) e indique data_type se conhecido.")
    return True


def _expand_classes(blk: Block, dec: Decisions, issues: list[Issue]) -> list[ClassReq]:
    cfg = load_config("classification_map.yaml")
    out: list[ClassReq] = []
    seen = set()
    for c in blk.classes:
        system = None
        for canon, aliases in cfg["systems"].items():
            if compact(c.system) in [compact(canon)] + [compact(a) for a in aliases]:
                system = canon
        if system is None:
            _issue(issues, "blocker", "class-system-unknown", blk,
                   f"Sistema de classificação '{c.system}' desconhecido.", c.row, c.system,
                   "Acrescente-o a config/classification_map.yaml.")
            continue
        if system != c.system:
            _issue(issues, "info", "fix-sistema", blk, f"sistema '{c.system}' normalizado para '{system}'.", c.row, c.system)
        groups = dec.table(c.raw)
        if groups is None:
            for tname, g in (cfg["tables"].get(system) or {}).items():
                if compact(tname) == compact(c.raw):
                    groups = g
        if groups is None:
            _issue(issues, "blocker", "class-table-unknown", blk,
                   f"Tabela '{c.raw}' do sistema {system} sem mapeamento para prefixos.", c.row, c.raw,
                   "Defina em decisions.yaml → classification_tables, ex.: \"%s\": [[Pr_]]" % c.raw)
            continue
        for g in groups:
            prefixes = [g] if isinstance(g, str) else list(g)
            key = (system, tuple(prefixes))
            if key in seen:
                continue
            seen.add(key)
            out.append(ClassReq(system=system, prefixes=prefixes, row=c.row, raw=c.raw))
    return out
