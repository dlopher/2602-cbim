"""Teste funcional: o IDS gerado aprova um IFC conforme e reprova um IFC não conforme."""
from __future__ import annotations

import ifcopenshell
import ifcopenshell.api
import pytest
from ifctester import ids

from loin2ids.core import convert
from loin2ids.decisions import Project

from loin_builder import WALL, workbook


def _model(conforming: bool) -> ifcopenshell.file:
    f = ifcopenshell.api.run("project.create_file", version="IFC4X3_ADD2")
    project = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run("unit.assign_unit", f)
    wall = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcWall", name="Parede 1",
                                predefined_type="STANDARD")
    if not conforming:
        return f
    pset = ifcopenshell.api.run("pset.add_pset", f, product=wall, name="Pset_WallCommon")
    ifcopenshell.api.run("pset.edit_pset", f, pset=pset, properties={"FireRating": "EI60", "IsExternal": True})
    qto = ifcopenshell.api.run("pset.add_qto", f, product=wall, name="Qto_WallBaseQuantities")
    ifcopenshell.api.run("pset.edit_qto", f, qto=qto, properties={"Length": 5.0})
    mat = ifcopenshell.api.run("material.add_material", f, name="Betão")
    ifcopenshell.api.run("material.assign_material", f, products=[wall], material=mat)
    system = ifcopenshell.api.run("classification.add_classification", f, classification="SECClasS")
    for code in ("Ss_25_10_30", "EF_25_10", "Pr_20_93_52"):
        ifcopenshell.api.run("classification.add_reference", f, products=[wall], identification=code,
                             name=code, classification=system)
    return f


@pytest.fixture(scope="module")
def generated_ids(tmp_path_factory):
    d = tmp_path_factory.mktemp("ifc")
    res = convert(workbook(d / "w.xlsx", [WALL]),
                  Project(title="t", ifc_version="IFC4X3_ADD2", phase="Projeto de Execução"))
    assert not res.blockers
    p = d / "w.ids"
    p.write_text(res.xml, encoding="utf-8")
    return p


def test_conforming_model_passes(generated_ids):
    doc = ids.open(str(generated_ids))
    doc.validate(_model(True))
    assert all(s.status for s in doc.specifications), [
        (s.identifier, [str(r.failures[:1]) for r in s.requirements if r.failures]) for s in doc.specifications]


def test_non_conforming_model_fails(generated_ids):
    doc = ids.open(str(generated_ids))
    doc.validate(_model(False))
    assert any(s.status is False for s in doc.specifications)
