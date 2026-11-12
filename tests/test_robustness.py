"""Folhas sintéticas: variações de layout dão o mesmo resultado ou um problema explícito."""
from __future__ import annotations

from loin2ids.core import convert
from loin2ids.decisions import Decisions, Project

from loin_builder import WALL, workbook

PE = "Projeto de Execução"


def _project(**kw):
    return Project(title="t", ifc_version="IFC4X3_ADD2", phase=PE, **kw)


def _facets(res):
    b = res.blocks[0]
    return (b.entity, sorted(a.name for a in b.attrs), sorted((p.pset, p.name, p.data_type) for p in b.props),
            sorted(c.pattern for c in b.classes), len(b.materials))


def test_basic_wall(tmp_path):
    res = convert(workbook(tmp_path / "w.xlsx", [WALL]), _project())
    assert not res.blockers
    ent, attrs, props, classes, mats = _facets(res)
    assert ent == "IfcWall"
    assert attrs == ["Name", "PredefinedType"]
    assert ("Qto_WallBaseQuantities", "Length", "IFCLENGTHMEASURE") in props   # 'Lenght' corrigido
    assert classes == ["EF_.*", "Pr_.*", "Ss_.*"]
    assert mats == 1


def test_shifted_phase_columns_same_result(tmp_path):
    a = convert(workbook(tmp_path / "a.xlsx", [WALL]), _project())
    b = convert(workbook(tmp_path / "b.xlsx", [dict(WALL, col_offset=2)]), _project())
    assert _facets(a) == _facets(b)


def test_extra_spaces_and_case(tmp_path):
    messy = dict(WALL, name=" ARQ-Paredes ", attrs=[("  name ", "x"), ("Predifined Type ", "X")],
                 props=[("FireRating   ", "Pset_WallCommon ", "X"), ("isexternal", "Pset_WallCommon", "X"),
                        ("Lenght", "Qto_WallBaseQuantities", "X")],
                 classif=[("SECCLASS", "Elementos/Funções, Sistemas e Produtos", "X")])
    a = convert(workbook(tmp_path / "a.xlsx", [WALL]), _project())
    b = convert(workbook(tmp_path / "b.xlsx", [messy]), _project())
    assert _facets(a) == _facets(b)


def test_phase_filter(tmp_path):
    s = dict(WALL, props=[("FireRating", "Pset_WallCommon", "X")], phase_marks=[False, False, True])
    path = workbook(tmp_path / "a.xlsx", [s])
    res = convert(path, Project(title="t", phase="Estudo Prévio"))
    assert res.blocks == [] and res.xml is None
    assert any(i.code == "no-specs" for i in res.blockers)
    res_pe = convert(path, Project(title="t", phase="Projeto de Execução"))
    assert [p.name for p in res_pe.blocks[0].props] == ["FireRating"]


def test_multi_phase_without_phase_is_blocker(tmp_path):
    res = convert(workbook(tmp_path / "a.xlsx", [WALL]), Project(title="t"))
    assert any(i.code == "phase" for i in res.blockers)
    assert res.xml is None


def test_unknown_entity_is_blocker(tmp_path):
    res = convert(workbook(tmp_path / "a.xlsx", [dict(WALL, entity="IfcParedeX")]), _project())
    assert any(i.code == "entity-unknown" for i in res.blockers)


def test_entity_typo_is_corrected(tmp_path):
    res = convert(workbook(tmp_path / "a.xlsx", [dict(WALL, entity="IfcPipeSgment", props=[])]), _project())
    assert res.blocks[0].entity == "IfcPipeSegment"
    assert any(i.code == "fix-entidade" for i in res.issues)


def test_unknown_property_in_standard_pset_is_blocker(tmp_path):
    s = dict(WALL, props=[("Espessura", "Pset_WallCommon", "X")])
    res = convert(workbook(tmp_path / "a.xlsx", [s]), _project())
    assert any(i.code == "prop-unknown" for i in res.blockers)


def test_unknown_classification_table_then_decision(tmp_path):
    s = dict(WALL, classif=[("SECClasS", "Tabela Nova", "X")])
    path = workbook(tmp_path / "a.xlsx", [s])
    res = convert(path, _project())
    assert any(i.code == "class-table-unknown" for i in res.blockers)
    dec = Decisions(classification_tables={"Tabela Nova": [["Pr_"]]})
    res2 = convert(path, _project(), dec)
    assert not res2.blockers
    assert [c.pattern for c in res2.blocks[0].classes] == ["Pr_.*"]


