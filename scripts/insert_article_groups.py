#!/usr/bin/env python3
"""Insere `article_groups` no banco a partir de Insert-data/article-groups.json.

Resolve `article_key` -> `article_id` cruzando o índice com a hierarquia já
carregada em `content.articles` (por caminho ordinal + título do artigo).

Uso:
  python scripts/insert_article_groups.py [--dry-run]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cic_digital.core.config import settings

SRC_INDEX = Path("docs/Índice do catecismo.txt")
SRC_JSON = Path("Insert-data/article-groups.json")

ORD = {
    "Primeira": 1, "Segunda": 2, "Terceira": 3, "Quarta": 4,
    "Primeiro": 1, "Segundo": 2, "Terceiro": 3, "Quarto": 4,
}
ART_LINE = re.compile(r"^Artigo (\d+|X)\s*(.*)$")
CH_LINE = re.compile(r"^Capítulo (Primeiro|Segundo|Terceiro|Quarto|X)\b(.*)$")
SEC_LINE = re.compile(r"^(Primeira|Segunda|Terceira|Quarta) Seção\b(.*)$")

# grupos cujo conteúdo já está modelado como artigos `section_preamble` no banco
SKIP_ARTICLE_KEYS = frozenset({
    "part-3/section-2/chapter-x/article-x",
})

# prólogo: títulos I–VI já são títulos de artigo; só subtítulos de «Estrutura» entram
PROLOGUE_SUBS_ONLY = "prologue/section-x/chapter-x/article-x"


def normalize_article_key(article_key: str) -> str:
    """Introdução não tem capítulo explícito no índice; no banco é chapter-1."""
    parts = article_key.split("/")
    if len(parts) == 3 and parts[1] == "intro":
        return f"{parts[0]}/intro/chapter-1/{parts[2]}"
    return article_key


def normalize(title: str) -> str:
    s = title.lower().strip()
    s = s.replace("–", "-").replace("—", "-").replace(":", "-")
    s = re.sub(r"[«»\"“”]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def struct_seg(typ: str, line_text: str) -> str | None:
    first = line_text.split()[0] if line_text.split() else ""
    if typ == "part":
        return "prologue" if line_text == "Prólogo" else f"part-{ORD[first]}"
    if typ == "section":
        if line_text == "Introdução":
            return "intro"
        if line_text.startswith("Seção X"):
            return "section-x"
        return f"section-{ORD[first]}"
    if typ == "chapter":
        if line_text.startswith("Capítulo X"):
            return "chapter-x"
        return f"chapter-{ORD[line_text.split()[1]]}"
    if typ == "article":
        m = ART_LINE.match(line_text)
        if not m:
            return None
        n = m.group(1)
        return "article-x" if n == "X" else f"article-{n}"
    return None


def classify(text: str, indent: int) -> str | None:
    if text == "Prólogo" or re.match(r"^(Primeira|Segunda|Terceira|Quarta) Parte\b", text):
        if indent == 0:
            return "part"
    if CH_LINE.match(text):
        return "chapter"
    if ART_LINE.match(text):
        return "article"
    if text == "Introdução" or SEC_LINE.match(text) or text.startswith("Seção X"):
        return "section"
    return None


def walk_index_articles() -> dict[str, str]:
    """article_key -> título descritivo (sem rótulo 'Artigo N')."""
    lines = SRC_INDEX.read_text(encoding="utf-8").lstrip("\ufeff").split("\n")
    stack: list[tuple[int, str, str]] = []  # indent, type, text
    path: list[str] = []
    out: dict[str, str] = {}

    for line in lines:
        if line.strip() == "Observações":
            break
        if not line.strip() or line.strip() == "Índice":
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        typ = classify(text, indent)
        while stack and stack[-1][0] >= indent:
            stack.pop()
            if path:
                path.pop()
        if typ:
            stack.append((indent, typ, text))
            seg = struct_seg(typ, text)
            if seg:
                path.append(seg)
            if typ == "article":
                m = ART_LINE.match(text)
                title = (m.group(2) or "").strip() if m else text
                out[normalize_article_key("/".join(path))] = title
    return out


def load_hierarchy(session: Session) -> tuple[dict[str, int], dict[int, list[dict]]]:
    """Retorna chapter_key -> id e chapter_id -> artigos."""
    rows = session.execute(text("""
        SELECT p.kind, p.sort_order AS part_so,
               s.sort_order AS sec_so, s.title AS sec_title,
               ch.sort_order AS ch_so, ch.id AS chapter_id,
               a.id AS article_id, a.sort_order AS art_so,
               a.title AS art_title, a.metadata AS art_meta
        FROM content.articles a
        JOIN content.chapters ch ON ch.id = a.chapter_id
        JOIN content.sections s ON s.id = ch.section_id
        JOIN content.parts p ON p.id = s.part_id
        ORDER BY p.sort_order, s.sort_order, ch.sort_order, a.sort_order
    """)).mappings().all()

    chapter_keys: dict[str, int] = {}
    articles: dict[int, list[dict]] = {}

    for r in rows:
        if r["kind"] == "prologue":
            part_key = "prologue"
        else:
            part_key = f"part-{r['part_so']}"

        if r["sec_so"] == 0 and "introdução" in (r["sec_title"] or "").lower():
            sec_key = "intro"
        elif part_key == "prologue":
            sec_key = "section-x"
        else:
            sec_key = f"section-{r['sec_so']}"

        if r["ch_so"] == 0:
            ch_key = "chapter-x"
        elif part_key == "prologue" and r["ch_so"] == 1:
            ch_key = "chapter-x"  # índice usa Capítulo X; banco sort_order=1
        else:
            ch_map = {1: "chapter-1", 2: "chapter-2", 3: "chapter-3", 4: "chapter-4"}
            ch_key = ch_map.get(r["ch_so"], f"chapter-{r['ch_so']}")
        ck = f"{part_key}/{sec_key}/{ch_key}"
        chapter_keys[ck] = r["chapter_id"]
        articles.setdefault(r["chapter_id"], []).append({
            "id": r["article_id"],
            "sort_order": r["art_so"],
            "title": r["art_title"] or "",
            "metadata": r["art_meta"] or {},
        })

    return chapter_keys, articles


def pick_placeholder(arts: list[dict]) -> int | None:
    for a in arts:
        meta = a["metadata"]
        if meta.get("placeholder") or meta.get("role") == "chapter_unassigned":
            return a["id"]
    for a in arts:
        if a["sort_order"] == 0 and not a["title"].strip():
            return a["id"]
    return None


def resolve_article_id(
    article_key: str,
    index_titles: dict[str, str],
    chapter_keys: dict[str, int],
    articles: dict[int, list[dict]],
) -> int | None:
    article_key = normalize_article_key(article_key)
    if article_key in SKIP_ARTICLE_KEYS:
        return None

    parts = article_key.split("/")
    if len(parts) != 4:
        return None
    chapter_key = "/".join(parts[:3])
    art_seg = parts[3]
    chapter_id = chapter_keys.get(chapter_key)
    if chapter_id is None:
        return None
    arts = articles.get(chapter_id, [])

    # Introdução: único artigo da seção
    if parts[1] == "intro" and art_seg == "article-x":
        return arts[0]["id"] if len(arts) == 1 else None

    # Prólogo: só subtítulos de «Estrutura deste catecismo» (artigo sort_order 4)
    if article_key == PROLOGUE_SUBS_ONLY:
        for a in arts:
            if normalize(a["title"]) == normalize("Estrutura deste Catecismo"):
                return a["id"]
        return None

    if art_seg == "article-x":
        return pick_placeholder(arts)

    title_hint = index_titles.get(article_key, "")
    if title_hint:
        nh = normalize(title_hint)
        for a in arts:
            if normalize(a["title"]) == nh:
                return a["id"]
        # correspondência parcial (títulos truncados no banco)
        for a in arts:
            at = normalize(a["title"])
            if at and (at.startswith(nh[:40]) or nh.startswith(at[:40])):
                return a["id"]

    # fallback: artigo numerado pelo rótulo do índice (Artigo 8, Artigo 9, ...)
    m = re.match(r"article-(\d+)$", art_seg)
    if m:
        num = int(m.group(1))
        numbered = [a for a in arts if not a["metadata"].get("placeholder")
                    and a["metadata"].get("role") not in ("chapter_unassigned", "section_preamble")]
        for a in numbered:
            im = re.search(r"artigo\s+" + str(num) + r"\b", index_titles.get(article_key, "").lower())
        # ordem no índice: lista de article_keys do mesmo capítulo na ordem do arquivo
    return None


def build_chapter_article_order(index_titles: dict[str, str]) -> dict[str, list[str]]:
    """chapter_key -> article_keys na ordem do índice."""
    order: dict[str, list[str]] = {}
    for ak in index_titles:
        ak = normalize_article_key(ak)
        ck = "/".join(ak.split("/")[:3])
        order.setdefault(ck, []).append(ak)
    return order


def resolve_with_order(
    article_key: str,
    index_titles: dict[str, str],
    chapter_keys: dict[str, int],
    articles: dict[int, list[dict]],
    chapter_order: dict[str, list[str]],
) -> int | None:
    article_key = normalize_article_key(article_key)
    base = resolve_article_id(article_key, index_titles, chapter_keys, articles)
    if base is not None:
        return base

    parts = article_key.split("/")
    if len(parts) != 4:
        return None
    chapter_key = "/".join(parts[:3])
    art_seg = parts[3]
    chapter_id = chapter_keys.get(chapter_key)
    if chapter_id is None or not art_seg.startswith("article-"):
        return None
    if art_seg == "article-x":
        return None

    num = int(art_seg.split("-")[1])
    arts = [a for a in articles.get(chapter_id, [])
            if not a["metadata"].get("placeholder")
            and a["metadata"].get("role") not in ("section_preamble", "chapter_unassigned")]
    keys = chapter_order.get(chapter_key, [])
    nums = []
    for k in keys:
        m = re.match(r"article-(\d+)$", k.split("/")[-1])
        if m:
            nums.append(int(m.group(1)))
    if num in nums:
        pos = nums.index(num)
        if pos < len(arts):
            return arts[pos]["id"]
    return None


def should_insert_group(article_key: str, group: dict) -> bool:
    if article_key in SKIP_ARTICLE_KEYS:
        return False
    if article_key == PROLOGUE_SUBS_ONLY:
        return group["article_group_key"].startswith("title-4/sub-")
    if article_key == "part-4/section-1/chapter-x/article-x":
        # título e três blocos já são artigos section_preamble
        return False
    return True


def main() -> None:
    dry = "--dry-run" in sys.argv
    groups = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    index_titles = walk_index_articles()
    chapter_order = build_chapter_article_order(index_titles)

    engine = create_engine(settings.database_url)
    inserted = skipped = unresolved = 0
    unresolved_keys: set[str] = set()

    with Session(engine) as session:
        chapter_keys, articles = load_hierarchy(session)
        existing = session.execute(
            text("SELECT count(*) FROM content.article_groups")
        ).scalar()
        if existing and not dry:
            if "--force" not in sys.argv:
                print(f"AVISO: já existem {existing} article_groups.")
                print("Use --force para apagar e reinserir.")
                sys.exit(1)
            session.execute(text("DELETE FROM content.article_groups"))
            session.commit()
            print(f"removidos {existing} article_groups anteriores")

        rows_to_insert: list[dict] = []
        sort_by_article: dict[int, int] = {}
        for g in groups:
            ak = g["article_key"]
            if not should_insert_group(ak, g):
                skipped += 1
                continue
            aid = resolve_with_order(ak, index_titles, chapter_keys, articles, chapter_order)
            if aid is None:
                unresolved += 1
                unresolved_keys.add(ak)
                continue
            sort_by_article[aid] = sort_by_article.get(aid, 0) + 1
            rows_to_insert.append({
                "article_id": aid,
                "title": g["title"],
                "title_format": g.get("title_format", "html"),
                "level": g["level"],
                "sort_order": sort_by_article[aid],
                "metadata": g.get("metadata"),
            })

        if dry:
            print(f"dry-run: inseriria {len(rows_to_insert)} grupos")
            print(f"ignorados (regra): {skipped}")
            print(f"sem article_id: {unresolved}")
            if unresolved_keys:
                print("article_keys não resolvidos:")
                for k in sorted(unresolved_keys):
                    print(f"  - {k}")
            return

        for row in rows_to_insert:
            session.execute(
                text("""
                    INSERT INTO content.article_groups
                        (article_id, title, title_format, level, sort_order, metadata)
                    VALUES
                        (:article_id, :title, :title_format, :level, :sort_order, :metadata)
                """),
                row,
            )
            inserted += 1
        session.commit()

    print(f"inseridos: {inserted}")
    print(f"ignorados (regra): {skipped}")
    print(f"sem article_id: {unresolved}")
    if unresolved_keys:
        print("article_keys não resolvidos:")
        for k in sorted(unresolved_keys):
            print(f"  - {k}")


if __name__ == "__main__":
    main()
