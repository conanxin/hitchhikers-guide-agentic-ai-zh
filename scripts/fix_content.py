from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ALLOWED_ACRONYMS = {
    "AI", "LLM", "API", "GPU", "CPU", "CUDA", "BPE", "RL", "SFT", "RAG",
    "DPO", "GRPO", "MDP", "PPO", "SGD", "ADAM", "ADAMW", "TRANSFORMER",
    "TOKEN", "ROPE", "VLLM", "FLASHATTENTION", "HUGGING", "FACE", "ARXIV",
    "DOI", "URL", "MCP", "A2A", "KV", "MLP", "RLHF", "RLVR", "TP", "PP",
    "DP", "FSDP", "DDP", "LORA", "QLORA", "PEFT", "MOE", "ICLR", "ACL",
    "NEURIPS", "ICML", "SOSP", "FASTAPI", "REACT", "LANGGRAPH",
}


TERM_REPLACEMENTS = [
    ("法学硕士", "LLM"),
    ("大型语言模型的强化学习", "LLM 的强化学习"),
    ("智能体工智能", "智能体式 AI"),
    ("代理式 AI", "智能体式 AI"),
    ("代理人工智能", "智能体式 AI"),
    ("代理式人工智能", "智能体式 AI"),
    ("智能体人工智能", "智能体式 AI"),
    ("智能人工智能", "智能体式 AI"),
    ("大语言模型", "大型语言模型"),
    ("变形金刚", "Transformer"),
    ("变压器", "Transformer"),
    ("令牌化", "分词 / 标记化"),
    ("标记化", "分词 / 标记化"),
    ("国家数据化", "分词 / 标记化"),
    ("代币化", "分词 / 标记化"),
    ("代币", "token"),
    ("令牌", "token"),
    ("词元", "token"),
    ("字节对编码", "字节对编码（BPE）"),
    ("自我注意力", "自注意力"),
    ("自注意力力", "自注意力"),
    ("注意力力", "注意力"),
    ("多头注意力力", "多头注意力"),
    ("管道并行性", "流水线并行"),
    ("嵌入式", "嵌入"),
    ("预先训练", "预训练"),
    ("国家数据化", "分词 / 标记化"),
    ("字级模型", "字符级模型"),
    ("代理", "智能体"),
    ("自主智能体式 AI系统", "智能体式 AI 系统"),
    ("智能体式 AI系统", "智能体式 AI 系统"),
    ("Transformer模型", "Transformer 模型"),
    ("tokenID", "token ID"),
    ("GPU内存", "GPU 内存"),
    ("KV缓存", "KV 缓存"),
    ("logits标记", "token"),
    ("思路链", "思维链"),
    ("对准", "对齐"),
    ("线束", "执行框架"),
]


