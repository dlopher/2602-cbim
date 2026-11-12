# Projeto: LOIN → IDS

Converte folhas LOIN (Level of Information Need, .xlsx/.ods, em português) em ficheiros
IDS 1.0 (buildingSMART) para verificar modelos IFC.

## Estrutura
- `00-ref-ids-gr/` — referências (golden): 2 projetos (bSPT, SRU0198) × Geral/ARQ/EST/MEP; folha + IDS feito à mão. **Só leitura.**
- `01-loin-target/` — folhas a converter.
- `loin2ids/` — conversor determinístico (readers → parser → normalize → rules → writer). Configuração em `loin2ids/config/`.
- `projects/<nome>/` — `project.yaml` (cabeçalho IDS, versão IFC, fase) e `decisions.yaml` (resoluções manuais/LLM).
- `out/` — IDS gerados + relatórios `.issues.md/.json`.
- `tests/` — pytest; `tests/golden/known_deviations.yaml` lista as diferenças aceites face às referências.
- `docs/` — documentação para terceiros (português).

## Regras
- A verdade é a **folha LOIN corrigida contra o esquema IFC** (ifcopenshell), não o IDS de referência; as referências têm erros documentados.
- O XML é sempre gerado pelo conversor. Ambiguidades resolvem-se em `decisions.yaml`, nunca editando o .ids.
- Para converter uma folha usar a skill `/loin-to-ids`.
- Ambiente: `.venv/` (`python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"`).
- Testes: `.venv/bin/pytest -q`. Um desvio novo face às referências faz falhar `tests/test_golden.py`: corrigir o conversor ou documentar o desvio com motivo.
- Documentação e mensagens do conversor em português.
