"""Consulta ao esquema IFC oficial (via ifcopenshell): entidades, atributos, Psets/Qtos e tipos."""
from __future__ import annotations

from functools import lru_cache

import ifcopenshell
import ifcopenshell.util.pset

SUPPORTED_VERSIONS = ("IFC2X3", "IFC4", "IFC4X3_ADD2")

_TEMPLATE_VERSION = {"IFC2X3": "IFC2X3", "IFC4": "IFC4", "IFC4X3_ADD2": "IFC4X3", "IFC4X3": "IFC4X3"}

# Tipo de quantidade (IfcQuantity*) → dataType IDS
QUANTITY_TYPES = {
    "Q_LENGTH": "IFCLENGTHMEASURE",
    "Q_AREA": "IFCAREAMEASURE",
    "Q_VOLUME": "IFCVOLUMEMEASURE",
    "Q_COUNT": "IFCCOUNTMEASURE",
    "Q_WEIGHT": "IFCMASSMEASURE",
    "Q_TIME": "IFCTIMEMEASURE",
    "Q_NUMBER": "IFCNUMERICMEASURE",
}


def _check(version: str) -> str:
    if version not in _TEMPLATE_VERSION:
        raise ValueError(f"Versão IFC não suportada: {version} (use {', '.join(SUPPORTED_VERSIONS)})")
    return version


@lru_cache(maxsize=None)
def _schema(version: str):
    return ifcopenshell.schema_by_name(_check(version) if version != "IFC4X3" else "IFC4X3_ADD2")


@lru_cache(maxsize=None)
def _template(version: str):
    return ifcopenshell.util.pset.get_template(_TEMPLATE_VERSION[_check(version)])


@lru_cache(maxsize=None)
def entity_names(version: str) -> tuple[str, ...]:
    s = _schema(version)
    return tuple(sorted(d.name() for d in s.declarations() if hasattr(d, "all_attributes")))


def entity(version: str, name: str) -> str | None:
    """Nome canónico (ex.: 'IfcWall') ou None."""
    try:
        return _schema(version).declaration_by_name(name).name()
    except (RuntimeError, KeyError):
        low = {n.lower(): n for n in entity_names(version)}
        return low.get(name.lower())


@lru_cache(maxsize=None)
def entity_attributes(version: str, name: str) -> tuple[str, ...]:
    decl = _schema(version).declaration_by_name(name)
    return tuple(a.name() for a in decl.all_attributes())


def is_subtype(version: str, name: str, parent: str) -> bool:
    decl = _schema(version).declaration_by_name(name)
    while decl is not None:
        if decl.name().lower() == parent.lower():
            return True
        decl = decl.supertype()
    return False


@lru_cache(maxsize=None)
def predefined_type_values(version: str, name: str) -> tuple[str, ...]:
    """Valores do enumerado PredefinedType da entidade (vazio se não tiver)."""
    decl = _schema(version).declaration_by_name(name)
    for a in decl.all_attributes():
        if a.name() == "PredefinedType":
            t = a.type_of_attribute()
            while hasattr(t, "declared_type"):
                t = t.declared_type()
            if hasattr(t, "enumeration_items"):
                return tuple(t.enumeration_items())
    return ()


@lru_cache(maxsize=None)
def pset_names(version: str) -> tuple[str, ...]:
    t = _template(version)
    names = []
    for tf in t.templates:
        for ps in tf.by_type("IfcPropertySetTemplate"):
            names.append(ps.Name)
    return tuple(sorted(set(names)))


def pset(version: str, name: str):
    return _template(version).get_by_name(name)


@lru_cache(maxsize=None)
def pset_properties(version: str, pset_name: str) -> dict[str, str | None]:
    """{propriedade: dataType IDS} para um Pset/Qto normalizado."""
    ps = pset(version, pset_name)
    if ps is None:
        return {}
    out = {}
    for p in ps.HasPropertyTemplates or ():
        out[p.Name] = template_data_type(p)
    return out


def template_data_type(p) -> str | None:
    tt = getattr(p, "TemplateType", None)
    if tt in QUANTITY_TYPES:
        return QUANTITY_TYPES[tt]
    if tt == "P_ENUMERATEDVALUE":
        return "IFCLABEL"
    if tt == "P_REFERENCEVALUE":
        return None
    mt = getattr(p, "PrimaryMeasureType", None)
    return mt.upper() if mt else None


def is_standard_pset(name: str) -> bool:
    return name.startswith(("Pset_", "Qto_"))
