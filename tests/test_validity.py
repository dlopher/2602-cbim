"""Todo o IDS gerado é válido (XSD 1.0 + esquema IFC) e a conversão é determinística."""
from __future__ import annotations

import pytest

from loin2ids.validate import semantic_errors, xsd_errors

from conftest import GOLDEN_TAGS, convert_golden


@pytest.mark.parametrize("tag", GOLDEN_TAGS)
def test_generated_ids_is_valid(tag, golden_results, tmp_path):
    p = tmp_path / f"{tag}.ids"
    p.write_text(golden_results[tag].xml, encoding="utf-8")
    assert xsd_errors(p) == []
    assert semantic_errors(p) == []


@pytest.mark.parametrize("tag", ["SRU0198-ARQ", "bSPT-MEP"])
def test_conversion_is_deterministic(tag, golden_results):
    assert convert_golden(tag).xml == golden_results[tag].xml


def test_reference_ids_are_flagged_by_semantic_check():
    """O verificador semântico deteta os erros conhecidos das referências (ex.: 'Lenght')."""
    from conftest import ROOT
    errs = semantic_errors(ROOT / "00-ref-ids-gr/SRU0198-IDS-MEP.ids")
    assert any("Lenght" in e for e in errs)
    assert any("ValveMechanisme" in e for e in errs)
