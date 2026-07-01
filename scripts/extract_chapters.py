from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from fix_content import clean_toc_title


PAGE_RE = re.compile(r'<a id="page-(\d{3})"></a>\s*\n\s*##\s+第\s+\d+\s+页\s*\n?', re.M)


@dataclass
class TocItem:
    level: int
    title: str
    page: int
    raw_title: str


@dataclass
class Chapter:
    number: int
    slug: str
    title: str
    part: str
    start_page: int
    end_page: int
    source_level: int = 2
    description: str = ""
    toc_items: list[TocItem] = field(default_factory=list)


def parse_pages(markdown_text: str) -> dict[int, str]:
    matches = list(PAGE_RE.finditer(markdown_text))
    pages: dict[int, str] = {}
    for idx, match in enumerate(matches):
        page = int(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        pages[page] = markdown_text[start:end].strip()
    return pages


def load_toc(toc_path: Path) -> list[TocItem]:
    raw = json.loads(toc_path.read_text(encoding="utf-8"))
    items: list[TocItem] = []
    for level, title, page in raw:
        items.append(TocItem(level=int(level), title=clean_toc_title(str(title)), page=int(page), raw_title=str(title)))
    return items


def chapter_summary(title: str) -> str:
    summaries = {
        "导读与前置说明": "阅读前的许可、作者背景、前言和全书导读。",
        "LLM 架构和优化方法": "从分词、Transformer、自注意力到训练优化和模型压缩的基础层。",
        "LLM 的系统基础": "从 GPU、并行训练、推理服务到大规模基础设施的系统视角。",
        "强化学习简介": "用 MDP、价值函数、策略梯度和信用分配建立强化学习基础。",
        "语言模型的强化学习基础": "把强化学习问题映射到语言模型的序列生成与偏好优化。",
        "PPO：近端策略优化": "PPO 的目标函数、优势估计、KL 控制和生产训练实践。",
        "DPO：直接偏好优化": "不用显式奖励模型的偏好优化方法及其理论直觉。",
        "GRPO：组相对策略优化": "面向推理模型的组相对优化、可验证奖励和采样策略。",
        "偏好优化变体": "IPO、KTO、ORPO、SimPO 等对齐方法的比较。",
        "奖励模型训练": "奖励模型、排序损失、标注质量和奖励黑客防护。",
        "SFT 最佳实践与技术": "监督微调的数据、模板、训练配方和调试要点。",
        "大规模系统架构与基础设施": "分布式训练、容错、监控、调度和大规模训练平台。",
        "LLM 智能体训练": "从轨迹缓冲区、环境奖励到智能体强化学习训练流水线。",
        "大型推理模型的强化学习": "思维链、可验证奖励、测试时扩展和推理专用 RL。",
        "LLM 评估": "从基准、LLM-as-judge 到污染检测和校准的评估体系。",
        "智能体式 AI 简介": "从聊天机器人到自主智能体的动机、架构和运行范式。",
        "检索增强生成（RAG）": "RAG 管线、索引、重排、评估和智能体式 RAG。",
        "智能体记忆系统": "短期/长期记忆、情景记忆、语义记忆和记忆训练。",
        "智能体执行框架：上下文管理与编排": "智能体运行时、上下文窗口、工具调用和编排层。",
        "智能体设计模式": "反思、规划、工具使用、多步骤执行和人类确认等模式。",
        "智能体环境与基准": "用于训练和评估智能体的环境、任务和基准。",
        "模型上下文协议（MCP）": "MCP 的协议结构、客户端/服务器模型和工具生态。",
        "智能体技能": "技能库、可复用能力、学习与组合。",
        "智能体间通信（A2A）": "A2A 协议、消息结构、协作和安全边界。",
        "多智能体系统": "多智能体协作、通信、协调、集中训练与分散执行。",
        "智能体开发框架": "LangGraph、AutoGen、CrewAI 等框架的比较和工程实践。",
        "智能体式 UI 框架": "面向智能体应用的界面模式、可解释执行和审批流。",
        "测验题与详解": "覆盖全书核心概念的复习题和答案。",
        "速查表": "公式、超参数、协议、故障模式和方法选择的快速索引。",
        "结论与未来方向": "总结技术路线，并展望智能体式 AI 的开放问题。",
    }
    return summaries.get(title, "本章整理该主题的关键概念、方法、系统实践和工程注意事项。")


def build_chapters(toc_items: list[TocItem], max_page: int) -> list[Chapter]:
    chapters: list[Chapter] = [
        Chapter(
            number=1,
            slug="chapter-01",
            title="导读与前置说明",
            part="前置",
            start_page=24,
            end_page=33,
            source_level=1,
            description=chapter_summary("导读与前置说明"),
            toc_items=[item for item in toc_items if 24 <= item.page <= 33 and item.level <= 2],
        )
    ]
    level2 = [item for item in toc_items if item.level == 2 and item.page < 579]
    parts = [item for item in toc_items if item.level == 1]
    for idx, item in enumerate(level2, start=2):
        next_page = level2[idx - 1].page if idx - 1 < len(level2) else 579
        end_page = min(next_page - 1, 578, max_page)
        part = ""
        for p in parts:
            if p.page <= item.page:
                part = p.title
        chapter_items = [
            sub for sub in toc_items
            if item.page <= sub.page <= end_page and sub.level >= 3
        ]
        chapters.append(
            Chapter(
                number=idx,
                slug=f"chapter-{idx:02d}",
                title=item.title,
                part=part,
                start_page=item.page,
                end_page=end_page,
                description=chapter_summary(item.title),
                toc_items=chapter_items,
            )
        )
    return chapters

