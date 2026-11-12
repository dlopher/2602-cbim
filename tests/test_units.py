"""Testes unitários: leitura, parser, normalização, esquema, classificação e diff."""
from __future__ import annotations

from loin2ids import schema as S
from loin2ids.idsdiff import _ALT
from loin2ids.model import Issue
from loin2ids.parser import find_phases, parse_sheet, section_of, select_phase
from loin2ids.readers import Sheet, read_workbook
from loin2ids.textutil import norm, resolve_name

from conftest import ROOT


# --- readers -------------------------------------------------------------------
def test_read_xlsx_and_ods_same_grammar():
    xs = read_workbook(ROOT / "00-ref-ids-gr/SRU0198-LOIN-ARQ.xlsx")
    os_ = read_workbook(ROOT / "00-ref-ids-gr/bSPT-LOIN-ARQ.ods")
    assert xs[0].name == "ARQ-Terreno" and os_[0].name == "Classificação"
    for sheets in (xs, os_):
        wall = next(s for s in sheets if s.name.strip() == "ARQ-Paredes")
        assert wall.cell(0, 0) == "Objetos" and wall.cell(0, 7) == "Paredes"


def test_ods_repeated_columns_are_expanded():
    s = next(s for s in read_workbook(ROOT / "00-ref-ids-gr/bSPT-LOIN-ARQ.ods") if s.name == "ARQ-Paredes")
    row = next(r for r in s.rows if len(r) > 2 and r[2] == "IsExternal")
    assert row[8:11] == ["X", "X", "X"]


# --- texto ---------------------------------------------------------------------
def test_norm_removes_accents_and_spaces():
    assert norm("  Classificação:  ") == "classificacao"
    assert norm("Width                    ") == "width"


def test_resolve_name_methods():
    cands = ["Length", "Width", "Height", "NetSideArea"]
    assert resolve_name("Length", cands)[:2] == ("Length", "exact")
    assert resolve_name("length", cands)[:2] == ("Length", "case")
    assert resolve_name("Lenght", cands)[:2] == ("Length", "fuzzy")
    assert resolve_name("With", cands)[:2] == ("Width", "fuzzy")
    assert resolve_name("Espessura?", cands)[0] is None
    # transposição conta 1: 'Lenght' fica mais perto de Length do que de Height
    assert resolve_name("Lenght", ["Length", "Height"])[0] == "Length"
    assert resolve_name("Xyz", ["Length", "Height"])[1] == "none"


# --- parser ----------------------------------------------------------------------
def test_section_aliases():
    assert section_of("Grupos de propriedades") == "propriedades"
    assert section_of("Conjuntos de propriedades") == "propriedades"
    assert section_of("Classe IFC IfcDamper") == "classe_ifc"
    assert section_of("Classificação") == "classificacao"
    assert section_of("Nota:") == "nota"


def test_phase_detection_variants():
    sru = Sheet("x", [[None] * 8 + ["FASE DE PROJETO:"], [None] * 8 + ["Estudo Prévio", "Anteprojeto"]])
    assert find_phases(sru) == {8: "Estudo Prévio", 9: "Anteprojeto"}
    single = Sheet("x", [["FASE DE PROJETO:"] + [None] * 7 + ["Projeto de Execução"]])
    assert find_phases(single) == {8: "Projeto de Execução"}
    assert select_phase({8: "A", 9: "Projeto de Execução"}, "projeto de execucao") == (9, None)
    assert select_phase({8: "A", 9: "B"}, None)[0] is None
    assert select_phase({8: "Projeto de Execução"}, None) == (8, None)


def test_parse_dotted_attributes_create_derived_blocks():
    s = next(s for s in read_workbook(ROOT / "00-ref-ids-gr/SRU0198-LOIN-Geral.xlsx") if s.name == "Projeto")
    ls = parse_sheet(s, "Projeto de Execução", [])
    ents = sorted(b.entity for b in ls.blocks)
    assert ents == ["IfcMapConversion", "IfcProject", "IfcProjectedCRS"]


def test_parse_irregular_entity_position():
    issues: list[Issue] = []
    s = next(s for s in read_workbook(ROOT / "00-ref-ids-gr/bSPT-LOIN-ARQ.ods") if s.name == "ARQ-Tetos")
    ls = parse_sheet(s, "Projeto de Execução", issues)
    assert ls.blocks[0].entity == "IfcCovering"
    assert any(i.code == "layout" for i in issues)
    assert any(i.code == "prop-no-pset" and i.item == "Espessura?" for i in issues)


def test_parse_ignores_index_sheet():
    issues: list[Issue] = []
    s = next(s for s in read_workbook(ROOT / "00-ref-ids-gr/bSPT-LOIN-EST.ods") if s.name == "OBS")
    assert parse_sheet(s, "Projeto de Execução", issues).ignored


def test_phase_column_selects_requirements():
    s = next(s for s in read_workbook(ROOT / "00-ref-ids-gr/SRU0198-LOIN-ARQ.xlsx") if s.name == "ARQ-Paredes")
    ep = parse_sheet(s, "Estudo Prévio", [])
    pe = parse_sheet(s, "Projeto de Execução", [])
    names = lambda ls: {p.name for p in ls.blocks[0].props}
    assert "WarrantyPeriod" not in names(ep) and "WarrantyPeriod" in names(pe)
    assert "Name" not in {a.name for a in ep.blocks[0].attrs}


# --- esquema ---------------------------------------------------------------------
def test_schema_data_types_by_version():
    assert S.pset_properties("IFC4X3_ADD2", "Pset_WallCommon")["FireRating"] == "IFCLABEL"
    assert S.pset_properties("IFC4X3_ADD2", "Qto_WallBaseQuantities")["Length"] == "IFCLENGTHMEASURE"
    assert S.pset_properties("IFC4X3_ADD2", "Pset_ValveTypeCommon")["ValveMechanism"] == "IFCLABEL"  # enumerado
    assert S.pset_properties("IFC4", "Pset_SwitchingDeviceTypeCommon")["NumberOfGangs"] == "IFCINTEGER"
    assert S.pset_properties("IFC4X3_ADD2", "Pset_SwitchingDeviceTypeCommon")["NumberOfGangs"] == "IFCCOUNTMEASURE"


def test_schema_predefined_types_differ_between_versions():
    assert "COPING" in S.predefined_type_values("IFC4X3_ADD2", "IfcCovering")
    assert "COPING" not in S.predefined_type_values("IFC4", "IfcCovering")


# --- diff -----------------------------------------------------------------------
def test_alternation_pattern_is_enumeration():
    assert _ALT.match("(CEILING|FLOORING)")
    assert not _ALT.match("Ss_.*")
