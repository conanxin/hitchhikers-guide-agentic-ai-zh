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
    "assets/data/search-index.json",
    "assets/data/chapters.json",
    "assets/data/glossary.json",
]
ALLOWED_WORDS = {
    "LLM", "AI", "API", "GPU", "CPU", "CUDA", "BPE", "RL", "SFT", "RAG", "DPO",
    "GRPO", "MDP", "PPO", "SGD", "ADAM", "ADAMW", "TRANSFORMER", "TOKEN",
    "ROPE", "VLLM", "FLASHATTENTION", "HUGGING", "FACE", "ARXIV", "DOI", "URL",
    "MCP", "A2A", "KV", "MLP", "RLHF", "RLVR", "TP", "PP", "DP", "FSDP", "DDP",
    "LORA", "QLORA", "PEFT", "MOE", "ICLR", "ACL", "NEURIPS", "ICML", "FASTAPI",
    "REACT", "LANGGRAPH", "BF16", "FP8", "INT8", "FP32", "AWQ", "AQLM", "V100",
    "A100", "H100", "H200", "B200", "GB", "TB", "TF", "HBM", "PCIE", "NVLINK",
    "INFINIBAND", "NDR", "RDMA", "ROCE", "TCP", "ETHERNET", "VOLTA", "AMPERE",
    "HOPPER", "BLACKWELL", "AMD", "GOOGLE", "TPU", "JAX", "XLA", "TENSOR",
    "CORE", "CORES", "SMOOTHQUANT", "DEEPSPEED", "ZERO", "KB", "MB", "L2",
    "TMA", "FP4", "TMEM", "BRADLEY", "TERRY", "MLE", "SIGMOID", "FLOP",
    "FLOPS", "ROOFLINE", "BATCH",
}


def html_files() -> list[Path]:
    return sorted(path for path in REPO.rglob("*.html") if ".git" not in path.parts)


def visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "pre", "code"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def english_residuals() -> list[dict[str, str]]:
    findings = []
    for path in html_files():
        if path.name == "references.html":
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for node in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            if node.find_parent(["pre", "code"]):
                continue
            text = node.get_text(" ", strip=True)
            if len(text) < 40 or re.search(r"https?://|arXiv|DOI", text):
                continue
            words = re.findall(r"[A-Za-z][A-Za-z\-']+", text)
            meaningful = [w for w in words if w.upper() not in ALLOWED_WORDS]
            han = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            if len(meaningful) >= 12 and len(meaningful) > max(10, han / 3):
                findings.append({"file": str(path.relative_to(REPO)), "text": text[:220]})
                if len(findings) >= 25:
                    return findings
    return findings


def page_heading_findings() -> list[str]:
    bad = []
    pattern = re.compile(r"<h[1-3][^>]*>\s*第\s*\d+\s*页\s*</h[1-3]>", re.I)
    for path in html_files():
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            bad.append(str(path.relative_to(REPO)))
    return bad


def garbled_findings() -> list[str]:
    bad = []
    pattern = re.compile(r"\ufffd|���|□□|鈥|锛|绗\?")
    for path in html_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if pattern.search(text):
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


def audit() -> dict:
    missing = [item for item in REQUIRED if not (REPO / item).exists()]
    chapters = json.loads((REPO / "assets/data/chapters.json").read_text(encoding="utf-8")) if (REPO / "assets/data/chapters.json").exists() else []
    search_index = json.loads((REPO / "assets/data/search-index.json").read_text(encoding="utf-8")) if (REPO / "assets/data/search-index.json").exists() else []
    page_headings = page_heading_findings()
    english = english_residuals()
    garbled = garbled_findings()
    links = broken_links()
    css_mobile = (REPO / "assets/css/responsive.css").exists() and "max-width" in (REPO / "assets/css/responsive.css").read_text(encoding="utf-8")
    status = "PASS"
    if missing or page_headings or garbled or links or len(chapters) < 5 or not search_index:
        status = "FAILED"
    elif english:
        status = "WARN"
    return {
        "status": status,
        "missing": missing,
        "chapter_count": len(chapters),
        "search_index_count": len(search_index),
        "page_heading_findings": page_headings,
        "english_residuals": english,
        "garbled_findings": garbled,
        "broken_links": links,
        "mobile_css": css_mobile,
        "left_nav": bool(list((REPO / "chapters").glob("chapter-*.html"))),
        "right_outline": "right-outline" in (REPO / "chapters" / "chapter-02.html").read_text(encoding="utf-8") if (REPO / "chapters" / "chapter-02.html").exists() else False,
    }


def main() -> None:
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "FAILED":
        sys.exit(2)


if __name__ == "__main__":
    main()
