from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

from bs4 import BeautifulSoup


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
SITE = REPO / "site-v4"
REPORT = ROOT / "report" / "v4_1_expanded_audit_report.md"

REQUIRED = [
    "index.html",
    "roadmap.html",
    "concepts.html",
    "glossary.html",
    "references.html",
    "search.html",
    "about.html",
    "chapters/chapter-02.html",
    "chapters/chapter-03.html",
    "chapters/chapter-09.html",
    "chapters/chapter-11.html",
    "chapters/chapter-12.html",
    "assets/css/main.css",
    "assets/js/main.js",
    "assets/js/search.js",
    "assets/data/search-index.json",
    "assets/data/v4_lessons.json",
    "assets/data/v4_expansion_metrics.json",
]

FOCUS_CHAPTERS = {
    "chapter-02",
    "chapter-03",
    "chapter-05",
    "chapter-06",
    "chapter-07",
    "chapter-08",
    "chapter-11",
    "chapter-12",
}

SEARCH_TERMS = [
    "RoPE",
    "FlashAttention",
    "KV Cache",
    "PPO",
    "DPO",
    "GRPO",
    "KTO",
    "IPO",
    "ORPO",
    "Reward Model",
    "Agentic AI",
    "ReAct",
    "STaR",
    "RAG",
    "trajectory buffer",
    "PagedAttention",
    "HBM",
    "NVLink",
]

ALLOWED_WORDS = {
    "AI",
    "LLM",
    "PPO",
    "DPO",
    "GRPO",
    "RAG",
    "SFT",
    "RLHF",
    "RL",
    "MDP",
    "BPE",
    "GPU",
    "CPU",
    "API",
    "MCP",
    "A2A",
    "KV",
    "PDF",
    "AST",
    "V3",
    "V4",
    "TOKEN",
    "TRANSFORMER",
    "ROPE",
    "ARXIV",
    "URL",
    "ZERO",
    "FSDP",
    "DAG",
    "HTML",
    "CSS",
    "JS",
    "JSON",
    "PAGEDATTENTION",
    "KTO",
    "IPO",
    "ORPO",
    "SM",
    "CUDA",
    "OPENAI",
    "O1",
    "O3",
    "HBM",
    "NVLINK",
    "PCIE",
    "FLASHATTENTION",
    "REACT",
    "STAR",
    "TOP",
}

TEMP_PATTERNS = [
    "公式内容已由 OCR 清洗",
    "fallback",
    "占位文案",
    "占位说明",
    "TODO",
    "FIXME",
    "临时提示",
]

GARBLED_PATTERN = re.compile(r"\ufffd|���|锟斤拷|□|鈻|閿|绗�|椤�|闁|铮|�")
PAGE_HEADING_PATTERN = re.compile(r"<h[1-6][^>]*>\s*第\s*\d+\s*页\s*</h[1-6]>", re.I)
PAGE_MARKDOWN_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s*第\s*\d+\s*页\s*$", re.M)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def html_files() -> list[Path]:
    return sorted(SITE.rglob("*.html")) if SITE.exists() else []


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(read_text(path))


