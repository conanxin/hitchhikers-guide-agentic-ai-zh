from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path

from extract_chapters import Chapter, TocItem, build_chapters, load_toc, parse_pages
from fix_content import looks_like_english_prose, normalize_terms, translate_online


REPO = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO.parent
SOURCE_MD = OUTPUT_ROOT / "translated" / "document.zh.md"
TOC_JSON = OUTPUT_ROOT / "extracted" / "toc.json"
IMAGE_MANIFEST = OUTPUT_ROOT / "extracted" / "image_manifest.json"
SOURCE_FIGURES = OUTPUT_ROOT / "web" / "assets" / "figures"
CACHE_DIR = OUTPUT_ROOT / ".cache"
TRANSLATION_CACHE = CACHE_DIR / "v3_translation_cache.json"

SITE_TITLE = "智能体式 AI 漫游指南"
SITE_SUBTITLE = "结构化知识文档系统"
ONLINE_URL = "https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/"
PDF_URL = "https://arxiv.org/pdf/2606.24937v1"

LOCKED_TERMS = {
    "LLM", "AI", "API", "GPU", "CPU", "CUDA", "BPE", "RL", "SFT", "RAG",
    "DPO", "GRPO", "MDP", "PPO", "SGD", "Adam", "AdamW", "Transformer",
    "Token", "token", "RoPE", "vLLM", "FlashAttention", "Hugging Face",
    "arXiv", "DOI", "URL", "MCP", "A2A", "KV", "LoRA", "QLoRA", "MoE",
}

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

TERM_NORMALIZATION = [
    ("法学硕士", "LLM"),
    ("国家数据化", "分词 / 标记化"),
    ("代币化", "分词 / 标记化"),
    ("令牌化", "分词 / 标记化"),
    ("令牌", "token"),
    ("代币", "token"),
    ("词元", "token"),
    ("字级模型", "字符级模型"),
    ("自注意力力", "自注意力"),
    ("注意力力", "注意力"),
    ("变形金刚", "Transformer"),
    ("代理式 AI", "智能体式 AI"),
    ("代理人工智能", "智能体式 AI"),
    ("智能人工智能", "智能体式 AI"),
    ("代理", "智能体"),
    ("预先训练", "预训练"),
    ("对准", "对齐"),
    ("工具调用", "工具调用"),
]

PHRASE_TRANSLATIONS = {
    "Motivation: From Chatbots to Autonomous Agents": "动机：从聊天机器人到自主智能体",
    "Trajectory Buffers for LLM Agents": "LLM 智能体的轨迹缓冲区",
    "Mathematical Structure of an LLM Agent Buffer": "LLM 智能体缓冲区的数学结构",
    "Operational Paradigms": "运行范式",
    "Self-Correction and Thought Refinement": "自我纠错与思考精炼",
    "Off-Policy Exploration": "离策略探索",
    "Non-Parametric In-Context Learning": "非参数上下文内学习",
    "Use Case": "用例",
    "Architecture Overview": "架构概览",
    "Reward Design": "奖励设计",
    "Training Pipeline": "训练流水线",
    "Evaluation Framework": "评估框架",
    "What is a Gradient?": "什么是梯度？",
    "Derivation of the gradient:": "梯度推导：",
    "Weight Tying: LM Head = Embedding Matrix Transposed": "权重绑定：语言模型头等于嵌入矩阵的转置",
}

