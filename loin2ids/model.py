"""Modelo intermédio: o que a folha LOIN pede, independente do formato IDS."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Level = Literal["blocker", "warning", "info"]


@dataclass
class Issue:
    level: Level
    code: str
    sheet: str
    message: str
    row: int | None = None          # linha 1-based na folha (como no Excel)
    item: str | None = None         # texto da célula em causa (chave para decisions.yaml)
    suggestion: str | None = None

    def location(self) -> str:
        loc = f"'{self.sheet}'"
        if self.row:
            loc += f" linha {self.row}"
        if self.item:
            loc += f" [{self.item}]"
        return loc


@dataclass
class AttrReq:
    name: str
    value: str | None = None        # valor exigido (ex.: SKIRTINGBOARD); None = só existência
    row: int | None = None
    raw: str | None = None


@dataclass
class PropReq:
    pset: str
    name: str
    data_type: str | None = None
    value: str | None = None
    row: int | None = None
    raw: str | None = None


@dataclass
class ClassReq:
    system: str
    prefixes: list[str]             # ["Ss_"] → pattern "Ss_.*"; ["Pr_","Ss_"] → "(Pr_|Ss_).*"
    row: int | None = None
    raw: str | None = None

    @property
    def pattern(self) -> str:
        if len(self.prefixes) == 1:
            return f"{self.prefixes[0]}.*"
        return "(" + "|".join(self.prefixes) + ").*"


@dataclass
class MaterialReq:
    value: str | None = None
    row: int | None = None


@dataclass
class ApplicabilityFilter:
    """Filtro adicional de aplicabilidade sobre um atributo da entidade."""
    attribute: str
    values: list[str] | None = None     # enumeração
    pattern: str | None = None


@dataclass
class Block:
    """Um bloco = uma especificação IDS (uma entidade IFC)."""
    sheet: str
    entity: str | None
    object_name: str | None
    attrs: list[AttrReq] = field(default_factory=list)
    props: list[PropReq] = field(default_factory=list)
    classes: list[ClassReq] = field(default_factory=list)
    materials: list[MaterialReq] = field(default_factory=list)
    filters: list[ApplicabilityFilter] = field(default_factory=list)
    suffix: str | None = None           # para blocos derivados (ex.: IfcMapConversion)
    entity_row: int | None = None
    identifier: str | None = None
    name: str | None = None
    skip: bool = False

    def is_empty(self) -> bool:
        return not (self.attrs or self.props or self.classes or self.materials)


@dataclass
class LoinSheet:
    name: str
    object_name: str | None = None
    phases: dict[int, str] = field(default_factory=dict)   # coluna → nome da fase
    phase_col: int | None = None
    purpose: str | None = None
    blocks: list[Block] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    ignored: bool = False
    ignored_reason: str | None = None
