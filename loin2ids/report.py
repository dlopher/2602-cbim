"""Relatório de problemas (Markdown para pessoas, JSON para a skill/LLM)."""
from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import asdict

from .model import Issue

LEVEL_TITLE = OrderedDict([
    ("blocker", "Bloqueantes (impedem gerar o IDS)"),
    ("warning", "Avisos (IDS gerado, mas confirme)"),
    ("info", "Informação"),
])


def to_json(issues: list[Issue], source: str, output: str | None) -> str:
    data = {
        "source": source,
        "output": output,
        "counts": {lvl: sum(1 for i in issues if i.level == lvl) for lvl in LEVEL_TITLE},
        "issues": [asdict(i) for i in issues],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def to_markdown(issues: list[Issue], source: str, output: str | None) -> str:
    lines = [f"# Relatório de conversão LOIN → IDS", "", f"- Origem: `{source}`",
             f"- IDS: `{output}`" if output else "- IDS: **não gerado** (há bloqueantes)", ""]
    counts = {lvl: sum(1 for i in issues if i.level == lvl) for lvl in LEVEL_TITLE}
    lines.append("| Nível | N.º |")
    lines.append("|---|---|")
    for lvl, n in counts.items():
        lines.append(f"| {lvl} | {n} |")
    lines.append("")
    for lvl, title in LEVEL_TITLE.items():
        group = [i for i in issues if i.level == lvl]
        if not group:
            continue
        lines += [f"## {title}", ""]
        # agrupa mensagens repetidas (ex.: mesma gralha em várias folhas)
        seen: OrderedDict[tuple, list[Issue]] = OrderedDict()
        for i in group:
            key = (i.code, i.message, i.suggestion)
            seen.setdefault(key, []).append(i)
        for (code, msg, sugg), items in seen.items():
            if len(items) == 1:
                i = items[0]
                lines.append(f"- **{code}** — {i.location()}: {i.message}")
            else:
                locs = ", ".join(f"'{i.sheet}'" + (f" l.{i.row}" if i.row else "") for i in items)
                lines.append(f"- **{code}** — {msg} ({len(items)}×: {locs})")
            if sugg:
                lines.append(f"  - Sugestão: {sugg}")
        lines.append("")
    return "\n".join(lines)
