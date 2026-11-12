# Plan: LOIN (.xlsx/.ods) → IDS 1.0 — conversor determinista + skill Claude Code

## Context
Se quiere traducir de forma fiable las tablas LOIN (Level of Information Need) de cada disciplina a ficheros `.ids` (buildingSMART IDS 1.0) para verificar modelos IFC. `00-ref-ids-gr/` contiene 8 pares golden (bSPT y SRU0198 × Geral/ARQ/EST/MEP; bSPT en .ods, SRU en .xlsx; IDS hechos con usBIM.IDSeditor). El primer fichero real a convertir es `01-loin-target/02-LOIN-Arquitetura.xlsx` (formato SRU, una sola columna de fase "Projeto de Execução").

Decisiones del usuario:
- **Verdad = hoja LOIN corregida contra el esquema IFC**; los golden se comparan con una lista de desviaciones conocidas (tienen errores: bSPT Paredes sin `Length`, SRU Esteiras con `Lenght`, omisiones en LançoEscadas/Rampas, etc.).
- **LLM = skill de Claude Code** (sin API): el LLM solo escribe `decisions.yaml`; nunca el XML.
- **Docs en portugués.**
- **Dependencias: ifcopenshell + ifctester** (+ openpyxl, odfpy o lector ODS propio, lxml, PyYAML, pytest).

## Hallazgos que fijan el diseño
- Gramática de hoja estable: col A cabeceras (`Objetos`, `Ator requerente/fornecedor`, `Propósito|Proposito`, `Referências EIR`, `Requisitos mínimos …`); col B secciones (`Classe IFC`, `Atributos`, `Grupos|Conjuntos de propriedades`, `Materiais`, `Classificação`, `Georeferenciação`, `Referências`); col C/D nombre; col H Pset/tabla; col I+ marcas por fase (`X` o valor, p.ej. `SKIRTINGBOARD`).
- Fases variables: 4 (SRU), 3 (bSPT), 1 (target). Los golden SRU usan la columna "Projeto de Execução".
- Mapeos: identifier = nombre de hoja (trim); name = `Objetos`; `X` en atributo → `attribute cardinality=required`; propiedad → `property` con `dataType` del esquema (Pset propio → sin dataType); `Materiais` → `material required`; SECClasS tabla → patrones (`Entidades`→`En_.*`, `Espaços/ locais`→`SL_.*`, `Sistemas`→`Ss_.*`, `Produtos`→`Pr_.*`, `Elementos/ Funções, Sistemas e Produtos`→`Ss_/EF_/Pr_`).
- Casos especiales: valor no-`X` en PredefinedType → filtro en applicability + requisito; varios `IfcCovering` → exclusión del enum en RevPavCobTet; Geral `IfcMapConversion.Eastings` → spec propia por entidad; hoja Classificação → 2 specs (IfcClassification + IfcClassificationReference); hojas a ignorar (`OBS`, `M-Betão`?); typos (`Predifined Type`, `Lenght`, `With`, espacios finales, `SECCLASS`).
- ifcVersion: bSPT=IFC4, SRU=IFC4X3_ADD2 → parámetro de proyecto (default IFC4X3_ADD2 para target).

## Arquitectura
```
loin2ids/                       paquete Python
  readers.py      xlsx/ods → grid normalizado (celdas combinadas, repeticiones ODS, trim)
  parser.py       grid → modelo intermedio (LoinSheet: entity, phases, attrs, props, materials, classif, notes)
  normalize.py    correcciones deterministas: alias de secciones, typos por fuzzy-match contra esquema, PredefinedType, case
  schema.py       ifcopenshell: entidades válidas, atributos, Psets/Qtos → dataType por versión IFC
  rules.py        modelo → specs IDS (mapeo SECClasS, splits Geral, exclusiones de applicability)
  decisions.py    carga/aplica decisions.yaml (overrides por hoja/fila)
  writer.py       specs → XML IDS 1.0 (orden y formato estables)
  report.py       issues.json/md: ambigüedades, correcciones aplicadas, nivel (info/warn/blocker)
  cli.py          `loin2ids convert <loin> --phase "Projeto de Execução" --project project.yaml [--decisions d.yaml]`
                  `loin2ids diff <a.ids> <b.ids>`  (comparación semántica, no textual)
config/
  classification_map.yaml       tabla SECClasS → patrones (ampliable)
  aliases.yaml                  sinónimos de secciones/cabeceras (pt)
projects/<proj>/project.yaml    info IDS: title, copyright, version, author(email), date, purpose, milestone, ifcVersion
projects/<proj>/decisions.yaml  decisiones (escritas por LLM/humano, versionadas)
out/                            .ids generados + issues.md
```
Flujo: `convert` → si hay issues `blocker` falla con código ≠0 y genera `issues.md`; la skill los resuelve en `decisions.yaml` y re-ejecuta.

