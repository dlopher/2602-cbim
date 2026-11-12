"""Interface de linha de comandos: ``loin2ids <comando>`` (ou ``python -m loin2ids``)."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import schema as S


def _cmd_convert(a) -> int:
    from .core import convert
    from .decisions import Decisions, Project
    from .report import to_json, to_markdown

    project = Project.load(a.project, ifc_version=a.ifc_version, phase=a.phase)
    decisions = Decisions.load(a.decisions)
    src = Path(a.loin)
    out = Path(a.output) if a.output else Path("out") / (src.stem.replace("LOIN", "IDS") + ".ids")
    res = convert(src, project, decisions, force=a.force)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = None
    if res.xml is not None:
        out.write_text(res.xml, encoding="utf-8")
        written = str(out)
    report = Path(a.report) if a.report else out.with_suffix(".issues.md")
    report.write_text(to_markdown(res.issues, str(src), written), encoding="utf-8")
    report.with_suffix(".json").write_text(to_json(res.issues, str(src), written), encoding="utf-8")

    n = {lvl: sum(1 for i in res.issues if i.level == lvl) for lvl in ("blocker", "warning", "info")}
    print(f"{len(res.blocks)} especificações | bloqueantes: {n['blocker']} | avisos: {n['warning']} | info: {n['info']}")
    for i in res.blockers:
        print(f"  BLOQUEANTE {i.code} {i.location()}: {i.message}")
    print(f"Relatório: {report}")
    if written:
        from .validate import semantic_errors, xsd_errors
        errs = xsd_errors(written) + semantic_errors(written)
        for e in errs:
            print(f"  INVÁLIDO: {e}")
        print(f"IDS: {written}" + (" (XSD + esquema IFC: OK)" if not errs else ""))
        if errs:
            return 3
    if res.blockers:
        return 2
    return 0


def _cmd_diff(a) -> int:
    from .idsdiff import diff_files

    d = diff_files(a.a, a.b)
    devs = d.deviations(include_meta=a.meta)
    print(f"Especificações emparelhadas: {len(d.pairs)} | só em A: {len(d.only_a)} | só em B: {len(d.only_b)}")
    for x in devs:
        print("  " + x)
    if not devs:
        print("  Sem diferenças semânticas.")
    return 0 if not devs else 1


def _cmd_validate(a) -> int:
    from .validate import run_on_ifc, semantic_errors, xsd_errors

    errs = xsd_errors(a.ids)
    for e in errs:
        print(f"XSD: {e}")
    if not errs:
        for e in semantic_errors(a.ids):
            print(f"ESQUEMA IFC: {e}")
            errs.append(e)
    if not errs:
        print("IDS válido (XSD 1.0 + esquema IFC).")
    if a.ifc:
        doc = run_on_ifc(a.ids, a.ifc)
        failed = 0
        for spec in doc.specifications:
            status = "OK" if spec.status else ("N/A" if spec.status is None else "FALHA")
            failed += spec.status is False
            print(f"  [{status}] {spec.identifier} — {spec.name}")
        return 1 if (errs or failed) else 0
    return 1 if errs else 0


def _cmd_schema(a) -> int:
    v = a.ifc_version
    if a.what == "entity":
        ent = S.entity(v, a.name)
        if not ent:
            from .textutil import resolve_name
            _, _, close = resolve_name(a.name, list(S.entity_names(v)))
            print(f"Entidade '{a.name}' não existe em {v}. Próximas: {', '.join(close)}")
            return 1
        print(f"{ent} ({v})")
        print("  atributos: " + ", ".join(S.entity_attributes(v, ent)))
        pt = S.predefined_type_values(v, ent)
        if pt:
            print("  PredefinedType: " + ", ".join(pt))
        return 0
    if a.what == "pset":
        props = S.pset_properties(v, a.name)
        if not props:
            from .textutil import resolve_name
            _, _, close = resolve_name(a.name, list(S.pset_names(v)))
            print(f"Conjunto '{a.name}' não existe em {v}. Próximos: {', '.join(close)}")
            return 1
        ps = S.pset(v, a.name)
        applic = getattr(ps, "ApplicableEntity", None)
        print(f"{a.name} ({v})" + (f" — aplicável a: {applic}" if applic else ""))
        for k, t in props.items():
            print(f"  {k}: {t or '(sem tipo)'}")
        return 0
    if a.what == "search":
        q = a.name.lower()
        hits = [n for n in S.pset_names(v) if q in n.lower()]
        hits += [f"{n}.{p}" for n in S.pset_names(v) for p in S.pset_properties(v, n) if q in p.lower()]
        print("\n".join(hits[:100]) or "(nada)")
        return 0
    return 1


def _cmd_inspect(a) -> int:
    from .core import convert
    from .decisions import Decisions, Project

    project = Project.load(a.project, ifc_version=a.ifc_version, phase=a.phase)
    res = convert(a.loin, project, Decisions.load(a.decisions), force=True)
    data = []
    for ls in res.sheets:
        data.append({"sheet": ls.name, "object": ls.object_name, "phases": ls.phases,
                     "phase_col": ls.phase_col, "ignored": ls.ignored_reason,
                     "blocks": [asdict(b) for b in ls.blocks], "notes": ls.notes})
    print(json.dumps(data, ensure_ascii=False, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="loin2ids", description="Conversor de folhas LOIN (.xlsx/.ods) para IDS 1.0")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--project", help="project.yaml (cabeçalho IDS, versão IFC, fase)")
        sp.add_argument("--decisions", help="decisions.yaml (resoluções manuais/LLM)")
        sp.add_argument("--phase", help="fase a usar quando a folha tem várias (ex.: 'Projeto de Execução')")
        sp.add_argument("--ifc-version", choices=S.SUPPORTED_VERSIONS, help="sobrepõe a versão do project.yaml")

    c = sub.add_parser("convert", help="converte uma folha LOIN em IDS")
    c.add_argument("loin")
    common(c)
    c.add_argument("-o", "--output", help="ficheiro .ids de saída (por omissão out/<nome>.ids)")
    c.add_argument("--report", help="relatório .md (por omissão ao lado do .ids)")
    c.add_argument("--force", action="store_true", help="gera o IDS mesmo com bloqueantes (omite o que falhar)")
    c.set_defaults(func=_cmd_convert)

    d = sub.add_parser("diff", help="compara semanticamente dois IDS (A=gerado, B=referência)")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--meta", action="store_true", help="inclui diferenças de name/identifier/ifcVersion")
    d.set_defaults(func=_cmd_diff)

    v = sub.add_parser("validate", help="valida um IDS (XSD + esquema IFC) e opcionalmente aplica-o a um IFC")
    v.add_argument("ids")
    v.add_argument("--ifc", help="modelo IFC a verificar")
    v.set_defaults(func=_cmd_validate)

    s = sub.add_parser("schema", help="consulta o esquema IFC (entity|pset|search)")
    s.add_argument("what", choices=["entity", "pset", "search"])
    s.add_argument("name")
    s.add_argument("--ifc-version", default="IFC4X3_ADD2", choices=S.SUPPORTED_VERSIONS)
    s.set_defaults(func=_cmd_schema)

    i = sub.add_parser("inspect", help="mostra o modelo intermédio lido da folha (JSON)")
    i.add_argument("loin")
    common(i)
    i.set_defaults(func=_cmd_inspect)

    a = p.parse_args(argv)
    try:
        return a.func(a)
    except (ValueError, FileNotFoundError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