def soup_for(path: Path) -> BeautifulSoup:
    soup = BeautifulSoup(read_text(path), "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup


def visible_text(path: Path) -> str:
    soup = soup_for(path)
    for tag in soup(["pre", "code"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def chinese_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def chapter_lengths() -> list[dict]:
    rows = []
    for path in sorted((SITE / "chapters").glob("chapter-*.html")) if (SITE / "chapters").exists() else []:
        soup = soup_for(path)
        article = soup.find("article") or soup
        text = article.get_text(" ", strip=True)
        slug = path.stem
        rows.append(
            {
                "chapter": slug,
                "chars": chinese_chars(text),
                "threshold": 5000 if slug in FOCUS_CHAPTERS else 2500,
                "status": "PASS",
            }
        )
    for row in rows:
        if row["chars"] < row["threshold"]:
            row["status"] = "SHORT"
    return rows


def english_residuals() -> list[dict]:
    issues = []
    for path in html_files():
        if path.name == "references.html":
            continue
        soup = soup_for(path)
        for node in soup.find_all(["p", "li", "td"]):
            text = node.get_text(" ", strip=True)
            if len(text) < 90 or "http" in text:
                continue
            words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text)
            meaningful = [word for word in words if word.upper() not in ALLOWED_WORDS]
            han = chinese_chars(text)
            if len(meaningful) >= 16 and len(meaningful) > max(10, han / 2.5):
                issues.append({"file": str(path.relative_to(SITE)), "text": text[:220]})
    return issues[:25]


def heading_english_issues() -> list[dict]:
    issues = []
    for path in html_files():
        soup = soup_for(path)
        for node in soup.find_all(["h1", "h2", "h3"]):
            text = node.get_text(" ", strip=True)
            words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text)
            meaningful = [word for word in words if word.upper() not in ALLOWED_WORDS]
            if len(meaningful) >= 3:
                issues.append({"file": str(path.relative_to(SITE)), "heading": text})
    return issues[:25]


def garbled_files() -> list[str]:
    hits = []
    for path in html_files():
        text = read_text(path)
        if GARBLED_PATTERN.search(text):
            hits.append(str(path.relative_to(SITE)))
    return hits


def page_pollution_files() -> list[str]:
    hits = []
    for path in html_files():
        text = read_text(path)
        if PAGE_HEADING_PATTERN.search(text) or PAGE_MARKDOWN_PATTERN.search(text):
            hits.append(str(path.relative_to(SITE)))
    return hits


def temp_text_files() -> list[str]:
    hits = []
    for path in html_files():
        text = read_text(path)
        if any(pattern in text for pattern in TEMP_PATTERNS):
            hits.append(str(path.relative_to(SITE)))
    return hits


def broken_links() -> list[str]:
    broken = []
    ids_by_file: dict[Path, set[str]] = {}
    all_files = html_files()
    for path in all_files:
        soup = BeautifulSoup(read_text(path), "html.parser")
        ids_by_file[path.resolve()] = {tag.get("id") for tag in soup.find_all(id=True)}
    for path in all_files:
        soup = BeautifulSoup(read_text(path), "html.parser")
        for tag in soup.find_all(["a", "link", "script"]):
            href = tag.get("href") if tag.name in {"a", "link"} else tag.get("src")
            if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            clean, frag = urldefrag(href)
            clean_path = clean.split("?", 1)[0]
            target = (path.parent / clean_path).resolve() if clean_path else path.resolve()
            if clean_path and not target.exists():
                broken.append(f"{path.relative_to(SITE)} -> {href}")
            elif frag and frag not in ids_by_file.get(target, set()):
                broken.append(f"{path.relative_to(SITE)} -> missing #{frag}")
    return broken[:80]


def search_coverage() -> dict:
    index_text = json.dumps(load_json(SITE / "assets/data/search-index.json", []), ensure_ascii=False)
    found = []
    missing = []
    lower = index_text.lower()
    for term in SEARCH_TERMS:
        if term.lower() in lower:
            found.append(term)
        else:
            missing.append(term)
    return {"found": found, "missing": missing}


def mobile_css_ok() -> bool:
    css = read_text(SITE / "assets/css/main.css") if (SITE / "assets/css/main.css").exists() else ""
    return "@media" in css and bool(re.search(r"max-width\s*:\s*(720|900|980)px", css))


def run_audit() -> dict:
    missing = [item for item in REQUIRED if not (SITE / item).exists()]
    lessons = load_json(SITE / "assets/data/v4_lessons.json", {})
    search_index = load_json(SITE / "assets/data/search-index.json", [])
    lengths = chapter_lengths()
    search = search_coverage()
    result = {
        "missing": missing,
        "lesson_schema": lessons.get("schema"),
        "lesson_count": len(lessons.get("lessons", [])),
        "chapter_pages": len(lengths),
        "search_index_count": len(search_index),
        "chapter_lengths": lengths,
        "short_chapters": [row for row in lengths if row["status"] != "PASS"],
        "garbled": garbled_files(),
        "page_pollution": page_pollution_files(),
        "temp_text": temp_text_files(),
        "english_residuals": english_residuals(),
        "heading_english": heading_english_issues(),
        "broken_links": broken_links(),
        "search": search,
        "mobile_css": mobile_css_ok(),
        "v3_root_local_present": (REPO / "index.html").exists(),
        "v4_target_local_present": (SITE / "index.html").exists(),
    }
    failed = (
        missing
        or result["lesson_schema"] != "v4_1_expanded_lessons"
        or result["lesson_count"] != 14
        or result["chapter_pages"] != 14
        or result["search_index_count"] < 14
        or result["short_chapters"]
        or result["garbled"]
        or result["page_pollution"]
        or result["temp_text"]
        or result["heading_english"]
        or result["broken_links"]
        or search["missing"]
        or not result["mobile_css"]
        or not result["v3_root_local_present"]
        or not result["v4_target_local_present"]
    )
    result["status"] = "FAILED" if failed else ("WARN" if result["english_residuals"] else "PASS")
    return result


def write_report(result: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    length_rows = "\n".join(
        f"| {row['chapter']} | {row['chars']} | {row['threshold']} | {row['status']} |"
        for row in result["chapter_lengths"]
    )
    report = f"""# V4.1 Expanded Edition Audit Report

## STATUS

{result['status']}

## Structural Checks

- Required files missing: {len(result['missing'])}
- Lesson schema: {result['lesson_schema']}
- Lesson count: {result['lesson_count']}
- Chapter pages: {result['chapter_pages']}
- Search index entries: {result['search_index_count']}
- Mobile CSS: {'PASS' if result['mobile_css'] else 'FAILED'}
- V3 root local present: {'PASS' if result['v3_root_local_present'] else 'FAILED'}
- V4 local site present: {'PASS' if result['v4_target_local_present'] else 'FAILED'}

## Chapter Lengths

| Chapter | Chinese chars | Threshold | Status |
|---|---:|---:|---|
{length_rows}

## Content Quality

- Short chapters: {len(result['short_chapters'])}
- OCR / garbled artifacts: {len(result['garbled'])}
- Broken formulas or temporary fallback text: {len(result['temp_text'])}
- Page-number pollution: {len(result['page_pollution'])}
- English heading residuals: {len(result['heading_english'])}
- Large English paragraphs: {len(result['english_residuals'])}
- Broken links: {len(result['broken_links'])}
- Search terms missing: {', '.join(result['search']['missing']) if result['search']['missing'] else 'None'}

## Details

### Missing Files
{json.dumps(result['missing'], ensure_ascii=False, indent=2)}

### Short Chapters
{json.dumps(result['short_chapters'], ensure_ascii=False, indent=2)}

### Garbled Files
{json.dumps(result['garbled'], ensure_ascii=False, indent=2)}

### Temporary Text Files
{json.dumps(result['temp_text'], ensure_ascii=False, indent=2)}

### Page Pollution Files
{json.dumps(result['page_pollution'], ensure_ascii=False, indent=2)}

### English Residual Samples
{json.dumps(result['english_residuals'], ensure_ascii=False, indent=2)}

### Broken Links
{json.dumps(result['broken_links'], ensure_ascii=False, indent=2)}
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    result = run_audit()
    write_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "FAILED":
        sys.exit(2)


if __name__ == "__main__":
    main()
