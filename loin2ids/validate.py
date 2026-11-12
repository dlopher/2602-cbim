"""Validação: IDS contra o XSD oficial 1.0 e (opcional) execução sobre um modelo IFC."""
from __future__ import annotations

from pathlib import Path

from ifctester import ids

from . import schema as S


def xsd_errors(path: str | Path) -> list[str]:
    """Erros de validação XSD (lista vazia = válido)."""
    schema = ids.get_schema()
    return [str(e.reason or e) for e in schema.iter_errors(str(path))]


def semantic_errors(path: str | Path) -> list[str]:
    """Verifica entidades, atributos e Psets normalizados contra o esquema IFC de cada especificação."""
    doc = ids.open(str(path))
    errs = []
    for spec in doc.specifications:
        for ver in spec.ifcVersion:
            ver = "IFC4X3_ADD2" if ver == "IFC4X3" else ver
            for f in spec.applicability:
                if isinstance(f, ids.Entity) and isinstance(f.name, str):
                    if S.entity(ver, f.name) is None:
                        errs.append(f"{spec.identifier}: entidade {f.name} não existe em {ver}")
            for f in spec.requirements:
                if isinstance(f, ids.Property) and isinstance(f.propertySet, str) and isinstance(f.baseName, str):
                    if S.is_standard_pset(f.propertySet):
                        props = S.pset_properties(ver, f.propertySet)
                        if not props:
                            errs.append(f"{spec.identifier}: {f.propertySet} não existe em {ver}")
                        elif f.baseName not in props:
                            errs.append(f"{spec.identifier}: {f.propertySet}.{f.baseName} não existe em {ver}")
                        elif f.dataType and props[f.baseName] and f.dataType.upper() != props[f.baseName]:
                            errs.append(f"{spec.identifier}: {f.propertySet}.{f.baseName} dataType {f.dataType} "
                                        f"≠ {props[f.baseName]}")
    return errs


def run_on_ifc(ids_path: str | Path, ifc_path: str | Path):
    """Executa o IDS sobre um IFC; devolve o objeto Ids com resultados (spec.status)."""
    import ifcopenshell

    doc = ids.open(str(ids_path))
    model = ifcopenshell.open(str(ifc_path))
    doc.validate(model)
    return doc
