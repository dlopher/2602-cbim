"""Decisões manuais/LLM (decisions.yaml) e configuração do projeto (project.yaml)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .textutil import compact


@dataclass
class Decisions:
    sheets: dict = field(default_factory=dict)
    psets: dict = field(default_factory=dict)
    classification_tables: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None) -> "Decisions":
        if not path or not Path(path).exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        unknown = set(data) - {"sheets", "psets", "classification_tables"}
        if unknown:
            raise ValueError(f"decisions.yaml: chaves desconhecidas {sorted(unknown)}")
        return cls(sheets=data.get("sheets") or {}, psets=data.get("psets") or {},
                   classification_tables=data.get("classification_tables") or {})

    def sheet(self, name: str) -> dict:
        key = compact(name)
        for k, v in self.sheets.items():
            if compact(k) == key:
                return v or {}
        return {}

    def row(self, sheet: str, item: str | None) -> dict | None:
        if not item:
            return None
        rows = self.sheet(sheet).get("rows") or {}
        for k, v in rows.items():
            if compact(k) == compact(item):
                return v or {}
        return None

    def pset(self, name: str) -> dict | None:
        for k, v in self.psets.items():
            if k == name:
                return v or {}
        return None

    def table(self, name: str):
        for k, v in self.classification_tables.items():
            if compact(k) == compact(name):
                return v
        return None


@dataclass
class Project:
    title: str = "IDS"
    copyright: str | None = None
    version: str | None = None
    description: str | None = None
    author: str | None = None
    date: str | None = None
    purpose: str | None = None
    milestone: str | None = None
    ifc_version: str = "IFC4X3_ADD2"
    phase: str | None = None
    identifier_prefix: str | None = None
    min_occurs: int = 1

    @classmethod
    def load(cls, path: str | Path | None, **overrides) -> "Project":
        data = {}
        if path:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        data.update({k: v for k, v in overrides.items() if v is not None})
        known = set(cls.__dataclass_fields__)
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"project.yaml: chaves desconhecidas {sorted(unknown)} (válidas: {sorted(known)})")
        if data.get("date") is not None:
            data["date"] = str(data["date"])
        if data.get("version") is not None:
            data["version"] = str(data["version"])
        return cls(**data)
