---
name: loin-to-ids
description: Converte uma folha LOIN (Level of Information Need, .xlsx/.ods) de 01-loin-target/ num ficheiro IDS 1.0 válido, usando o conversor determinístico loin2ids e resolvendo as ambiguidades em decisions.yaml. Usar quando o utilizador pedir para gerar/atualizar um .ids a partir de uma folha LOIN, ou para rever problemas de uma conversão.
---

# LOIN → IDS

O XML é SEMPRE gerado pelo conversor determinístico (`loin2ids`). O teu papel é
(1) executá-lo, (2) interpretar o relatório, (3) propor e registar decisões em
`decisions.yaml` quando o conversor não consegue decidir sozinho, e (4) validar.
**Nunca escrevas nem edites o .ids à mão.**

Referência da gramática das folhas e exemplos: `reference.md` (nesta pasta) e
`docs/gramatica-loin.md`.

## Passos

1. **Identificar a entrada.** Ficheiro em `01-loin-target/` (ou o indicado). Escolher a pasta
   do projeto `projects/<nome>/`. Se não existir `project.yaml`, cria-o a partir de
   `projects/arquitetura/project.yaml` e pergunta ao utilizador o que não se deduz:
   `ifc_version` (IFC4 ou IFC4X3_ADD2), `phase` (se a folha tiver várias fases),
   `author` (e-mail), `copyright`, `min_occurs` (1 = obrigatório existir pelo menos um elemento).

2. **Converter.**
   ```bash
   .venv/bin/loin2ids convert <folha> --project projects/<nome>/project.yaml \
       --decisions projects/<nome>/decisions.yaml -o out/<nome>.ids
   ```
   Códigos de saída: 0 = OK; 2 = há bloqueantes (IDS não gerado); 3 = IDS inválido (bug — reporta).

3. **Ler o relatório** `out/<nome>.issues.json` (estruturado) ou `.issues.md`.
   - `blocker`: tem de ser resolvido antes de gerar.
   - `warning`: correções automáticas (gralhas) ou Psets próprios — confirma que fazem sentido.
   - `info`: registo; normalmente não exige ação.

4. **Resolver cada bloqueante/aviso relevante em `decisions.yaml`** (nunca alterando o código
   nem a folha do utilizador sem autorização). Usa o esquema IFC para justificar:
   ```bash
   .venv/bin/loin2ids schema pset Pset_CoveringCommon --ifc-version IFC4X3_ADD2
   .venv/bin/loin2ids schema entity IfcCovering
   .venv/bin/loin2ids schema search thickness
   .venv/bin/loin2ids inspect <folha> --phase "..."     # modelo intermédio em JSON
   ```
   Tabela de decisões típicas:

   | Código | O que significa | Decisão típica |
   |---|---|---|
   | `prop-no-pset` | propriedade marcada sem Pset (ex.: `Espessura?`) | `rows: {"Espessura?": {pset: Qto_CoveringBaseQuantities, name: Width}}` ou `{skip: true}` |
   | `prop-unknown` / `pset-unknown` | nome não existe no esquema e não há correção única | `rows` com o nome certo, ou `psets: {X: {accept: true}}` se for intencional |
   | `pset-custom` (aviso) | Pset próprio do projeto | `psets: {WBS_bSPT: {accept: true, data_type: IFCLABEL}}` (data_type opcional) |
   | `class-table-unknown` | tabela de classificação sem prefixos | `classification_tables: {"Nova tabela": [[Pr_]]}` |
   | `applicability-overlap` | várias folhas para a mesma entidade sem distinção | `predefined_type: [CEILING]`, `applicability: [...]` ou `skip: true` |
   | `material-applicability` | folha de material (IfcMaterial) sem filtro | `applicability: [{attribute: Name, pattern: ".*concrete.*"}]` |
   | `entity-unknown` / `attr-unknown` | classe/atributo inexistente | `entity: IfcX` na folha, ou `rows: {...: {name: ...}}` |
   | `phase` | várias fases e nenhuma escolhida | `phase:` no project.yaml |

   Regras:
   - Cada decisão leva um comentário `# porquê` e, quando aplicável, a fonte (esquema IFC, utilizador).
   - **Pergunta ao utilizador** antes de: omitir (`skip`) uma folha ou linha com requisitos,
     escolher entre candidatos ambíguos, ou inventar um padrão de aplicabilidade.
     Apresenta a tua proposta e a alternativa.
   - Decisões mecânicas com uma única resposta no esquema (ex.: dataType de um Pset normalizado)
     não precisam de pergunta.

5. **Repetir** o passo 2 até 0 bloqueantes.

6. **Validar e resumir.**
   ```bash
   .venv/bin/loin2ids validate out/<nome>.ids                      # XSD 1.0 + esquema IFC
   .venv/bin/loin2ids validate out/<nome>.ids --ifc modelo.ifc     # opcional, se houver modelo
   .venv/bin/loin2ids diff out/<nome>.ids <ids-anterior-ou-referência>   # opcional
   ```
   Resume ao utilizador: n.º de especificações, correções automáticas aplicadas,
   decisões tomadas (e quais foram confirmadas por ele), avisos pendentes.

## Formato de decisions.yaml

```yaml
sheets:
  "<nome da folha>":
    skip: true                      # omite a folha
    reason: "..."
    entity: IfcCovering             # força a entidade
    identifier: ARQ-Tetos           # sobrepõe identifier/name da especificação
    name: Tetos
    predefined_type: [CEILING]      # filtro de aplicabilidade por PredefinedType
    applicability:                  # filtros extra de aplicabilidade
      - {attribute: Name, pattern: ".*concrete.*"}
    rows:                           # por texto da célula (coluna C/D)
      "Espessura?": {pset: Qto_CoveringBaseQuantities, name: Width}
      "Outra": {skip: true}
psets:
  WBS_bSPT: {accept: true, data_type: IFCLABEL, properties: {WBS_codigo: IFCLABEL}}
classification_tables:
  "Nova tabela": [[Pr_], [Ss_]]     # dois requisitos; [[Pr_, Ss_]] = um requisito (Pr_|Ss_).*
```

Se uma ambiguidade se repetir em vários projetos, propõe ao utilizador movê-la para a
configuração (`loin2ids/config/aliases.yaml` ou `classification_map.yaml`) e acrescentar um
teste em `tests/test_robustness.py`.
