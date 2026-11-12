"""Utilitários de texto: normalização e correspondência aproximada."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent / "config"


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str | None) -> str:
    """Minúsculas, sem acentos, espaços colapsados, sem ':' final."""
    if s is None:
        return ""
    s = strip_accents(str(s)).lower().replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(":").strip()


def compact(s: str | None) -> str:
    """Forma compacta para comparar identificadores: sem espaços, '_', '-', '.', acentos."""
    return re.sub(r"[\s_\-./]", "", norm(s))


def clean(s: str | None) -> str | None:
    """Remove espaços nas pontas e colapsa espaços internos (mantém maiúsculas/acentos)."""
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s).replace(" ", " ")).strip()
    return s or None


def levenshtein(a: str, b: str) -> int:
    """Distância de edição com transposição de letras adjacentes (Damerau/OSA):
    'Lenght' → 'Length' = 1 (e não 2, o que empataria com 'Height')."""
    if a == b:
        return 0
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[n][m]


def resolve_name(name: str, candidates: list[str], max_dist: int = 2) -> tuple[str | None, str, list[str]]:
    """Procura ``name`` em ``candidates``.

    Devolve (nome_canónico | None, método, candidatos_próximos). Método:
    'exact', 'case', 'compact', 'fuzzy' (distância ≤ max_dist e única), 'ambiguous', 'none'.
    """
    if name in candidates:
        return name, "exact", []
    low = {c.lower(): c for c in candidates}
    if name.lower() in low:
        return low[name.lower()], "case", []
    comp = {}
    for c in candidates:
        comp.setdefault(compact(c), []).append(c)
    hits = comp.get(compact(name), [])
    if len(hits) == 1:
        return hits[0], "compact", []
    target = compact(name)
    scored = sorted((levenshtein(target, compact(c)), c) for c in candidates)
    close = [c for d, c in scored if d <= max_dist]
    if len(close) == 1:
        return close[0], "fuzzy", close
    if len(close) > 1:
        best = scored[0][0]
        best_hits = [c for d, c in scored if d == best]
        if len(best_hits) == 1:
            return best_hits[0], "fuzzy", close
        return None, "ambiguous", close
    return None, "none", [c for _, c in scored[:5]]


@lru_cache(maxsize=None)
def load_config(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)
