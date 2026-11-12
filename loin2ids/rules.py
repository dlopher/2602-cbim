"""Regras entre blocos: identificadores, nomes, sobreposição de aplicabilidade, materiais."""
from __future__ import annotations

from collections import defaultdict

from . import schema as S
from .decisions import Decisions, Project
from .model import ApplicabilityFilter, Block, Issue
from .textutil import clean


def _ident(blk: Block, project: Project) -> str:
    base = clean(blk.sheet) or blk.sheet
    if project.identifier_prefix and not base.upper().startswith(project.identifier_prefix.upper()):
        base = f"{project.identifier_prefix}{base}"
    if blk.suffix:
        suf = blk.suffix[3:] if blk.suffix.startswith("Ifc") else blk.suffix
        base = f"{base}-{suf}"
    return base


def finalize(blocks: list[Block], project: Project, dec: Decisions, issues: list[Issue]) -> list[Block]:
    version = project.ifc_version
    live = [b for b in blocks if not b.skip]

    for b in live:
        sd = dec.sheet(b.sheet) if b.suffix is None else {}
        b.identifier = sd.get("identifier") or _ident(b, project)
        if sd.get("name"):
            b.name = sd["name"]
        elif b.suffix:
            b.name = f"{b.object_name or b.sheet} ({b.entity})"
        else:
            b.name = b.object_name or clean(b.sheet)
        if b.is_empty():
            issues.append(Issue("warning", "spec-empty", b.sheet,
                                f"Especificação {b.entity} sem requisitos na fase escolhida; omitida."))
            b.skip = True

    live = [b for b in live if not b.skip]

    # --- materiais (IfcMaterial) precisam de um filtro de aplicabilidade --------
    for b in live:
        if b.entity and S.entity(version, b.entity) and b.entity.lower() == "ifcmaterial" and not b.filters:
            issues.append(Issue("blocker", "material-applicability", b.sheet,
                                f"Folha de material '{b.object_name}': é preciso um filtro de aplicabilidade "
                                f"(ex.: Name com padrão) para não aplicar a todos os materiais.",
                                item=b.object_name,
                                suggestion="decisions.yaml → sheets.<folha>.applicability: "
                                           "[{attribute: Name, pattern: '.*concrete.*'}]"))

    # --- sobreposição: várias folhas com a mesma entidade -----------------------
    by_entity: dict[str, list[Block]] = defaultdict(list)
    for b in live:
        by_entity[b.entity.lower()].append(b)
    for ent, group in by_entity.items():
        if len(group) < 2:
            continue
        fixed = [b for b in group if any(f.attribute == "PredefinedType" for f in b.filters)]
        free = [b for b in group if b not in fixed and not b.filters]
        if not free:
            continue
        if len(free) > 1:
            names = ", ".join(f"'{b.sheet}'" for b in free)
            for b in free[1:]:
                issues.append(Issue("blocker", "applicability-overlap", b.sheet,
                                    f"Várias folhas aplicam-se a {b.entity} sem distinção ({names}).",
                                    item=b.entity,
                                    suggestion="Defina predefined_type ou applicability em decisions.yaml, ou skip."))
            continue
        b = free[0]
        allowed = list(S.predefined_type_values(version, b.entity))
        taken = {v for fb in fixed for f in fb.filters if f.attribute == "PredefinedType" for v in (f.values or [])}
        if allowed and taken:
            rest = [v for v in allowed if v not in taken]
            b.filters.append(ApplicabilityFilter("PredefinedType", values=rest))
            issues.append(Issue("info", "applicability-exclusion", b.sheet,
                                f"{b.entity}: PredefinedType {sorted(taken)} excluído da aplicabilidade "
                                f"(coberto por outra folha)."))
    return live
