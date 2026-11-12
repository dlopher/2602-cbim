from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loin2ids.core import convert
from loin2ids.decisions import Decisions, Project

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).parent / "golden"
CASES = yaml.safe_load((GOLDEN / "cases.yaml").read_text(encoding="utf-8"))


def golden_case(tag: str) -> dict:
    c = dict(CASES["cases"][tag])
    d = CASES["defaults"]
    c["loin_path"] = ROOT / d["ref_dir"] / c["loin"]
    c["ids_path"] = ROOT / d["ref_dir"] / c["ids"]
    c["decisions_path"] = GOLDEN / "decisions" / f"{tag}.yaml"
    c["project"] = Project(title=tag, ifc_version=c["ifc_version"], phase=d["phase"],
                           identifier_prefix=c.get("identifier_prefix"), min_occurs=d["min_occurs"])
    return c


def convert_golden(tag: str):
    c = golden_case(tag)
    return convert(c["loin_path"], c["project"], Decisions.load(c["decisions_path"]))


GOLDEN_TAGS = list(CASES["cases"])


@pytest.fixture(scope="session")
def golden_results():
    return {tag: convert_golden(tag) for tag in GOLDEN_TAGS}