TITLE_TRANSLATIONS = {
    "Disclaimer": "免责声明",
    "About the Author": "关于作者",
    "Preface": "前言",
    "Introduction": "简介",
    "I Foundations": "第一部分：基础",
    "II RL Methods for LLMs": "第二部分：LLM 的强化学习方法",
    "III Reasoning": "第三部分：推理",
    "IV Evaluation": "第四部分：评估",
    "V Agentic AI": "第五部分：智能体式 AI",
    "VI Assessment & Reference": "第六部分：测验与参考",
    "LLM Architecture and Optimization Methods": "LLM 架构和优化方法",
    "Systems Foundations for LLMs": "LLM 的系统基础",
    "Introduction to Reinforcement Learning": "强化学习简介",
    "RL Foundations for Language Models": "语言模型的强化学习基础",
    "PPO - Proximal Policy Optimization": "PPO：近端策略优化",
    "PPO бк Proximal Policy Optimization": "PPO：近端策略优化",
    "DPO - Direct Preference Optimization": "DPO：直接偏好优化",
    "DPO бк Direct Preference Optimization": "DPO：直接偏好优化",
    "GRPO - Group Relative Policy Optimization": "GRPO：组相对策略优化",
    "GRPO бк Group Relative Policy Optimization": "GRPO：组相对策略优化",
    "Preference Optimization Variants": "偏好优化变体",
    "Reward Model Training": "奖励模型训练",
    "SFT Best Practices and Techniques": "SFT 最佳实践与技术",
    "System Architecture & Infrastructure at Scale": "大规模系统架构与基础设施",
    "LLM Agentic Training": "LLM 智能体训练",
    "RL for Large Reasoning Models": "大型推理模型的强化学习",
    "LLM Evaluation": "LLM 评估",
    "Introduction to Agentic AI": "智能体式 AI 简介",
    "Retrieval-Augmented Generation (RAG)": "检索增强生成（RAG）",
    "Agentic Memory Systems": "智能体记忆系统",
    "Agent Harness - Context Management and Orchestration": "智能体执行框架：上下文管理与编排",
    "Agent Harness иC Context Management and Orchestration": "智能体执行框架：上下文管理与编排",
    "Agent Design Patterns": "智能体设计模式",
    "Agentic Environments and Benchmarks": "智能体环境与基准",
    "Model Context Protocol (MCP)": "模型上下文协议（MCP）",
    "Agent Skills": "智能体技能",
    "Agent-to-Agent Communication (A2A)": "智能体间通信（A2A）",
    "Multi-Agent Systems": "多智能体系统",
    "Agent Development Frameworks": "智能体开发框架",
    "Agentic UI Frameworks": "智能体式 UI 框架",
    "Quiz Questions & Detailed Answers": "测验题与详解",
    "Quick Reference": "速查表",
    "Conclusion and Future Directions": "结论与未来方向",
    "How LLMs Work: An Intuitive Overview": "LLM 如何工作：直观概览",
    "Tokenization": "分词 / 标记化",
    "Why Not Characters or Words?": "为什么不是字符或单词？",
    "Byte-Pair Encoding (BPE)": "字节对编码（BPE）",
    "Other Tokenization Methods": "其他分词方法",
    "Tokenization Best Practices": "分词最佳实践",
    "Tokenization in Practice: HuggingFace Example": "实践中的分词：Hugging Face 示例",
    "Special Tokens and Structured Prompts": "特殊 token 与结构化提示",
    "The Transformer Architecture": "Transformer 架构",
    "High-Level Structure": "高层结构",
    "Original Encoder-Decoder Transformer": "原始编码器-解码器 Transformer",
    "Decoder-Only vs. Encoder-Decoder": "仅解码器与编码器-解码器",
    "Embeddings: From Discrete Tokens to Continuous Space": "嵌入：从离散 token 到连续空间",
    "Self-Attention Mechanism": "自注意力机制",
    "Multi-Head Attention": "多头注意力",
    "Positional Encoding": "位置编码",
    "RoPE: Rotary Position Embedding": "RoPE：旋转位置嵌入",
    "Feed-Forward Network (MLP)": "前馈网络（MLP）",
    "Layer Normalization": "层归一化",
    "Model Size Reference": "模型规模参考",
    "Attention Pathologies": "注意力异常",
    "Prediction Heads: What Transformers Output": "预测头：Transformer 输出什么",
    "Optimization Theory for LLM Training": "LLM 训练的优化理论",
    "Gradient Descent: Basics": "梯度下降：基础",
    "Why Vanilla SGD Fails for LLMs": "为什么普通 SGD 不适合 LLM",
    "Learning Rate - The Most Important Hyperparameter": "学习率：最重要的超参数",
    "Flash Attention": "FlashAttention",
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
    "Summary": "小结",
    "Further Reading": "延伸阅读",
}


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
    "Weight Tying: LM Head = Embedding Matrix Transposed": "权重绑定：语言模型头等于嵌入矩阵的转置",
    "Listing 1.3: Loading and using different prediction heads with HuggingFace.": "清单 1.3：在 Hugging Face 中加载并使用不同的预测头。",
    "FSDP communicates 3× more data than DDP per step:": "FSDP 每一步通信的数据量约为 DDP 的 3 倍：",
    "Only for critical applications": "仅适用于关键应用",
    "Diminishing returns start": "收益开始递减",
    "Strong. Often matches PPO quality": "效果很强，通常可接近 PPO 质量",
    "Derivation of the gradient:": "梯度推导：",
    "where M is the message size (bytes) and N is the number of participants.": "其中 M 是消息大小（字节），N 是参与方数量。",
    "condition that marginal return per FLOP is equalized between training and inference:": "最优条件是：训练与推理之间每个 FLOP 的边际收益相等。",
}


