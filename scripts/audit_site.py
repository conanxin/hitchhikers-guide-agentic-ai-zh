from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

from bs4 import BeautifulSoup


REPO = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html",
    "chapters/index.html",
    "glossary.html",
    "references.html",
    "search.html",
    "quality-report.html",
    "assets/css/main.css",
    "assets/css/article.css",
    "assets/css/responsive.css",
    "assets/js/main.js",
    "assets/js/search.js",
    "assets/js/toc.js",
    "assets/js/progress.js",
    "assets/data/clean_chapter_tree.json",
    "assets/data/search-index.json",
    "assets/data/glossary.json",
]

ALLOWED_WORDS = {
    "LLM", "AI", "API", "GPU", "CPU", "CUDA", "BPE", "RL", "SFT", "RAG",
    "DPO", "GRPO", "MDP", "PPO", "SGD", "ADAM", "ADAMW", "TRANSFORMER",
    "TOKEN", "ROPE", "VLLM", "FLASHATTENTION", "HUGGING", "FACE", "ARXIV",
    "DOI", "URL", "MCP", "A2A", "KV", "MLP", "RLHF", "RLVR", "TP", "PP",
    "DP", "FSDP", "DDP", "LORA", "QLORA", "PEFT", "MOE", "ICLR", "ACL",
    "NEURIPS", "ICML", "FASTAPI", "REACT", "LANGGRAPH", "BF16", "FP8",
    "INT8", "FP32", "AWQ", "AQLM", "V100", "A100", "H100", "H200",
    "B200", "GB", "TB", "TF", "HBM", "PCIE", "NVLINK", "INFINIBAND",
    "NDR", "RDMA", "ROCE", "TCP", "ETHERNET", "VOLTA", "AMPERE",
    "HOPPER", "BLACKWELL", "AMD", "GOOGLE", "TPU", "JAX", "XLA",
    "TENSOR", "CORE", "CORES", "FLOP", "FLOPS", "ROOFLINE", "BATCH",
    "KAHNEMAN", "TVERSKY", "KAHNEMAN-TVERSKY", "QWQ", "QWEN", "DEEPSEEK",
}


def html_files() -> list[Path]:
    return sorted(path for path in REPO.rglob("*.html") if ".git" not in path.parts)


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def visible_soup(path: Path) -> BeautifulSoup:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "pre", "code"]):
        tag.decompose()
    return soup


def english_residuals() -> list[dict[str, str]]:
    findings = []
    for path in html_files():
        if path.name == "references.html":
            continue
        soup = visible_soup(path)
        for node in soup.find_all(["h1", "h2", "h3", "p", "li", "figcaption"]):
            text = node.get_text(" ", strip=True)
            if len(text) < 48 or re.search(r"https?://|arXiv|DOI", text):
                continue
            words = re.findall(r"[A-Za-z][A-Za-z\-']+", text)
            meaningful = [w for w in words if w.upper() not in ALLOWED_WORDS]
            han = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            if len(meaningful) >= 12 and len(meaningful) > max(10, han / 3):
                findings.append({"file": str(path.relative_to(REPO)), "text": text[:220]})
                if len(findings) >= 25:
                    return findings
    return findings


def english_heading_residuals() -> list[dict[str, str]]:
    findings = []
    for path in html_files():
        if path.name == "references.html":
            continue
        soup = visible_soup(path)
        for node in soup.find_all(["h1", "h2", "h3"]):
            text = node.get_text(" ", strip=True)
            words = re.findall(r"[A-Za-z][A-Za-z\-']+", text)
            meaningful = [w for w in words if w.upper() not in ALLOWED_WORDS]
            if len(meaningful) >= 2:
                findings.append({"file": str(path.relative_to(REPO)), "text": text})
                if len(findings) >= 50:
                    return findings
    return findings


def page_number_dom_findings() -> list[str]:
    bad = []
    patterns = [
        re.compile(r"第\s*\d+\s*页"),
        re.compile(r"原\s*PDF\s*p\.?\s*\d+", re.I),
        re.compile(r"pdf-p\d+", re.I),
        re.compile(r"page-ref", re.I),
        re.compile(r"page_\d{3}", re.I),
    ]
    for path in html_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(p.search(text) for p in patterns):
            bad.append(str(path.relative_to(REPO)))
    return bad


def garbled_findings() -> list[str]:
    bad = []
    pattern = re.compile(r"\ufffd|���|□□|鈥|锛|绗\?||||\\fn")
    for path in html_files():
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            bad.append(str(path.relative_to(REPO)))
    return bad


