# V3 Architecture

## Why V3

V1/V2 的页面仍然带有 PDF 长卷和 OCR/Markdown 直渲染的痕迹：目录容易混入页码、Markdown heading 不能稳定表达真实章节结构，OCR 文本也可能把公式、图注、页码和正文混在一起。V3 的目标是把站点升级成结构化知识文档系统，而不是 PDF 转 HTML 的长页。

V3 因此引入 clean content AST：先把文档内容清洗、拆分、归一化，再由结构化数据生成页面、目录、搜索与组件。

## Canonical Content AST

`assets/data/clean_chapter_tree.json` 是 V3 的 canonical content AST。它保存：

- 文档级 metadata
- 章节列表
- 语义聚类
- 小节结构
- 段落、代码、图片、公式等 block 节点
- 每个章节、小节、block 的 source page metadata
- 每章和每节的 key concepts

网页不再直接渲染原始 OCR 文本或 Markdown heading，而是从这个 clean AST 生成。

## Build Scripts

`scripts/build_site.py` 是稳定入口，当前会调用 V3 构建器。它负责：

- 读取已清洗的译文和 PDF bookmark/TOC 线索
- 构建 `clean_chapter_tree.json`
- 生成首页、章节页、术语表、参考文献、搜索页和质量报告页
- 生成 CSS、JS、搜索索引和 glossary data

`scripts/audit_site.py` 是质量门禁。它负责检查：

- 必需页面和静态资源是否存在
- 是否仍有 legacy `chapters.json`
- 页码是否进入 DOM
- 是否存在明显英文 heading 或大段英文正文
- 是否存在 OCR 乱码
- 内部链接是否有效
- clean AST schema 是否正确
- 公式 fallback 是否存在
- 搜索索引、移动端 CSS、Key Concepts 和 Section Overview 是否生成

## TOC Generation

V3 的 TOC 不使用 Markdown headings 作为真源。章节结构优先来自 PDF bookmark/TOC 线索，再经过语义聚类和标题清洗，生成适合网站阅读的目录。

左侧目录显示主章节与语义分组。右侧大纲来自当前章节 AST sections，只显示本页关键小节。

## Search Generation

搜索索引 `assets/data/search-index.json` 由 clean AST 生成。索引内容包括：

- 章节标题
- 小节标题
- 小节摘要
- 正文 block 文本
- key concepts

这样搜索不会索引未清洗 OCR 噪声，也不会把 PDF 页码当作正文结果。

## Chapter Pages

章节页从 AST components 生成：

- `article-header`
- `key-concepts-panel`
- `section-overview`
- paragraph/code/formula/image blocks
- previous/next chapter navigation
- left semantic nav
- right page outline

这让页面更像技术文档站，而不是 PDF 长卷。

## Page Numbers As Metadata

PDF 页码用于溯源，但不属于正文语义。V3 将页码保存在 `metadata.source_pages` 或 `metadata.source_page` 中，不渲染为 DOM 节点。

这样可以避免出现巨大“第 X 页”标题，也不会让搜索、目录和阅读流被页码污染。

## Term Normalization And English Residual Rules

V3 使用三层英文处理：

1. 锁定术语：保留 LLM、AI、BPE、RoPE、MCP、A2A、RAG、SFT、RL、GPU、API 等技术缩写和专名。
2. 标题与短语翻译：对章节标题、小节标题和常见英文短语做中文化映射。
3. 段落与代码分离：解释性英文段落翻译为中文；代码、伪代码、API 名称和参考文献标题保留合理英文。

`audit_site.py` 会拦截明显英文 heading、大段英文正文和乱码字符。

## Formula Fallback

OCR 对数学公式尤其不稳定。V3 对公式节点做 fallback：

- 可恢复的公式以 LaTeX / readable text 表示
- RoPE 等关键公式使用修复后的 LaTeX
- 无法可靠恢复的公式区域使用图像 fallback

正文中不保留大面积乱码或无法阅读的符号串。

## Toward A General PDF-to-Knowledge-Site Engine

后续可以把本项目抽象为通用引擎：

- 把 PDF extraction/OCR、translation、AST build、site render 拆成独立 pipeline
- 为不同文档类型配置不同 semantic schema
- 抽象 TOC clustering、term locking、formula fallback 和 search indexing
- 支持多语言输出和多主题模板
- 将 `clean_chapter_tree.json` 作为跨站点、跨渲染器的稳定中间格式
