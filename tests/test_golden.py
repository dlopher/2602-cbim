"""Regressão contra os IDS de referência (00-ref-ids-gr) com desvios conhecidos documentados."""
from __future__ import annotations

import pytest
import yaml

from loin2ids.idsdiff import Diff, load_specs, match_specs

from conftest import GOLDEN, GOLDEN_TAGS, golden_case

KNOWN = yaml.safe_load((GOLDEN / "known_deviations.yaml").read_text(encoding="utf-8"))


def _deviations(result, ids_path, tmp_path) -> list[str]:
    out = tmp_path / "gen.ids"
    out.write_text(result.xml, encoding="utf-8")
    _, a = load_specs(out)
    _, b = load_specs(ids_path)
    return Diff(*match_specs(a, b)).deviations()


@pytest.mark.parametrize("tag", GOLDEN_TAGS)
def test_golden_no_blockers(tag, golden_results):
    res = golden_results[tag]
    assert not res.blockers, "\n".join(f"{i.code} {i.location()}: {i.message}" for i in res.blockers)
    assert res.xml


@pytest.mark.parametrize("tag", GOLDEN_TAGS)
def test_golden_deviations_are_known(tag, golden_results, tmp_path):
    devs = set(_deviations(golden_results[tag], golden_case(tag)["ids_path"], tmp_path))
    known = set((KNOWN.get(tag) or {}).keys())
    new = sorted(devs - known)
    stale = sorted(known - devs)
    msg = []
    if new:
        msg.append("Desvios NOVOS (corrija o conversor ou documente em known_deviations.yaml):\n  "
                   + "\n  ".join(new))
    if stale:
        msg.append("Desvios listados que já não ocorrem (remova-os de known_deviations.yaml):\n  "
                   + "\n  ".join(stale))
    assert not msg, "\n".join(msg)


def test_every_known_deviation_has_reason():
    for tag, devs in KNOWN.items():
        if tag == "reasons":
            continue
        assert tag in GOLDEN_TAGS, f"caso desconhecido em known_deviations.yaml: {tag}"
        for k, reason in (devs or {}).items():
            assert isinstance(reason, str) and len(reason) > 10, f"{tag}: '{k}' sem motivo"


@pytest.mark.parametrize("tag", GOLDEN_TAGS)
def test_golden_all_reference_specs_matched(tag, golden_results, tmp_path):
    """Nenhuma especificação da referência pode ficar sem par (exceto se documentado)."""
    devs = _deviations(golden_results[tag], golden_case(tag)["ids_path"], tmp_path)
    missing = [d for d in devs if "só na referência" in d]
    known = set((KNOWN.get(tag) or {}).keys())
    assert set(missing) <= known
