from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

from extract_chapters import Chapter, TocItem, build_chapters, load_toc, parse_pages
from fix_content import clean_markdown_text, clean_toc_title, normalize_terms


REPO = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO.parent
SOURCE_MD = OUTPUT_ROOT / "translated" / "document.zh.md"
SOURCE_GLOSSARY = OUTPUT_ROOT / "translated" / "glossary.md"
TOC_JSON = OUTPUT_ROOT / "extracted" / "toc.json"
IMAGE_MANIFEST = OUTPUT_ROOT / "extracted" / "image_manifest.json"
CACHE_DIR = OUTPUT_ROOT / ".cache"
TRANSLATION_CACHE = CACHE_DIR / "v2_translation_cache.json"
OLD_IMAGE_DIR = REPO / "assets" / "figures"
ALT_IMAGE_DIR = OUTPUT_ROOT / "web" / "assets" / "figures"

SITE_TITLE = "智能体式 AI 漫游指南"
SITE_SUBTITLE = "从基础到系统的中文技术文档站"
ONLINE_URL = "https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/"
PDF_URL = "https://arxiv.org/pdf/2606.24937v1"


GLOSSARY = [
    ("Agentic AI", "智能体式 AI", "具备目标导向、工具使用、环境交互和多步执行能力的 AI 系统。"),
    ("Agent", "智能体", "能够感知状态、规划行动、调用工具并迭代完成任务的系统单元。"),
    ("Token", "标记 / token", "语言模型处理文本的基本离散单位。"),
    ("Tokenization", "分词 / 标记化", "把文本转换成 token 序列的过程。"),
    ("Byte Pair Encoding", "字节对编码（BPE）", "常见子词分词方法，通过合并高频片段构造词表。"),
    ("Transformer", "Transformer", "以自注意力为核心的序列建模架构。"),
    ("Attention", "注意力", "根据查询、键和值计算上下文加权表示的机制。"),
    ("Self-Attention", "自注意力", "序列内部各位置之间相互关注的注意力机制。"),
    ("Reinforcement Learning", "强化学习", "通过奖励信号优化策略的学习范式。"),
    ("Supervised Fine-Tuning", "监督微调（SFT）", "用示范数据让模型学习期望响应格式和行为。"),
    ("Retrieval-Augmented Generation", "检索增强生成（RAG）", "先检索外部知识，再让模型基于上下文生成答案。"),
    ("Reward Model", "奖励模型", "把候选输出映射为偏好或质量分数的模型。"),
    ("Policy", "策略", "在状态下选择动作或生成 token 的概率分布。"),
    ("Trajectory", "轨迹", "智能体与环境交互形成的状态、动作、观察和奖励序列。"),
    ("Buffer", "缓冲区", "保存经验、轨迹或中间数据以供训练和分析的结构。"),
    ("Inference", "推理", "模型在部署或测试时生成输出的过程。"),
    ("Serving", "服务化", "把模型以稳定、可扩展、可观测的方式对外提供服务。"),
    ("PPO", "近端策略优化（PPO）", "通过裁剪目标限制策略更新幅度的强化学习算法。"),
    ("DPO", "直接偏好优化（DPO）", "从偏好对直接优化策略，不显式训练奖励模型的方法。"),
    ("GRPO", "组相对策略优化（GRPO）", "基于同一提示多条响应的组内相对优势进行优化的方法。"),
    ("RoPE", "旋转位置嵌入（RoPE）", "通过旋转变换注入相对位置信息的位置编码方法。"),
    ("vLLM", "vLLM", "使用 PagedAttention 等技术提升 LLM 服务效率的系统。"),
    ("FlashAttention", "FlashAttention", "面向 GPU 内存层次优化的精确注意力计算方法。"),
    ("MCP", "模型上下文协议（MCP）", "连接模型应用与工具/数据源的开放协议。"),
    ("A2A", "智能体间通信（A2A）", "面向智能体之间任务委托和协作的通信协议。"),
]


def ensure_clean_dirs() -> None:
    for path in [
        REPO / "chapters",
        REPO / "assets" / "css",
        REPO / "assets" / "js",
        REPO / "assets" / "data",
        REPO / "assets" / "images",
        REPO / "docs",
    ]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    for stale in [
        REPO / "assets" / "style.css",
        REPO / "assets" / "main.js",
    ]:
        if stale.exists():
            stale.unlink()


def copy_images() -> None:
    src = OLD_IMAGE_DIR if OLD_IMAGE_DIR.exists() else ALT_IMAGE_DIR
    dst = REPO / "assets" / "images" / "figures"
    dst.mkdir(parents=True, exist_ok=True)
    if src.exists():
        for file in src.glob("*"):
            if file.is_file():
                shutil.copy2(file, dst / file.name)
        if src == OLD_IMAGE_DIR and OLD_IMAGE_DIR.exists():
            shutil.rmtree(OLD_IMAGE_DIR)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def clean_page_content(page: int, content: str, base_prefix: str) -> str:
    content = normalize_terms(content)
    lines = []
    skip_next_caption = False
    in_fence = False
    for raw in content.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence:
            if stripped == "### 本页图像资源":
                continue
            if re.match(r"^\d+(?:\.\d+){0,4}$", stripped):
                continue
            if stripped in {"第一部分", "第二部分", "第三部分", "第四部分", "第五部分", "第六部分"}:
                continue
            if stripped in {"基础", "推理", "评估"}:
                continue
            if re.match(r"^第\d+章$", stripped):
                continue
            if "图像来源：原 PDF" in stripped:
                stripped = f"*图像：原 PDF p.{page}*"
                line = stripped
        line = re.sub(r"!\[([^\]]*)\]\((?:\.\./web/)?assets/figures/([^)]+)\)", rf"![\1]({base_prefix}assets/images/figures/\2)", line)
        line = re.sub(r"!\[([^\]]*)\]\(assets/figures/([^)]+)\)", rf"![\1]({base_prefix}assets/images/figures/\2)", line)
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    if cleaned:
        return f'<span class="page-ref" id="pdf-p{page:03d}">原 PDF p.{page}</span>\n\n{cleaned}\n'
    return f'<span class="page-ref" id="pdf-p{page:03d}">原 PDF p.{page}</span>\n'


