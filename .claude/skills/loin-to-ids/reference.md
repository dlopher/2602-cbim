# Referência rápida: folha LOIN → IDS

Colunas (layout das referências SRU0198 e bSPT):

| Coluna | Conteúdo |
|---|---|
| A | Cabeçalhos: `Objetos`/`Classe`/`Material` (valor em H), `Ator…`, `Propósito`/`Referências EIR`, `Requisitos mínimos de informação geométrica/alfanumérica` |
| B | Secções: `Classe IFC`, `Atributos`, `Grupos/Conjuntos de propriedades`, `Materiais`, `Classificação`, `Georeferenciação`, `Referências`, `Nota:` |
| C | Item: atributo, propriedade, sistema de classificação (`SECClasS`) |
| D | Sub-item (atributos dentro de `Referências`) |
| H | Pset/Qto, `IfcMaterial`, tabela de classificação |
| I… | Uma coluna por fase; `X` = obrigatório; outro texto = valor exigido (ex.: `SKIRTINGBOARD`) |

Mapeamento:

| Folha | IDS |
|---|---|
| `Classe IFC` | `applicability/entity` (nome em maiúsculas) |
| Atributo com `X` | `requirements/attribute` required |
| `Predifined Type` = valor | `applicability/attribute PredefinedType = valor` + requisito de existência |
| `IfcMapConversion.Eastings` | especificação própria para `IfcMapConversion` |
| Propriedade + Pset normalizado | `requirements/property` com `dataType` do esquema IFC |
| Propriedade + Pset próprio | `requirements/property` sem `dataType` (aviso) |
| `Materiais` com `X` | `requirements/material` required |
| `SECClasS` + tabela | `requirements/classification` com padrão de prefixo (ver `config/classification_map.yaml`) |
| Várias folhas, mesma entidade | a sem filtro exclui os PredefinedType das outras |
| Folha `IfcMaterial` | precisa de filtro de aplicabilidade (decisão) |
| Linhas sem marca, notas, links | ignoradas |

Erros reais encontrados nas folhas de referência (e como o conversor os trata):
`Predifined Type` (alias), `Lenght`/`With`/`ValveMechanisme` (correção por distância de edição),
`IfcPipeSgment` (correção da entidade), espaços finais (`Width          `), `SECCLASS` (normalização),
`Classe IFC IfcCovering` em C (layout irregular, aviso), `Espessura?` sem Pset (bloqueante → decisão),
folhas `OBS` (ignoradas), folhas sobrepostas para `IfcCovering`/`IfcDuctSegment` (bloqueante → decisão).

Exemplos de decisões reais: `tests/golden/decisions/*.yaml` e `projects/arquitetura/decisions.yaml`.
