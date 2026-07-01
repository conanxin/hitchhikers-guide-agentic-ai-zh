# Hitchhiker's Guide to Agentic AI 中文站

这是 *The Hitchhiker's Guide to Agentic AI* 的中文在线阅读项目，包含结构化文档站和中文重编教材版。

## Online

- 根路径文档站: https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/
- 中文教材版: https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/v4/
- 原始 arXiv PDF: https://arxiv.org/pdf/2606.24937v1

## Versions

- V3: 结构化中文文档站，位于根路径。
- V4.1: 中文重编教材版，位于 `/v4/`。

## V4.1 Chinese Learning Edition

V4.1 面向学习者重新组织 Agentic AI 知识，覆盖 LLM 基础、GPU 与服务化系统、强化学习、SFT/RLHF、PPO、DPO、GRPO、奖励模型、智能体训练、RAG、记忆、工具使用、评估、安全与部署。

页面目标是正式教材阅读体验：章节导读、学习目标、核心概念、正文讲解、表格、公式解释、小结、思考题、延伸阅读和全文搜索。

## Local Server

```bash
cd D:/WSL/Codex/pdf_zh_web_output/github_pages_repo
python -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080/
http://127.0.0.1:8080/v4/
```

## Build And Audit

```bash
python scripts/build_v4_expanded.py
python scripts/audit_v4_expanded.py
```

## Main Paths

- V4 site: `v4/`
- V4 source build output: `site-v4/`
- V4 builder: `scripts/build_v4_expanded.py`
- V4 audit: `scripts/audit_v4_expanded.py`
- V3 builder: `scripts/build_site_v3.py`
- V3 audit: `scripts/audit_site.py`