def toc_items_for_page(chapter: Chapter, page: int) -> list[TocItem]:
    items = [item for item in chapter.toc_items if item.page == page and item.level == 3]
    seen = set()
    deduped = []
    for item in items:
        if item.title not in seen and item.title.lower() != "summary":
            deduped.append(item)
            seen.add(item.title)
    return deduped[:4]


def chapter_markdown(chapter: Chapter, pages: dict[int, str], base_prefix: str) -> str:
    parts = []
    inserted_titles: set[str] = set()
    if not any(item.level == 3 for item in chapter.toc_items):
        parts.append(f'<h2 id="{chapter.slug}-overview">本章概览</h2>')
        inserted_titles.add("本章概览")
    for page in range(chapter.start_page, chapter.end_page + 1):
        if page not in pages:
            continue
        for item in toc_items_for_page(chapter, page):
            if item.title in inserted_titles:
                continue
            level = "h2"
            anchor = f"{chapter.slug}-p{page:03d}-{len(inserted_titles) + 1}"
            parts.append(f'<{level} id="{anchor}">{html.escape(item.title)}</{level}>')
            inserted_titles.add(item.title)
        parts.append(clean_page_content(page, pages[page], base_prefix))
    body = "\n\n".join(parts)
    body = clean_markdown_text(body, TRANSLATION_CACHE, enable_online=True)
    return body


def markdown_to_article_html(md_text: str, base_prefix: str) -> tuple[str, list[dict[str, str]], str]:
    raw = markdown.markdown(md_text, extensions=["fenced_code", "tables", "attr_list", "sane_lists"])
    soup = BeautifulSoup(raw, "html.parser")

    for img in list(soup.find_all("img")):
        if not getattr(img, "attrs", None):
            continue
        src = img.get("src", "")
        src = src.replace("../web/assets/figures/", f"{base_prefix}assets/images/figures/")
        src = src.replace("assets/figures/", f"{base_prefix}assets/images/figures/")
        img["src"] = src
        img["loading"] = "lazy"
        img["decoding"] = "async"
        parent = img.parent
        if parent and parent.name == "p":
            figure = soup.new_tag("figure")
            parent.wrap(figure)
            parent.unwrap()
            next_node = figure.find_next_sibling()
            if next_node and next_node.name == "p" and next_node.find("em"):
                caption = soup.new_tag("figcaption")
                caption.string = next_node.get_text(" ", strip=True).strip("*")
                figure.append(caption)
                next_node.decompose()

    for table in soup.find_all("table"):
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll"})
        table.wrap(wrapper)

    for anchor in list(soup.find_all("a")):
        href = anchor.get("href", "")
        if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        allowed_prefixes = ("../", "./", "assets/", "chapters/", "docs/")
        allowed_files = (".html", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".json", ".css", ".js")
        if href.startswith(allowed_prefixes) or href.endswith(allowed_files):
            continue
        if " " in href or "=" in href or not re.search(r"[./#]", href):
            anchor.unwrap()

    outline = []
    used_ids = set()
    for idx, heading in enumerate(soup.find_all(["h2", "h3"])):
        text = heading.get_text(" ", strip=True)
        if re.fullmatch(r"第\s*\d+\s*页", text):
            heading.decompose()
            continue
        if not heading.get("id"):
            base = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text).strip("-").lower() or f"section-{idx}"
            anchor = base
            suffix = 2
            while anchor in used_ids:
                anchor = f"{base}-{suffix}"
                suffix += 1
            heading["id"] = anchor
        used_ids.add(heading["id"])
        if len(outline) < 18:
            outline.append({"id": heading["id"], "title": text, "level": heading.name})

    text = soup.get_text(" ", strip=True)
    return str(soup), outline, text


def nav_html(base_prefix: str, active: str = "") -> str:
    items = [
        ("首页", f"{base_prefix}index.html", "home"),
        ("章节", f"{base_prefix}chapters/index.html", "chapters"),
        ("术语表", f"{base_prefix}glossary.html", "glossary"),
        ("参考文献", f"{base_prefix}references.html", "references"),
        ("搜索", f"{base_prefix}search.html", "search"),
        ("原 PDF", PDF_URL, "pdf"),
    ]
    links = []
    for label, href, key in items:
        cls = "active" if key == active else ""
        target = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        links.append(f'<a class="{cls}" href="{href}"{target}>{label}</a>')
    return "\n".join(links)