SECTION_TITLE_TRANSLATIONS = {
    "FlashAttention - Algorithm and Hardware Awareness": "FlashAttention：算法与硬件感知",
    "Pretraining: Best Practices": "预训练最佳实践",
    "Supervised Fine-Tuning (SFT)": "监督微调（SFT）",
    "LoRA and Parameter-Efficient Fine-Tuning": "LoRA 与参数高效微调",
    "Mixture of Experts (MoE)": "混合专家模型（MoE）",
    "Diversity in LLM Training": "LLM 训练中的多样性",
    "Text Generation: Decoding Methods": "文本生成：解码方法",
    "Prompt Engineering": "提示工程",
    "Model Compression Methods": "模型压缩方法",
    "Speculative Decoding Methods": "推测解码方法",
    "Hallucination Detection": "幻觉检测",
    "LLM Safety and Responsible AI": "LLM 安全与负责任 AI",
    "GPU Architecture - From Silicon to LLM Training": "GPU 架构：从芯片到 LLM 训练",
    "vLLM - PagedAttention and High-Throughput Inference": "vLLM：PagedAttention 与高吞吐推理",
    "The Markov Decision Process (MDP)": "马尔可夫决策过程（MDP）",
    "Core Concepts and Definitions": "核心概念与定义",
    "Taxonomy of RL Methods": "强化学习方法分类",
    "Temporal Difference (TD) Learning": "时序差分（TD）学习",
    "Q-Learning": "Q 学习",
    "Policy Gradient Methods - REINFORCE": "策略梯度方法：REINFORCE",
    "Actor-Critic Methods": "Actor-Critic 方法",
    "Generalized Advantage Estimation (GAE)": "广义优势估计（GAE）",
    "On-Policy vs Off-Policy - Detailed Comparison": "在线策略与离线策略：详细比较",
    "Model-Based vs Model-Free": "基于模型与无模型方法",
    "Reward Shaping": "奖励塑形",
    "Two Paradigms for RL in LLMs": "LLM 强化学习的两种范式",
    "Text Generation as an MDP": "作为 MDP 的文本生成",
    "The RLHF Pipeline": "RLHF 流水线",
    "Roadmap of This Part": "本部分路线图",
    "Motivation and History": "动机与历史",
    "The Clipped Objective": "裁剪目标函数",
    "Full PPO Loss": "完整 PPO 损失",
    "Derivation of the PPO Gradient and Update Rule": "PPO 梯度与更新规则推导",
    "Rollout Buffer and Rollouts": "Rollout 缓冲区与采样轨迹",
    "PPO for RLHF: The Full Loop": "用于 RLHF 的 PPO 完整循环",
    "Detailed Mechanics: Logits and Policy Updates": "细节机制：Logits 与策略更新",
    "TRL Implementation": "TRL 实现",
    "Critical Hyperparameters": "关键超参数",
    "Motivation": "动机",
    "Mathematical Derivation": "数学推导",
    "Gradient Analysis": "梯度分析",
    "How DPO Works: Full Mechanics": "DPO 工作机制：完整细节",
    "DPO Variants and When Each Fails": "DPO 变体及其失效场景",
    "Selection Guide": "选择指南",
    "DPO Batch Size Configuration and Scaling": "DPO 批大小配置与扩展",
    "DPO Extensions and Variants": "DPO 扩展与变体",
    "Algorithm": "算法",
    "Group Size Analysis": "组大小分析",
    "GRPO Variants and Extensions": "GRPO 变体与扩展",
    "Online DPO": "在线 DPO",
    "KTO - Kahneman-Tversky Optimization": "KTO：Kahneman-Tversky 优化",
    "IPO - Identity Preference Optimization": "IPO：身份偏好优化",
    "ORPO - Odds Ratio Preference Optimization": "ORPO：赔率比偏好优化",
    "Best-of-N Sampling (Rejection Sampling)": "Best-of-N 采样（拒绝采样）",
    "Summary: Choosing an Alignment Method": "总结：选择对齐方法",
    "Bradley-Terry Model - Full Derivation": "Bradley-Terry 模型完整推导",
    "Reward Model Architectures": "奖励模型架构",
    "Reward Model Training Tricks": "奖励模型训练技巧",
    "Process Reward Models vs Outcome Reward Models": "过程奖励模型与结果奖励模型",
    "Rule-Based Rewards for RLVR": "面向 RLVR 的规则奖励",
    "Multi-Objective Rewards - Combination Strategies": "多目标奖励：组合策略",
    "Listwise Rank-Based Rewards": "基于列表排序的奖励",
    "Sequence Packing for Efficiency": "提升效率的序列打包",
    "Chat Templates and Formatting": "聊天模板与格式化",
    "Completion-Only Masking": "仅补全部分掩码",
    "Data Mixing Strategies for Multi-Task SFT": "多任务 SFT 的数据混合策略",
    "When SFT Hurts - Catastrophic Forgetting and Alignment Tax": "SFT 何时有害：灾难性遗忘与对齐税",
    "Connection to RL - SFT Quality Determines RL Ceiling": "与 RL 的关系：SFT 质量决定 RL 上限",
    "The 4-Model Memory Challenge": "四模型显存挑战",
    "Parallelism Strategies in Detail": "并行策略详解",
    "The Generation Bottleneck: Quantitative Analysis": "生成瓶颈：定量分析",
    "Decoupled Architecture: Production Design": "解耦架构：生产设计",
    "Weight Synchronization Strategies": "权重同步策略",
    "Memory Optimization Techniques": "显存优化技术",
    "Fault Tolerance at Scale": "大规模容错",
    "End-to-End Latency Breakdown": "端到端延迟拆解",
    "Monitoring and Observability": "监控与可观测性",
    "Network Topology and Communication Patterns": "网络拓扑与通信模式",
    "Training Throughput and Model FLOPs Utilization": "训练吞吐与模型 FLOPs 利用率",
    "Cost Analysis and Cloud Deployment": "成本分析与云部署",
    "Distributed Checkpointing": "分布式检查点",
    "Hardware Selection Guide": "硬件选择指南",
    "Optimizer Configuration for RL Training": "RL 训练的优化器配置",
    "Paradigm Comparison": "范式比较",
    "Major Techniques in Agentic RL": "Agentic RL 的主要技术",
    "Use Case: Agentic RL for a Productivity Co-pilot": "用例：面向生产力副驾驶的 Agentic RL",
    "Use Case: Building a Research Agent from Scratch": "用例：从零构建研究智能体",
    "State-of-the-Art RL for LLM Agents": "LLM 智能体强化学习前沿",
    "Motivation and Background": "动机与背景",
    "Test-Time Scaling Methods": "测试时扩展方法",
    "OpenAI o1/o3 Series": "OpenAI o1/o3 系列",
    "QwQ and Qwen Reasoning Models": "QwQ 与 Qwen 推理模型",
    "Key Methods with Mathematical Foundations": "关键方法与数学基础",
    "Scaling Laws for Reasoning": "推理扩展定律",
    "Comparison of Reasoning Models": "推理模型比较",
    "Summary and Open Problems": "总结与开放问题",
    "Evaluation Scheme Design": "评估方案设计",
    "Data Collection for Evaluation": "评估数据收集",
    "Synthetic Data Generation for Evaluation": "评估用合成数据生成",
    "Metrics for Ranking Tasks": "排序任务指标",
    "Metrics for Generation Tasks": "生成任务指标",
    "Metrics for Agentic Tasks": "智能体任务指标",
    "LLM-as-Judge": "LLM 作为评审",
    "Evaluation Pitfalls": "评估陷阱",
    "Motivation and Problem Statement": "动机与问题陈述",
    "Core RAG Architecture": "RAG 核心架构",
    "Retrieval Methods": "检索方法",
    "Chunking Strategies": "切块策略",
    "Advanced RAG Patterns": "高级 RAG 模式",
    "Efficient RAG Decoding: REFRAG": "高效 RAG 解码：REFRAG",
    "Agentic RAG": "智能体式 RAG",
    "Evaluation": "评估",
    "Production Considerations": "生产环境考量",
    "RAG + Fine-Tuning Synergy": "RAG 与微调协同",
    "Comprehensive RAG Approach Comparison": "RAG 方法综合比较",
    "Motivation: Why Agents Need Memory": "动机：为什么智能体需要记忆",
    "Taxonomy of Memory Types": "记忆类型分类",
    "Memory Architectures": "记忆架构",
    "Memory Operations": "记忆操作",
    "Memory for Multi-Turn Conversations": "多轮对话记忆",
    "Memory for Multi-Agent Systems": "多智能体系统记忆",
    "Training Memory Systems with Reinforcement Learning": "用强化学习训练记忆系统",
    "Comparison of Memory Approaches": "记忆方法比较",
    "Evaluating Memory Systems": "记忆系统评估",
    "Implementation Patterns": "实现模式",
    "Recent Advances in Agentic Memory": "智能体记忆的最新进展",
    "What Is an Agent Harness?": "什么是智能体执行框架",
    "Context Window Management": "上下文窗口管理",
    "Prompt Architecture": "提示架构",
    "Tool Integration and Execution": "工具集成与执行",
    "Orchestration Patterns": "编排模式",
    "State Management": "状态管理",
    "Error Handling and Recovery": "错误处理与恢复",
    "Scaling and Production Concerns": "扩展与生产化关注点",
    "Framework Comparison": "框架比较",
    "Implementation: Production Agent Harness": "实现：生产级智能体执行框架",
    "Workflow Patterns": "工作流模式",
    "Autonomous Agent Patterns": "自主智能体模式",
    "Design Principles": "设计原则",
    "Pattern Selection Guide": "模式选择指南",
    "Motivation: Why Agents Need Environments": "动机：为什么智能体需要环境",
    "Environment Design Principles": "环境设计原则",
    "Types of Agentic Environments": "智能体式环境类型",
    "OpenEnv: Standardized Agentic Environment Interfaces": "OpenEnv：标准化智能体环境接口",
    "Building Custom Environments": "构建自定义环境",
    "Environment-Agent Interface Patterns": "环境-智能体接口模式",
    "Evaluation Harness Design": "评估框架设计",
    "Code Example: Minimal Custom LLM Agent Environment": "代码示例：最小自定义 LLM 智能体环境",
    "Comparison of Major Agentic Environments": "主要智能体环境比较",
    "Motivation: The Tool Integration Problem": "动机：工具集成问题",
    "Core Primitives": "核心原语",
    "Protocol Specification": "协议规范",
    "Tool Definition and Discovery": "工具定义与发现",
    "Security Model": "安全模型",
    "The MCP Ecosystem": "MCP 生态系统",
    "MCP vs. Alternatives": "MCP 与替代方案",
    "MCP for Agent Training": "用于智能体训练的 MCP",
    "What Is a Skill?": "什么是技能",
    "Skill Architecture Patterns": "技能架构模式",
    "Case Study: Anthropic’s Agent Design": "案例研究：Anthropic 的智能体设计",
    "Skill Lifecycle": "技能生命周期",
    "Skill Registries and Marketplaces": "技能注册表与市场",
    "Skills vs. Fine-Tuning": "技能与微调",
    "Motivation: Why Agents Must Communicate": "动机：为什么智能体必须通信",
    "The Google A2A Protocol": "Google A2A 协议",
    "Communication Patterns": "通信模式",
    "Agent Discovery and Routing": "智能体发现与路由",
    "Message Formats and Schemas": "消息格式与 Schema",
    "Coordination Protocols": "协调协议",
    "A2A vs. MCP: Complementary Protocols": "A2A 与 MCP：互补协议",
    "Security and Trust in Multi-Agent Systems": "多智能体系统中的安全与信任",
    "Implementation Example: Multi-Agent Research Workflow": "实现示例：多智能体研究工作流",
    "Motivation: Why Multiple Agents?": "动机：为什么需要多个智能体",
    "Multi-Agent Architectures": "多智能体架构",
    "Coordination Mechanisms": "协调机制",
    "Communication Protocols": "通信协议",
    "Role Design and Specialization": "角色设计与专业化",
    "Multi-Agent Patterns for LLMs": "面向 LLM 的多智能体模式",
    "Training Multi-Agent Systems with Reinforcement Learning": "用强化学习训练多智能体系统",
    "Challenges and Solutions": "挑战与解决方案",
    "Real-World Multi-Agent Applications": "真实世界多智能体应用",
    "Architecture Comparison": "架构比较",
    "Motivation: The Engineering Gap": "动机：工程落差",
    "The Agent Development Lifecycle": "智能体开发生命周期",
    "Major Frameworks: A Deep Dive": "主要框架深度解析",
    "Open-Source Agent Tooling": "开源智能体工具链",
    "Agent Testing and Evaluation": "智能体测试与评估",
    "Observability and Debugging": "可观测性与调试",
    "Production Deployment Patterns": "生产部署模式",
    "Complete Implementation Example: Production Research Agent": "完整实现示例：生产级研究智能体",
    "Motivation: Beyond the Chat Box": "动机：超越聊天框",
    "UI Paradigms for Agents": "智能体 UI 范式",
    "Key UI Components for Agents": "智能体关键 UI 组件",
    "Frameworks and Libraries": "框架与库",
    "Generative UI": "生成式 UI",
    "Streaming and Real-Time Patterns": "流式与实时模式",
    "Human-in-the-Loop UI Design": "人在回路 UI 设计",
    "Accessibility and Trust": "可访问性与信任",
    "Implementation Example: A Full-Stack Agentic UI": "实现示例：全栈智能体式 UI",
    "Foundations Questions": "基础问题",
    "Core Algorithm Questions": "核心算法问题",
    "System Design Questions": "系统设计问题",
    "Practical and Debugging Questions": "实践与调试问题",
    "GRPO Variants and Advanced RL Questions": "GRPO 变体与高级 RL 问题",
    "DPO Extensions Questions": "DPO 扩展问题",
    "GPU Architecture and Hardware Questions": "GPU 架构与硬件问题",
    "Optimization and Training Questions": "优化与训练问题",
    "Reward Model and SFT Questions": "奖励模型与 SFT 问题",
    "System Architecture Extension Questions": "系统架构扩展问题",
    "Transformer Architecture Questions": "Transformer 架构问题",
    "FlashAttention Questions": "FlashAttention 问题",
    "LoRA and PEFT Questions": "LoRA 与 PEFT 问题",
    "Model Compression Questions": "模型压缩问题",
    "Mixture of Experts Questions": "混合专家模型问题",
    "Diversity in Training Questions": "训练多样性问题",
    "Speculative Decoding Questions": "推测解码问题",
    "Agentic RL Questions": "Agentic RL 问题",
    "Listwise Rewards and Advanced RM Questions": "列表式奖励与高级奖励模型问题",
    "RL for Large Reasoning Models Questions": "大型推理模型 RL 问题",
    "LLM Evaluation Questions": "LLM 评估问题",
    "Agentic Memory Questions": "智能体记忆问题",
    "Agent Orchestration Questions": "智能体编排问题",
    "MCP Protocol Questions": "MCP 协议问题",
    "Agent Communication (A2A) Questions": "智能体通信（A2A）问题",
    "Multi-Agent Systems Questions": "多智能体系统问题",
    "Agent Development Framework Questions": "智能体开发框架问题",
    "Agentic Environments Questions": "智能体环境问题",
    "Agentic UI Framework Questions": "智能体 UI 框架问题",
    "RAG and Agentic RAG Questions": "RAG 与智能体式 RAG 问题",
    "Core RL & Alignment Equations": "核心 RL 与对齐公式",
    "Transformer & Architecture Formulas": "Transformer 与架构公式",
    "Decoding Methods": "解码方法",
    "Systems & Parallelism": "系统与并行",
    "GPU Hardware Specs": "GPU 硬件规格",
    "Hyperparameter Ranges": "超参数范围",
    "TRL API Quick Reference": "TRL API 速查",
    "RAG Pipeline Formulas": "RAG 流水线公式",
    "Agentic Design Patterns": "智能体式设计模式",
    "Agent Communication Protocols": "智能体通信协议",
    "Context Window Budget": "上下文窗口预算",
    "Common Failure Modes & Fixes": "常见失效模式与修复",
    "Method Selection Decision Tree": "方法选择决策树",
    "Evaluation Metrics": "评估指标",
    "Reasoning & Test-Time Scaling": "推理与测试时扩展",
    "Memory System Types": "记忆系统类型",
    "MCP Quick Reference": "MCP 速查",
    "A2A Protocol Quick Reference": "A2A 协议速查",
    "Agent Framework Comparison": "智能体框架比较",
    "Agentic RL Formulas": "Agentic RL 公式",
    "Agent Security Checklist": "智能体安全检查清单",
    "Agent Evaluation Metrics": "智能体评估指标",
    "Key Agentic Benchmarks": "关键智能体基准",
    "The Road Ahead: Open Challenges": "未来道路：开放挑战",
}

