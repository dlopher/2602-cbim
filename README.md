# loin2ids — de folhas LOIN para IDS

Converte folhas **LOIN** (*Level of Information Need*, em `.xlsx` ou `.ods`) em ficheiros
**IDS 1.0** (*Information Delivery Specification*, buildingSMART), prontos a usar na
verificação de modelos IFC (ifctester, usBIM.IDSeditor, Solibri, BIMcollab, etc.).

- **Determinístico**: a mesma folha com as mesmas decisões dá sempre o mesmo IDS.
- **Corrigido contra o esquema IFC oficial** (IFC2X3, IFC4, IFC4X3_ADD2): gralhas como
  `Lenght` ou `Predifined Type` são corrigidas e reportadas, e os `dataType` vêm do esquema.
- **Ambiguidades explícitas**: o que não se pode decidir mecanicamente vai para um relatório
  e resolve-se num ficheiro `decisions.yaml`, revisto por uma pessoa (ou proposto pelo
  Claude Code através da skill `/loin-to-ids`).
- **Validado**: cada IDS gerado é validado contra o XSD IDS 1.0 e contra o esquema IFC.

## Instalação

Requer Python ≥ 3.10.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Uso rápido

```bash
# 1. converter
.venv/bin/loin2ids convert 01-loin-target/02-LOIN-Arquitetura.xlsx \
    --project projects/arquitetura/project.yaml \
    --decisions projects/arquitetura/decisions.yaml \
    -o out/02-IDS-Arquitetura.ids

# 2. ler o relatório (bloqueantes, avisos, correções aplicadas)
cat out/02-IDS-Arquitetura.issues.md

# 3. validar (e, opcionalmente, verificar um modelo)
.venv/bin/loin2ids validate out/02-IDS-Arquitetura.ids --ifc modelo.ifc
```

Outros comandos:

| Comando | Para quê |
|---|---|
| `loin2ids diff A.ids B.ids [--meta]` | comparação semântica de dois IDS (ignora ordem e formatação) |
| `loin2ids schema pset Pset_WallCommon` | propriedades e tipos de um Pset/Qto no esquema IFC |
| `loin2ids schema entity IfcCovering` | atributos e valores de PredefinedType |
| `loin2ids schema search thickness` | procura Psets/propriedades por nome |
| `loin2ids inspect folha.xlsx --phase "..."` | mostra o que o conversor leu da folha (JSON) |

Códigos de saída de `convert`: `0` OK · `2` há bloqueantes (IDS não gerado) · `3` IDS inválido.

## Com o Claude Code

Na pasta do projeto, escreva `/loin-to-ids` (ou peça "converte a folha X para IDS"). O Claude
executa o conversor, lê o relatório, propõe decisões em `decisions.yaml` (perguntando-lhe nas
que exigem critério), volta a converter até não haver bloqueantes e valida o resultado.
O Claude nunca escreve o XML: só as decisões, que ficam registadas e versionadas.

## Documentação

- [Guia do utilizador](docs/guia-utilizador.md) — preparar a folha, `project.yaml`, `decisions.yaml`, fluxo de trabalho.
- [Gramática da folha LOIN](docs/gramatica-loin.md) — estrutura esperada e mapeamento para IDS, com exemplos.
- [Desenvolvimento e testes](docs/desenvolvimento.md) — arquitetura, o que é determinístico vs. LLM, bateria de testes, como estender.
- [Desvios face às referências](docs/desvios-golden.md) — erros encontrados nos IDS de referência.

## Estrutura

```
00-ref-ids-gr/        referências (folha + IDS feito à mão) — só leitura
01-loin-target/       folhas a converter
loin2ids/             conversor (config/ com aliases e tabelas de classificação)
projects/<nome>/      project.yaml + decisions.yaml de cada conversão
out/                  IDS gerados + relatórios
tests/                pytest (golden, unitários, robustez, validade, IFC funcional)
docs/                 documentação
.claude/skills/       skill /loin-to-ids para o Claude Code
```