def test_custom_pset_warning_and_decision(tmp_path):
    s = dict(WALL, props=[("WBS_codigo", "WBS_bSPT", "X")])
    path = workbook(tmp_path / "a.xlsx", [s])
    res = convert(path, _project())
    assert any(i.code == "pset-custom" for i in res.issues)
    assert res.blocks[0].props[0].data_type is None
    res2 = convert(path, _project(), Decisions(psets={"WBS_bSPT": {"data_type": "IFCLABEL"}}))
    assert not any(i.code == "pset-custom" for i in res2.issues)
    assert res2.blocks[0].props[0].data_type == "IFCLABEL"


def test_overlap_same_entity_is_blocker_then_resolved(tmp_path):
    a = dict(WALL, name="ARQ-Paredes", classif=[])
    b = dict(WALL, name="ARQ-ParedesExt", classif=[])
    path = workbook(tmp_path / "a.xlsx", [a, b])
    res = convert(path, _project())
    assert any(i.code == "applicability-overlap" for i in res.blockers)
    dec = Decisions(sheets={"ARQ-ParedesExt": {"predefined_type": ["PARAPET"]}})
    res2 = convert(path, _project(), dec)
    assert not res2.blockers
    walls = {b.identifier: b for b in res2.blocks}
    assert walls["ARQ-ParedesExt"].filters[0].values == ["PARAPET"]
    assert "PARAPET" not in walls["ARQ-Paredes"].filters[0].values


def test_predefined_value_goes_to_applicability(tmp_path):
    rod = dict(WALL, name="ARQ-Rodapes", entity="IfcCovering", attrs=[("Predifined Type", "SKIRTINGBOARD")],
               props=[], classif=[])
    rev = dict(WALL, name="ARQ-Rev", entity="IfcCovering", attrs=[("Name", "X")], props=[], classif=[])
    res = convert(workbook(tmp_path / "a.xlsx", [rod, rev]), _project())
    assert not res.blockers
    by = {b.identifier: b for b in res.blocks}
    assert by["ARQ-Rodapes"].filters[0].values == ["SKIRTINGBOARD"]
    assert "SKIRTINGBOARD" not in by["ARQ-Rev"].filters[0].values


def test_invalid_predefined_value_is_blocker(tmp_path):
    s = dict(WALL, attrs=[("Predifined Type", "PAREDEX")])
    res = convert(workbook(tmp_path / "a.xlsx", [s]), _project())
    assert any(i.code == "predefined-unknown" for i in res.blockers)


def test_prop_without_pset_decision(tmp_path):
    s = dict(WALL, props=[("Espessura?", None, "X")])
    path = workbook(tmp_path / "a.xlsx", [s])
    res = convert(path, _project())
    assert any(i.code == "prop-no-pset" for i in res.blockers)
    dec = Decisions(sheets={"ARQ-Paredes": {"rows": {"Espessura?": {"pset": "Qto_WallBaseQuantities", "name": "Width"}}}})
    res2 = convert(path, _project(), dec)
    assert not res2.blockers
    assert ("Qto_WallBaseQuantities", "Width") in [(p.pset, p.name) for p in res2.blocks[0].props]
    dec_skip = Decisions(sheets={"ARQ-Paredes": {"rows": {"Espessura?": {"skip": True}}}})
    assert not convert(path, _project(), dec_skip).blockers


def test_material_sheet_needs_filter(tmp_path):
    m = dict(name="M-Betão", obj="Betão", entity="IfcMaterial", attrs=[("Name", "X")],
             props=[("CompressiveStrength", "Pset_MaterialConcrete", "X")])
    path = workbook(tmp_path / "a.xlsx", [m])
    assert any(i.code == "material-applicability" for i in convert(path, _project()).blockers)
    dec = Decisions(sheets={"M-Betão": {"applicability": [{"attribute": "Name", "pattern": ".*concrete.*"}]}})
    res = convert(path, _project(), dec)
    assert not res.blockers and res.blocks[0].filters[0].pattern == ".*concrete.*"


def test_notes_and_reference_links_are_ignored(tmp_path):
    s = dict(WALL, extra_rows=[{2: "Nota:"}, {2: "Em paredes com várias camadas ..."},
                               {3: "Pset_WallCommon"}, {3: "https://standards.buildingsmart.org/..."}])
    a = convert(workbook(tmp_path / "a.xlsx", [WALL]), _project())
    b = convert(workbook(tmp_path / "b.xlsx", [s]), _project())
    assert _facets(a) == _facets(b)
    assert not b.blockers
