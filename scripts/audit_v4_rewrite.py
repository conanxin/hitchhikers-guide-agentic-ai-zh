from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

from bs4 import BeautifulSoup


REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site-v4"

REQUIRED = [
    "index.html",
    "roadmap.html",
    "concepts.html",
    "glossary.html",
    "references.html",
    "search.html",
    "about.html",
    "assets/css/main.css",
    "assets/js/main.js",
    "assets/js/search.js",
    "assets/data/search-index.json",
    "assets/data/v4_lessons.json",
]

ALLOWED = {
    "AI", "LLM", "PPO", "DPO", "GRPO", "RAG", "SFT", "RLHF", "RL", "MDP",
    "BPE", "GPU", "API", "MCP", "A2A", "KV", "PDF", "OCR", "AST", "V3",
    "V4", "TOKEN", "TRANSFORMER", "ROPE", "ARXIV", "URL", "ZERO", "FSDP",
    "DAG", "HTML", "CSS", "JS", "JSON", "PAGEDATTENTION", "KTO", "IPO", "ORPO",
}


def html_files() -> list[Path]:
    return sorted(SITE.rglob("*.html"))


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def visible_soup(path: Path) -> BeautifulSoup:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "pre", "code"]):
        tag.decompose()
    return soup


def heading_issues() -> list[dict]:
    bad = []
    for path in html_files():
        soup = visible_soup(path)
        for node in soup.find_all(["h1", "h2", "h3"]):
            text = node.get_text(" ", strip=True)
            words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text)
            meaningful = [w for w in words if w.upper() not in ALLOWED]
            if len(meaningful) >= 2:
                bad.append({"file": str(path.relative_to(SITE)), "text": text})
    return bad[:30]


def english_paragraphs() -> list[dict]:
    bad = []
    for path in html_files():
        if path.name == "references.html":
            continue
        soup = visible_soup(path)
        for node in soup.find_all(["p", "li", "td"]):
            text = node.get_text(" ", strip=True)
            if len(text) < 60 or "http" in text:
                continue
            words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text)
            meaningful = [w for w in words if w.upper() not in ALLOWED]
            han = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            if len(meaningful) >= 12 and len(meaningful) > max(8, han / 3):
                bad.append({"file": str(path.relative_to(SITE)), "text": text[:180]})
    return bad[:30]


def garbled() -> list[str]:
    pattern = re.compile(r"\ufffd|锟斤拷|���|□□|||\\fn|绗\?|鈥|閳|泑|梊")
    return [str(path.relative_to(SITE)) for path in html_files() if pattern.search(path.read_text(encoding="utf-8", errors="replace"))]


def page_pollution() -> list[str]:
    pattern = re.compile(r"第\s*\d+\s*页|原\s*PDF\s*p\.?\s*\d+|page-ref|pdf-p\d+|page_\d+", re.I)
    return [str(path.relative_to(SITE)) for path in html_files() if pattern.search(path.read_text(encoding="utf-8", errors="replace"))]


def broken_links() -> list[str]:
    broken = []
    ids_by_file = {}
    for path in html_files():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        ids_by_file[path.resolve()] = {tag.get("id") for tag in soup.find_all(id=True)}
    for path in html_files():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for tag in soup.find_all(["a", "link", "script"]):
            href = tag.get("href") if tag.name in {"a", "link"} else tag.get("src")
            if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            clean, frag = urldefrag(href)
            target = (path.parent / clean).resolve() if clean else path.resolve()
            if clean and not target.exists():
                broken.append(f"{path.relative_to(SITE)} -> {href}")
            elif frag and frag not in ids_by_file.get(target, set()):
                broken.append(f"{path.relative_to(SITE)} -> missing #{frag}")
    return broken[:50]


def audit() -> dict:
    missing = [item for item in REQUIRED if not (SITE / item).exists()]
    chapters = sorted((SITE / "chapters").glob("chapter-*.html")) if (SITE / "chapters").exists() else []
    lesson_data = load_json(SITE / "assets/data/v4_lessons.json", {})
    search_index = load_json(SITE / "assets/data/search-index.json", [])
    issues = {
        "missing": missing,
        "chapter_pages": len(chapters),
        "lesson_schema": lesson_data.get("schema"),
        "lesson_count": len(lesson_data.get("lessons", [])),
        "search_index_count": len(search_index),
        "heading_issues": heading_issues(),
        "english_paragraphs": english_paragraphs(),
        "garbled": garbled(),
        "page_pollution": page_pollution(),
        "broken_links": broken_links(),
        "has_learning_path": "学习路径" in (SITE / "index.html").read_text(encoding="utf-8", errors="replace") if (SITE / "index.html").exists() else False,
        "has_about_rewrite_notice": "不是逐字翻译版" in (SITE / "about.html").read_text(encoding="utf-8", errors="replace") if (SITE / "about.html").exists() else False,
    }
    status = "PASS"
    if (
        missing or len(chapters) != 14 or issues["lesson_schema"] != "v4_learning_lessons"
        or issues["lesson_count"] != 14 or len(search_index) != 14 or issues["heading_issues"]
        or issues["garbled"] or issues["page_pollution"] or issues["broken_links"]
        or not issues["has_learning_path"] or not issues["has_about_rewrite_notice"]
    ):
        status = "FAILED"
    elif issues["english_paragraphs"]:
        status = "WARN"
    issues["status"] = status
    return issues


def main() -> None:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "FAILED":
        sys.exit(2)


if __name__ == "__main__":
    main()
