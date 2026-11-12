# Relatório de conversão LOIN → IDS

- Origem: `01-loin-target/02-LOIN-Arquitetura.xlsx`
- IDS: `out/02-IDS-Arquitetura.ids`

| Nível | N.º |
|---|---|
| blocker | 0 |
| warning | 1 |
| info | 11 |

## Avisos (IDS gerado, mas confirme)

- **fix-propriedade** — 'ARQ-Guardas' linha 22 [Lenght]: propriedade 'Lenght' corrigido para 'Length' (fuzzy).

## Informação

- **fix-atributo** — atributo 'Predifined Type' corrigido para 'PredefinedType' (alias). (10×: 'ARQ-Paredes' l.16, 'ARQ-Pavimentos' l.16, 'ARQ-RevPavCobTet' l.16, 'ARQ-Rodapés' l.16, 'ARQ-Coberturas' l.16, 'ARQ-Escadas' l.16, 'ARQ-Rampas' l.16, 'ARQ-Portas' l.16, 'ARQ-Janelas' l.16, 'ARQ-Guardas' l.16)
- **applicability-exclusion** — 'ARQ-RevPavCobTet': IfcCovering: PredefinedType ['SKIRTINGBOARD'] excluído da aplicabilidade (coberto por outra folha).