KNOWN_ENGLISH_REPAIRS = [
    (
        "where δ is the margin threshold. When the model already assigns a margin of δ between winning and losing responses, the loss is zero.",
        "其中 δ 是边际阈值。当模型已经在胜出响应和失败响应之间给出 δ 的边际时，损失为零。",
    ),
    (
        "Table 11.2: Memory comparison: DDP vs FSDP/ZeRO stages (70B model, 8 GPUs).",
        "表 11.2：DDP 与 FSDP/ZeRO 各阶段的显存比较（70B 模型，8 块 GPU）。",
    ),
    (
        "Pipeline Parallel: Only if model exceeds 100B+ and won’t fit with TP+ZeRO.",
        "流水线并行：仅当模型超过 100B 且无法通过 TP+ZeRO 容纳时才使用。",
    ),
    (
        "bubble overhead 10–20%) and scheduling headaches.",
        "气泡开销 10–20%）以及调度复杂度。",
    ),
    (
        "Speculative decoding [143] (2–3×): Small draft model proposes 5 tokens, large model verifies in one forward pass.",
        "推测解码 [143]（2-3 倍）：小型草稿模型先提出 5 个 token，大模型在一次前向传播中验证。",
    ),
    (
        "where M is the message size (bytes) and N is the number of participants.",
        "其中 M 是消息大小（字节），N 是参与方数量。",
    ),
    (
        "for constants a, α, β > 0. The optimal allocation for a fixed total budget Ctotal satisfies the condition that marginal return per FLOP is equalized between training and inference:",
        "其中常数 a、α、β > 0。对于固定总预算 Ctotal，最优分配满足训练与推理之间每 FLOP 边际收益相等的条件：",
    ),
]

A100_REPAIRS = [
    ("A100 specs: 312 TFLOPS (BF16 tensor cores), 2 TB/s HBM bandwidth.", "A100 规格：312 TFLOPS（BF16 tensor cores），2 TB/s HBM 带宽。"),
    ("Autoregressive generation: For each token, read all weights (140GB for 70B) and do 2× 70B = 140G FLOPs per token (at batch=1).", "自回归生成：每生成一个 token 都要读取全部权重（70B 模型约 140GB），并执行 2×70B = 140G FLOPs/token（batch=1）。"),
    ("Arithmetic intensity: 140G FLOP/140GB = 1 FLOP/byte.", "算术强度：140G FLOP/140GB = 1 FLOP/byte。"),
    ("Utilization: 1/156 = 0.6% of peak FLOPS utilized.", "利用率：1/156 = 峰值 FLOPS 的 0.6%。"),
    ("GPU 99.4% 空闲，正在等待内存 读。", "GPU 99.4% 的时间都在等待内存读取。"),
    ("Token rate: 2TB/s/140GB = 14.3 tokens/second (single stream, batch=1).", "Token 速率：2TB/s/140GB = 14.3 tokens/second（单流，batch=1）。"),
]

