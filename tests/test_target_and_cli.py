"""Folha real em 01-loin-target e interface de linha de comandos."""
from __future__ import annotations

import pytest

from loin2ids.cli import main
from loin2ids.core import convert
from loin2ids.decisions import Decisions, Project

from conftest import ROOT

TARGET = ROOT / "01-loin-target/02-LOIN-Arquitetura.xlsx"
PROJ = ROOT / "projects/arquitetura"


@pytest.mark.skipif(not TARGET.exists(), reason="folha alvo ausente")
def test_target_converts_without_blockers():
    res = convert(TARGET, Project.load(PROJ / "project.yaml"), Decisions.load(PROJ / "decisions.yaml"))
    assert not res.blockers
    assert len(res.blocks) == 13
    assert not [i for i in res.issues if i.code == "pset-custom"]


@pytest.mark.skipif(not TARGET.exists(), reason="folha alvo ausente")
def test_cli_convert_and_validate(tmp_path, capsys):
    out = tmp_path / "t.ids"
    rc = main(["convert", str(TARGET), "--project", str(PROJ / "project.yaml"),
               "--decisions", str(PROJ / "decisions.yaml"), "-o", str(out)])
    assert rc == 0 and out.exists()
    assert (tmp_path / "t.issues.md").exists() and (tmp_path / "t.issues.json").exists()
    assert main(["validate", str(out)]) == 0
    ref = ROOT / "00-ref-ids-gr/SRU0198-IDS-ARQ.ids"
    main(["diff", str(out), str(ref)])
    assert "Especificações emparelhadas: 13" in capsys.readouterr().out


def test_cli_blockers_exit_code(tmp_path):
    from loin_builder import WALL, workbook
    path = workbook(tmp_path / "a.xlsx", [dict(WALL, entity="IfcNaoExiste")])
    rc = main(["convert", str(path), "--phase", "Projeto de Execução", "-o", str(tmp_path / "a.ids")])
    assert rc == 2
    assert not (tmp_path / "a.ids").exists()


def test_cli_schema(capsys):
    assert main(["schema", "pset", "Pset_WallCommon"]) == 0
    assert "FireRating: IFCLABEL" in capsys.readouterr().out
    assert main(["schema", "entity", "IfcWal"]) == 1