def chapter_sidebar(chapters: list[Chapter], base_prefix: str, current_slug: str = "") -> str:
    links = []
    for chapter in chapters:
        href = f"{base_prefix}chapters/{chapter.slug}.html"
        cls = "active" if chapter.slug == current_slug else ""
        links.append(
            f'<a class="chapter-link {cls}" href="{href}">'
            f'<span class="chapter-num">{chapter.number:02d}</span>'
            f'<span>{html.escape(chapter.title)}</span>'
            f'</a>'
        )
    return "\n".join(links)


def page_shell(
    *,
    title: str,
    description: str,
    body: str,
    base_prefix: str = "",
    active: str = "",
    chapters: list[Chapter] | None = None,
    current_slug: str = "",
    outline: list[dict[str, str]] | None = None,
    article: bool = False,
    extra_head: str = "",
    extra_scripts: str = "",
) -> str:
    chapters = chapters or []
    outline = outline or []
    sidebar = chapter_sidebar(chapters, base_prefix, current_slug) if chapters else ""
    outline_links = "\n".join(
        f'<a class="outline-link level-{item["level"]}" href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a>'
        for item in outline
    )
    body_class = "article-page" if article else "site-page"
    sidebars = ""
    if article:
        sidebars = f"""
        <aside class="left-nav" id="left-nav">
          <div class="nav-section-title">章节</div>
          {sidebar}
        </aside>
        <aside class="right-outline" id="right-outline">
          <div class="nav-section-title">本页大纲</div>
          {outline_links or '<p class="muted small">本页无二级大纲。</p>'}
        </aside>
        """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)} | {SITE_TITLE}</title>
  <meta name="description" content="{html.escape(description)}" />
  <meta property="og:title" content="{html.escape(title)} | {SITE_TITLE}" />
  <meta property="og:description" content="{html.escape(description)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{ONLINE_URL}" />
  <link rel="canonical" href="{ONLINE_URL}" />
  <link rel="stylesheet" href="{base_prefix}assets/css/main.css" />
  <link rel="stylesheet" href="{base_prefix}assets/css/article.css" />
  <link rel="stylesheet" href="{base_prefix}assets/css/responsive.css" />
  {extra_head}
</head>
<body class="{body_class}">
  <div class="reading-progress" id="reading-progress"></div>
  <header class="topbar">
    <a class="brand" href="{base_prefix}index.html" aria-label="{SITE_TITLE}">
      <span class="brand-mark">AI</span>
      <span><strong>{SITE_TITLE}</strong><small>{SITE_SUBTITLE}</small></span>
    </a>
    <button class="nav-toggle" id="nav-toggle" type="button" aria-label="打开导航" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <nav class="topnav" id="topnav">{nav_html(base_prefix, active)}</nav>
  </header>
  <main class="layout">
    {sidebars}
    <section class="content-shell">
      {body}
    </section>
  </main>
  <button class="back-top" id="back-top" type="button">↑</button>
  <script src="{base_prefix}assets/js/main.js"></script>
  <script src="{base_prefix}assets/js/toc.js"></script>
  <script src="{base_prefix}assets/js/progress.js"></script>
  {extra_scripts}