def broken_links() -> list[str]:
    broken = []
    ids_by_file = {}
    for path in html_files():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        ids_by_file[path.resolve()] = {tag.get("id") for tag in soup.find_all(id=True)}
    for path in html_files():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for tag in soup.find_all(["a", "link", "script", "img"]):
            attr = "href" if tag.name in {"a", "link"} else "src"
            href = tag.get(attr)
            if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            clean, frag = urldefrag(href)
            target = (path.parent / clean).resolve() if clean else path.resolve()
            if clean and not target.exists():
                broken.append(f"{path.relative_to(REPO)} -> {href}")
            elif frag and frag not in ids_by_file.get(target, set()):
                broken.append(f"{path.relative_to(REPO)} -> missing #{frag}")
    return broken[:50]


def audit_ast(ast: dict) -> dict:
    issues = []
    if ast.get("schema") != "clean_chapter_tree.v3":
        issues.append("clean_chapter_tree schema is not v3")
    if not ast.get("chapters"):
        issues.append("no chapters in clean AST")
    formula_count = 0
    fallback_count = 0
    raw_markdown_count = 0
    for chapter in ast.get("chapters", []):
        if "metadata" not in chapter or "source_pages" not in chapter["metadata"]:
            issues.append(f"{chapter.get('id')} missing page metadata")
        if not chapter.get("sections"):
            issues.append(f"{chapter.get('id')} missing sections")
        for section in chapter.get("sections", []):
            for block in section.get("blocks", []):
                if block.get("type") in {"formula", "formula_image"}:
                    formula_count += 1
                    if block.get("fallback") in {"latex", "image"}:
                        fallback_count += 1
                if block.get("type") == "raw_markdown":
                    raw_markdown_count += 1
                text = json.dumps(block, ensure_ascii=False)
                if re.search(r"<a id=|##\s+第\s*\d+\s*页|page-ref", text):
                    issues.append(f"{chapter.get('id')} contains raw markdown/page marker")
    if raw_markdown_count:
        issues.append("raw markdown block exists")
    if formula_count == 0 or fallback_count == 0:
        issues.append("formula fallback not found")
    return {"issues": issues, "formula_count": formula_count, "fallback_count": fallback_count}


def audit() -> dict:
    missing = [item for item in REQUIRED if not (REPO / item).exists()]
    ast = load_json(REPO / "assets/data/clean_chapter_tree.json", {})
    search_index = load_json(REPO / "assets/data/search-index.json", [])
    chapter_files = list((REPO / "chapters").glob("chapter-*.html"))
    page_dom = page_number_dom_findings()
    english = english_residuals()
    english_headings = english_heading_residuals()
    garbled = garbled_findings()
    links = broken_links()
    ast_result = audit_ast(ast)
    css_mobile = "max-width" in (REPO / "assets/css/responsive.css").read_text(encoding="utf-8") if (REPO / "assets/css/responsive.css").exists() else False
    structure_sources = {
        "clean_chapter_tree": (REPO / "assets/data/clean_chapter_tree.json").exists(),
        "legacy_chapters_json": (REPO / "assets/data/chapters.json").exists(),
    }
    status = "PASS"
    if missing or not ast.get("chapters") or not search_index or page_dom or english_headings or garbled or links or ast_result["issues"] or structure_sources["legacy_chapters_json"]:
        status = "FAILED"
    elif english:
        status = "WARN"
    return {
        "status": status,
        "missing": missing,
        "chapter_count": len(ast.get("chapters", [])),
        "chapter_page_count": len(chapter_files),
        "search_index_count": len(search_index),
        "structure_sources": structure_sources,
        "page_number_dom_findings": page_dom,
        "english_heading_residuals": english_headings,
        "english_residuals": english,
        "garbled_findings": garbled,
        "broken_links": links,
        "ast_issues": ast_result["issues"],
        "formula_count": ast_result["formula_count"],
        "fallback_count": ast_result["fallback_count"],
        "mobile_css": css_mobile,
        "componentized_sections": "section-overview" in (chapter_files[0].read_text(encoding="utf-8") if chapter_files else ""),
        "key_concepts": "key-concepts-panel" in (chapter_files[0].read_text(encoding="utf-8") if chapter_files else ""),
    }


def main() -> None:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "FAILED":
        sys.exit(2)


if __name__ == "__main__":
    main()
