# Desenvolvimento e testes

## Arquitetura

```
readers.py    .xlsx (openpyxl) / .ods (content.xml) → grelha de texto, igual para os dois formatos
parser.py     grelha → modelo intermédio (LoinSheet → Block: entidade, atributos, propriedades,
              materiais, classificação), escolhendo a coluna da fase
normalize.py  Block × esquema IFC × decisions.yaml → nomes canónicos, dataTypes, prefixos de
              classificação; cada correção/ambiguidade vira uma Issue
rules.py      regras entre blocos: identificadores, sobreposição de aplicabilidade,
              folhas de material
writer.py     blocos → IDS 1.0 via ifctester (estrutura garantida pelo XSD)
validate.py   XSD 1.0 + verificação semântica (entidades/Psets/dataTypes) + execução sobre IFC
idsdiff.py    comparação semântica de dois IDS (base dos testes golden)
report.py     relatório .md/.json
schema.py     acesso ao esquema IFC e às plantilhas de Psets/Qtos (ifcopenshell)
config/       aliases.yaml (rótulos, marcas, correções conhecidas), classification_map.yaml
```

## O que é determinístico e o que é LLM

| Determinístico (código) | Requer critério (LLM/pessoa, via decisions.yaml) |
|---|---|
| ler .xlsx/.ods, células mescladas, repetições ODS | propriedade sem Pset (`Espessura?`) |
| detetar secções, fases e coluna da fase | nome sem correspondência única no esquema |
| `X` → requisito; valor → aplicabilidade/valor | tabela de classificação nova |
| dataType a partir do esquema IFC | dataType de Psets próprios |
| corrigir gralhas com correspondência única (distância ≤ 2, transposições contam 1) | várias folhas para a mesma entidade sem distinção |
| tabelas de classificação conhecidas → prefixos | filtro de aplicabilidade de folhas de material |
| atributos `IfcX.Attr` → especificação própria | omitir folhas incompletas/duplicadas |
| exclusão de PredefinedType entre folhas da mesma entidade | |
| escrever e validar o XML | |

O LLM (skill `/loin-to-ids`) nunca escreve o XML: só `decisions.yaml`, com o motivo de cada
decisão. Assim o resultado é reprodutível e revisível, e os testes não dependem do modelo.

## Testes

```bash
.venv/bin/pytest -q
```

| Ficheiro | O que garante |
|---|---|
| `tests/test_golden.py` | para os 8 pares de referência: 0 bloqueantes e **todas** as diferenças face ao IDS de referência estão em `tests/golden/known_deviations.yaml` com motivo; um desvio novo ou um desvio listado que desapareceu faz falhar o teste |
| `tests/test_units.py` | leitores, deteção de secções/fases, seleção de fase, blocos derivados, correspondência de nomes, dataTypes por versão |
| `tests/test_validity.py` | todo o IDS gerado passa XSD 1.0 e verificação semântica; conversão byte-a-byte determinística; o verificador semântico deteta os erros das referências |
| `tests/test_robustness.py` | folhas sintéticas (`tests/loin_builder.py`): colunas deslocadas, espaços/maiúsculas, notas e links, fase, e cada tipo de bloqueante e a respetiva decisão |
| `tests/test_ifc_functional.py` | IFC sintético (ifcopenshell): um modelo conforme passa o IDS gerado e um modelo incompleto falha |
| `tests/test_target_and_cli.py` | a folha real em `01-loin-target` converte sem bloqueantes; CLI (`convert`, `validate`, `diff`, `schema`) e códigos de saída |

### Golden e desvios conhecidos

As referências em `00-ref-ids-gr/` foram feitas à mão e têm erros (ver
[desvios-golden.md](desvios-golden.md)). A regra é: **a folha corrigida contra o esquema IFC é a
verdade**. Quando um teste golden falha:

1. Veja a diferença (`loin2ids diff gerado.ids referência.ids`).
2. Se for um erro do conversor → corrija o conversor.
3. Se for um erro da referência → acrescente-a a `tests/golden/known_deviations.yaml` com o motivo
   e regenere `docs/desvios-golden.md` (`.venv/bin/python tools/gen_desvios.py`).

As decisões usadas nos casos golden estão em `tests/golden/decisions/` e servem também de
exemplo de decisões reais.

## Estender

- **Novo rótulo/variação de folha**: `loin2ids/config/aliases.yaml` + teste em `test_robustness.py`.
- **Nova tabela de classificação**: `loin2ids/config/classification_map.yaml`.
- **Nova correção conhecida de atributo**: `attribute_aliases` em `aliases.yaml`.
- **Novo par de referência**: acrescente-o a `tests/golden/cases.yaml` (e as decisões em
  `tests/golden/decisions/<caso>.yaml`), corra os testes e documente os desvios.
- **Nova regra de conversão**: `normalize.py` (por bloco) ou `rules.py` (entre blocos), com
  código de Issue próprio, documentado em `docs/guia-utilizador.md` e na skill.