BLOCK_REPLACEMENTS = [
    (
        "Most modern LLMs tie the LM head weights with the input embedding matrix: lm_head.weight =\nmodel.embed_tokens.weight。 This means the LM head is not a separately learned layer—it reuses\n嵌入表。优点：更少的参数（|V| × d 保存）、更好的泛化能力以及\ngeometric structure of the embedding space directly determines token probabilities.您可以验证\nthis in HuggingFace: model.lm_head.weight is model.model.embed_tokens.weight returns\n对于大多数型号都是如此。",
        "大多数现代 LLM 会将语言模型头的权重与输入嵌入矩阵绑定：`lm_head.weight = model.embed_tokens.weight`。这意味着 LM 头不是一个单独学习的层，而是复用嵌入表。优点包括：参数更少（节省 |V| × d）、泛化更好，并且嵌入空间的几何结构会直接决定 token 概率。你可以在 Hugging Face 中验证：对多数模型而言，`model.lm_head.weight is model.model.embed_tokens.weight` 会返回 true。",
    ),
    (
        "A100 specs: 312 TFLOPS (BF16 tensor cores), 2 TB/s HBM bandwidth.\nRoofline 交叉：312T/2T = 156 FLOP/字节。",
        "A100 规格：312 TFLOPS（BF16 Tensor Core）和 2 TB/s HBM 带宽。Roofline 交叉点为 312T/2T = 156 FLOP/字节。",
    ),
    (
        "Autoregressive generation: For each token, read all weights (140GB for 70B) and do 2× 70B =\n140G FLOPs per token (at batch=1).\nArithmetic intensity: 140G FLOP/140GB = 1 FLOP/byte.这是屋顶线以下 156 倍！\nUtilization: 1/156 = 0.6% of peak FLOPS utilized. GPU 99.4% 空闲，正在等待内存\n读。\nToken rate: 2TB/s/140GB = 14.3 tokens/second (single stream, batch=1).",
        "自回归生成：对每个 token，都需要读取全部权重（70B 模型约 140GB），并执行 2 × 70B = 每 token 140G FLOPs（batch=1）。算术强度为 140G FLOP / 140GB = 1 FLOP/字节，比 Roofline 交叉点低 156 倍。利用率为 1/156 = 峰值 FLOPS 的 0.6%，GPU 约 99.4% 的时间在等待内存读取。token 速率为 2TB/s / 140GB = 14.3 token/s（单流，batch=1）。",
    ),
    (
        "Speculative decoding [143] (2–3×): Small draft model proposes 5 tokens, large model verifies\nin one forward pass.平均接受 3-4 个。",
        "推测解码 [143]（2–3×）：小型草稿模型先提出 5 个 token，大模型在一次前向传递中验证，平均接受 3–4 个。",
    ),
    (
        "Table 11.2: Memory comparison: DDP vs FSDP/ZeRO stages (70B model, 8 GPUs).基线：BF16 参数\n(140 GB) + BF16 grads (140 GB) + FP32 master+m+v (840 GB) = 1120 GB per GPU.",
        "表 11.2：DDP 与 FSDP/ZeRO 各阶段的内存比较（70B 模型，8 块 GPU）。基线：BF16 参数（140 GB）+ BF16 梯度（140 GB）+ FP32 master+m+v（840 GB）= 每块 GPU 1120 GB。",
    ),
    (
        "Let Lt = min(rt ˆAt, ¯rt ˆAt) where ¯rt = clip(rt, 1−ϵ, 1+ϵ).",
        "令 Lt = min(rt ˆAt, ¯rt ˆAt)，其中 ¯rt = clip(rt, 1−ϵ, 1+ϵ)。",
    ),
]


POST_TRANSLATION_REPLACEMENTS = [
    ("大型语言模型", "大型语言模型"),
    ("自主代理", "自主智能体"),
    ("代理", "智能体"),
    ("令牌", "token"),
    ("标记", "token"),
    ("嵌入矩阵转置", "嵌入矩阵的转置"),
    ("拥抱脸", "Hugging Face"),
    ("近端政策优化", "近端策略优化"),
    ("政策", "策略"),
    ("轨迹缓冲器", "轨迹缓冲区"),
    ("奖励模型", "奖励模型"),
]


def normalize_terms(text: str) -> str:
    for old, new in BLOCK_REPLACEMENTS:
        text = text.replace(old, new)
    for old, new in TERM_REPLACEMENTS:
        text = text.replace(old, new)
    text = re.sub(r"(?<![A-Za-z])HuggingFace(?![A-Za-z])", "Hugging Face", text)
    text = text.replace("Flash Attention", "FlashAttention")
    text = text.replace("Paged Attention", "PagedAttention")
    text = text.replace("智能体式 AI的", "智能体式 AI 的")
    text = text.replace("LLM服务", "LLM 服务")
    text = text.replace("LLM服务化", "LLM 服务化")
    text = text.replace("多智能体", "多智能体")
    return text


