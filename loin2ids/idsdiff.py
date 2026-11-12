"""Comparação semântica de dois ficheiros IDS (ignora ordem, formatação e comentários).

Duas especificações são emparelhadas por identificador (normalizado), depois pelo
sufixo do identificador e por fim pela entidade. As facetas são comparadas como
conjuntos de tuplos canónicos; padrões que são simples alternativas de literais
("(A|B|C)") são tratados como enumerações.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET

from .textutil import compact

I = "{http://standards.buildingsmart.org/IDS}"
XS = "{http://www.w3.org/2001/XMLSchema}"
_ALT = re.compile(r"^\(?([A-Za-z0-9_]+(?:\|[A-Za-z0-9_]+)*)\)?$")


def _value(el) -> tuple | None:
    if el is None:
        return None
    sv = el.find(I + "simpleValue")
    if sv is not None:
        return ("=", (sv.text or "").strip())
    r = el.find(XS + "restriction")
    if r is None:
        return None
    enums = [c.get("value") for c in r if c.tag == XS + "enumeration"]
    pats = [c.get("value") for c in r if c.tag == XS + "pattern"]
    others = tuple(sorted((c.tag.replace(XS, ""), c.get("value")) for c in r
                          if c.tag not in (XS + "enumeration", XS + "pattern")))
    if enums and not pats and not others:
        return ("in", tuple(sorted(enums)))
    if pats and not enums and not others and len(pats) == 1:
        m = _ALT.match(pats[0])
        if m:
            return ("in", tuple(sorted(m.group(1).split("|"))))
        return ("re", pats[0])
    return ("r", tuple(sorted(enums)), tuple(sorted(pats)), others)


def _fmt_value(v) -> str:
    if v is None:
        return ""
    if v[0] == "=":
        return f"={v[1]}"
    if v[0] == "in":
        return "∈{" + ",".join(v[1]) + "}"
    if v[0] == "re":
        return f"~/{v[1]}/"
    return "restr" + str(v[1:])


def facet(el, default_card: str | None) -> tuple:
    t = el.tag.replace(I, "")
    card = el.get("cardinality", default_card)
    if t == "entity":
        return ("entity", _fmt_value(_value(el.find(I + "name"))).lstrip("=").upper(),
                _fmt_value(_value(el.find(I + "predefinedType"))))
    if t == "attribute":
        return ("attribute", _fmt_value(_value(el.find(I + "name"))).lstrip("="),
                _fmt_value(_value(el.find(I + "value"))), card)
    if t == "property":
        dt = el.get("dataType")
        return ("property", _fmt_value(_value(el.find(I + "propertySet"))).lstrip("="),
                _fmt_value(_value(el.find(I + "baseName"))).lstrip("="),
                dt.upper() if dt else "", _fmt_value(_value(el.find(I + "value"))), card)
    if t == "classification":
        return ("classification", _fmt_value(_value(el.find(I + "system"))).lstrip("="),
                _fmt_value(_value(el.find(I + "value"))), card)
    if t == "material":
        return ("material", _fmt_value(_value(el.find(I + "value"))), card)
    if t == "partOf":
        return ("partOf", el.get("relation", ""), card)
    return (t, ET.tostring(el, encoding="unicode"))


def fmt_facet(f: tuple) -> str:
    kind = f[0]
    if kind == "entity":
        return f"entity {f[1]}" + (f" predefinedType{f[2]}" if f[2] else "")
    if kind == "attribute":
        return f"attribute {f[1]}{f[2]}" + (f" [{f[3]}]" if f[3] and f[3] != "required" else "")
    if kind == "property":
        s = f"property {f[1]}.{f[2]}"
        s += f" ({f[3]})" if f[3] else " (sem dataType)"
        s += f[4]
        return s + (f" [{f[5]}]" if f[5] and f[5] != "required" else "")
    if kind == "classification":
        return f"classification {f[1]}{f[2]}" + (f" [{f[3]}]" if f[3] and f[3] != "required" else "")
    if kind == "material":
        return f"material{f[1]}" + (f" [{f[2]}]" if f[2] and f[2] != "required" else "")
    return " ".join(map(str, f))


@dataclass
class Spec:
    identifier: str
    name: str
    ifc_version: str
    min_occurs: str
    max_occurs: str
    applicability: frozenset
    requirements: frozenset
    duplicates: list = field(default_factory=list)

    @property
    def entity(self) -> str:
        ents = [f[1] for f in self.applicability if f[0] == "entity"]
        return ents[0] if ents else ""


def load_specs(path: str | Path) -> tuple[dict, list[Spec]]:
    root = ET.parse(path).getroot()
    info_el = root.find(I + "info")
    info = {c.tag.replace(I, ""): (c.text or "").strip() for c in info_el} if info_el is not None else {}
    specs = []
    for s in root.iter(I + "specification"):
        app = s.find(I + "applicability")
        req = s.find(I + "requirements")
        app_f = [facet(f, None) for f in app] if app is not None else []
        req_f = [facet(f, "required") for f in req] if req is not None else []
        dups = sorted({f for f in req_f if req_f.count(f) > 1})
        specs.append(Spec(identifier=(s.get("identifier") or "").strip(), name=(s.get("name") or "").strip(),
                          ifc_version=" ".join(sorted((s.get("ifcVersion") or "").split())),
                          min_occurs=(app.get("minOccurs", "0") if app is not None else ""),
                          max_occurs=(app.get("maxOccurs", "unbounded") if app is not None else ""),
                          applicability=frozenset(app_f), requirements=frozenset(req_f), duplicates=dups))
    return info, specs


def _suffix(ident: str) -> str:
    return compact(ident.split("-", 1)[1] if "-" in ident else ident)


def match_specs(a: list[Spec], b: list[Spec]) -> tuple[list[tuple[Spec, Spec]], list[Spec], list[Spec]]:
    pairs = []
    ra, rb = list(a), list(b)
    for keyf in (lambda s: compact(s.identifier), lambda s: _suffix(s.identifier),
                 lambda s: compact(s.name), lambda s: s.entity + "|" + "|".join(sorted(map(str, s.applicability)))):
        for sa in list(ra):
            cands = [sb for sb in rb if keyf(sb) == keyf(sa) and keyf(sa)]
            if len(cands) == 1 and sum(1 for x in ra if keyf(x) == keyf(sa)) == 1:
                pairs.append((sa, cands[0]))
                ra.remove(sa)
                rb.remove(cands[0])
    # por fim: entidade única dos dois lados
    for sa in list(ra):
        cands = [sb for sb in rb if sb.entity == sa.entity]
        if len(cands) == 1 and sum(1 for x in ra if x.entity == sa.entity) == 1:
            pairs.append((sa, cands[0]))
            ra.remove(sa)
            rb.remove(cands[0])
    return pairs, ra, rb


@dataclass
class Diff:
    """Diferenças entre A (gerado) e B (referência)."""
    pairs: list[tuple[Spec, Spec]]
    only_a: list[Spec]
    only_b: list[Spec]

    def deviations(self, include_meta: bool = False) -> list[str]:
        """Lista estável de diferenças, chaveada pelo identificador da referência (B)."""
        out = []
        for sa, sb in self.pairs:
            key = sb.identifier
            for f in sorted(sa.applicability - sb.applicability):
                out.append(f"{key} | aplicabilidade + {fmt_facet(f)}")
            for f in sorted(sb.applicability - sa.applicability):
                out.append(f"{key} | aplicabilidade - {fmt_facet(f)}")
            for f in sorted(sa.requirements - sb.requirements):
                out.append(f"{key} | requisito + {fmt_facet(f)}")
            for f in sorted(sb.requirements - sa.requirements):
                out.append(f"{key} | requisito - {fmt_facet(f)}")
            for f in sb.duplicates:
                out.append(f"{key} | referência duplicada {fmt_facet(f)}")
            if sa.min_occurs != sb.min_occurs:
                out.append(f"{key} | minOccurs {sa.min_occurs} vs {sb.min_occurs}")
            if include_meta:
                if sa.name != sb.name:
                    out.append(f"{key} | name '{sa.name}' vs '{sb.name}'")
                if sa.identifier != sb.identifier:
                    out.append(f"{key} | identifier '{sa.identifier}' vs '{sb.identifier}'")
                if sa.ifc_version != sb.ifc_version:
                    out.append(f"{key} | ifcVersion {sa.ifc_version} vs {sb.ifc_version}")
        for s in self.only_a:
            out.append(f"(gerado) {s.identifier} | especificação só no gerado ({s.entity})")
        for s in self.only_b:
            out.append(f"{s.identifier} | especificação só na referência ({s.entity})")
        return sorted(out)

    def is_equal(self) -> bool:
        return not self.deviations()


def diff_files(a: str | Path, b: str | Path) -> Diff:
    _, sa = load_specs(a)
    _, sb = load_specs(b)
    return Diff(*match_specs(sa, sb))
