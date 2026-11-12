# HANDOFF — LOIN (.xlsx/.ods) → IDS 1.0

_Actualizado: 2026-11-12_

## Objetivo
Convertir las tablas LOIN de `01-loin-target/` en ficheros `.ids` (buildingSMART IDS 1.0)
con un conversor Python determinista (`loin2ids`) y una skill de Claude Code (`/loin-to-ids`)
para resolver las ambigüedades. Los golden están en `00-ref-ids-gr/`: bSPT (.ods, IFC4) y
SRU0198 (.xlsx, IFC4X3_ADD2), cada uno con Geral/ARQ/EST/MEP. Plan aprobado: `docs/PLAN.md`.

## Decisiones tomadas
- **La verdad es la hoja LOIN corregida contra el esquema IFC.** Los golden tienen errores;
  cada diferencia aceptada está en `tests/golden/known_deviations.yaml` con su motivo
  (43 en total; resumen en `docs/desvios-golden.md`).
- **LLM = skill de Claude Code (sin API).** El LLM solo escribe `decisions.yaml`, nunca XML.
- **Documentación en portugués** (`README.md`, `docs/`).
- **Dependencias:** ifcopenshell 0.9 + ifctester, openpyxl, pyyaml, pytest. El lector ODS es
  propio (zipfile + ElementTree).

## Estado actual — todo el plan implementado
- [x] `loin2ids/`: readers, parser, normalize, schema, rules, writer, decisions, report,
      validate, idsdiff, cli (`convert`, `diff`, `validate`, `schema`, `inspect`)
- [x] Config en `loin2ids/config/` (`aliases.yaml`, `classification_map.yaml`)
- [x] Tests: 71 en verde (`.venv/bin/pytest -q`) — golden + desviaciones, unitarios, XSD +
      esquema, determinismo, robustez con hojas sintéticas, IFC sintético conforme/no conforme,
      target y CLI
- [x] Skill `.claude/skills/loin-to-ids/` (SKILL.md + reference.md) y `CLAUDE.md`
- [x] Target convertido: `out/02-IDS-Arquitetura.ids` (13 specs, 0 bloqueantes, válido)
      con `projects/arquitetura/{project,decisions}.yaml`
- [x] Docs en portugués

## Pendiente / a confirmar por el usuario
- `projects/arquitetura/project.yaml`: completar `author` (e-mail) y `copyright` si se quieren
  en el IDS; revisar `min_occurs` (1 = como los golden).
- `projects/arquitetura/decisions.yaml`: `WBS_bSPT` aceptado **sin dataType** (cualquier valor).
  Poner `data_type: IFCLABEL` si se quiere exigir texto.
- La hoja objetivo tiene la errata `Lenght` en ARQ-Guardas (corregida automáticamente, con aviso).
- `.gitignore` original (copiado desde Windows) fue sobrescrito por error; revisar su contenido.
- Nada está commiteado todavía.

## Recrear el entorno
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]"

## Hallazgos clave (no repetir el análisis)
- Gramática y mapeo completos: `docs/gramatica-loin.md`.
- Fases: SRU 4 columnas, bSPT 3, target 1. Los golden usan "Projeto de Execução".
- dataType: plantillas oficiales de ifcopenshell; los enumerados → IFCLABEL; Qto por TemplateType.
  Cambia entre versiones (NumberOfGangs: IFCINTEGER en IFC4, IFCCOUNTMEASURE en IFC4X3).
- Errores de los golden: entidades cruzadas en SRU EST LançoEscadas/LançoRampas, `Lenght`,
  `ValveMechanisme` con dataType IFCVALVETYPEENUM, omisiones, duplicados. Ver `docs/desvios-golden.md`.
- Decisiones reales de ejemplo (hojas solapadas, `Espessura?`, filtro de M-Betão):
  `tests/golden/decisions/*.yaml`.
