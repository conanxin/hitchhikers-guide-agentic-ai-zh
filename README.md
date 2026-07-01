# Hitchhiker's Guide to Agentic AI 中文技术文档站

这是 *The Hitchhiker's Guide to Agentic AI* 的中文技术文档站封版仓库。V3 版本已经从早期的 PDF 长页阅读器升级为结构化、多页面、可搜索的中文知识文档系统。

## Online

- 在线访问: https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/
- 原始 PDF / arXiv: https://arxiv.org/pdf/2606.24937v1
- 发布方式: GitHub Pages + GitHub Actions

## Versions

- V3 stable documentation site: root path `/`
- V4 Chinese learning edition preview: `/v4/`

## V3 Architecture

V3 的核心是 `assets/data/clean_chapter_tree.json`。它是 canonical content AST，也就是站点唯一可信的结构化内容源。

站点从该 AST 生成：

- 多页面章节站点: `chapters/chapter-01.html` 到 `chapters/chapter-30.html`
- 语义目录: 按主题聚类与章节结构生成，不依赖原 Markdown heading
- 术语表: `glossary.html` 与 `assets/data/glossary.json`
- 搜索: `search.html` 与 `assets/data/search-index.json`
- Key Concepts: 每章自动抽取核心概念
- Section Overview: 每个重要小节都有概览卡片
- 公式 fallback: OCR 不可靠的公式以 LaTeX 或图像 fallback 保留
- 页码 metadata: PDF 页码仅存放在 AST metadata 中，不进入正文 DOM

## Local Preview

```bash
cd D:/WSL/Codex/pdf_zh_web_output/github_pages_repo
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/
```

## Build And Audit

```bash
python scripts/build_site.py
python scripts/audit_site.py
```

`scripts/build_site.py` 会从清洗后的结构源重新生成静态站点。`scripts/audit_site.py` 会检查页面、链接、乱码、页码 DOM、英文残留、公式 fallback、搜索索引和移动端 CSS 等关键质量门禁。

## Documentation

- V3 architecture: `docs/v3_architecture.md`
- V3 final release: `docs/final_release_v3.md`
- V3 rebuild report: `docs/v3_site_rebuild_report.md`
