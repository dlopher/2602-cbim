# Gramática da folha LOIN e mapeamento para IDS

## Estrutura de uma folha

Exemplo (folha `ARQ-Paredes`, layout SRU0198 com quatro fases):

| | A | B | C | … | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Objetos | | | | Paredes | | | | |
| 2 | Ator requerente | | | | SRU | | | | |
| 4 | | | | | | FASE DE PROJETO: | | | |
| 5 | | | | | | Estudo Prévio | Anteprojeto | Projeto de Execução | P. Execução Final |
| 6 | Propósito | | | | | EIR01… | EIR01… | EIR01… | EIR01… |
| 7 | Requisitos mínimos de informação geométrica | | | | | | | | |
| … | | Detalhe / Dimensão / … *(ignorado)* | | | | | | | |
| 15 | Requisitos mínimos de informação alfanumérica | | | | | | | | |
| 16 | | Classe IFC | | | | IfcWall | IfcWall | IfcWall | IfcWall |
| 17 | | Atributos | | | | | | | |
| 18 | | | Name | | | | X | X | X |
| 19 | | | Predifined Type | | | X | X | X | X |
| 21 | | Grupos de propriedades | | | | | | | |
| 22 | | | Propriedade | | Grupo de propriedades | | | | |
| 23 | | | FireRating | | Pset_WallCommon | | X | X | X |
| 24 | | | Length | | Qto_WallBaseQuantities | X | X | X | X |
| 30 | | Materiais | | | | | | | |
| 31 | | | Name | | IfcMaterial | | X | X | X |
| 32 | | Classificação | | | | | | | |
| 33 | | | Sistema | | Tabela | | | | |
| 34 | | | SECClasS | | Elementos/ Funções, Sistemas e Produtos | X | X | X | X |
| 35 | | Nota: | | | | | | | |

Variações aceites:
- **Fases**: qualquer número de colunas a partir de I; a linha das fases é a que contém
  `FASE DE PROJETO` (ou a linha seguinte). Uma folha com uma só fase (como
  `01-loin-target/02-LOIN-Arquitetura.xlsx`) não precisa de `--phase`.
- **Rótulos**: `Grupos`/`Conjuntos de propriedades`; `Propósito`/`Proposito`/`Referências EIR`;
  `Objetos`/`Classe`/`Material`. Todos configuráveis em `loin2ids/config/aliases.yaml`.
- `Classe IFC IfcDamper` na coluna B (entidade no próprio rótulo) e `Classe IFC IfcCovering` na
  coluna C (layout irregular, gera aviso).
- Atributos com notação `IfcMapConversion.Eastings` (secção `Georeferenciação`).
- Secção `Referências` com `Classe IFC` e `Atributos` próprios (sub-itens na coluna D).
- Linhas sem marca na fase escolhida, notas e links de referência no fim: ignorados.
- Folhas de índice (`OBS`) e folhas sem secção alfanumérica: ignoradas.

## Mapeamento para IDS

| Na folha | No IDS |
|---|---|
| nome do separador | `specification/@identifier` (com `identifier_prefix` se configurado) |
| `Objetos` (coluna H) | `specification/@name` |
| `ifc_version` (project.yaml) | `specification/@ifcVersion` |
| `min_occurs` (project.yaml) | `applicability/@minOccurs` |
| `Classe IFC` | `applicability/entity/name` (maiúsculas, ex.: `IFCWALL`) |
| atributo com `X` | `requirements/attribute` (`cardinality="required"`) |
| `Predifined Type` = `SKIRTINGBOARD` | `applicability/attribute PredefinedType = SKIRTINGBOARD` + requisito `attribute PredefinedType` |
| `IfcProjectedCRS.Name` | especificação adicional `<folha>-ProjectedCRS` para `IFCPROJECTEDCRS` |
| `Referências` → `Classe IFC` | especificação adicional `<folha>-Referências` |
| propriedade + Pset normalizado (`Pset_`/`Qto_`) | `requirements/property` + `dataType` do esquema IFC |
| propriedade + Pset próprio | `requirements/property` sem `dataType` (ou o de `decisions.yaml`) |
| `Materiais` com `X` | `requirements/material` |
| `SECClasS` + tabela | `requirements/classification` (sistema `SECClasS`, valor por padrão) |
| valor diferente de `X` numa propriedade | `requirements/property/value` |

### dataType

Vem do esquema IFC da versão escolhida (plantilhas oficiais de Psets/Qtos do ifcopenshell):

| Tipo no esquema | dataType IDS |
|---|---|
| propriedade simples (`IfcLabel`, `IfcBoolean`, `IfcThermalTransmittanceMeasure`, …) | o próprio tipo em maiúsculas |
| propriedade enumerada (`P_ENUMERATEDVALUE`) | `IFCLABEL` |
| quantidade comprimento/área/volume/peso/contagem/tempo | `IFCLENGTHMEASURE` / `IFCAREAMEASURE` / `IFCVOLUMEMEASURE` / `IFCMASSMEASURE` / `IFCCOUNTMEASURE` / `IFCTIMEMEASURE` |

Atenção: o tipo pode mudar entre versões (ex.: `Pset_SwitchingDeviceTypeCommon.NumberOfGangs`
é `IFCINTEGER` em IFC4 e `IFCCOUNTMEASURE` em IFC4X3).

### Classificação (SECClasS)

Definido em `loin2ids/config/classification_map.yaml`:

| Tabela na folha | Requisitos IDS |
|---|---|
| Entidades | `En_.*` |
| Espaços/ locais | `SL_.*` |
| Sistemas | `Ss_.*` |
| Produtos | `Pr_.*` |
| Elementos/ Funções, Sistemas e Produtos | três requisitos: `Ss_.*`, `EF_.*`, `Pr_.*` |
| Produtos ou Sistemas | um requisito: `(Pr_|Ss_).*` |

### Várias folhas para a mesma entidade

Exemplo: `ARQ-RevPavCobTet` e `ARQ-Rodapés` são ambas `IfcCovering`; Rodapés tem
`Predifined Type = SKIRTINGBOARD`. O conversor:
- aplica Rodapés só a `PredefinedType = SKIRTINGBOARD`;
- aplica RevPavCobTet a todos os outros valores do enumerado (lista do esquema da versão escolhida).

Se houver duas ou mais folhas **sem** filtro para a mesma entidade, é um bloqueante
(`applicability-overlap`): decida em `decisions.yaml` (`predefined_type`, `applicability` ou `skip`).

### Folhas de material

Uma folha com `Classe IFC = IfcMaterial` (ex.: `M-Betão`) gera uma especificação sobre
materiais, mas precisa de um filtro (ex.: `Name ~ .*concrete.*`) para não se aplicar a todos os
materiais do modelo. O filtro é uma decisão (`material-applicability`).