def clean_toc_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = title.replace("бк", "-").replace("иC", "-").replace("–", "-").replace("—", "-")
    title = re.sub(r"\s+-\s+", " - ", title)
    title = TITLE_TRANSLATIONS.get(title, title)
    title = normalize_terms(title)
    return title


def postprocess_translation(text: str) -> str:
    for old, new in POST_TRANSLATION_REPLACEMENTS:
        text = text.replace(old, new)
    text = normalize_terms(text)
    return text


def is_reference_line(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r"^\[?\d{1,3}\]|\barXiv\b|\bDOI\b|https?://", stripped, re.I))


def is_code_like(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    code_markers = [
        "=", "==", "!=", "<|", "|>", "->", "=>", "::", "{", "}", ";",
        "import ", "from ", "def ", "class ", "return ", "print(", "torch.",
        "model.", "tokenizer.", "dataset", "Config(", "lambda ", "self.",
        "()", "**", ".py", "json", "yaml", "http://", "https://",
    ]
    if any(marker in stripped for marker in code_markers):
        return True
    if re.search(r"[A-Za-z_]+\([^\)]*\)", stripped):
        return True
    if len(re.findall(r"[A-Za-z_]+", stripped)) > 0 and len(re.findall(r"[_./=(){}\[\]]", stripped)) >= 2:
        return True
    return False


def looks_like_english_prose(line: str) -> bool:
    stripped = re.sub(r"^[#>*\-\s\d\.\)]+", "", line.strip())
    stripped = stripped.strip()
    if len(stripped) < 24:
        return False
    if is_reference_line(stripped) or is_code_like(stripped):
        return False
    ascii_letters = sum(1 for c in stripped if c.isalpha() and ord(c) < 128)
    han = sum(1 for c in stripped if "\u4e00" <= c <= "\u9fff")
    words = re.findall(r"[A-Za-z][A-Za-z\-']+", stripped)
    meaningful = [w for w in words if w.upper() not in ALLOWED_ACRONYMS]
    if len(meaningful) < 4:
        return False
    return ascii_letters >= 24 and ascii_letters > max(30, han * 1.8)


def load_cache(cache_path: Path) -> dict[str, str]:
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_cache(cache_path: Path, cache: dict[str, str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def translate_online(text: str, cache: dict[str, str], cache_path: Path | None = None) -> str:
    key = text.strip()
    if not key:
        return text
    if key in PHRASE_TRANSLATIONS:
        return PHRASE_TRANSLATIONS[key]
    if key in cache:
        return cache[key]
    quoted = urllib.parse.quote(key)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={quoted}"
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        translated = "".join(part[0] for part in payload[0] if part and part[0])
        translated = postprocess_translation(translated)
        if translated:
            cache[key] = translated
            if cache_path is not None and len(cache) % 20 == 0:
                save_cache(cache_path, cache)
            time.sleep(0.04)
            return translated
    except Exception:
        return text
    return text


def fix_residual_english(text: str, cache_path: Path, enable_online: bool = True) -> str:
    cache = load_cache(cache_path)
    out: list[str] = []
    in_fence = False
    fence_lang = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                fence_lang = stripped[3:].strip().lower()
                in_fence = True
            else:
                fence_lang = ""
                in_fence = False
            out.append(line)
            continue

        fixed = line
        for old, new in PHRASE_TRANSLATIONS.items():
            fixed = fixed.replace(old, new)

        can_translate = looks_like_english_prose(fixed)
        if in_fence and fence_lang not in {"", "text", "math"}:
            can_translate = False
        if in_fence and is_code_like(fixed):
            can_translate = False

        if enable_online and can_translate:
            prefix_match = re.match(r"^(\s*(?:[>*\-•]\s*)?)", fixed)
            prefix = prefix_match.group(1) if prefix_match else ""
            body = fixed[len(prefix):].strip()
            translated = translate_online(body, cache, cache_path)
            if translated != body:
                fixed = prefix + translated

        out.append(fixed)

    save_cache(cache_path, cache)
    return "\n".join(out) + "\n"


def clean_markdown_text(text: str, cache_path: Path | None = None, enable_online: bool = True) -> str:
    text = normalize_terms(text)
    text = text.replace("\ufffd", "")
    text = re.sub(r"[\u25a1]{2,}", "[公式符号缺失]", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    if cache_path is not None:
        text = fix_residual_english(text, cache_path, enable_online=enable_online)
    return normalize_terms(text)
