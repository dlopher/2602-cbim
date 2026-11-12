"""Gera docs/desvios-golden.md a partir de tests/golden/known_deviations.yaml."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    data = yaml.safe_load((ROOT / "tests/golden/known_deviations.yaml").read_text(encoding="utf-8"))
    lines = [
        "# Desvios face aos IDS de referência",
        "",
        "Gerado por `tools/gen_desvios.py` a partir de `tests/golden/known_deviations.yaml`. Não editar à mão.",
        "",
        "Os IDS em `00-ref-ids-gr/` foram feitos manualmente e servem de referência, mas têm erros.",
        "A regra do projeto é que a **folha LOIN corrigida contra o esquema IFC** é a verdade. Abaixo,",
        "cada diferença entre o IDS gerado e o de referência, agrupada por motivo.",
        "",
        "Legenda: `+` existe no gerado e falta na referência · `-` existe na referência e falta no gerado.",
        "",
    ]
    total = 0
    for tag, devs in data.items():
        if tag == "reasons":
            continue
        lines.append(f"## {tag}")
        lines.append("")
        if not devs:
            lines += ["Sem diferenças semânticas.", ""]
            continue
        by_reason = defaultdict(list)
        for k, reason in devs.items():
            by_reason[reason].append(k)
            total += 1
        for reason, keys in by_reason.items():
            lines.append(f"**{reason}**")
            lines.append("")
            for k in sorted(keys):
                lines.append(f"- `{k}`")
            lines.append("")
    lines.insert(4, f"Total: {total} diferenças documentadas.\n")
    out = ROOT / "docs/desvios-golden.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Escrito {out} ({total} desvios)")


if __name__ == "__main__":
    main()