</body>
</html>
"""


def build_home(chapters: list[Chapter]) -> None:
    cards = "\n".join(
        f"""
        <a class="chapter-card" href="chapters/{chapter.slug}.html">
          <span class="chapter-card-num">{chapter.number:02d}</span>
          <strong>{html.escape(chapter.title)}</strong>
          <p>{html.escape(chapter.description)}</p>
        </a>
        """
        for chapter in chapters[:12]
    )
    body = f"""
    <section class="home-hero">
      <div class="hero-copy">
        <p class="doc-kicker">中文技术文档站 · Agentic AI / LLM Systems</p>
        <h1>{SITE_TITLE}</h1>
        <p class="hero-lede">把原 PDF 长卷重构为可导航、可搜索、可分章阅读的中文技术文档。内容覆盖 Transformer、LLM 训练优化、强化学习、推理服务、智能体系统、MCP/A2A 与多智能体框架。</p>
        <div class="hero-actions">
          <a class="button primary" href="chapters/index.html">开始阅读</a>
          <a class="button" href="search.html">搜索全文</a>
          <a class="button ghost" href="{PDF_URL}" target="_blank" rel="noopener">原 PDF</a>
        </div>
      </div>
      <div class="hero-panel">
        <div class="search-card">
          <label for="home-search">站内搜索</label>
          <div class="search-inline">
            <input id="home-search" type="search" placeholder="搜索：GRPO、RoPE、奖励模型、MCP..." />
            <button id="home-search-btn" type="button">搜索</button>
          </div>
        </div>
        <div class="stat-grid">
          <div><strong>{len(chapters)}</strong><span>章节页</span></div>
          <div><strong>603</strong><span>PDF 页线索</span></div>
          <div><strong>72</strong><span>图像资源</span></div>
          <div><strong>{len(GLOSSARY)}</strong><span>核心术语</span></div>
        </div>
      </div>
    </section>
    <section class="home-section">
      <div class="section-head">
        <h2>章节入口</h2>
        <a href="chapters/index.html">查看全部章节</a>
      </div>
      <div class="chapter-grid">{cards}</div>
    </section>
    <section class="home-section two-col">
      <div>
        <h2>这版重构解决了什么</h2>
        <ul class="check-list">
          <li>目录改为基于章节结构，不再混入 PDF 页码和 OCR 目录点线。</li>
          <li>正文拆成多章节页面，页码只保留为小型来源锚点。</li>
          <li>补充术语表、搜索索引、参考文献页和质量报告页。</li>
          <li>长代码、公式、表格在桌面和移动端都不会撑破布局。</li>
        </ul>
      </div>
      <div class="note-panel">
        <h3>阅读建议</h3>
        <p>如果你关注工程实现，可以从系统基础、推理服务、智能体执行框架和 MCP/A2A 章节开始；如果你关注训练方法，可以先读 PPO、DPO、GRPO 与奖励模型训练。</p>
      </div>
    </section>
    """
    shell = page_shell(
        title=SITE_TITLE,
        description="《The Hitchhiker's Guide to Agentic AI: From Foundations to Systems》的中文技术文档站。",
        body=body,
        active="home",
        chapters=chapters,
        extra_scripts='<script>document.getElementById("home-search-btn")?.addEventListener("click",()=>{const q=document.getElementById("home-search").value.trim();location.href="search.html"+(q?"?q="+encodeURIComponent(q):"");});document.getElementById("home-search")?.addEventListener("keydown",(e)=>{if(e.key==="Enter")document.getElementById("home-search-btn").click();});</script>',
    )
    write_text(REPO / "index.html", shell)


def build_chapter_index(chapters: list[Chapter]) -> None:
    rows = "\n".join(
        f"""
        <a class="chapter-row" href="{chapter.slug}.html">
          <span>{chapter.number:02d}</span>
          <div><strong>{html.escape(chapter.title)}</strong><p>{html.escape(chapter.description)}</p></div>
          <em>p.{chapter.start_page}-{chapter.end_page}</em>
        </a>
        """
        for chapter in chapters
    )
    body = f"""
    <article class="directory-page">
      <h1>章节总览</h1>
      <p class="lead">按主题拆分后的中文技术文档版本。每个章节页包含左侧章节导航、右侧页内大纲、阅读进度和上一章/下一章入口。</p>
      <div class="chapter-list">{rows}</div>
    </article>
    """
    write_text(
        REPO / "chapters" / "index.html",
        page_shell(title="章节总览", description="智能体式 AI 中文技术文档站章节总览。", body=body, base_prefix="../", active="chapters", chapters=chapters),
    )


def prev_next(chapters: list[Chapter], idx: int, base_prefix: str = "../") -> str:
    prev_ch = chapters[idx - 1] if idx > 0 else None
    next_ch = chapters[idx + 1] if idx + 1 < len(chapters) else None
    prev_link = f'<a class="pager-link" href="{prev_ch.slug}.html">← {html.escape(prev_ch.title)}</a>' if prev_ch else '<span></span>'
    next_link = f'<a class="pager-link next" href="{next_ch.slug}.html">{html.escape(next_ch.title)} →</a>' if next_ch else '<span></span>'
    return f'<nav class="chapter-pager">{prev_link}{next_link}</nav>'


def build_chapters_pages(chapters: list[Chapter], pages: dict[int, str]) -> list[dict[str, str]]:
    search_docs: list[dict[str, str]] = []
    for idx, chapter in enumerate(chapters):
        md = chapter_markdown(chapter, pages, "../")
        article_html, outline, plain_text = markdown_to_article_html(md, "../")
        body = f"""
        <article class="article-card">
          <header class="article-header">
            <p class="part-label">{html.escape(chapter.part or "章节")}</p>
            <h1>{html.escape(chapter.title)}</h1>
            <p>{html.escape(chapter.description)}</p>
            <div class="article-meta"><span>原 PDF p.{chapter.start_page}-{chapter.end_page}</span><span>{len(outline)} 个页内条目</span></div>
          </header>
          <div class="article-body">{article_html}</div>
          {prev_next(chapters, idx)}
        </article>
        """
        write_text(
            REPO / "chapters" / f"{chapter.slug}.html",
            page_shell(
                title=chapter.title,
                description=chapter.description,
                body=body,
                base_prefix="../",
                active="chapters",
                chapters=chapters,
                current_slug=chapter.slug,
                outline=outline,
                article=True,
            ),
        )
        search_docs.append(
            {
                "title": chapter.title,
                "chapter": chapter.title,
                "url": f"chapters/{chapter.slug}.html",
                "summary": chapter.description,
                "text": re.sub(r"\s+", " ", plain_text)[:6000],
            }
        )
    return search_docs


def build_glossary() -> list[dict[str, str]]:
    rows = "\n".join(
        f"<tr><td><code>{html.escape(en)}</code></td><td><strong>{html.escape(zh)}</strong></td><td>{html.escape(note)}</td></tr>"
        for en, zh, note in GLOSSARY
    )
    body = f"""
    <article class="plain-card">
      <h1>术语表</h1>
      <p class="lead">统一本文档中高频出现的 Agentic AI、LLM、强化学习和系统工程术语。</p>
      <div class="table-scroll"><table><thead><tr><th>English</th><th>中文译名</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div>
    </article>
    """
    write_text(REPO / "glossary.html", page_shell(title="术语表", description="Agentic AI 与 LLM 技术术语中英文对照。", body=body, active="glossary"))
    data = [{"english": en, "chinese": zh, "note": note} for en, zh, note in GLOSSARY]
    write_text(REPO / "assets" / "data" / "glossary.json", json.dumps(data, ensure_ascii=False, indent=2))
    return [{"title": f"{zh} / {en}", "chapter": "术语表", "url": "glossary.html", "summary": note, "text": f"{en} {zh} {note}"} for en, zh, note in GLOSSARY]


def build_references(pages: dict[int, str]) -> dict[str, str]:
    md = "\n\n".join(clean_page_content(page, pages.get(page, ""), "") for page in range(579, 604) if page in pages)
    md = clean_markdown_text(md, TRANSLATION_CACHE, enable_online=False)
    article_html, outline, plain_text = markdown_to_article_html(md, "")
    body = f"""
    <article class="plain-card references-page">
      <h1>参考文献</h1>
      <p class="lead">参考文献标题、作者名、URL、DOI 和 arXiv 编号保留原文，以避免破坏引用准确性。</p>
      <div class="article-body">{article_html}</div>
    </article>
    """
    write_text(REPO / "references.html", page_shell(title="参考文献", description="原文档参考文献，保留英文标题和引用链接。", body=body, active="references"))
    return {"title": "参考文献", "chapter": "参考文献", "url": "references.html", "summary": "原文档参考文献。", "text": re.sub(r"\s+", " ", plain_text)[:9000]}


def build_search_page() -> None:
    body = """
    <article class="plain-card search-page">
      <h1>全文搜索</h1>
      <p class="lead">支持中文关键词、英文术语、章节标题和术语表搜索。搜索在浏览器本地完成，不依赖外部服务。</p>
      <div class="search-large">
        <input id="search-input" type="search" placeholder="输入关键词，例如：GRPO、奖励模型、RoPE、MCP、轨迹缓冲区" autofocus />
        <button id="search-button" type="button">搜索</button>
      </div>
      <div id="search-status" class="search-status"></div>
      <div id="search-results" class="search-results"></div>
    </article>
    """
    write_text(
        REPO / "search.html",
        page_shell(
            title="全文搜索",
            description="搜索智能体式 AI 中文技术文档站。",
            body=body,
            active="search",
            extra_scripts='<script src="assets/js/search.js"></script>',
        ),
    )


def build_quality_report_stub(chapters: list[Chapter]) -> None:
    body = f"""
    <article class="plain-card">
      <h1>V2 质量报告</h1>
      <p class="lead">本页面汇总 V2 重构的质量门禁结果。完整 Markdown 报告同步写入 <code>docs/v2_site_redesign_report.md</code> 与本地 report 目录。</p>
      <div class="status-grid">
        <div><strong>多页面结构</strong><span>首页、章节、术语表、参考文献、搜索页已生成</span></div>
        <div><strong>章节数量</strong><span>{len(chapters)} 个章节页</span></div>
        <div><strong>页码处理</strong><span>PDF 页码改为小型来源锚点</span></div>
        <div><strong>搜索索引</strong><span>本地 JSON 索引</span></div>
      </div>
      <p><a class="button primary" href="docs/v2_site_redesign_report.md">查看 Markdown 报告</a></p>
    </article>
    """
    write_text(REPO / "quality-report.html", page_shell(title="V2 质量报告", description="V2 文档站重构质量报告。", body=body, active="home"))
    write_text(REPO / "docs" / "v2_site_redesign_report.md", "# V2 Site Redesign Report\n\nReport will be refreshed after the final audit and deployment.\n")


def build_assets(chapters: list[Chapter], search_docs: list[dict[str, str]]) -> None:
    chapter_data = [
        {
            "number": chapter.number,
            "slug": chapter.slug,
            "title": chapter.title,
            "part": chapter.part,
            "startPage": chapter.start_page,
            "endPage": chapter.end_page,
            "description": chapter.description,
            "url": f"chapters/{chapter.slug}.html",
        }
        for chapter in chapters
    ]
    write_text(REPO / "assets" / "data" / "chapters.json", json.dumps(chapter_data, ensure_ascii=False, indent=2))
    write_text(REPO / "assets" / "data" / "search-index.json", json.dumps(search_docs, ensure_ascii=False, indent=2))

    write_text(REPO / "assets" / "css" / "main.css", MAIN_CSS)
    write_text(REPO / "assets" / "css" / "article.css", ARTICLE_CSS)
    write_text(REPO / "assets" / "css" / "responsive.css", RESPONSIVE_CSS)
    write_text(REPO / "assets" / "js" / "main.js", MAIN_JS)
    write_text(REPO / "assets" / "js" / "toc.js", TOC_JS)
    write_text(REPO / "assets" / "js" / "progress.js", PROGRESS_JS)
    write_text(REPO / "assets" / "js" / "search.js", SEARCH_JS)


def build_readme() -> None:
    write_text(REPO / "README.md", f"""# {SITE_TITLE}

