#!/usr/bin/env python3
"""Gera o JSON de `article_groups` a partir do índice limpo.

Percorre `docs/Índice do catecismo.txt` montando a árvore por indentação
(pilha) e classifica cada nó por palavra-chave + posição:

  Prólogo / N Parte         -> part
  N Seção / Introdução       -> section
  Capítulo ...               -> chapter
  Artigo ...                 -> article
  Parágrafo ...              -> agrupamento § (level 1)
  romano 'I.' / descritivo   -> título  (level 2)  [filho de artigo ou §]
  demais sob um artigo       -> subtítulo (level 3) [filho de título]

`level` é semântico (1=§, 2=título, 3=subtítulo); a reconstrução usa
`level` + `sort_order`. Placeholders ('Parágrafo X', 'Título X', ...) são
usados só para calcular o nível dos filhos e NÃO são emitidos (colapsados).

Saída: Insert-data/article-groups.json  (sem inserir no banco).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SRC = Path("docs/Índice do catecismo.txt")
OUT = Path("Insert-data/article-groups.json")

ORD = {
    "Primeira": 1, "Segunda": 2, "Terceira": 3, "Quarta": 4,
    "Primeiro": 1, "Segundo": 2, "Terceiro": 3, "Quarto": 4,
}
ROMAN = re.compile(r"^[IVXLCDM]+\.\s+")
PAR_LABEL = re.compile(r"^Parágrafo (?:\d+|X)\s*")
PLACEHOLDER = re.compile(r"^(?:Parágrafo|Título|Artigo|Capítulo|Seção) X$")
LEVEL_SEG = {1: "par", 2: "title", 3: "sub"}


def classify(text: str, indent: int) -> str:
    if text == "Prólogo" or re.match(r"^(Primeira|Segunda|Terceira|Quarta) Parte\b", text):
        if indent == 0:
            return "part"
    if re.match(r"^Capítulo (?:Primeiro|Segundo|Terceiro|Quarto|X)\b", text):
        return "chapter"
    if re.match(r"^Artigo (?:\d+|X)\b", text):
        return "article"
    if re.match(r"^Parágrafo (?:\d+|X)\b", text):
        return "par"
    if text == "Introdução" or re.match(r"^(Primeira|Segunda|Terceira|Quarta) Seção\b", text) \
            or re.match(r"^Seção X\b", text):
        return "section"
    return "free"


def struct_seg(node: dict) -> str | None:
    text, typ = node["text"], node["type"]
    first = text.split()[0] if text.split() else ""
    if typ == "part":
        return "prologue" if text == "Prólogo" else f"part-{ORD[first]}"
    if typ == "section":
        if text == "Introdução":
            return "intro"
        if text.startswith("Seção X"):
            return "section-x"
        return f"section-{ORD[first]}"
    if typ == "chapter":
        if text.startswith("Capítulo X"):
            return "chapter-x"
        return f"chapter-{ORD[text.split()[1]]}"
    if typ == "article":
        m = re.match(r"^Artigo (\d+|X)", text)
        n = m.group(1)
        return "article-x" if n == "X" else f"article-{n}"
    return None


def strip_marker(node: dict) -> str:
    text = node["text"]
    if node["type"] == "par":
        out = PAR_LABEL.sub("", text).strip()
        return out or text
    if node["level"] == 2 and ROMAN.match(text):
        out = ROMAN.sub("", text).strip()
        return out or text
    return text


def nearest(node: dict, pred) -> dict | None:
    p = node["parent"]
    while p is not None:
        if pred(p):
            return p
        p = p["parent"]
    return None


def main() -> None:
    raw = SRC.read_text(encoding="utf-8").lstrip("\ufeff").split("\n")
    nodes: list[dict] = []
    stack: list[dict] = []
    for i, line in enumerate(raw):
        if line.strip() == "Observações":
            break
        if not line.strip() or line.strip() == "Índice":
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        node = {
            "line": i + 1, "indent": indent, "text": text,
            "parent": None, "type": None, "level": None,
            "is_group": False, "placeholder": bool(PLACEHOLDER.match(text)),
            "gkey": None, "article_key": None,
        }
        while stack and stack[-1]["indent"] >= indent:
            stack.pop()
        node["parent"] = stack[-1] if stack else None
        node["type"] = classify(text, indent)
        nodes.append(node)
        stack.append(node)

    # is_group: 'par' sempre; 'free' apenas se descende de um artigo
    for n in nodes:
        if n["type"] == "par":
            n["is_group"] = True
        elif n["type"] == "free":
            n["is_group"] = nearest(n, lambda p: p["type"] == "article") is not None

    # níveis (ordem do documento garante pais antes dos filhos)
    for n in nodes:
        if not n["is_group"]:
            continue
        if n["type"] == "par":
            n["level"] = 1
            continue
        ga = nearest(n, lambda p: p["is_group"])
        n["level"] = 2 if ga is None or ga["level"] == 1 else 3

    # article_key para nós de artigo
    for n in nodes:
        if n["type"] != "article":
            continue
        segs, p = [struct_seg(n)], n["parent"]
        while p is not None:
            s = struct_seg(p)
            if s:
                segs.append(s)
            p = p["parent"]
        n["article_key"] = "/".join(reversed(segs))

    records: list[dict] = []
    counters: dict[tuple, int] = {}
    sort_counter: dict[str, int] = {}
    placeholders: set[str] = set()

    for n in nodes:
        art = nearest(n, lambda p: p["type"] == "article")
        if n["type"] == "article" and n["placeholder"]:
            placeholders.add(n["article_key"])
        if not n["is_group"]:
            continue
        if n["placeholder"]:
            continue  # colapsado
        ak = art["article_key"]
        # ancestral de grupo já emitido (pula placeholders colapsados)
        anc = nearest(n, lambda p: p["is_group"] and p["gkey"] is not None)
        prefix = f"{anc['gkey']}/" if anc else ""
        seg = LEVEL_SEG[n["level"]]
        ckey = (ak, prefix, seg)
        counters[ckey] = counters.get(ckey, 0) + 1
        n["gkey"] = f"{prefix}{seg}-{counters[ckey]}"
        sort_counter[ak] = sort_counter.get(ak, 0) + 1
        records.append({
            "article_key": ak,
            "article_group_key": n["gkey"],
            "title": strip_marker(n),
            "title_format": "html",
            "level": n["level"],
            "sort_order": sort_counter[ak],
            "metadata": None,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # relatório
    by_level = {1: 0, 2: 0, 3: 0}
    for r in records:
        by_level[r["level"]] += 1
    arts = sorted({r["article_key"] for r in records})
    ph_used = sorted(k for k in placeholders if any(r["article_key"] == k for r in records))
    print(f"grupos: {len(records)}  (§={by_level[1]}, título={by_level[2]}, subtítulo={by_level[3]})")
    print(f"artigos com grupos: {len(arts)}")
    print(f"artigos placeholder (Artigo X) com grupos: {len(ph_used)}")
    for k in ph_used:
        print(f"  - {k}")


if __name__ == "__main__":
    main()
