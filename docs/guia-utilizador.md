# Guia do utilizador

## 1. Fluxo de trabalho

```
folha LOIN (.xlsx/.ods)          project.yaml          decisions.yaml
          │                           │                      │
          └──────────────┬────────────┴──────────────────────┘
                         ▼
                 loin2ids convert
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   relatório .issues.md/.json     IDS (.ids) — só se não houver bloqueantes
          │
          └─► resolver bloqueantes/avisos em decisions.yaml ─► voltar a converter
```

1. Coloque a folha em `01-loin-target/`.
2. Crie `projects/<nome>/project.yaml` (copie `projects/arquitetura/project.yaml`).
3. Execute `loin2ids convert …`.
4. Leia o relatório. Se houver **bloqueantes**, resolva-os em `projects/<nome>/decisions.yaml`
   (ou corrija a folha) e volte ao passo 3.
5. Reveja os **avisos** (correções automáticas e Psets próprios).
6. Valide com `loin2ids validate` e, se tiver um modelo, `--ifc modelo.ifc`.

## 2. Preparar a folha

A folha deve seguir a estrutura descrita em [gramatica-loin.md](gramatica-loin.md) — é a
estrutura das folhas de referência SRU0198 e bSPT. Pontos essenciais:

- uma folha (separador) por tipo de objeto;
- linha `Classe IFC` com a entidade (ex.: `IfcWall`) na coluna de cada fase;
- uma coluna por fase de projeto; `X` na fase em que o requisito é exigido;
- propriedades com o nome na coluna C e o Pset/Qto na coluna H;
- classificação: sistema (`SECClasS`) na coluna C e tabela na coluna H.

O conversor tolera e corrige: gralhas pequenas nos nomes (com aviso), espaços a mais,
maiúsculas/minúsculas, `Grupos`/`Conjuntos de propriedades`, notas e links no fim da folha,
folhas de índice (`OBS`). **Não** adivinha: propriedades sem Pset, tabelas de classificação
desconhecidas, folhas sobrepostas, nomes com mais de uma correção possível.

## 3. `project.yaml`

```yaml
title: Arquitetura                 # título do IDS
copyright: Entidade                # opcional
version: V1                        # opcional
author: nome@dominio.pt            # opcional; tem de ser e-mail (IDS 1.0)
date: 2026-11-12                   # opcional (AAAA-MM-DD)
purpose: EIR01, EIR04 …            # opcional; por omissão, lido da linha "Propósito"/"Referências EIR"
milestone: Projeto de Execução     # opcional; por omissão, o nome da fase escolhida
description: …                     # opcional
ifc_version: IFC4X3_ADD2           # IFC2X3 | IFC4 | IFC4X3_ADD2
phase: Projeto de Execução         # obrigatório se a folha tiver várias fases
identifier_prefix: "G-"            # opcional; prefixo para identificadores de folhas sem prefixo
min_occurs: 1                      # 1 = o modelo tem de conter ≥1 elemento de cada especificação
                                   # 0 = a especificação só se verifica se existirem elementos
```

`min_occurs`: as referências usam `1`, o que faz falhar a verificação se, por exemplo, o
projeto não tiver rampas mas o IDS tiver uma especificação de rampas. Use `0` se o mesmo IDS
for aplicado a projetos que podem não ter todos os tipos de objeto.

## 4. O relatório

Cada conversão escreve `<saída>.issues.md` (para ler) e `<saída>.issues.json` (para
ferramentas). Níveis:

| Nível | Significado | IDS gerado? |
|---|---|---|
| `blocker` | o conversor não sabe o que fazer | não (use `--force` para gerar sem os itens em falta) |
| `warning` | gerado, mas com uma correção ou suposição a confirmar | sim |
| `info` | registo (folhas ignoradas, aliases aplicados, exclusões de aplicabilidade) | sim |

Códigos mais frequentes:

| Código | Causa | Como resolver |
|---|---|---|
| `fix-atributo`, `fix-propriedade`, `fix-pset`, `fix-entidade` | gralha corrigida automaticamente | confirmar; idealmente corrigir a folha |
| `pset-custom` | Pset próprio (não normalizado) → sem `dataType` | `psets:` em decisions.yaml |
| `prop-no-pset` | propriedade marcada sem Pset (coluna H vazia) | `rows:` em decisions.yaml ou corrigir a folha |
| `prop-unknown`, `pset-unknown`, `attr-unknown`, `entity-unknown` | nome sem correspondência (única) no esquema | corrigir a folha ou `rows:`/`entity:`/`psets: accept` |
| `class-table-unknown` | tabela de classificação sem prefixos definidos | `classification_tables:` ou `config/classification_map.yaml` |
| `applicability-overlap` | várias folhas para a mesma entidade sem filtro | `predefined_type:`, `applicability:` ou `skip:` |
| `material-applicability` | folha de material sem filtro | `applicability:` com padrão de `Name` |
| `phase` | fase não indicada/inexistente | `phase:` no project.yaml |
| `layout` | estrutura fora do habitual (ex.: `Classe IFC` na coluna C) | confirmar o resultado; corrigir a folha |

## 5. `decisions.yaml`

Regista as decisões que o conversor não pode tomar. É texto simples, versionável e revisto
por uma pessoa. Todas as secções são opcionais.

```yaml
sheets:
  "ARQ-Tetos":                      # nome da folha (sem distinção de acentos/espaços)
    skip: true                      # omite a folha inteira
    reason: "Sobreposta a ARQ-RevPavCobTet"
  "ARQ-Revestimentos":
    predefined_type: [FLOORING]     # filtro de aplicabilidade por PredefinedType
  "M-Betão":
    applicability:                  # filtros de aplicabilidade adicionais
      - {attribute: Name, pattern: ".*concrete.*"}
  "ARQ-Paredes":
    identifier: ARQ-Paredes         # sobrepõe identifier / name
    name: Paredes
    entity: IfcWall                 # força a entidade
    rows:                           # por texto da célula da coluna C (ou D)
      "Espessura?": {pset: Qto_WallBaseQuantities, name: Width}
      "Uso": {skip: true}
      "Codigo": {data_type: IFCIDENTIFIER}

psets:                              # Psets próprios ou não reconhecidos
  WBS_bSPT:
    accept: true
    data_type: IFCLABEL             # tipo por omissão (opcional)
    properties: {WBS_codigo: IFCLABEL}

classification_tables:              # tabelas não previstas em config/classification_map.yaml
  "Nova tabela": [[Pr_]]            # [[A],[B]] = dois requisitos; [[A,B]] = um requisito (A|B).*
```

Sem `data_type`, o IDS exige apenas que a propriedade exista, com qualquer valor.

## 6. Usar o Claude Code (skill `/loin-to-ids`)

A skill automatiza os passos 3–6: executa o conversor, interpreta o relatório, consulta o
esquema IFC (`loin2ids schema …`), escreve as decisões **com o motivo** em `decisions.yaml` e
volta a converter. Pergunta-lhe antes de omitir folhas/linhas, de escolher entre candidatos
ambíguos ou de inventar filtros de aplicabilidade. Não precisa de chave de API: usa a sessão
do Claude Code.

## 7. Verificar um modelo

```bash
.venv/bin/loin2ids validate out/02-IDS-Arquitetura.ids --ifc modelo.ifc
```

Mostra, por especificação, `OK`, `FALHA` ou `N/A`. Para relatórios detalhados (HTML, BCF)
use diretamente o `ifctester` ou outra ferramenta compatível com IDS 1.0.
