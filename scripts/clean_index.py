#!/usr/bin/env python3
"""Limpeza e normalização do índice do CIC.

Aplica, em uma passada, sobre `docs/Índice do catecismo.txt`:
  1. Remove espaços finais e colapsa espaços duplos internos.
  2. Normaliza indentação anômala (13 -> 12).
  3. Remove referências de parágrafo (parênteses só com dígitos/§/hífen),
     preservando referências bíblicas (que contêm letras).
  4. Corrige typos pontuais e unifica reticências ('…' -> '...').
  5. Sentence-case dos títulos que estão em CAIXA ALTA, preservando nomes
     próprios (dicionário curado). Títulos já em sentence-case e o bloco
     'Observações' não são tocados.

Uso: python scripts/clean_index.py [--check]
  --check  não escreve; apenas relata o que mudaria.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ARQ = Path("docs/Índice do catecismo.txt")

# --- dicionário de nomes próprios (editável) -------------------------------
PROPER = {
    "deus": "Deus", "senhor": "Senhor", "cristo": "Cristo", "jesus": "Jesus",
    "espírito": "Espírito", "santo": "Santo", "santa": "Santa",
    "santíssima": "Santíssima", "santíssimo": "Santíssimo", "trindade": "Trindade",
    "pai": "Pai", "filho": "Filho", "verbo": "Verbo", "igreja": "Igreja",
    "maria": "Maria", "virgem": "Virgem", "israel": "Israel", "mediador": "Mediador",
    "salvador": "Salvador", "providência": "Providência", "purgatório": "Purgatório",
    "sábado": "Sábado", "escritura": "Escritura", "escrituras": "Escrituras",
    "sagrada": "Sagrada", "decálogo": "Decálogo", "pentecostes": "Pentecostes",
    "getsêmani": "Getsêmani", "jerusalém": "Jerusalém", "noé": "Noé",
    "abraão": "Abraão", "moisés": "Moisés", "david": "David", "elias": "Elias",
    "salmos": "Salmos", "magistério": "Magistério", "pôncio": "Pôncio",
    "pilatos": "Pilatos", "testamento": "Testamento", "adão": "Adão", "eva": "Eva",
    "messias": "Messias", "evangelho": "Evangelho", "cordeiro": "Cordeiro",
    "eucaristia": "Eucaristia", "batismo": "Batismo", "confirmação": "Confirmação",
    "penitência": "Penitência", "reconciliação": "Reconciliação",
    "matrimônio": "Matrimônio", "unção": "Unção", "viático": "Viático",
    "cânon": "Cânon", "encarnação": "Encarnação", "ressurreição": "Ressurreição",
    "apóstolos": "Apóstolos", "baptista": "Baptista",
}

# frases multi-palavra que sobrescrevem (aplicadas case-insensitive)
PHRASES = [
    "Espírito Santo", "Santíssima Trindade", "Sagrada Escritura",
    "Antigo Testamento", "Novo Testamento", "Pôncio Pilatos", "Todo-Poderoso",
    "Mãe de Deus", "Reino de Deus", "Filho de Deus", "Filho Único",
    "Nossa Senhora", "Santa Igreja",
]

# título da Parte 4 vem duplicado na fonte
POSTFIX = {"A oração cristã a oração cristã": "A oração cristã"}

PAR_REF = re.compile(r"\s*\((?:[0-9§\s\-\u2013\u2014]+)\)")
ROMAN = re.compile(r"^([IVXLCDM]+\.)\s+(.+)$")
LABELS = re.compile(
    r"^((?:Primeira|Segunda|Terceira|Quarta) (?:Parte|Seção)"
    r"|Capítulo (?:Primeiro|Segundo|Terceiro|Quarto|X)"
    r"|Artigo (?:\d+|X)"
    r"|Parágrafo (?:\d+|X))\s+(.+)$"
)


def is_caps(seg: str) -> bool:
    # artefato: qualquer palavra 2+ letras toda maiúscula (exceto numeral romano)
    for w in re.findall(r"[A-ZÀ-Ý]{2,}", seg):
        if not re.fullmatch(r"[IVXLCDM]+", w):
            return True
    letters = [c for c in seg if c.isalpha()]
    if not letters:
        return False
    up = sum(1 for c in letters if c.isupper())
    return up / len(letters) >= 0.5


def recase(seg: str) -> str:
    """Converte um segmento em CAIXA ALTA para sentence-case + nomes próprios."""
    # protege referências bíblicas entre parênteses (contêm letras): ex. (Sl 115, 3)
    holds: list[str] = []

    def _hold(m: re.Match) -> str:
        holds.append(m.group(0))
        return f"\x00{len(holds) - 1}\x00"

    s = re.sub(r"\([^)]*[A-Za-zÀ-ÿ][^)]*\)", _hold, seg)
    s = s.lower()
    # capitaliza 1ª letra do segmento e após '«' ou aspas
    out, cap_next = [], True
    for ch in s:
        if cap_next and ch.isalpha():
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
            if ch in "«\"“":
                cap_next = True
    s = "".join(out)
    # nomes próprios (palavra inteira)
    s = re.sub(
        r"[A-Za-zÀ-ÿ]+",
        lambda m: PROPER.get(m.group(0).lower(), m.group(0)),
        s,
    )
    # frases
    for ph in PHRASES:
        s = re.sub(re.escape(ph), ph, s, flags=re.IGNORECASE)
    # restaura refs bíblicas
    for i, h in enumerate(holds):
        s = s.replace(f"\x00{i}\x00", h)
    return s


def recase_if_caps(seg: str) -> str:
    return recase(seg) if is_caps(seg) else seg


def clean_content(content: str) -> str:
    # remove referências de parágrafo
    content = PAR_REF.sub("", content)
    # typos pontuais
    content = content.replace("graças. memorial", "graças, memorial")
    # reticências unicode -> ascii
    content = content.replace("\u2026", "...")
    # espaços duplos internos
    content = re.sub(r" {2,}", " ", content)
    # remove ponto final solto de título romano (ex.: '... na liturgia.')
    content = re.sub(r"(\S)\.$", r"\1", content) if ROMAN.match(content) else content
    return content.rstrip()


def transform_line(line: str) -> str:
    indent = len(line) - len(line.lstrip(" "))
    # normaliza indentação anômala 13 -> 12
    if indent == 13:
        indent = 12
    content = line.strip()
    if not content:
        return ""
    content = clean_content(content)

    m = LABELS.match(content)
    if m:
        label, title = m.group(1), m.group(2)
        title = recase_if_caps(title)
        title = POSTFIX.get(title, title)
        return " " * indent + f"{label} {title}"
    m = ROMAN.match(content)
    if m:
        marker, body = m.group(1), m.group(2)
        return " " * indent + f"{marker} {recase_if_caps(body)}"
    # linha sem rótulo (subtítulo, título descritivo, overview, placeholder)
    return " " * indent + recase_if_caps(content)


def main() -> None:
    check = "--check" in sys.argv
    lines = ARQ.read_text(encoding="utf-8").split("\n")
    out, frozen = [], False
    changed = 0
    for ln in lines:
        if ln.strip() == "Observações":
            frozen = True
        if frozen or ln.strip() in ("", "Índice"):
            out.append(ln)
            continue
        new = transform_line(ln)
        if new != ln:
            changed += 1
        out.append(new)
    text = "\n".join(out)
    if check:
        print(f"linhas que mudariam: {changed}")
        return
    ARQ.write_text(text, encoding="utf-8")
    print(f"OK - {changed} linhas alteradas")


if __name__ == "__main__":
    main()