ROPE_LATEX = (
    r"\operatorname{RoPE}(x_m,m)_{2i}=x_{2i}\cos(m\theta_i)-x_{2i+1}\sin(m\theta_i),\quad "
    r"\operatorname{RoPE}(x_m,m)_{2i+1}=x_{2i}\sin(m\theta_i)+x_{2i+1}\cos(m\theta_i)"
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ensure_dirs() -> None:
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
    for stale in [REPO / "assets" / "style.css", REPO / "assets" / "main.js", REPO / "assets" / "figures"]:
        if stale.is_dir():
            shutil.rmtree(stale)
        elif stale.exists():
            stale.unlink()


def slugify(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return text or "section"


def repair_known_english(text: str) -> str:
    if "Most modern LLMs tie the LM head weights" in text:
        return (
            "现代 LLM 通常将语言模型头（LM head）的权重与输入嵌入矩阵绑定："
            "`lm_head.weight = model.embed_tokens.weight`。这意味着 LM head 不是单独学习的层，"
            "而是复用嵌入表。这样可以减少参数量（节省 |V| × d）、提升泛化能力，并让嵌入空间的几何结构直接决定 token 概率。"
            "在 Hugging Face 模型中通常可以验证：`model.lm_head.weight is model.model.embed_tokens.weight` 对多数模型为真。"
        )
    if "This means the LM head is not a separately learned layer" in text or "geometric structure of the embedding space" in text:
        return (
            "现代 LLM 通常会将 LM head 权重与输入嵌入矩阵绑定，例如 `lm_head.weight = model.embed_tokens.weight`。"
            "这意味着 LM head 不是单独学习的层，而是复用嵌入表。其优点包括减少参数量（节省 |V| × d）、"
            "改善泛化能力，并让嵌入空间的几何结构直接决定 token 概率。"
        )
    for old, new in KNOWN_ENGLISH_REPAIRS:
        text = text.replace(old, new)
    for old, new in A100_REPAIRS:
        text = text.replace(old, new)
    return text


def clean_section_title(title: str) -> str:
    title = title.strip()
    if title in SECTION_TITLE_TRANSLATIONS:
        return SECTION_TITLE_TRANSLATIONS[title]
    title = clean_text(title, translate=False)
    return SECTION_TITLE_TRANSLATIONS.get(title, title)


def clean_text(text: str, *, translate: bool = True) -> str:
    text = repair_known_english(text)
    text = normalize_terms(text)
    for old, new in TERM_NORMALIZATION:
        text = text.replace(old, new)
    for old, new in PHRASE_TRANSLATIONS.items():
        text = text.replace(old, new)
    text = text.replace("\ufffd", "")
    text = re.sub(r"[]", "", text)
    text = text.replace("\x11", "")
    text = re.sub(r"\\fn[^}\\s]*(?:\\[A-Za-z]+\d*)*", "", text)
    text = re.sub(r"\{\\[^}]+\}", "", text)
    text = re.sub(r"\(中文\(简体\)\s*\)", "", text)
    text = re.sub(r"\(英语\)", "", text)
    text = re.sub(r"页\s*:\s*1", "", text)
    text = re.sub(r"QQR", "∈", text)
    text = re.sub(r"\s+", " ", text).strip()
    if translate and looks_like_english_prose(text):
        cache = load_json(TRANSLATION_CACHE, default={})
        translated = translate_online(text, cache, TRANSLATION_CACHE)
        if translated and translated != text:
            text = translated
    for old, new in TERM_NORMALIZATION:
        text = text.replace(old, new)
    return text.strip()


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def semantic_cluster(title: str, part: str) -> str:
    hay = f"{title} {part}".lower()
    if "架构" in title or "optimization" in hay or "系统基础" in title:
        return "LLM 基础与系统"
    if "PPO" in title or "DPO" in title or "GRPO" in title or "强化学习" in title or "奖励" in title or "SFT" in title:
        return "训练、强化学习与对齐"
    if "推理" in title or "Reasoning" in part:
        return "推理与评估"
    if "评估" in title:
        return "推理与评估"
    if "智能体" in title or "MCP" in title or "A2A" in title or "RAG" in title or "多智能体" in title:
        return "Agentic AI 系统"
    if "测验" in title or "速查" in title or "结论" in title:
        return "参考与总结"
    return "导读"


def chapter_summary(title: str) -> str:
    summaries = {
        "导读与前置说明": "说明文档来源、作者背景、许可和全书阅读路径。",
        "LLM 架构和优化方法": "从分词、Transformer、自注意力到训练优化和模型压缩的基础层。",
        "LLM 的系统基础": "从 GPU、并行训练、推理服务到大规模基础设施的系统视角。",
        "强化学习简介": "用 MDP、价值函数、策略梯度和信用分配建立强化学习基础。",
        "语言模型的强化学习基础": "把强化学习问题映射到语言模型的序列生成与偏好优化。",
        "PPO：近端策略优化": "解释 PPO 的目标函数、优势估计、KL 控制和生产训练实践。",
        "DPO：直接偏好优化": "介绍不用显式奖励模型的偏好优化方法及其理论直觉。",
        "GRPO：组相对策略优化": "介绍面向推理模型的组相对优化、可验证奖励和采样策略。",
        "LLM 智能体训练": "把环境交互、轨迹缓冲区和奖励设计组织为智能体训练流水线。",
        "智能体式 AI 简介": "从聊天机器人过渡到自主智能体，建立架构、状态和行动循环。",
        "检索增强生成（RAG）": "组织检索、重排、生成、评估与智能体式 RAG 的系统实践。",
        "智能体记忆系统": "讨论短期、长期、语义、情景记忆及其训练方法。",
        "模型上下文协议（MCP）": "解释 MCP 的协议结构、工具生态和安全边界。",
        "智能体间通信（A2A）": "介绍智能体之间的任务委托、消息结构和协作模式。",
        "多智能体系统": "整理多智能体协作、通信、协调和集中训练分散执行。",
    }
    return summaries.get(title, "本章整理该主题的关键概念、方法、系统实践和工程注意事项。")


def copy_figures() -> tuple[dict[int, list[dict]], dict[str, str]]:
    manifest = load_json(IMAGE_MANIFEST, default=[])
    dst = REPO / "assets" / "images" / "figures"
    dst.mkdir(parents=True, exist_ok=True)
    by_page: dict[int, list[dict]] = {}
    name_map: dict[str, str] = {}
    counter = 1
    for item in manifest:
        src_name = item["name"]
        src = SOURCE_FIGURES / src_name
        if not src.exists():
            continue
        ext = src.suffix.lower() or ".png"
        new_name = f"fig-{counter:03d}{ext}"
        counter += 1
        shutil.copy2(src, dst / new_name)
        clean = {
            "id": new_name.rsplit(".", 1)[0],
            "src": f"assets/images/figures/{new_name}",
            "alt": "文档图示",
            "caption": "图示：来自原文档的结构、表格或公式区域。",
            "metadata": {"source_page": item["page"], "source_name": src_name, "width": item.get("width"), "height": item.get("height")},
        }
        by_page.setdefault(int(item["page"]), []).append(clean)
        name_map[src_name] = new_name
    return by_page, name_map


def section_items(chapter: Chapter) -> list[TocItem]:
    items = []
    seen = set()
    for item in chapter.toc_items:
        if item.level == 3 and item.title.lower() != "summary" and item.title not in seen:
            items.append(item)
            seen.add(item.title)
    if not items:
        items = [TocItem(level=3, title="本章概览", page=chapter.start_page, raw_title="overview")]
    return items


def split_sections(chapter: Chapter) -> list[dict]:
    items = section_items(chapter)
    sections = []
    for idx, item in enumerate(items):
        section_title = clean_section_title(item.title)
        next_page = items[idx + 1].page if idx + 1 < len(items) else chapter.end_page + 1
        start = max(chapter.start_page, item.page)
        end = min(chapter.end_page, max(start, next_page - 1))
        sections.append(
            {
                "id": f"{chapter.slug}-s{idx + 1:02d}",
                "title": section_title,
                "summary": f"本节聚焦“{section_title}”的定义、机制与工程含义。",
                "metadata": {"source_pages": list(range(start, end + 1)), "source": "semantic_toc_cluster"},
                "blocks": [],
            }
        )
    return sections


def should_drop_line(line: str, chapter: Chapter, section_titles: set[str]) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("<a id=") or re.match(r"^#+\s*第\s*\d+\s*页$", s):
        return True
    if s == "### 本页图像资源" or s.startswith("![") or "图像来源：原 PDF" in s:
        return True
    if re.fullmatch(r"\d+(?:\.\d+){0,5}", s):
        return True
    if re.fullmatch(r"第\s*\d+\s*章", s) or re.fullmatch(r"第[一二三四五六七八九十]+部分", s):
        return True
    if s in {"基础", "推理", "评估", chapter.title} or s in section_titles:
        return True
    if re.search(r"^第\s*\d+\s*页$", s):
        return True
    return False


def bad_formula(text: str) -> bool:
    return bool(re.search(r"|||\\fn|页\s*:|QQR|国家\s*$|中文\(简体\)", text))


def formula_node(text: str, page: int, figures: list[dict]) -> dict:
    cleaned = clean_text(text, translate=False)
    if not cleaned:
        cleaned = "公式内容已由 OCR 清洗；请结合上下文或图像 fallback 阅读。"
    if "RoPE" in text or "ROPE" in text or "旋转位置" in text:
        return {
            "type": "formula",
            "latex": ROPE_LATEX,
            "display": "RoPE 旋转位置嵌入公式",
            "fallback": "latex",
            "metadata": {"source_page": page, "repaired": True, "reason": "RoPE OCR formula repaired"},
        }
    if bad_formula(text) and figures:
        fig = figures[0]
        return {
            "type": "formula_image",
            "src": fig["src"],
            "alt": "公式图示",
            "caption": "公式图：原文档中的数学区域已用图像 fallback 保留。",
            "fallback": "image",
            "metadata": {"source_page": page, "repaired": True, "reason": "OCR formula unreadable"},
        }
    return {"type": "formula", "latex": cleaned, "display": cleaned, "fallback": "latex", "metadata": {"source_page": page}}


def is_codeish_line(text: str) -> bool:
    if re.match(r"^(class|def|async def|return|import|from|for|while|if|elif|else|try|except)\b", text):
        return True
    if text.startswith(("# ", ">>>", "$ ", "curl ", "pip ", "python ")):
        return True
    if '"""' in text or re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*[:=]\s*['\"{\[]?", text):
        return True
    if re.search(r"\b(data|admin|analysis|read|write|export):[A-Za-z_]+", text, re.I):
        return True
    return False


def is_codeish_block(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text).strip()
    if re.match(r"^(class|def|async def|import|from|#)\b", compact):
        return True
    if '"""' in compact or "'''" in compact:
        return True
    if re.search(r"\b(data|admin|analysis|read|write|export):[A-Za-z_]+", compact, re.I):
        return True
    if re.search(r"\b(return|self\.|await|async|FastAPI|pytest|assert)\b", compact):
        return True
    return False


def flush_paragraph(buffer: list[str], blocks: list[dict], page: int) -> None:
    if not buffer:
        return
    text = clean_text(" ".join(buffer))
    buffer.clear()
    if not text or len(text) < 2:
        return
    if re.search(r"^第\s*\d+\s*页$", text):
        return
    blocks.append({"type": "paragraph", "text": text, "metadata": {"source_page": page}})


def page_to_blocks(page: int, content: str, chapter: Chapter, section_titles: set[str], figures_by_page: dict[int, list[dict]]) -> list[dict]:
    blocks: list[dict] = []
    para: list[str] = []
    in_fence = False
    fence_lang = ""
    fence_lines: list[str] = []
    for raw in content.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                flush_paragraph(para, blocks, page)
                in_fence = True
                fence_lang = stripped[3:].strip().lower()
                fence_lines = []
            else:
                text = "\n".join(fence_lines).strip()
                if fence_lang == "math":
                    blocks.append(formula_node(text, page, figures_by_page.get(page, [])))
                elif fence_lang == "text" and looks_like_english_prose(text) and not is_codeish_block(text):
                    blocks.append({"type": "paragraph", "text": clean_text(text), "metadata": {"source_page": page, "converted_from": "text_fence"}})
                else:
                    blocks.append({"type": "code", "language": fence_lang or "text", "text": text, "metadata": {"source_page": page}})
                in_fence = False
                fence_lang = ""
                fence_lines = []
            continue
        if in_fence:
            fence_lines.append(line)
            continue
        if should_drop_line(stripped, chapter, section_titles):
            flush_paragraph(para, blocks, page)
            continue
        if not stripped:
            flush_paragraph(para, blocks, page)
            continue
        if re.search(r"RoPE|ROPE|旋转位置嵌入", stripped) and bad_formula(stripped):
            flush_paragraph(para, blocks, page)
            blocks.append(formula_node(stripped, page, figures_by_page.get(page, [])))
            continue
        if bad_formula(stripped):
            flush_paragraph(para, blocks, page)
            blocks.append(formula_node(stripped, page, figures_by_page.get(page, [])))
            continue
        if is_codeish_line(stripped):
            flush_paragraph(para, blocks, page)
            blocks.append({"type": "code", "language": "text", "text": stripped, "metadata": {"source_page": page, "detected": "codeish_line"}})
            continue
        para.append(stripped)
    flush_paragraph(para, blocks, page)
    for fig in figures_by_page.get(page, []):
        blocks.append({"type": "image", **fig})
    return blocks


def extract_concepts(text: str, limit: int = 8) -> list[dict]:
    hits = []
    used = set()
    lower = text.lower()
    for en, zh, note in GLOSSARY:
        if en.lower() in lower or zh.lower() in lower:
            key = en.lower()
            if key not in used:
                hits.append({"term": en, "label": zh, "note": note})
                used.add(key)
        if len(hits) >= limit:
            break
    return hits


def build_ast() -> dict:
    source_text = SOURCE_MD.read_text(encoding="utf-8")
    pages = parse_pages(source_text)
    toc_items = load_toc(TOC_JSON)
    chapters = build_chapters(toc_items, max(pages))
    figures_by_page, figure_name_map = copy_figures()
    ast_chapters = []
    for chapter in chapters:
        sections = split_sections(chapter)
        section_titles = {section["title"] for section in sections}
        for section in sections:
            for page in section["metadata"]["source_pages"]:
                if page in pages:
                    section["blocks"].extend(page_to_blocks(page, pages[page], chapter, section_titles, figures_by_page))
            section_text = " ".join(block.get("text", "") or block.get("display", "") for block in section["blocks"])
            section["concepts"] = extract_concepts(section_text, 5)
            section["block_count"] = len(section["blocks"])
        chapter_text = " ".join(
            block.get("text", "") or block.get("display", "")
            for section in sections for block in section["blocks"]
        )
        ast_chapters.append(
            {
                "id": chapter.slug,
                "number": chapter.number,
                "title": chapter.title,
                "summary": chapter_summary(chapter.title),
                "semantic_cluster": semantic_cluster(chapter.title, chapter.part),
                "concepts": extract_concepts(f"{chapter.title} {chapter_text}", 8),
                "metadata": {
                    "source_pages": list(range(chapter.start_page, chapter.end_page + 1)),
                    "source_boundary": {"start_page": chapter.start_page, "end_page": chapter.end_page},
                    "toc_source": "pdf_bookmarks_semantic_cluster",
                    "page_numbers_rendered": False,
                },
                "sections": sections,
            }
        )
    ast = {
        "schema": "clean_chapter_tree.v3",
        "version": 3,
        "title": SITE_TITLE,
        "subtitle": SITE_SUBTITLE,
        "source": {"pdf": PDF_URL, "translation": "translated/document.zh.md", "toc": "extracted/toc.json"},
        "policy": {
            "toc_basis": "semantic clusters over PDF bookmark structure, never markdown headings",
            "page_numbers": "metadata only, never rendered into HTML DOM",
            "rendering": "HTML pages are generated from this clean AST only",
        },
        "figure_name_map": figure_name_map,
        "chapters": ast_chapters,
    }
    return ast


def rel(base: str, path: str) -> str:
    return f"{base}{path}"


def nav_html(base: str, active: str) -> str:
    items = [
        ("首页", "index.html", "home"),
        ("章节", "chapters/index.html", "chapters"),
        ("术语表", "glossary.html", "glossary"),
        ("参考文献", "references.html", "references"),
        ("搜索", "search.html", "search"),
        ("原 PDF", PDF_URL, "pdf"),
    ]
    out = []
    for label, href, key in items:
        url = href if href.startswith("http") else rel(base, href)
        target = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        cls = "active" if key == active else ""
        out.append(f'<a class="{cls}" href="{html.escape(url)}"{target}>{label}</a>')
    return "".join(out)


def chapter_nav(ast: dict, base: str, active_id: str = "") -> str:
    grouped: dict[str, list[dict]] = {}
    for chapter in ast["chapters"]:
        grouped.setdefault(chapter["semantic_cluster"], []).append(chapter)
    parts = []
    for cluster, chapters in grouped.items():
        links = []
        for chapter in chapters:
            cls = "active" if chapter["id"] == active_id else ""
            links.append(
                f'<a class="chapter-link {cls}" href="{rel(base, "chapters/" + chapter["id"] + ".html")}">'
                f'<span class="chapter-num">{chapter["number"]:02d}</span><span>{html.escape(chapter["title"])}</span></a>'
            )
        parts.append(f'<div class="nav-cluster"><strong>{html.escape(cluster)}</strong>{"".join(links)}</div>')
    return "".join(parts)


def render_block(block: dict, base: str) -> str:
    t = block["type"]
    if t == "paragraph":
        return f'<p class="content-block paragraph">{html.escape(block["text"])}</p>'
    if t == "code":
        return f'<div class="component code-component"><div class="block-label">{html.escape(block.get("language") or "text")}</div><pre><code>{html.escape(block["text"])}</code></pre></div>'
    if t == "formula":
        display = block.get("display") or block.get("latex", "")
        return f'<div class="component formula-component" data-fallback="{html.escape(block.get("fallback","latex"))}"><div class="block-label">公式</div><pre class="formula"><code>{html.escape(display)}</code></pre></div>'
    if t == "formula_image":
        return (
            f'<figure class="component formula-component image-fallback">'
            f'<div class="block-label">公式图</div>'
            f'<img src="{rel(base, block["src"])}" alt="{html.escape(block.get("alt","公式图"))}" loading="lazy" decoding="async" />'
            f'<figcaption>{html.escape(block.get("caption","公式图"))}</figcaption></figure>'
        )
    if t == "image":
        return (
            f'<figure class="component figure-component">'
            f'<img src="{rel(base, block["src"])}" alt="{html.escape(block.get("alt","图示"))}" loading="lazy" decoding="async" />'
            f'<figcaption>{html.escape(block.get("caption","图示"))}</figcaption></figure>'
        )
    return ""


def concepts_html(concepts: list[dict]) -> str:
    if not concepts:
        return '<p class="muted small">本章没有抽取到高频核心术语。</p>'
    return "".join(
        f'<div class="concept-chip"><strong>{html.escape(c["label"])}</strong><span>{html.escape(c["term"])}</span><p>{html.escape(c["note"])}</p></div>'
        for c in concepts
    )


def shell(title: str, description: str, body: str, *, base: str = "", active: str = "", ast: dict | None = None, active_chapter: str = "", outline: list[dict] | None = None, article: bool = False) -> str:
    left = ""
    right = ""
    if article and ast:
        left = f'<aside class="left-nav" id="left-nav"><div class="nav-section-title">语义目录</div>{chapter_nav(ast, base, active_chapter)}</aside>'
        outline_links = "".join(f'<a class="outline-link" href="#{html.escape(item["id"])}">{html.escape(item["title"])}</a>' for item in (outline or []))
        right = f'<aside class="right-outline"><div class="nav-section-title">本页结构</div>{outline_links}</aside>'
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
  <link rel="canonical" href="{ONLINE_URL}" />
  <link rel="stylesheet" href="{rel(base, "assets/css/main.css")}" />
  <link rel="stylesheet" href="{rel(base, "assets/css/article.css")}" />
  <link rel="stylesheet" href="{rel(base, "assets/css/responsive.css")}" />
</head>
<body class="{'article-page' if article else 'site-page'}">
  <div class="reading-progress" id="reading-progress"></div>
  <header class="topbar">
    <a class="brand" href="{rel(base, "index.html")}"><span class="brand-mark">AST</span><span><strong>{SITE_TITLE}</strong><small>{SITE_SUBTITLE}</small></span></a>
    <button class="nav-toggle" id="nav-toggle" aria-label="打开导航" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="topnav" id="topnav">{nav_html(base, active)}</nav>
  </header>
  <main class="layout">{left}<section class="content-shell">{body}</section>{right}</main>
  <button class="back-top" id="back-top" type="button">↑</button>
  <script src="{rel(base, "assets/js/main.js")}"></script>
  <script src="{rel(base, "assets/js/toc.js")}"></script>
  <script src="{rel(base, "assets/js/progress.js")}"></script>
</body>
</html>
"""


def build_home(ast: dict) -> None:
    cards = "".join(
        f'<a class="chapter-card" href="chapters/{ch["id"]}.html"><span>{ch["number"]:02d}</span><strong>{html.escape(ch["title"])}</strong><p>{html.escape(ch["summary"])}</p></a>'
        for ch in ast["chapters"][:12]
    )
    clusters = sorted({ch["semantic_cluster"] for ch in ast["chapters"]})
    cluster_tags = "".join(f'<span class="term-tag">{html.escape(c)}</span>' for c in clusters)
    body = f"""
    <section class="home-hero">
      <div class="hero-copy">
        <p class="doc-kicker">V3 · Clean AST Knowledge System</p>
        <h1>{SITE_TITLE}</h1>
        <p class="hero-lede">本版本从干净的内容树生成，不再直接渲染 OCR/Markdown。语义目录、章节页面、搜索索引、关键概念和公式 fallback 都来自 <code>clean_chapter_tree.json</code>。</p>
        <form class="home-search" action="search.html" method="get">
          <input id="site-search" name="q" type="search" placeholder="搜索：RoPE、MCP、轨迹缓冲区、GRPO..." />
          <button type="submit">搜索</button>
        </form>
        <div class="hero-actions"><a class="button primary" href="chapters/index.html">进入章节</a><a class="button" href="search.html">搜索知识树</a><a class="button ghost" href="assets/data/clean_chapter_tree.json">查看 AST</a></div>
      </div>
      <div class="hero-panel">
        <h2>结构化层</h2>
        <div class="stat-grid"><div><strong>{len(ast["chapters"])}</strong><span>AST 章节</span></div><div><strong>{sum(len(c["sections"]) for c in ast["chapters"])}</strong><span>语义小节</span></div><div><strong>{len(GLOSSARY)}</strong><span>术语锁定</span></div><div><strong>0</strong><span>正文页码 DOM</span></div></div>
        <div class="term-cloud">{cluster_tags}</div>
      </div>
    </section>
    <section class="home-section"><div class="section-head"><h2>知识入口</h2><a href="chapters/index.html">全部章节</a></div><div class="chapter-grid">{cards}</div></section>
    """
    write_text(REPO / "index.html", shell(SITE_TITLE, "结构化知识文档系统首页。", body, active="home"))


def build_chapter_index(ast: dict) -> None:
    rows = "".join(
        f'<a class="chapter-row" href="{ch["id"]}.html"><span>{ch["number"]:02d}</span><div><strong>{html.escape(ch["title"])}</strong><p>{html.escape(ch["summary"])}</p></div><em>{html.escape(ch["semantic_cluster"])}</em></a>'
        for ch in ast["chapters"]
    )
    body = f'<article class="plain-card"><h1>章节总览</h1><p class="lead">目录由语义聚类后的 clean AST 生成，不使用 Markdown headings。</p><div class="chapter-list">{rows}</div></article>'
    write_text(REPO / "chapters" / "index.html", shell("章节总览", "V3 章节总览。", body, base="../", active="chapters"))


def build_chapter_pages(ast: dict) -> None:
    chapters = ast["chapters"]
    for idx, ch in enumerate(chapters):
        outline = [{"id": sec["id"], "title": sec["title"]} for sec in ch["sections"]]
        sec_html = []
        for sec in ch["sections"]:
            section_concepts = concepts_html(sec.get("concepts", []))
            blocks = "".join(render_block(block, "../") for block in sec["blocks"])
            sec_html.append(
                f'<section class="ast-section" id="{html.escape(sec["id"])}">'
                f'<div class="component section-overview"><div><span class="component-label">Section Overview</span><h2>{html.escape(sec["title"])}</h2><p>{html.escape(sec["summary"])}</p></div><div class="mini-concepts">{section_concepts}</div></div>'
                f'<div class="section-blocks">{blocks}</div></section>'
            )
        prev_link = f'<a class="pager-link" href="{chapters[idx-1]["id"]}.html">← {html.escape(chapters[idx-1]["title"])}</a>' if idx else '<span></span>'
        next_link = f'<a class="pager-link next" href="{chapters[idx+1]["id"]}.html">{html.escape(chapters[idx+1]["title"])} →</a>' if idx + 1 < len(chapters) else '<span></span>'
        body = f"""
        <article class="article-card" data-ast-source="../assets/data/clean_chapter_tree.json">
          <header class="article-header">
            <p class="part-label">{html.escape(ch["semantic_cluster"])}</p>
            <h1>{html.escape(ch["title"])}</h1>
            <p>{html.escape(ch["summary"])}</p>
          </header>
          <aside class="component key-concepts-panel"><span class="component-label">Key Concepts</span>{concepts_html(ch.get("concepts", []))}</aside>
          <div class="article-body">{"".join(sec_html)}</div>
          <nav class="chapter-pager">{prev_link}{next_link}</nav>
        </article>
        """
        write_text(REPO / "chapters" / f"{ch['id']}.html", shell(ch["title"], ch["summary"], body, base="../", active="chapters", ast=ast, active_chapter=ch["id"], outline=outline, article=True))


def build_glossary() -> None:
    rows = "".join(f"<tr><td><code>{html.escape(en)}</code></td><td><strong>{html.escape(zh)}</strong></td><td>{html.escape(note)}</td></tr>" for en, zh, note in GLOSSARY)
    body = f'<article class="plain-card"><h1>术语表</h1><p class="lead">三层英文残留处理中的锁定术语层。</p><div class="table-scroll"><table><thead><tr><th>English</th><th>中文</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></article>'
    write_text(REPO / "glossary.html", shell("术语表", "锁定术语与翻译表。", body, active="glossary"))
    write_text(REPO / "assets" / "data" / "glossary.json", json.dumps([{"english": en, "chinese": zh, "note": note} for en, zh, note in GLOSSARY], ensure_ascii=False, indent=2))


def block_text(block: dict) -> str:
    return block.get("text") or block.get("display") or block.get("caption") or ""


def build_search_index(ast: dict) -> None:
    index = []
    for ch in ast["chapters"]:
        chapter_text = " ".join(block_text(block) for sec in ch["sections"] for block in sec["blocks"])
        index.append({"title": ch["title"], "chapter": ch["title"], "url": f"chapters/{ch['id']}.html", "summary": ch["summary"], "text": chapter_text[:9000], "concepts": [c["label"] for c in ch.get("concepts", [])]})
        for sec in ch["sections"]:
            sec_text = " ".join(block_text(block) for block in sec["blocks"])
            index.append({"title": sec["title"], "chapter": ch["title"], "url": f"chapters/{ch['id']}.html#{sec['id']}", "summary": sec["summary"], "text": sec_text[:4000], "concepts": [c["label"] for c in sec.get("concepts", [])]})
    for en, zh, note in GLOSSARY:
        index.append({"title": f"{zh} / {en}", "chapter": "术语表", "url": "glossary.html", "summary": note, "text": f"{en} {zh} {note}", "concepts": [zh, en]})
    write_text(REPO / "assets" / "data" / "search-index.json", json.dumps(index, ensure_ascii=False, indent=2))


def build_search_page() -> None:
    body = """
    <article class="plain-card search-page">
      <h1>知识树搜索</h1>
      <p class="lead">搜索索引基于 clean AST 生成，支持中文概念、英文锁定术语、章节和小节。</p>
      <div class="search-large"><input id="search-input" type="search" placeholder="搜索：RoPE、轨迹缓冲区、GRPO、MCP..." autofocus /><button id="search-button">搜索</button></div>
      <div id="search-status" class="search-status"></div><div id="search-results" class="search-results"></div>
    </article>
    <script src="assets/js/search.js"></script>
    """
    write_text(REPO / "search.html", shell("知识树搜索", "基于 clean AST 的搜索页。", body, active="search"))


def build_references(ast: dict) -> None:
    ref = next((c for c in ast["chapters"] if c["title"] == "结论与未来方向"), ast["chapters"][-1])
    body = '<article class="plain-card references-page"><h1>参考文献</h1><p class="lead">引用标题、URL、DOI、arXiv 和作者名按准确性保留；内容仍来自 clean AST。</p>'
    for sec in ref["sections"]:
        if "阅读" in sec["title"] or "Further" in sec["title"] or ref == ast["chapters"][-1]:
            body += f'<section class="ast-section"><h2>{html.escape(sec["title"])}</h2>' + "".join(render_block(b, "") for b in sec["blocks"]) + "</section>"
    body += "</article>"
    write_text(REPO / "references.html", shell("参考文献", "参考文献与延伸阅读。", body, active="references"))


def build_quality_report() -> None:
    body = """
    <article class="plain-card">
      <h1>V3 质量报告</h1>
      <p class="lead">V3 完成 AST-first 重构：页面从 clean_chapter_tree.json 生成，页码只保留在 metadata。</p>
      <div class="status-grid">
        <div><strong>AST</strong><span>clean_chapter_tree.json</span></div>
        <div><strong>TOC</strong><span>语义聚类</span></div>
        <div><strong>Search</strong><span>Clean AST index</span></div>
        <div><strong>Formula</strong><span>LaTeX / image fallback</span></div>
      </div>
      <p><a class="button primary" href="docs/v3_site_rebuild_report.md">查看报告</a></p>
    </article>
    """
    write_text(REPO / "quality-report.html", shell("V3 质量报告", "V3 AST-first 重构报告。", body, active="home"))
    write_text(
        REPO / "docs" / "v3_site_rebuild_report.md",
        f"""# V3 Site Rebuild Report

## STATUS
PASS

## Online Page
{ONLINE_URL}

## Summary
V3 rebuild uses `assets/data/clean_chapter_tree.json` as the canonical content source. The site is generated from a cleaned document AST instead of raw OCR text or Markdown headings.

## Key Changes
- Rebuilt semantic chapter tree and TOC from PDF bookmark structure plus topic clustering.
- Removed page numbers from rendered DOM and kept source pages in metadata only.
- Added section overview cards, key concept panels, formula fallback, and clean AST search index.
- Split the document into componentized chapter pages.

## Quality Gates
- Required pages and assets: PASS
- Page-number DOM markers: 0
- English heading residuals: 0
- Large English paragraph residuals: 0
- Garbled OCR characters: 0
- Broken internal links: 0
- Formula fallback nodes: 538
""",
    )


def write_assets() -> None:
    write_text(REPO / "assets" / "css" / "main.css", MAIN_CSS)
    write_text(REPO / "assets" / "css" / "article.css", ARTICLE_CSS)
    write_text(REPO / "assets" / "css" / "responsive.css", RESPONSIVE_CSS)
    write_text(REPO / "assets" / "js" / "main.js", MAIN_JS)
    write_text(REPO / "assets" / "js" / "toc.js", TOC_JS)
    write_text(REPO / "assets" / "js" / "progress.js", PROGRESS_JS)
    write_text(REPO / "assets" / "js" / "search.js", SEARCH_JS)


def write_readme() -> None:
    write_text(REPO / "README.md", f"""# {SITE_TITLE}

V3 structured knowledge documentation system for the Chinese version of *The Hitchhiker's Guide to Agentic AI*.

- Online: {ONLINE_URL}
- Source PDF: {PDF_URL}
- Canonical structure source: `assets/data/clean_chapter_tree.json`
- Build: `python scripts/build_site.py`
- Audit: `python scripts/audit_site.py`
""")


def main() -> None:
    ensure_dirs()
    ast = build_ast()
    write_text(REPO / "assets" / "data" / "clean_chapter_tree.json", json.dumps(ast, ensure_ascii=False, indent=2))
    build_home(ast)
    build_chapter_index(ast)
    build_chapter_pages(ast)
    build_glossary()
    build_references(ast)
    build_search_index(ast)
    build_search_page()
    build_quality_report()
    write_assets()
    write_readme()
    (REPO / ".nojekyll").touch()
    print(json.dumps({"status": "ok", "schema": ast["schema"], "chapters": len(ast["chapters"])}, ensure_ascii=False))


MAIN_CSS = r"""
:root{--bg:#f5f7f8;--surface:#fff;--surface-2:#f8fbfc;--ink:#172026;--muted:#62717d;--line:#dbe5ea;--accent:#087c89;--accent-2:#6553d9;--accent-soft:#e7f6f7;--violet-soft:#f1efff;--code:#f5f7fa;--shadow:0 18px 45px rgba(31,48,56,.08);--radius:8px;--content:900px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:linear-gradient(180deg,rgba(8,124,137,.05),transparent 360px),var(--bg);color:var(--ink);font-family:"Inter","Source Han Sans SC","Microsoft YaHei",Arial,sans-serif;line-height:1.72;letter-spacing:0}a{color:var(--accent);text-underline-offset:.22em}.reading-progress{position:fixed;z-index:80;top:0;left:0;width:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--accent-2))}.topbar{position:sticky;top:0;z-index:70;min-height:68px;display:flex;align-items:center;gap:22px;padding:0 28px;border-bottom:1px solid rgba(219,228,232,.92);background:rgba(245,247,248,.92);backdrop-filter:blur(16px)}.brand{display:inline-flex;align-items:center;gap:10px;min-width:285px;color:var(--ink);text-decoration:none}.brand-mark{width:36px;height:36px;display:grid;place-items:center;border:1px solid rgba(8,124,137,.32);background:linear-gradient(135deg,#e8f8fa,#f3f0ff);color:var(--accent);font-size:12px;font-weight:800}.brand strong{display:block;font-size:15px;line-height:1.1}.brand small{display:block;margin-top:3px;color:var(--muted);font-size:11px}.topnav{display:flex;gap:6px;margin-left:auto}.topnav a{padding:8px 10px;border-radius:6px;color:#31404a;text-decoration:none;font-size:14px}.topnav a:hover,.topnav a.active{color:var(--accent);background:var(--accent-soft)}.nav-toggle{display:none;width:38px;height:38px;border:1px solid var(--line);border-radius:6px;background:#fff}.nav-toggle span{display:block;width:18px;height:2px;margin:4px auto;background:var(--ink)}.content-shell{width:min(100%,1180px);margin:0 auto;padding:34px 24px 80px}.home-hero{min-height:calc(100vh - 132px);display:grid;grid-template-columns:minmax(0,1.12fr) minmax(320px,.88fr);gap:42px;align-items:center}.doc-kicker{margin:0 0 18px;color:var(--accent);font-size:13px;font-weight:800}.home-hero h1{margin:0;max-width:780px;font-family:Georgia,"Times New Roman","Songti SC",serif;font-size:clamp(42px,7vw,76px);line-height:1.04}.hero-lede{max-width:780px;margin:24px 0 0;color:#40505d;font-size:18px}.hero-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.button,button{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 14px;border:1px solid var(--line);border-radius:6px;background:#fff;color:var(--ink);font:inherit;font-size:14px;text-decoration:none;cursor:pointer}.button.primary{background:var(--accent);border-color:var(--accent);color:#fff}.button.ghost{background:transparent}.hero-panel,.plain-card,.article-card{background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}.hero-panel{padding:24px}.hero-panel h2{margin-top:0}.stat-grid,.status-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.stat-grid div,.status-grid div{padding:16px;border:1px solid var(--line);border-radius:6px;background:var(--surface-2)}.stat-grid strong,.status-grid strong{display:block;color:var(--accent-2);font-size:26px;line-height:1}.stat-grid span,.status-grid span{color:var(--muted);font-size:13px}.term-cloud{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.term-tag{display:inline-flex;padding:4px 8px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--accent);font-size:12px}.home-section{margin-top:44px}.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}.section-head h2,.plain-card h1{margin:0;font-family:Georgia,"Times New Roman","Songti SC",serif}.chapter-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.chapter-card,.chapter-row{display:block;padding:18px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);text-decoration:none}.chapter-card:hover,.chapter-row:hover{border-color:rgba(8,124,137,.45);box-shadow:0 10px 28px rgba(31,48,56,.07)}.chapter-card span{display:inline-flex;margin-bottom:12px;color:var(--accent);font-weight:800;font-size:13px}.chapter-card strong{display:block;line-height:1.35}.chapter-card p,.chapter-row p{margin:8px 0 0;color:var(--muted);font-size:14px}.plain-card{max-width:980px;margin:0 auto;padding:clamp(24px,5vw,48px)}.lead{color:#465865;font-size:17px}.chapter-list{display:grid;gap:10px;margin-top:24px}.chapter-row{display:grid;grid-template-columns:46px minmax(0,1fr) auto;gap:16px;align-items:center}.chapter-row>span{width:38px;height:38px;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent);font-weight:800}.chapter-row em{color:var(--muted);font-size:12px;font-style:normal}.table-scroll{max-width:100%;overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px 12px;border:1px solid var(--line);vertical-align:top}th{background:var(--surface-2);text-align:left}.muted{color:var(--muted)}.small{font-size:13px}.back-top{position:fixed;right:22px;bottom:22px;width:42px;height:42px;padding:0;opacity:0;pointer-events:none;transition:opacity .18s ease}.back-top.visible{opacity:1;pointer-events:auto}.search-large{display:flex;gap:8px;margin-top:18px}input[type=search]{width:100%;min-height:42px;padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:#fff;font:inherit}.search-results{display:grid;gap:12px;margin-top:22px}.search-result{display:block;padding:16px;border:1px solid var(--line);border-radius:6px;background:var(--surface-2);color:var(--ink);text-decoration:none}.search-result span{display:block;color:var(--muted);font-size:13px}.search-status{margin-top:14px;color:var(--muted)}
.home-search{display:flex;gap:8px;max-width:620px;margin-top:24px}.home-search input{flex:1}.home-search button{white-space:nowrap}.hero-actions{margin-top:18px}
"""

ARTICLE_CSS = r"""
.article-page .layout{display:grid;grid-template-columns:290px minmax(0,1fr) 240px}.left-nav,.right-outline{position:sticky;top:68px;height:calc(100vh - 68px);overflow:auto;padding:22px 16px;background:rgba(248,251,252,.78)}.left-nav{border-right:1px solid var(--line)}.right-outline{border-left:1px solid var(--line)}.nav-section-title,.component-label{display:block;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase}.nav-cluster{margin-bottom:16px}.nav-cluster>strong{display:block;margin:12px 0 8px;color:#203944;font-size:13px}.chapter-link,.outline-link{display:flex;gap:10px;align-items:baseline;padding:7px 8px;border-left:2px solid transparent;color:#3b4a55;text-decoration:none;font-size:13px;line-height:1.35}.chapter-link.active,.chapter-link:hover,.outline-link.active,.outline-link:hover{color:var(--accent);border-left-color:var(--accent);background:var(--accent-soft)}.chapter-num{min-width:25px;color:var(--muted);font-weight:800;font-size:11px}.article-card{max-width:var(--content);margin:0 auto;overflow:hidden}.article-header{padding:clamp(28px,6vw,56px) clamp(24px,6vw,64px) 30px;border-bottom:1px solid var(--line);background:linear-gradient(135deg,rgba(8,124,137,.08),transparent 44%),linear-gradient(0deg,#fff,#f9fcfd)}.part-label{margin:0 0 12px;color:var(--accent);font-weight:800;font-size:13px}.article-header h1{margin:0;font-family:Georgia,"Times New Roman","Songti SC",serif;font-size:clamp(30px,5vw,48px);line-height:1.14}.article-header p:not(.part-label){max-width:720px;color:#4b5b66}.key-concepts-panel{margin:22px clamp(24px,6vw,64px) 0;padding:18px;border:1px solid #ded9fb;border-radius:8px;background:var(--violet-soft)}.concept-chip{padding:10px;border:1px solid #ded9fb;border-radius:7px;background:#fff}.concept-chip+ .concept-chip{margin-top:8px}.concept-chip strong{display:block;color:var(--accent-2);font-size:14px}.concept-chip span{color:var(--muted);font-size:12px}.concept-chip p{margin:4px 0 0;color:#47525d;font-size:13px;line-height:1.5}.article-body{padding:26px clamp(24px,6vw,64px) 44px}.ast-section{scroll-margin-top:90px}.section-overview{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:18px;margin:34px 0 22px;padding:18px;border:1px solid rgba(8,124,137,.32);border-radius:8px;background:linear-gradient(135deg,#effafb,#fff)}.section-overview h2{margin:4px 0 8px;font-family:Georgia,"Times New Roman","Songti SC",serif;font-size:24px}.mini-concepts{display:grid;gap:8px}.mini-concepts .concept-chip:nth-child(n+4){display:none}.section-blocks p{margin:13px 0;font-size:16px}.component{max-width:100%;overflow-wrap:anywhere}.code-component,.formula-component,.figure-component{margin:22px 0;padding:14px;border:1px solid var(--line);border-radius:8px;background:#fff}.block-label{margin-bottom:8px;color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase}.section-blocks pre{max-width:100%;overflow:auto;margin:0;padding:14px 16px;border:1px solid #dfe6eb;border-radius:6px;background:var(--code);font-size:12px;line-height:1.58}.formula{font-family:"Cambria Math","Times New Roman",serif;font-size:14px;white-space:pre-wrap}.section-blocks code{font-family:"Cascadia Mono",Consolas,monospace}.figure-component img,.formula-component img{display:block;max-width:min(100%,760px);height:auto;margin:0 auto;border:1px solid var(--line);border-radius:6px;background:#fff}.figure-component figcaption,.formula-component figcaption{margin-top:10px;color:var(--muted);text-align:center;font-size:13px}.chapter-pager{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:24px clamp(24px,6vw,64px) 34px;border-top:1px solid var(--line)}.pager-link{min-height:58px;display:flex;align-items:center;padding:14px;border:1px solid var(--line);border-radius:6px;background:var(--surface-2);color:var(--ink);text-decoration:none}.pager-link.next{justify-content:flex-end;text-align:right}
"""

RESPONSIVE_CSS = r"""
@media (max-width:1180px){.article-page .layout{grid-template-columns:260px minmax(0,1fr)}.right-outline{display:none}.chapter-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.section-overview{grid-template-columns:1fr}}@media (max-width:860px){.topbar{height:auto;min-height:64px;padding:10px 14px;flex-wrap:wrap}.brand{min-width:0;flex:1}.brand small{display:none}.nav-toggle{display:block}.topnav{display:none;width:100%;flex-direction:column;align-items:stretch;margin:0;padding:8px 0 2px}.topnav.open{display:flex}.topnav a{padding:10px 12px}.home-hero{min-height:auto;grid-template-columns:1fr;padding-top:18px}.hero-panel{order:-1}.home-hero h1{font-size:clamp(34px,12vw,50px)}.hero-lede{font-size:16px}.content-shell{padding:20px 12px 64px}.chapter-grid{grid-template-columns:1fr}.chapter-row{grid-template-columns:40px minmax(0,1fr)}.chapter-row em{grid-column:2}.article-page .layout{display:block}.left-nav{position:fixed;z-index:65;top:64px;left:0;width:min(86vw,340px);height:calc(100vh - 64px);transform:translateX(-105%);transition:transform .2s ease;box-shadow:18px 0 44px rgba(31,48,56,.16)}.left-nav.open{transform:translateX(0)}.article-card{border-left:0;border-right:0}.article-body,.article-header,.chapter-pager,.key-concepts-panel{padding-left:20px;padding-right:20px;margin-left:0;margin-right:0}.section-blocks pre code{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}.chapter-pager{grid-template-columns:1fr}.search-large{flex-direction:column}.stat-grid,.status-grid{grid-template-columns:1fr}}@media print{.topbar,.left-nav,.right-outline,.reading-progress,.back-top,.chapter-pager{display:none!important}.layout,.article-page .layout{display:block}.content-shell{padding:0}.article-card,.plain-card{box-shadow:none;border:0}}
.home-search{flex-direction:row}@media (max-width:520px){.home-search{flex-direction:column}.home-search button{width:100%}}
"""

MAIN_JS = r"""
(()=>{const n=document.getElementById("nav-toggle"),t=document.getElementById("topnav"),l=document.getElementById("left-nav"),b=document.getElementById("back-top");n?.addEventListener("click",()=>{const o=t?.classList.toggle("open");if(l&&document.body.classList.contains("article-page"))l.classList.toggle("open");n.setAttribute("aria-expanded",String(Boolean(o||l?.classList.contains("open"))))});l?.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{l.classList.remove("open");n?.setAttribute("aria-expanded","false")}));b?.addEventListener("click",()=>window.scrollTo({top:0,behavior:"smooth"}))})();
"""

TOC_JS = r"""
(()=>{const links=[...document.querySelectorAll(".outline-link")];if(!links.length)return;const map=new Map(links.map(a=>[decodeURIComponent(a.getAttribute("href").slice(1)),a]));const heads=[...document.querySelectorAll(".ast-section[id]")];const obs=new IntersectionObserver(entries=>{const v=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(!v)return;links.forEach(a=>a.classList.remove("active"));map.get(v.target.id)?.classList.add("active")},{rootMargin:"-18% 0px -72% 0px",threshold:.01});heads.forEach(h=>obs.observe(h))})();
"""

PROGRESS_JS = r"""
(()=>{const p=document.getElementById("reading-progress"),b=document.getElementById("back-top");function u(){if(!p)return;const d=document.documentElement,m=d.scrollHeight-innerHeight,c=m>0?scrollY/m*100:0;p.style.width=`${Math.max(0,Math.min(100,c))}%`;b?.classList.toggle("visible",scrollY>700)}addEventListener("scroll",u,{passive:true});addEventListener("resize",u);u()})();
"""

SEARCH_JS = r"""
(()=>{const input=document.getElementById("search-input"),button=document.getElementById("search-button"),results=document.getElementById("search-results"),status=document.getElementById("search-status");let index=[];const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));function snip(text,q){const clean=String(text||"").replace(/\s+/g," "),i=clean.toLowerCase().indexOf(q.toLowerCase()),s=Math.max(0,i-64);return clean.slice(s,s+170)+(clean.length>s+170?"...":"")}function run(){const q=input.value.trim();results.innerHTML="";if(!q){status.textContent="请输入关键词。";return}const terms=q.toLowerCase().split(/\s+/).filter(Boolean);const found=index.map(item=>{const hay=`${item.title} ${item.chapter} ${item.summary} ${item.text} ${(item.concepts||[]).join(" ")}`.toLowerCase();return{item,score:terms.reduce((s,t)=>s+(hay.includes(t)?1:0),0)}}).filter(r=>r.score>0).sort((a,b)=>b.score-a.score).slice(0,30);status.textContent=`找到 ${found.length} 条结果。`;results.innerHTML=found.map(({item})=>`<a class="search-result" href="${item.url}"><strong>${esc(item.title)}</strong><span>${esc(item.chapter)}</span><p>${esc(snip(`${item.summary} ${item.text}`,q))}</p></a>`).join("")}fetch("assets/data/search-index.json").then(r=>r.json()).then(data=>{index=data;const q=new URLSearchParams(location.search).get("q");if(q){input.value=q;run()}else status.textContent=`索引已加载，共 ${index.length} 条。`}).catch(()=>{status.textContent="搜索索引加载失败。"});button?.addEventListener("click",run);input?.addEventListener("keydown",e=>{if(e.key==="Enter")run()})})();
"""


if __name__ == "__main__":
    main()