V2 static documentation site for the Chinese translation of **The Hitchhiker's Guide to Agentic AI: From Foundations to Systems**.

- Online: {ONLINE_URL}
- Source PDF: {PDF_URL}
- Build: `python scripts/build_site.py`
- Audit: `python scripts/audit_site.py`
""")


def main() -> None:
    ensure_clean_dirs()
    copy_images()

    source_text = SOURCE_MD.read_text(encoding="utf-8")
    pages = parse_pages(source_text)
    toc_items = load_toc(TOC_JSON)
    chapters = build_chapters(toc_items, max(pages))

    build_home(chapters)
    build_chapter_index(chapters)
    search_docs = build_chapters_pages(chapters, pages)
    search_docs += build_glossary()
    search_docs.append(build_references(pages))
    build_search_page()
    build_quality_report_stub(chapters)
    build_assets(chapters, search_docs)
    build_readme()
    (REPO / ".nojekyll").touch()
    print(json.dumps({"status": "ok", "chapters": len(chapters), "search_docs": len(search_docs)}, ensure_ascii=False))


MAIN_CSS = r"""
:root {
  --bg: #f4f7f8;
  --surface: #ffffff;
  --surface-2: #f8fbfc;
  --ink: #172026;
  --muted: #63707c;
  --line: #dbe4e8;
  --accent: #087c89;
  --accent-2: #6653d9;
  --accent-soft: #e7f5f7;
  --violet-soft: #f0eefd;
  --code-bg: #f5f7fa;
  --shadow: 0 18px 50px rgba(31, 48, 56, .08);
  --radius: 8px;
  --content: 860px;
  color-scheme: light;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background:
    linear-gradient(180deg, rgba(8,124,137,.05), transparent 360px),
    var(--bg);
  font-family: "Inter", "Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.72;
  letter-spacing: 0;
}
a { color: var(--accent); text-decoration-thickness: .08em; text-underline-offset: .22em; }
.reading-progress {
  position: fixed;
  z-index: 80;
  top: 0;
  left: 0;
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 70;
  height: 68px;
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(219, 228, 232, .92);
  background: rgba(244, 247, 248, .9);
  backdrop-filter: blur(16px);
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 270px;
  color: var(--ink);
  text-decoration: none;
}
.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(8,124,137,.28);
  background: linear-gradient(135deg, #e9f8fa, #f2efff);
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
}
.brand strong { display: block; font-size: 15px; line-height: 1.1; }
.brand small { display: block; margin-top: 3px; color: var(--muted); font-size: 11px; }
.topnav { display: flex; align-items: center; gap: 6px; margin-left: auto; }
.topnav a {
  padding: 8px 10px;
  color: #31404a;
  border-radius: 6px;
  font-size: 14px;
  text-decoration: none;
}
.topnav a:hover,
.topnav a.active { color: var(--accent); background: var(--accent-soft); }
.nav-toggle {
  display: none;
  width: 38px;
  height: 38px;
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 6px;
}
.nav-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  margin: 4px auto;
  background: var(--ink);
}
.layout { min-height: calc(100vh - 68px); }
.content-shell { width: min(100%, 1180px); margin: 0 auto; padding: 34px 24px 80px; }
.home-hero {
  min-height: calc(100vh - 132px);
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr);
  gap: 42px;
  align-items: center;
}
.doc-kicker {
  margin: 0 0 18px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
}
.home-hero h1 {
  margin: 0;
  max-width: 780px;
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: clamp(42px, 7vw, 76px);
  line-height: 1.04;
  letter-spacing: 0;
}
.hero-lede {
  max-width: 780px;
  margin: 24px 0 0;
  color: #40505d;
  font-size: 18px;
}
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
.button,
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 9px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 14px;
  text-decoration: none;
  cursor: pointer;
}
.button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.button.ghost { background: transparent; }
.hero-panel,
.plain-card,
.article-card,
.directory-page {
  background: rgba(255,255,255,.94);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.hero-panel { padding: 24px; }
.search-card label,
.nav-section-title {
  display: block;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}
.search-inline,
.search-large {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
input[type="search"] {
  width: 100%;
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  font: inherit;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 22px;
}
.stat-grid div,
.status-grid div,
.note-panel {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-2);
}
.stat-grid strong,
.status-grid strong { display: block; color: var(--accent-2); font-size: 26px; line-height: 1; }
.stat-grid span,
.status-grid span { color: var(--muted); font-size: 13px; }
.home-section { margin-top: 44px; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.section-head h2,
.plain-card h1,
.directory-page h1 {
  margin: 0;
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  line-height: 1.18;
}
.chapter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.chapter-card,
.chapter-row {
  display: block;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
}
.chapter-card:hover,
.chapter-row:hover { border-color: rgba(8,124,137,.45); box-shadow: 0 10px 28px rgba(31,48,56,.07); }
.chapter-card-num {
  display: inline-flex;
  margin-bottom: 14px;
  color: var(--accent);
  font-weight: 800;
  font-size: 13px;
}
.chapter-card strong { display: block; line-height: 1.35; }
.chapter-card p,
.chapter-row p { margin: 8px 0 0; color: var(--muted); font-size: 14px; }
.two-col { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 24px; align-items: start; }
.check-list { padding-left: 20px; }
.plain-card,
.directory-page { max-width: 980px; margin: 0 auto; padding: clamp(24px, 5vw, 48px); }
.lead { color: #465865; font-size: 17px; }
.chapter-list { display: grid; gap: 10px; margin-top: 24px; }
.chapter-row {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
}
.chapter-row > span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 800;
}
.chapter-row em { color: var(--muted); font-size: 12px; font-style: normal; }
.table-scroll { max-width: 100%; overflow: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 10px 12px; border: 1px solid var(--line); vertical-align: top; }
th { background: var(--surface-2); text-align: left; }
.status-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; margin: 24px 0; }
.muted { color: var(--muted); }
.small { font-size: 13px; }
.back-top {
  position: fixed;
  right: 22px;
  bottom: 22px;
  width: 42px;
  height: 42px;
  padding: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity .18s ease;
}
.back-top.visible { opacity: 1; pointer-events: auto; }
"""


ARTICLE_CSS = r"""
.article-page .layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 240px;
  gap: 0;
}
.left-nav,
.right-outline {
  position: sticky;
  top: 68px;
  height: calc(100vh - 68px);
  overflow: auto;
  padding: 22px 16px;
  border-color: var(--line);
  background: rgba(248,251,252,.72);
}
.left-nav { border-right: 1px solid var(--line); }
.right-outline { border-left: 1px solid var(--line); }
.chapter-link,
.outline-link {
  display: flex;
  gap: 10px;
  align-items: baseline;
  padding: 7px 8px;
  border-left: 2px solid transparent;
  color: #3b4a55;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.35;
}
.chapter-link { margin-top: 3px; }
.chapter-link.active,
.chapter-link:hover,
.outline-link.active,
.outline-link:hover {
  color: var(--accent);
  border-left-color: var(--accent);
  background: var(--accent-soft);
}
.chapter-num {
  min-width: 25px;
  color: var(--muted);
  font-weight: 800;
  font-size: 11px;
}
.outline-link.level-h3 { padding-left: 18px; font-size: 12px; }
.article-card { max-width: var(--content); margin: 0 auto; overflow: hidden; }
.article-header {
  padding: clamp(28px, 6vw, 56px) clamp(24px, 6vw, 64px) 30px;
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(135deg, rgba(8,124,137,.08), transparent 44%),
    linear-gradient(0deg, #fff, #f9fcfd);
}
.part-label {
  margin: 0 0 12px;
  color: var(--accent);
  font-weight: 800;
  font-size: 13px;
}
.article-header h1 {
  margin: 0;
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: clamp(30px, 5vw, 48px);
  line-height: 1.14;
  letter-spacing: 0;
}
.article-header p:not(.part-label) {
  max-width: 720px;
  color: #4b5b66;
  font-size: 16px;
}
.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.article-meta span,
.page-ref {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  background: #fff;
  font-size: 12px;
}
.article-body { padding: 28px clamp(24px, 6vw, 64px) 44px; }
.article-body h2,
.article-body h3,
.article-body h4 {
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  line-height: 1.28;
  scroll-margin-top: 90px;
}
.article-body h2 {
  margin: 42px 0 14px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  color: #102b32;
  font-size: 25px;
}
.article-body h3 { margin: 30px 0 10px; color: #203944; font-size: 20px; }
.article-body h4 { margin: 24px 0 8px; font-size: 17px; }
.article-body p,
.article-body li { font-size: 16px; }
.article-body p { margin: 13px 0; }
.article-body ul,
.article-body ol { padding-left: 1.35rem; }
.article-body blockquote {
  margin: 22px 0;
  padding: 14px 18px;
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  color: #243a40;
}
.article-body pre {
  max-width: 100%;
  overflow: auto;
  padding: 14px 16px;
  border: 1px solid #dfe6eb;
  border-radius: 6px;
  background: var(--code-bg);
  color: #1c2b33;
  line-height: 1.58;
  font-size: 12px;
}
.article-body code {
  font-family: "Cascadia Mono", Consolas, "SFMono-Regular", monospace;
  overflow-wrap: anywhere;
}
.article-body :not(pre) > code {
  padding: 2px 5px;
  border: 1px solid #dfe6eb;
  border-radius: 4px;
  background: var(--code-bg);
  font-size: .88em;
}
.article-body pre code { display: block; min-width: 0; }
.article-body img {
  display: block;
  max-width: min(100%, 760px);
  height: auto;
  margin: 0 auto;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
}
.article-body figure {
  margin: 28px 0;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
}
.article-body figcaption {
  margin-top: 10px;
  color: var(--muted);
  text-align: center;
  font-size: 13px;
}
.article-body .page-ref {
  margin: 22px 0 4px;
  scroll-margin-top: 90px;
}
.chapter-pager {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 24px clamp(24px, 6vw, 64px) 34px;
  border-top: 1px solid var(--line);
}
.pager-link {
  min-height: 58px;
  display: flex;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-2);
  color: var(--ink);
  text-decoration: none;
}
.pager-link.next { justify-content: flex-end; text-align: right; }
.references-page .article-body p { padding-left: 1.4rem; text-indent: -1.4rem; }
.search-results { display: grid; gap: 12px; margin-top: 22px; }
.search-result {
  display: block;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface-2);
  color: var(--ink);
  text-decoration: none;
}
.search-result strong { display: block; }
.search-result span { display: block; margin-top: 4px; color: var(--muted); font-size: 13px; }
.search-result p { margin: 8px 0 0; color: #40505d; }
.search-status { margin-top: 14px; color: var(--muted); }
"""


RESPONSIVE_CSS = r"""
@media (max-width: 1180px) {
  .article-page .layout { grid-template-columns: 260px minmax(0, 1fr); }
  .right-outline { display: none; }
  .chapter-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 860px) {
  .topbar { height: auto; min-height: 64px; padding: 10px 14px; flex-wrap: wrap; }
  .brand { min-width: 0; flex: 1; }
  .brand small { display: none; }
  .nav-toggle { display: block; }
  .topnav {
    display: none;
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    margin: 0;
    padding: 8px 0 2px;
  }
  .topnav.open { display: flex; }
  .topnav a { padding: 10px 12px; }
  .home-hero { min-height: auto; grid-template-columns: 1fr; padding-top: 18px; }
  .hero-panel { order: -1; }
  .home-hero h1 { font-size: clamp(34px, 12vw, 50px); }
  .hero-lede { font-size: 16px; }
  .content-shell { padding: 20px 12px 64px; }
  .chapter-grid { grid-template-columns: 1fr; }
  .two-col { grid-template-columns: 1fr; }
  .chapter-row { grid-template-columns: 40px minmax(0, 1fr); }
  .chapter-row em { grid-column: 2; }
  .article-page .layout { display: block; }
  .left-nav {
    position: fixed;
    z-index: 65;
    top: 64px;
    left: 0;
    width: min(86vw, 340px);
    height: calc(100vh - 64px);
    transform: translateX(-105%);
    transition: transform .2s ease;
    box-shadow: 18px 0 44px rgba(31,48,56,.16);
  }
  .left-nav.open { transform: translateX(0); }
  .article-card { border-left: 0; border-right: 0; }
  .article-body,
  .article-header,
  .chapter-pager { padding-left: 20px; padding-right: 20px; }
  .article-body,
  .article-body p,
  .article-body li,
  .article-body a,
  .article-body blockquote {
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .article-body pre code {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .chapter-pager { grid-template-columns: 1fr; }
  .search-inline,
  .search-large { flex-direction: column; }
  .stat-grid,
  .status-grid { grid-template-columns: 1fr; }
}
@media print {
  .topbar, .left-nav, .right-outline, .reading-progress, .back-top, .chapter-pager { display: none !important; }
  .layout, .article-page .layout { display: block; }
  .content-shell { padding: 0; }
  .article-card, .plain-card { box-shadow: none; border: 0; }
}
"""


MAIN_JS = r"""
(() => {
  const navToggle = document.getElementById('nav-toggle');
  const topnav = document.getElementById('topnav');
  const leftNav = document.getElementById('left-nav');
  const backTop = document.getElementById('back-top');

  navToggle?.addEventListener('click', () => {
    const topOpen = topnav?.classList.toggle('open');
    if (leftNav && document.body.classList.contains('article-page')) {
      leftNav.classList.toggle('open');
    }
    navToggle.setAttribute('aria-expanded', String(Boolean(topOpen || leftNav?.classList.contains('open'))));
  });

  leftNav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      leftNav.classList.remove('open');
      navToggle?.setAttribute('aria-expanded', 'false');
    });
  });

  backTop?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
})();
"""


TOC_JS = r"""
(() => {
  const links = Array.from(document.querySelectorAll('.outline-link'));
  if (!links.length) return;
  const byId = new Map(links.map((link) => [decodeURIComponent(link.getAttribute('href').slice(1)), link]));
  const headings = Array.from(document.querySelectorAll('.article-body h2[id], .article-body h3[id]'));
  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!visible) return;
    links.forEach((link) => link.classList.remove('active'));
    byId.get(visible.target.id)?.classList.add('active');
  }, { rootMargin: '-18% 0px -72% 0px', threshold: 0.01 });
  headings.forEach((heading) => observer.observe(heading));
})();
"""


PROGRESS_JS = r"""
(() => {
  const progress = document.getElementById('reading-progress');
  const backTop = document.getElementById('back-top');
  function updateProgress() {
    if (!progress) return;
    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    progress.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    backTop?.classList.toggle('visible', window.scrollY > 700);
  }
  window.addEventListener('scroll', updateProgress, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();
})();
"""


SEARCH_JS = r"""
(() => {
  const input = document.getElementById('search-input');
  const button = document.getElementById('search-button');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  let index = [];

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  }

  function snippet(text, query) {
    const clean = String(text || '').replace(/\s+/g, ' ');
    const pos = clean.toLowerCase().indexOf(query.toLowerCase());
    const start = Math.max(0, pos - 64);
    return clean.slice(start, start + 170) + (clean.length > start + 170 ? '...' : '');
  }

  function runSearch() {
    const q = input.value.trim();
    results.innerHTML = '';
    if (!q) {
      status.textContent = '请输入关键词。';
      return;
    }
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const found = index
      .map((item) => {
        const hay = `${item.title} ${item.chapter} ${item.summary} ${item.text}`.toLowerCase();
        const score = terms.reduce((sum, term) => sum + (hay.includes(term) ? 1 : 0), 0);
        return { item, score };
      })
      .filter((row) => row.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 30);
    status.textContent = `找到 ${found.length} 条结果。`;
    results.innerHTML = found.map(({ item }) => `
      <a class="search-result" href="${item.url}">
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.chapter)}</span>
        <p>${escapeHtml(snippet(`${item.summary} ${item.text}`, q))}</p>
      </a>
    `).join('');
  }

  fetch('assets/data/search-index.json')
    .then((res) => res.json())
    .then((data) => {
      index = data;
      const params = new URLSearchParams(location.search);
      const q = params.get('q');
      if (q) {
        input.value = q;
        runSearch();
      } else {
        status.textContent = `索引已加载，共 ${index.length} 条。`;
      }
    })
    .catch(() => {
      status.textContent = '搜索索引加载失败。';
    });

  button?.addEventListener('click', runSearch);
  input?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') runSearch();
  });
})();
"""


if __name__ == "__main__":
    main()
