"""Pipeline completo: ficheiro LOIN → (XML IDS, issues, blocos)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .decisions import Decisions, Project
from .model import Block, Issue, LoinSheet
from .normalize import normalize_block
from .parser import parse_sheet
from .readers import read_workbook
from .rules import finalize
from .textutil import clean
from .writer import build_ids, to_xml


def _fill_header(project: Project, sheets: list[LoinSheet], issues: list[Issue]) -> Project:
    """Completa purpose/milestone a partir das folhas quando o project.yaml não os define."""
    from collections import Counter
    from dataclasses import replace

    used = [s for s in sheets if not s.ignored and s.phase_col is not None]
    changes = {}
    if project.milestone is None and used:
        phase = Counter(s.phases[s.phase_col] for s in used).most_common(1)[0][0]
        changes["milestone"] = phase
    if project.purpose is None:
        purposes = Counter(s.purpose for s in used if s.purpose)
        if purposes:
            changes["purpose"] = purposes.most_common(1)[0][0]
            if len(purposes) > 1:
                issues.append(Issue("info", "header-purpose", "(cabeçalho)",
                                    f"Folhas com propósitos diferentes; usado o mais frequente: "
                                    f"'{changes['purpose']}'. Defina 'purpose' no project.yaml para fixar."))
    if project.author and "@" not in project.author:
        issues.append(Issue("warning", "header-author", "(cabeçalho)",
                            f"author '{project.author}' não é um e-mail; o IDS 1.0 exige e-mail — omitido."))
        changes["author"] = None
    return replace(project, **changes) if changes else project


@dataclass
class Result:
    xml: str | None
    issues: list[Issue]
    sheets: list[LoinSheet]
    blocks: list[Block]

    @property
    def blockers(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "blocker"]


def convert(path: str | Path, project: Project, decisions: Decisions | None = None,
            force: bool = False) -> Result:
    decisions = decisions or Decisions()
    issues: list[Issue] = []
    sheets = [parse_sheet(s, project.phase, issues) for s in read_workbook(path)]
    blocks: list[Block] = []
    for ls in sheets:
        if ls.ignored:
            continue
        sd = decisions.sheet(ls.name)
        for b in ls.blocks:
            normalize_block(b, project.ifc_version, decisions, issues)
            blocks.append(b)
        if sd.get("skip"):
            # problemas de folhas omitidas deixam de interessar (fica só o registo da omissão)
            sname = clean(ls.name)
            issues[:] = [i for i in issues if not (i.sheet == sname and i.code != "sheet-skipped")]
    live = finalize(blocks, project, decisions, issues)
    project = _fill_header(project, sheets, issues)
    if not live:
        issues.append(Issue("blocker", "no-specs", "(ficheiro)",
                            "Nenhuma especificação com requisitos na fase escolhida — o IDS 1.0 exige pelo menos uma."))
        return Result(xml=None, issues=issues, sheets=sheets, blocks=live)
    blockers = [i for i in issues if i.level == "blocker"]
    xml = None
    if not blockers or force:
        xml = to_xml(build_ids(live, project))
    return Result(xml=xml, issues=issues, sheets=sheets, blocks=live)