## Qué es determinista y qué LLM
- **Determinista (script)**: lectura, detección de secciones y fase, mapeo X→facetas, dataType, typos con match único contra esquema (distancia ≤2), SECClasS conocidos, splits Geral, exclusión de PredefinedType entre specs de la misma entidad, escritura y validación.
- **LLM (skill, vía decisions.yaml)**: filas sin Pset o con nombre no resoluble (`Espessura?`), layouts irregulares (`Classe IFC IfcCovering` dentro de Atributos), tablas de clasificación nuevas, Psets propios sin tipo (`WBS_bSPT`, `MapaQuantidadesSRU`), hojas dudosas a ignorar, typos con varios candidatos, nombres de spec.

## Skill `.claude/skills/loin-to-ids/SKILL.md`
Pasos: (1) identificar fichero en `01-loin-target/` y proyecto; crear/pedir `project.yaml` (author email, ifcVersion, fase); (2) ejecutar `convert`; (3) leer `issues.md`, proponer entradas en `decisions.yaml` justificadas con el esquema IFC (consultar `schema.py` vía CLI `loin2ids schema pset Pset_X`), pedir confirmación al usuario en las de nivel blocker; (4) re-ejecutar hasta 0 blockers; (5) validar con ifctester y resumir. Incluye referencia `reference.md` con la gramática LOIN y ejemplos de los golden. Además un `CLAUDE.md` del repo con contexto del proyecto.

## Tests (pytest, `tests/`)
1. **Unitarios**: readers (merged cells, ODS repeat), parser por sección, normalize (typos), mapeo SECClasS, dataType lookup IFC4 vs IFC4X3.
2. **Golden (regresión)**: para los 8 pares, `convert` (fase PE, ifcVersion del golden) y `diff` semántico contra el `.ids` golden; comparación por specs (identifier normalizado AQR→ARQ, acentos) y facetas como conjuntos (orden irrelevante). Diferencias permitidas solo si están en `tests/golden/known_deviations.yaml` con motivo (p.ej. "golden omite Qto_WallBaseQuantities.Length"). Nueva desviación = test rojo.
3. **Validez**: todo `.ids` generado valida contra XSD IDS 1.0 (ifctester `ids.open(...)`/validación XSD); todas las entidades/Psets/propiedades existen en el esquema elegido.
4. **Funcional con IFC sintéticos**: con ifcopenshell crear un IFC mínimo que cumple (pared con Psets, clasificación Ss_/EF_/Pr_, material) y otro que incumple; ifctester debe dar pass/fail esperado por spec.
5. **Determinismo**: dos ejecuciones → bytes idénticos; `decisions.yaml` vacío vs aplicado cambia solo lo esperado.
6. **Robustez**: fixtures mutadas (columnas de fase desplazadas, hojas extra, espacios, mayúsculas) → mismo resultado o issue explícito, nunca salida silenciosa errónea.
7. **Target**: test de humo sobre `01-loin-target/02-LOIN-Arquitetura.xlsx` → 0 blockers tras decisions.

## Documentación (portugués, `docs/`)
`README.md` (instalação, uso rápido), `docs/guia-utilizador.md` (preparar a folha LOIN, convenções, project.yaml, decisions.yaml, fluxo com Claude Code), `docs/gramatica-loin.md` (estrutura esperada da folha e mapeamento → IDS com exemplos), `docs/desenvolvimento.md` (arquitetura, testes, como acrescentar classificações/aliases), `docs/desvios-golden.md` (gerado a partir de known_deviations.yaml).

## Orden de implementación
1. `pyproject.toml` + deps, readers + parser + tests unitarios sobre los 8 golden.
2. schema + normalize + rules + writer → convert; `diff` semántico.
3. Test golden; iterar hasta que solo queden desviaciones explicables → `known_deviations.yaml`.
4. decisions + report + CLI; tests de validez, IFC sintéticos, determinismo, robustez.
5. Skill + CLAUDE.md; convertir el target y generar `out/02-IDS-Arquitetura.ids`.
6. Docs en portugués.

## Verificación
- `pytest -q` verde (golden con desviaciones documentadas, XSD, IFC sintéticos, determinismo).
- `loin2ids convert 01-loin-target/02-LOIN-Arquitetura.xlsx --project projects/target/project.yaml` → `.ids` válido; `loin2ids diff` contra `SRU0198-IDS-ARQ.ids` muestra solo diferencias esperadas (WBS_bSPT en lugar de MapaQuantidadesSRU, info header).
- Abrir el `.ids` en ifctester (y opcionalmente usBIM.IDSeditor) sin errores.
