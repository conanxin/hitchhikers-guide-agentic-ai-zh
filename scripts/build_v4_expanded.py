from __future__ import annotations

import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
SITE = REPO / "site-v4"

AST_PATH = REPO / "assets" / "data" / "clean_chapter_tree.json"
SOURCE_TEXT = ROOT / "extracted" / "source_text.md"
TRANSLATED_MD = ROOT / "translated" / "document.zh.md"
SOURCE_PDF = ROOT / "source" / "2606.24937v1.pdf"

ONLINE_STABLE = "https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/"
PDF_URL = "https://arxiv.org/pdf/2606.24937v1"
TITLE = "智能体式 AI 中文重编版"
SUBTITLE = "面向学习者的 Agentic AI 在线教材"


GLOSSARY = [
    ("智能体式 AI", "Agentic AI", "能够设定目标、使用工具、记忆上下文并与环境多步交互的 AI 系统。"),
    ("智能体", "Agent", "能观察状态、选择行动、调用工具并根据反馈调整行为的系统单元。"),
    ("大型语言模型", "Large Language Model / LLM", "以大规模文本训练得到的序列生成模型，是智能体系统的语言与推理底座。"),
    ("标记", "Token", "模型处理文本的基本离散单元，可以是字、子词、符号或字节片段。"),
    ("分词", "Tokenization", "把文本切分并映射成 token 序列的过程。"),
    ("Transformer", "Transformer", "以注意力机制为核心的序列建模架构。"),
    ("注意力", "Attention", "根据查询、键和值计算上下文加权表示的机制。"),
    ("旋转位置嵌入", "Rotary Position Embedding / RoPE", "通过旋转变换向注意力表示注入相对位置信息的方法。"),
    ("监督微调", "Supervised Fine-Tuning / SFT", "用示范数据让模型学习回答格式、任务风格和基础指令遵循能力。"),
    ("人类反馈强化学习", "Reinforcement Learning from Human Feedback / RLHF", "用偏好数据和奖励信号优化模型行为的训练流程。"),
    ("近端策略优化", "Proximal Policy Optimization / PPO", "通过裁剪目标限制策略更新幅度的强化学习算法。"),
    ("直接偏好优化", "Direct Preference Optimization / DPO", "不显式训练奖励模型，直接用偏好对优化策略的方法。"),
    ("组相对策略优化", "Group Relative Policy Optimization / GRPO", "在同一提示的一组候选回答内做相对优势估计的偏好优化方法。"),
    ("检索增强生成", "Retrieval-Augmented Generation / RAG", "先检索外部知识，再把检索结果作为上下文交给模型生成答案。"),
    ("模型上下文协议", "Model Context Protocol / MCP", "连接模型应用与工具、数据源和上下文服务的开放协议。"),
    ("智能体间通信", "Agent-to-Agent / A2A", "智能体之间交换任务、状态、结果和能力描述的通信机制。"),
    ("奖励模型", "Reward Model", "把候选输出映射成偏好或质量分数的模型。"),
    ("轨迹", "Trajectory", "智能体与环境交互产生的观察、动作、工具调用和反馈序列。"),
]


LESSON_BLUEPRINTS = [
    {
        "slug": "chapter-01",
        "title": "导读：什么是智能体式 AI",
        "subtitle": "从聊天模型走向能执行任务的系统",
        "sources": ["chapter-01", "chapter-16"],
        "stage": "入门",
        "objectives": ["区分聊天模型、工作流和智能体", "理解智能体式 AI 的基本循环", "建立后续学习的全局地图"],
        "sections": [
            ("为什么需要重编版", "原 PDF 覆盖了模型架构、强化学习、系统工程和智能体协议，信息量很大。V4 不再逐页翻译，而是把这些材料重新编成学习路径：先理解 LLM，再理解训练方法，最后进入智能体系统。"),
            ("智能体式 AI 的核心循环", "智能体式 AI（Agentic AI）不是只回答一句话的模型，而是围绕目标反复经历“观察、思考、行动、反馈”的循环。工具调用、记忆、检索、环境交互和评估共同决定它能否稳定完成任务。"),
            ("从模型到系统", "LLM 提供语言理解和生成能力；强化学习和偏好优化塑造行为；RAG、记忆和工具让模型接触外部世界；评估、安全和部署则决定系统能不能被可靠使用。"),
        ],
        "table": ("三类 AI 形态", ["形态", "主要能力", "局限"], [
            ["聊天模型", "根据上下文生成回答", "通常不主动规划和执行多步任务"],
            ["工作流", "按固定流程调用模型和工具", "灵活性依赖预先写好的流程"],
            ["智能体", "能根据目标选择步骤、工具和记忆", "更需要评估、权限控制和失败恢复"],
        ]),
        "formula": "本章没有必须掌握的数学公式。可以先把智能体理解为一个不断更新状态并选择动作的闭环系统。",
        "summary": ["智能体式 AI 是模型能力和系统能力的结合。", "学习路线应先打牢 LLM 与强化学习基础，再进入智能体协议和部署。"],
        "questions": ["一个普通聊天机器人和一个智能体的边界在哪里？", "如果工具调用失败，智能体需要哪些恢复机制？"],
        "reading": ["原 PDF 中 Agentic AI 简介相关章节", "V3 clean AST 中 chapter-16 的语义结构"],
    },
    {
        "slug": "chapter-02",
        "title": "LLM 基础：Token、Transformer 与推理",
        "subtitle": "理解大语言模型如何把文本变成下一个 token",
        "sources": ["chapter-02"],
        "stage": "模型基础",
        "objectives": ["理解 token、分词与标记化的关系", "掌握 Transformer 的基本数据流", "理解 RoPE、KV cache 与 FlashAttention 在推理中的作用"],
        "sections": [
            ("分词与标记化", "大型语言模型（Large Language Model / LLM）不能直接处理自然语言字符串，它会先通过分词 / 标记化（Tokenization）把文本转换成 token 序列。一个 token 可能是一个汉字、一个词的一部分、一个空格加单词片段，也可能是特殊控制符。字节对编码（Byte Pair Encoding / BPE）这类子词方法，会在词表规模、未知词覆盖和压缩效率之间折中。"),
            ("Transformer 的信息流", "Transformer 先把 token 映射为向量，再通过多层注意力（Attention）和前馈网络反复更新表示。注意力可以理解为：当前位置提出查询（Query），上下文位置提供键（Key）和值（Value），模型根据相关性加权汇总信息，最后由语言模型头（LM Head）给出下一个 token 的概率分布。"),
            ("RoPE 如何表达位置", "旋转位置嵌入（Rotary Position Embedding / RoPE）不是把“第几个位置”作为普通特征拼进去，而是在注意力计算前对查询和键做位置相关的旋转。这样模型在比较两个 token 时，会自然感知相对距离。学习时先把 RoPE 理解为“让注意力知道相对位置的旋转操作”，完整推导可回到原 PDF 核对。"),
            ("推理为什么慢", "自回归生成一次只产生一个 token。新 token 会追加到上下文里，再触发下一轮前向计算。KV cache 会保存历史 token 的 Key/Value，避免每一步都重新计算整段上下文；批处理和调度器则把多个请求合并，提高 GPU 利用率。"),
            ("FlashAttention 为什么快", "FlashAttention 的核心不是改变注意力结果，而是改变计算和访存方式。它把注意力矩阵分块放入更快的片上存储中计算，减少对 HBM 的读写，并用数值稳定的在线 softmax 避免保存完整注意力矩阵。因此它通常能在长上下文场景显著降低显存占用和延迟。"),
        ],
        "table": ("LLM 基础组件", ["组件", "作用", "学习提示"], [
            ["Tokenizer / 分词器", "把文本切成 token，并处理特殊控制符", "关注词表、特殊 token 和中英文混合文本"],
            ["Embedding / 嵌入层", "把 token 映射为向量", "理解向量空间中的相似性"],
            ["Attention / 注意力", "聚合上下文信息", "理解 Query、Key、Value 的关系"],
            ["RoPE / 旋转位置嵌入", "把相对位置信息注入注意力", "把它看成位置相关的向量旋转即可"],
            ["FlashAttention", "减少注意力计算的 HBM 读写", "它是精确注意力的高效实现，不是近似算法"],
            ["LM Head / 语言模型头", "输出词表概率", "连接隐藏状态与下一个 token"],
        ]),
        "formula": "注意力的简化形式可以写作 softmax(QK^T / sqrt(d))V：Q 和 K 决定相关性，V 提供要汇总的信息。RoPE 可以理解为先按位置旋转 Q 与 K，再做同样的注意力计算；完整数学推导请参考原 PDF。",
        "summary": ["LLM 的最小主线是 token → embedding → Transformer → LM head。", "RoPE 解决位置信息，KV cache 减少重复计算，FlashAttention 减少显存读写。"],
        "questions": ["为什么中文文档里的 token 不一定等于一个汉字？", "KV cache 主要节省了哪部分重复计算？", "FlashAttention 为什么能在不近似结果的情况下更快？"],
        "reading": ["Transformer 架构", "RoPE 位置编码", "FlashAttention 与解码方法"],
    },
    {
        "slug": "chapter-03",
        "title": "LLM 系统基础：GPU、显存、并行与服务化",
        "subtitle": "从模型算法走向可运行的基础设施",
        "sources": ["chapter-03", "chapter-12"],
        "stage": "系统基础",
        "objectives": ["理解 GPU、HBM、SM、CUDA 与 NVLink 的分工", "理解显存为何是 LLM 系统瓶颈", "区分并行训练和服务化推理的核心取舍"],
        "sections": [
            ("GPU 是并行计算机器", "GPU 由大量流式多处理器（Streaming Multiprocessor / SM）组成，适合执行矩阵乘法、注意力和归一化等高度并行计算。CUDA 是开发和调度 GPU 计算的编程体系，Tensor Core 则专门加速低精度矩阵运算。"),
            ("HBM 与互联决定上限", "高带宽显存（High Bandwidth Memory / HBM）提供模型权重、激活和 KV cache 的主要存储空间。NVLink 或 PCIe 决定多卡之间交换数据的速度：张量并行和流水线并行越依赖跨卡通信，互联瓶颈越明显。"),
            ("显存是第一约束", "大模型部署时，参数、激活、优化器状态、KV cache 都会占用显存。训练时还要保存梯度和优化器状态；推理时重点关注权重加载、KV cache 与并发请求。上下文越长、并发越高，KV cache 越容易成为主要压力。"),
            ("并行策略怎么选", "数据并行适合扩展 batch；张量并行把单层矩阵计算切到多卡；流水线并行把模型层切段。真实系统通常会组合这些方法，再用 ZeRO/FSDP 降低冗余显存。选择并行方式时，要同时看显存、通信、吞吐和工程复杂度。"),
            ("服务化关注什么", "服务化不只是把模型放到 API 后面。调度器、动态批处理、KV cache 管理、限流、监控和故障恢复共同决定用户体验与成本。vLLM 的 PagedAttention 把 KV cache 像分页内存一样管理，能减少碎片并提升高并发吞吐。"),
        ],
        "table": ("LLM 系统硬件与运行时要点", ["对象", "主要作用", "容易成为瓶颈的地方"], [
            ["GPU / SM", "执行大规模并行矩阵计算和注意力计算", "kernel 调度、算子融合和低利用率会浪费算力"],
            ["Tensor Core", "加速 FP16、BF16、FP8 等低精度矩阵乘法", "精度格式、对齐和算子支持会影响实际吞吐"],
            ["HBM", "存放权重、激活、KV cache 和运行时缓冲", "容量不足会限制模型大小、上下文长度和并发数"],
            ["NVLink / PCIe", "负责多 GPU 之间通信", "张量并行、流水线并行和权重同步会放大互联压力"],
            ["CUDA / Runtime", "把模型算子调度到 GPU 上执行", "kernel 启动开销、内存拷贝和同步点会造成延迟"],
            ["vLLM / PagedAttention", "管理 KV cache 并提高推理吞吐", "需要配合请求调度、批处理和显存预算使用"],
        ]),
        "formula": "推理显存可以用“权重显存 + KV cache + 临时缓冲 + 框架开销”估算。KV cache 近似随 batch size、上下文长度、层数、头数和每个元素字节数线性增长，因此长上下文和高并发会迅速推高显存需求。",
        "summary": ["训练和推理的瓶颈不同，不能用同一套直觉处理。", "LLM 服务化是 GPU 算力、HBM 容量、互联带宽和调度策略的综合工程。"],
        "questions": ["为什么 batch 变大可能提高吞吐但增加单请求延迟？", "什么时候张量并行比数据并行更必要？", "为什么长上下文服务经常先撞到 KV cache 显存瓶颈？"],
        "reading": ["vLLM 与 PagedAttention", "GPU/HBM/NVLink 架构基础", "大规模系统架构与基础设施"],
    },
    {
        "slug": "chapter-04",
        "title": "强化学习基础",
        "subtitle": "用状态、动作和奖励描述学习问题",
        "sources": ["chapter-04"],
        "stage": "训练基础",
        "objectives": ["理解 MDP、策略和价值函数", "区分在线策略与离线策略", "理解奖励设计为什么困难"],
        "sections": [
            ("MDP 是统一语言", "马尔可夫决策过程（Markov Decision Process / MDP）把问题拆成状态、动作、转移、奖励和折扣。它为后续把语言模型输出看作动作序列提供了统一语言。"),
            ("策略与价值", "策略决定在状态下选择什么动作；价值函数估计状态或动作的长期收益。强化学习的核心就是在探索和利用之间寻找更好的策略。"),
            ("奖励不是答案", "奖励信号会塑造模型行为，但它也可能被钻空子。智能体系统尤其需要把结果奖励、过程奖励、规则奖励和人工偏好结合起来。"),
        ],
        "table": ("强化学习核心对象", ["对象", "含义", "在 LLM 中的对应"], [
            ["状态", "当前可见信息", "prompt、上下文、工具结果"],
            ["动作", "可选择行为", "生成 token、调用工具、结束任务"],
            ["奖励", "反馈信号", "偏好分数、任务成功、规则验证"],
            ["策略", "动作分布", "当前语言模型"],
        ]),
        "formula": "回报可以理解为“当前奖励加上未来奖励的折扣和”。公式细节可回到原 PDF，但学习时先掌握长期收益的直觉更重要。",
        "summary": ["强化学习让模型从反馈中优化行为。", "奖励设计决定了系统最终会追求什么。"],
        "questions": ["为什么短期高奖励可能导致长期效果变差？", "LLM 的一个 token 能否看作一个动作？"],
        "reading": ["MDP、策略梯度、Actor-Critic、GAE"],
    },
    {
        "slug": "chapter-05",
        "title": "从 SFT 到 RLHF",
        "subtitle": "让模型先会答，再学会答得更好",
        "sources": ["chapter-05", "chapter-11"],
        "stage": "对齐基础",
        "objectives": ["理解 SFT 的作用", "理解 RLHF 的基本流水线", "知道 SFT 数据质量如何影响后续 RL"],
        "sections": [
            ("SFT 解决起点问题", "监督微调（Supervised Fine-Tuning / SFT）用高质量示范回答教模型遵循指令、组织格式和覆盖常见任务。它不是终点，但会决定后续偏好优化的天花板。"),
            ("RLHF 解决偏好问题", "人类反馈强化学习（RLHF）通常包括采样候选、收集偏好、训练奖励模型、再用强化学习优化策略。它把“哪种回答更好”变成可训练信号。"),
            ("数据格式很关键", "聊天模板、completion-only mask、序列打包和多任务混合都会影响训练稳定性。V4 把这些工程细节放在学习路径中，而不是散落在 PDF 长页里。"),
        ],
        "table": ("SFT 与 RLHF", ["阶段", "输入", "输出"], [
            ["SFT", "示范问答", "会遵循指令的初始模型"],
            ["偏好收集", "同一 prompt 的多候选回答", "胜负偏好对"],
            ["奖励建模", "偏好对", "给回答打分的奖励模型"],
            ["策略优化", "奖励信号", "更符合偏好的模型"],
        ]),
        "formula": "偏好优化的关键不是背公式，而是理解：模型会被鼓励提高胜出回答的概率，同时控制偏离参考模型的幅度。",
        "summary": ["SFT 提供行为起点，RLHF 进一步塑造偏好。", "数据质量、模板和 mask 会显著影响训练结果。"],
        "questions": ["为什么低质量 SFT 会限制 RLHF 上限？", "偏好对比单个分数更容易收集吗？为什么？"],
        "reading": ["SFT 最佳实践", "语言模型的强化学习基础"],
    },
    {
        "slug": "chapter-06",
        "title": "PPO：近端策略优化",
        "subtitle": "在不让策略大幅漂移的前提下学习偏好",
        "sources": ["chapter-06"],
        "stage": "偏好优化",
        "objectives": ["理解 PPO 为什么要限制更新幅度", "理解 rollout、优势估计和 KL 控制", "知道 PPO 在 RLHF 中的完整循环"],
        "sections": [
            ("PPO 的核心直觉", "近端策略优化（Proximal Policy Optimization / PPO）希望新策略比旧策略更好，但不能一步走太远。裁剪目标函数就是为了避免策略更新突然失控。"),
            ("RLHF 中的 PPO", "在语言模型里，rollout 是模型生成的回答序列。奖励模型给出分数，优势估计告诉模型哪些 token 或片段值得增加概率，KL 惩罚则防止模型偏离参考模型太多。"),
            ("为什么实现复杂", "PPO 需要维护参考模型、奖励模型、价值模型和当前策略，还要处理采样、归一化、batch、KL 系数和分布式训练，因此系统复杂度高。"),
        ],
        "table": ("PPO 训练循环", ["步骤", "说明"], [
            ["采样", "用当前策略生成回答"],
            ["评分", "奖励模型或规则给出反馈"],
            ["估计优势", "判断哪些动作比预期更好"],
            ["裁剪更新", "限制新旧策略概率比"],
            ["监控 KL", "避免模型偏离参考行为"],
        ]),
        "formula": "PPO 公式可理解为：如果新策略相对旧策略的变化超出安全范围，就裁剪收益，迫使更新保持近端。先掌握这个更新约束，再回到原 PDF 核对完整目标函数。",
        "summary": ["PPO 强大但系统成本高。", "KL 控制和优势估计是理解 PPO 的两个入口。"],
        "questions": ["为什么 PPO 需要参考模型？", "如果 KL 惩罚过强，会发生什么？"],
        "reading": ["PPO 损失、rollout buffer、TRL 实现"],
    },
    {
        "slug": "chapter-07",
        "title": "DPO：直接偏好优化",
        "subtitle": "不用显式奖励模型的偏好学习路径",
        "sources": ["chapter-07"],
        "stage": "偏好优化",
        "objectives": ["理解 DPO 与 PPO/RLHF 的区别", "掌握偏好对如何直接优化模型", "知道 DPO 的适用边界"],
        "sections": [
            ("DPO 想简化什么", "直接偏好优化（Direct Preference Optimization / DPO）把偏好学习改写成监督式目标，避免显式训练奖励模型和运行复杂 PPO 循环。"),
            ("偏好对是核心数据", "DPO 需要同一输入下的胜出回答和失败回答。训练目标会提高胜出回答相对失败回答的概率，同时通过参考模型约束更新幅度。"),
            ("什么时候会失效", "如果偏好数据噪声大、胜负差异不清晰，或任务需要在线探索，DPO 可能不如更复杂的强化学习方法。"),
        ],
        "table": ("DPO 与 PPO 对比", ["维度", "DPO", "PPO"], [
            ["奖励模型", "通常不需要显式奖励模型", "通常需要奖励模型"],
            ["训练复杂度", "较低，接近监督学习", "较高，需要 rollout 和价值估计"],
            ["探索能力", "主要依赖离线偏好数据", "更适合在线采样和探索"],
        ]),
        "formula": "DPO 的核心是比较胜出回答与失败回答的相对 log 概率。学习时先记住“拉开偏好差距，同时不要偏离参考模型”。",
        "summary": ["DPO 是偏好优化的简化路径。", "它依赖高质量偏好对，不是所有任务的万能替代。"],
        "questions": ["为什么 DPO 可以不显式训练奖励模型？", "偏好对中两个回答过于接近会带来什么问题？"],
        "reading": ["DPO 推导、梯度分析、DPO 变体"],
    },
    {
        "slug": "chapter-08",
        "title": "GRPO 与新型偏好优化方法",
        "subtitle": "用组内比较降低价值模型依赖",
        "sources": ["chapter-08"],
        "stage": "偏好优化",
        "objectives": ["理解 GRPO 的组内相对思想", "知道它为何适合推理模型训练", "比较 PPO、DPO 和 GRPO 的取舍"],
        "sections": [
            ("组相对的想法", "组相对策略优化（Group Relative Policy Optimization / GRPO）会为同一 prompt 采样一组回答，再用组内相对表现估计优势。这样可以减少对单独价值模型的依赖。"),
            ("为什么适合推理", "推理任务常常可以通过规则、验证器或最终答案判断正确性。同一题目的多条思路可以相互比较，形成更稳定的训练信号。"),
            ("工程取舍", "GRPO 仍然需要采样多个候选，因此推理成本不低。它的关键在于奖励设计、组大小、采样温度和结果验证。"),
        ],
        "table": ("三种偏好优化直觉", ["方法", "核心数据", "适合场景"], [
            ["PPO", "在线 rollout + 奖励", "需要探索和复杂反馈"],
            ["DPO", "离线胜负偏好对", "偏好数据明确、希望训练简单"],
            ["GRPO", "同题多候选组内比较", "推理、数学、代码等可验证任务"],
        ]),
        "formula": "GRPO 的重点不是单个回答的绝对分数，而是同组回答相对均值的优势。V4 用这个解释替代易损坏的公式抄录。",
        "summary": ["GRPO 通过组内比较获得训练信号。", "它适合可验证推理，但采样和奖励设计仍然关键。"],
        "questions": ["为什么同一 prompt 下多采样可以帮助训练？", "组大小过小或过大会分别带来什么问题？"],
        "reading": ["GRPO 算法、组大小分析、推理模型训练"],
    },
    {
        "slug": "chapter-09",
        "title": "KTO、IPO、ORPO 等偏好优化变体",
        "subtitle": "理解偏好优化家族的设计空间",
        "sources": ["chapter-09"],
        "stage": "偏好优化",
        "objectives": ["认识常见 DPO 变体", "理解不同目标函数背后的假设", "形成方法选择直觉"],
        "sections": [
            ("为什么会有很多变体", "偏好数据并不总是成对、干净、平衡。KTO、IPO、ORPO、Best-of-N 和 Online DPO 等方法，都是围绕“数据长什么样、目标函数多稳定、训练成本多高”这三个问题做取舍。"),
            ("KTO：从好坏反馈学习", "KTO（Kahneman-Tversky Optimization）更适合只有单条样本正负反馈的场景。它借鉴人类对收益和损失不对称敏感的直觉，让模型增加好回答概率、降低坏回答概率，而不强依赖同一提示下的成对比较。"),
            ("IPO 与 ORPO：让目标更稳定", "IPO 关注偏好差距的稳定控制，避免把胜负差距无限拉大；ORPO 则把偏好项并入常规语言模型训练目标，减少单独对齐阶段的复杂度。学习时可以先理解它们想解决的工程问题，再回到论文公式。"),
            ("Best-of-N 与在线方法", "Best-of-N 不是训练目标，而是一种推理或数据构造策略：对同一提示采样多个候选，再用奖励模型或规则挑选最好的。在线 DPO 和相关方法会把新采样结果继续纳入训练，探索能力更强，但成本和安全控制也更重要。"),
            ("方法选择", "如果有清晰偏好对，DPO 是简单基线；如果只有正负反馈，可考虑 KTO 类方法；如果希望训练流程简洁，可以评估 ORPO；如果要更强在线探索，则回到 PPO、GRPO 或任务特定强化学习。"),
        ],
        "table": ("偏好优化方法对比", ["方法", "核心思想", "需要的数据", "优点", "局限", "适用场景"], [
            ["KTO", "按好/坏反馈调整模型偏好，并体现收益/损失不对称", "单样本正负标签或可判定好坏的输出", "不强依赖成对偏好，数据收集更灵活", "对标签质量敏感，目标直觉需要结合任务校准", "只有点赞/点踩、通过/失败等反馈的场景"],
            ["IPO", "控制偏好差距，避免目标把胜负间隔推得过大", "成对偏好数据", "训练更稳，能缓解过度自信", "需要理解并设置合适的间隔尺度", "偏好对质量较好但希望稳定训练的离线对齐"],
            ["ORPO", "把 odds ratio 偏好项并入常规语言模型训练", "正样本与负样本，通常来自偏好对", "流程简洁，减少单独奖励模型或复杂 RL 环节", "任务适配性需要实验验证", "希望低复杂度完成 SFT 与偏好对齐的项目"],
            ["Best-of-N", "同一提示生成多个候选，再选择得分最高者", "奖励模型、规则评估器或人工选择信号", "实现直观，可用于推理增强或构造训练数据", "推理成本随 N 增加，奖励模型偏差会被放大", "高价值任务、离线数据蒸馏、拒绝采样"],
            ["Online DPO", "用当前模型持续采样并更新偏好数据", "在线候选、偏好标注或自动评估信号", "比纯离线方法更能适应新分布", "成本高，需要安全边界和数据回放策略", "任务分布持续变化、需要探索的对齐训练"],
        ]),
        "formula": "这些方法的公式细节不同，但共同目标是：提高高质量回答的相对概率，同时限制噪声偏好和过度更新。方法选择时应先判断数据形态、反馈成本和训练稳定性，再选择目标函数。",
        "summary": ["偏好优化变体反映了数据条件和工程成本的差异。", "先判断数据形态，再选择训练目标，不要只按方法名套用。"],
        "questions": ["如果只有“好/坏”标签而没有成对比较，DPO 是否仍然合适？", "为什么 margin 过大可能让训练变得困难？", "Best-of-N 为什么可能放大奖励模型偏差？"],
        "reading": ["Online DPO、KTO、IPO、ORPO、Best-of-N"],
    },
    {
        "slug": "chapter-10",
        "title": "奖励模型与数据构造",
        "subtitle": "把“好回答”变成可训练信号",
        "sources": ["chapter-10"],
        "stage": "数据与奖励",
        "objectives": ["理解奖励模型的角色", "区分结果奖励和过程奖励", "掌握数据构造的常见风险"],
        "sections": [
            ("奖励模型是什么", "奖励模型（Reward Model）把输入和候选回答映射为质量分数。它让偏好判断可以规模化，但也会继承标注偏差和数据覆盖问题。"),
            ("结果奖励与过程奖励", "结果奖励只看最终答案，适合可验证任务；过程奖励会评价中间步骤，适合长链推理和工具调用，但标注成本更高。"),
            ("数据构造比模型更重要", "偏好数据要覆盖真实任务、困难负例、边界条件和安全场景。只用容易样本训练，模型可能在生产环境中表现脆弱。"),
        ],
        "table": ("奖励信号类型", ["类型", "优点", "风险"], [
            ["人工偏好", "贴近用户感受", "成本高且有主观差异"],
            ["规则奖励", "可扩展、可复现", "容易遗漏语义质量"],
            ["过程奖励", "能指导中间步骤", "标注复杂"],
            ["结果奖励", "简单直接", "对长任务反馈稀疏"],
        ]),
        "formula": "Bradley-Terry 模型可理解为：两个回答的奖励分差越大，前者被偏好的概率越高。V4 保留这个解释，不强行展示易错公式。",
        "summary": ["奖励模型把偏好转化为训练信号。", "奖励设计与数据覆盖决定训练方向。"],
        "questions": ["奖励模型被模型“钻空子”是什么意思？", "什么任务更适合过程奖励？"],
        "reading": ["Bradley-Terry、奖励模型架构、RLVR 规则奖励"],
    },
    {
        "slug": "chapter-11",
        "title": "智能体训练",
        "subtitle": "从单次回答优化到多步任务优化",
        "sources": ["chapter-13", "chapter-21"],
        "stage": "智能体训练",
        "objectives": ["理解轨迹缓冲区", "理解智能体环境和 benchmark", "掌握训练智能体的主要难点"],
        "sections": [
            ("智能体训练不同在哪里", "智能体训练面对的是多步轨迹（Trajectory），其中包含观察、计划、工具调用、环境反馈和最终结果。训练目标不再只是单条回答是否好，而是整条任务路径是否有效。"),
            ("环境很重要", "智能体需要在环境中试错。环境可以是浏览器、代码仓库、数据库、游戏、网页应用或模拟任务。好的环境要能记录状态、验证结果并控制安全边界。"),
            ("轨迹数据如何使用", "成功轨迹可以用于 SFT，失败轨迹可以用于反思和偏好数据，工具调用日志可以训练模型更好地选择工具和恢复错误。"),
        ],
        "table": ("智能体训练数据", ["数据", "用途"], [
            ["成功轨迹", "模仿学习、SFT、技能抽取"],
            ["失败轨迹", "错误恢复、偏好对、反思训练"],
            ["工具调用日志", "训练工具选择与参数生成"],
            ["环境奖励", "强化学习或规则优化"],
        ]),
        "formula": "智能体轨迹可以写成观察、动作、反馈的序列。关键是保留每一步为什么发生、调用了什么工具、环境返回了什么结果，以及这些结果如何影响下一步决策。",
        "summary": ["智能体训练关注整条任务轨迹。", "环境、日志和评估器比单纯回答数据更重要。"],
        "questions": ["为什么成功答案本身不足以训练智能体？", "一个好的智能体环境应记录哪些信息？"],
        "reading": ["Agentic RL、智能体环境、OpenEnv"],
    },
    {
        "slug": "chapter-12",
        "title": "RAG、记忆与工具使用",
        "subtitle": "让模型连接外部知识和真实任务",
        "sources": ["chapter-17", "chapter-18", "chapter-19", "chapter-20", "chapter-22", "chapter-23", "chapter-24", "chapter-25", "chapter-26", "chapter-27"],
        "stage": "智能体系统",
        "objectives": ["理解 RAG 的基本流水线", "区分记忆、工具和协议", "掌握多智能体协作的系统边界"],
        "sections": [
            ("RAG 解决知识边界", "检索增强生成（Retrieval-Augmented Generation / RAG）让模型先检索外部知识，再基于检索结果回答。它能缓解知识过期和上下文不足，但也引入检索质量、切块和引用可信度问题。"),
            ("记忆解决连续性", "短期记忆维持当前任务状态，长期记忆保存用户偏好和历史经验，语义记忆组织可检索知识。记忆系统必须考虑隐私、更新、遗忘和冲突处理。"),
            ("工具和协议解决行动能力", "工具调用让模型能查数据库、运行代码或操作系统。MCP、A2A 等协议把工具发现、权限、消息格式和智能体协作标准化。"),
        ],
        "table": ("智能体系统能力层", ["层次", "代表技术", "主要问题"], [
            ["知识", "RAG、向量检索、重排序", "检索是否相关、来源是否可信"],
            ["记忆", "短期/长期/语义记忆", "何时写入、何时遗忘"],
            ["工具", "函数调用、MCP", "权限、参数、失败恢复"],
            ["协作", "A2A、多智能体编排", "任务拆分、冲突和责任边界"],
        ]),
        "formula": "RAG 的工程公式可以理解为：答案质量 = 检索召回 × 上下文组织 × 生成可靠性。任何一环薄弱都会影响最终输出。",
        "summary": ["RAG、记忆和工具共同扩展模型能力边界。", "协议化能降低系统集成和权限管理复杂度。"],
        "questions": ["RAG 为什么不能自动保证答案正确？", "MCP 与 A2A 分别解决什么问题？"],
        "reading": ["RAG、智能体记忆、MCP、A2A、多智能体系统"],
    },
    {
        "slug": "chapter-13",
        "title": "评估、安全与部署",
        "subtitle": "从演示系统走向可运行产品",
        "sources": ["chapter-15", "chapter-26"],
        "stage": "工程落地",
        "objectives": ["理解 LLM 与智能体评估指标", "掌握安全和权限边界", "建立部署、监控与回归测试意识"],
        "sections": [
            ("评估要贴近任务", "LLM 评估不能只看通用榜单。生成质量、排序、工具调用、任务完成率、成本、延迟和安全性都可能是关键指标。"),
            ("安全不是最后加的", "智能体能使用工具和访问数据，因此必须设计权限、审计、速率限制、敏感信息处理和人工接管机制。"),
            ("部署后仍要学习", "生产系统需要日志、监控、回归测试、灰度发布和成本控制。智能体尤其要关注工具失败、循环调用、越权请求和不可解释决策。"),
        ],
        "table": ("上线前检查", ["维度", "检查问题"], [
            ["质量", "关键任务是否通过离线与在线评估"],
            ["安全", "是否有权限控制、审计和敏感信息策略"],
            ["成本", "token、检索、工具和 GPU 成本是否可控"],
            ["稳定性", "失败重试、超时和降级路径是否明确"],
        ]),
        "formula": "部署评估可以用“收益 - 成本 - 风险”的框架。V4 不追求单一公式，而是强调多指标权衡。",
        "summary": ["评估应覆盖质量、成本、延迟和安全。", "智能体部署必须把权限和失败恢复当作核心设计。"],
        "questions": ["一个智能体 benchmark 为什么可能无法代表真实生产任务？", "哪些工具调用需要人工确认？"],
        "reading": ["LLM 评估、Agent Testing、Observability、Production Deployment"],
    },
    {
        "slug": "chapter-14",
        "title": "总结与学习路线",
        "subtitle": "把模型、训练和系统连成一张图",
        "sources": ["chapter-14", "chapter-28", "chapter-29", "chapter-30"],
        "stage": "复盘",
        "objectives": ["形成全书知识地图", "知道下一步如何深入", "用问题驱动复习"],
        "sections": [
            ("一条主线", "智能体式 AI 可以沿着一条主线学习：LLM 基础提供生成能力，SFT/RLHF 塑造行为，PPO/DPO/GRPO 提供偏好优化方法，RAG/记忆/工具把模型接入世界，评估和部署保证系统可靠。"),
            ("如何继续深入", "如果你偏算法，深入优化目标、奖励建模和推理模型训练；如果你偏工程，深入 GPU 服务化、RAG、协议和可观测性；如果你偏产品，关注评估、安全和人机协作体验。"),
            ("用问题复习", "V4 将原文的测验与速查表压缩为学习问题。建议读完每章后先回答思考题，再回到 V3 或原 PDF 查看更完整细节。"),
        ],
        "table": ("学习路线", ["阶段", "目标", "对应章节"], [
            ["入门", "知道智能体式 AI 是什么", "第 1 章"],
            ["模型", "理解 LLM 与系统基础", "第 2-3 章"],
            ["训练", "掌握 RLHF 与偏好优化", "第 4-10 章"],
            ["系统", "构建智能体应用", "第 11-13 章"],
            ["复盘", "形成路线图", "第 14 章"],
        ]),
        "formula": "最终可以记住一个概念公式：智能体能力 = 模型能力 × 工具/记忆/环境 × 评估与安全约束。",
        "summary": ["V4 是学习版，不是逐字翻译版。", "真正掌握需要在算法、系统和产品三个视角之间来回切换。"],
        "questions": ["你的目标更偏算法、工程还是产品？对应应先补哪三章？", "如果要做一个研究智能体，最小可行系统需要哪些模块？"],
        "reading": ["原 PDF 测验题与速查表", "V3 结构化文档站"],
    },
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def rel(base: str, target: str) -> str:
    return f"{base}{target}"


def text_from_blocks(chapter: dict) -> str:
    pieces: list[str] = []
    for section in chapter.get("sections", []):
        pieces.append(section.get("title", ""))
        pieces.append(section.get("summary", ""))
        for block in section.get("blocks", [])[:12]:
            if block.get("type") == "paragraph":
                pieces.append(block.get("text", ""))
    return "\n".join(pieces)


def load_sources() -> tuple[dict, dict]:
    ast = json.loads(AST_PATH.read_text(encoding="utf-8"))
    source_text = SOURCE_TEXT.read_text(encoding="utf-8", errors="ignore") if SOURCE_TEXT.exists() else ""
    translated = TRANSLATED_MD.read_text(encoding="utf-8", errors="ignore") if TRANSLATED_MD.exists() else ""
    pdf_size = SOURCE_PDF.stat().st_size if SOURCE_PDF.exists() else 0
    terms = ["Agentic AI", "Transformer", "PPO", "DPO", "GRPO", "RAG", "MCP", "A2A", "RLHF", "RoPE"]
    inventory = {
        "source_text_chars": len(source_text),
        "translated_md_chars": len(translated),
        "pdf_bytes": pdf_size,
        "v3_chapters": len(ast.get("chapters", [])),
        "term_counts": {term: source_text.count(term) + translated.count(term) for term in terms},
    }
    return ast, inventory


def concepts_for_sources(ast_by_id: dict[str, dict], source_ids: list[str]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for source_id in source_ids:
        for item in ast_by_id[source_id].get("concepts", []):
            label = item.get("label") or item.get("term")
            if not label or label in seen:
                continue
            seen.add(label)
            out.append({"label": label, "term": item.get("term", label), "note": item.get("note", "本章核心概念")})
            if len(out) >= 8:
                return out
    for zh, en, note in GLOSSARY:
        if zh not in seen:
            out.append({"label": zh, "term": en, "note": note})
            if len(out) >= 8:
                break
    return out


def source_topics(ast_by_id: dict[str, dict], source_ids: list[str]) -> list[str]:
    topics: list[str] = []
    for source_id in source_ids:
        for section in ast_by_id[source_id].get("sections", [])[:6]:
            title = section.get("title", "")
            if title and title not in topics:
                topics.append(title)
    return topics[:10]


def build_lessons(ast: dict, inventory: dict) -> list[dict]:
    ast_by_id = {ch["id"]: ch for ch in ast["chapters"]}
    lessons: list[dict] = []
    for index, blueprint in enumerate(LESSON_BLUEPRINTS, start=1):
        source_ids = blueprint["sources"]
        source_chapters = [ast_by_id[sid] for sid in source_ids]
        merged_text = "\n".join(text_from_blocks(ch) for ch in source_chapters)
        term_counter = Counter(re.findall(r"[A-Za-z][A-Za-z0-9+\-]*|[\u4e00-\u9fff]{2,}", merged_text))
        lesson = {
            "number": index,
            "id": blueprint["slug"],
            "title": blueprint["title"],
            "subtitle": blueprint["subtitle"],
            "stage": blueprint["stage"],
            "sources": source_ids,
            "source_titles": [ch["title"] for ch in source_chapters],
            "source_topics": source_topics(ast_by_id, source_ids),
            "objectives": blueprint["objectives"],
            "concepts": concepts_for_sources(ast_by_id, source_ids),
            "sections": [{"title": title, "body": body} for title, body in blueprint["sections"]],
            "table": {"title": blueprint["table"][0], "headers": blueprint["table"][1], "rows": blueprint["table"][2]},
            "formula": blueprint["formula"],
            "summary": blueprint["summary"],
            "questions": blueprint["questions"],
            "reading": blueprint["reading"],
            "keywords": [word for word, _ in term_counter.most_common(12)],
            "source_inventory": inventory,
        }
        lessons.append(lesson)
    return lessons


def nav_html(base: str, active: str) -> str:
    items = [
        ("首页", "index.html", "home"),
        ("路线图", "roadmap.html", "roadmap"),
        ("核心概念", "concepts.html", "concepts"),
        ("术语表", "glossary.html", "glossary"),
        ("参考资料", "references.html", "references"),
        ("搜索", "search.html", "search"),
        ("说明", "about.html", "about"),
    ]
    return "".join(
        f'<a class="{"active" if key == active else ""}" href="{rel(base, href)}">{esc(label)}</a>'
        for label, href, key in items
    )


def chapter_nav(lessons: list[dict], base: str, active_id: str = "") -> str:
    return "".join(
        f'<a class="chapter-link {"active" if lesson["id"] == active_id else ""}" href="{rel(base, "chapters/" + lesson["id"] + ".html")}"><span>{lesson["number"]:02d}</span>{esc(lesson["title"])}</a>'
        for lesson in lessons
    )


def shell(title: str, description: str, body: str, *, base: str = "", active: str = "", lessons: list[dict] | None = None, active_chapter: str = "", article: bool = False) -> str:
    side = ""
    if article and lessons:
        side = f'<aside class="side-nav" id="side-nav"><div class="side-title">课程章节</div>{chapter_nav(lessons, "../", active_chapter)}</aside>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)} | {TITLE}</title>
  <meta name="description" content="{esc(description)}" />
  <meta property="og:title" content="{esc(title)} | {TITLE}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:type" content="website" />
  <link rel="stylesheet" href="{rel(base, "assets/css/main.css")}" />
</head>
<body class="{"lesson-page" if article else "site-page"}">
  <div class="progress" id="progress"></div>
  <header class="topbar">
    <a class="brand" href="{rel(base, "index.html")}"><strong>{TITLE}</strong><span>{SUBTITLE}</span></a>
    <button class="menu-button" id="menu-button" type="button" aria-label="打开菜单" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="topnav" id="topnav">{nav_html(base, active)}</nav>
  </header>
  <main class="page-grid">{side}<div class="main-content">{body}</div></main>
  <button class="to-top" id="to-top" type="button">返回顶部</button>
  <script src="{rel(base, "assets/js/main.js")}"></script>
</body>
</html>
"""


def card_grid(lessons: list[dict]) -> str:
    return "".join(
        f'<a class="lesson-card" href="chapters/{lesson["id"]}.html"><span>第 {lesson["number"]:02d} 章</span><h3>{esc(lesson["title"])}</h3><p>{esc(lesson["subtitle"])}</p><em>{esc(lesson["stage"])}</em></a>'
        for lesson in lessons
    )


def build_home(lessons: list[dict]) -> None:
    cards = card_grid(lessons)
    roadmap = "".join(
        f'<li><span>{lesson["number"]:02d}</span><strong>{esc(lesson["title"])}</strong><p>{esc(lesson["subtitle"])}</p></li>'
        for lesson in lessons
    )
    body = f"""
    <section class="hero">
      <div>
        <h1>{TITLE}</h1>
        <p class="hero-lead">这不是逐字 PDF 翻译版，而是基于原论文、中文译文、V3 clean AST 和术语体系重新编排的中文在线教材。目标是把 Agentic AI 的模型基础、训练方法和系统工程讲清楚。</p>
        <form class="hero-search" action="search.html" method="get"><input name="q" type="search" placeholder="搜索：PPO、RAG、MCP、智能体训练..." /><button>搜索</button></form>
      </div>
      <aside class="reader-panel">
        <h2>适合谁阅读</h2>
        <ul>
          <li>想系统理解智能体式 AI 的工程师</li>
          <li>正在学习 LLM 对齐、偏好优化和 RAG 的读者</li>
          <li>需要把模型能力落成产品系统的开发者</li>
        </ul>
      </aside>
    </section>
    <section class="band">
      <div class="section-head"><h2>学习路径</h2><a href="roadmap.html">查看完整路线图</a></div>
      <ol class="roadmap-mini">{roadmap}</ol>
    </section>
    <section class="band">
      <div class="section-head"><h2>章节卡片</h2><a href="concepts.html">核心概念索引</a></div>
      <div class="lesson-grid">{cards}</div>
    </section>
    """
    write(SITE / "index.html", shell(TITLE, "中文重编版 Agentic AI 在线教材首页。", body, active="home"))


def concept_chips(concepts: list[dict]) -> str:
    return "".join(
        f'<li><strong>{esc(c["label"])}</strong><span>{esc(c["term"])}</span><p>{esc(c["note"])}</p></li>'
        for c in concepts
    )


def render_table(table: dict) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in table["headers"])
    rows = "".join("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in table["rows"])
    return f'<section class="lesson-block"><h2>关键图表 / 表格：{esc(table["title"])}</h2><div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>'


def build_chapters(lessons: list[dict]) -> None:
    for idx, lesson in enumerate(lessons):
        prev_link = f'<a href="{lessons[idx-1]["id"]}.html">上一章：{esc(lessons[idx-1]["title"])}</a>' if idx else "<span></span>"
        next_link = f'<a class="next" href="{lessons[idx+1]["id"]}.html">下一章：{esc(lessons[idx+1]["title"])}</a>' if idx + 1 < len(lessons) else "<span></span>"
        section_html = "".join(
            f'<section class="lesson-block"><h2>{esc(section["title"])}</h2><p>{esc(section["body"])}</p></section>'
            for section in lesson["sections"]
        )
        source_badges = "".join(f"<span>{esc(title)}</span>" for title in lesson["source_titles"])
        topics = "".join(f"<li>{esc(topic)}</li>" for topic in lesson["source_topics"][:8])
        body = f"""
        <article class="lesson-article">
          <header class="lesson-header">
            <p class="chapter-number">第 {lesson["number"]:02d} 章 · {esc(lesson["stage"])}</p>
            <h1>{esc(lesson["title"])}</h1>
            <p>{esc(lesson["subtitle"])}</p>
            <div class="source-badges">{source_badges}</div>
          </header>
          <section class="lesson-block intro"><h2>本章导读</h2><p>本章把原材料中的相关内容重新组织为学习版讲解，重点追求清晰、连贯和可复习。原始细节可回到 V3 结构化文档或 arXiv PDF 查阅。</p></section>
          <section class="lesson-block"><h2>学习目标</h2><ul class="check-list">{"".join(f"<li>{esc(item)}</li>" for item in lesson["objectives"])}</ul></section>
          <section class="lesson-block"><h2>核心概念</h2><ul class="concept-list">{concept_chips(lesson["concepts"])}</ul></section>
          {section_html}
          {render_table(lesson["table"])}
          <section class="lesson-block formula-note"><h2>公式解释</h2><p>{esc(lesson["formula"])}</p><p class="muted">需要逐式核对时，请参考原 PDF：<a href="{PDF_URL}">{PDF_URL}</a></p></section>
          <section class="lesson-block"><h2>来自原文的主题线索</h2><ul class="topic-list">{topics}</ul></section>
          <section class="lesson-block"><h2>小结</h2><ul>{"".join(f"<li>{esc(item)}</li>" for item in lesson["summary"])}</ul></section>
          <section class="lesson-block"><h2>思考题</h2><ol>{"".join(f"<li>{esc(item)}</li>" for item in lesson["questions"])}</ol></section>
          <section class="lesson-block"><h2>延伸阅读</h2><ul>{"".join(f"<li>{esc(item)}</li>" for item in lesson["reading"])}</ul></section>
          <nav class="pager">{prev_link}{next_link}</nav>
        </article>
        """
        write(SITE / "chapters" / f"{lesson['id']}.html", shell(lesson["title"], lesson["subtitle"], body, base="../", active="roadmap", lessons=lessons, active_chapter=lesson["id"], article=True))


def build_roadmap(lessons: list[dict]) -> None:
    stages: dict[str, list[dict]] = {}
    for lesson in lessons:
        stages.setdefault(lesson["stage"], []).append(lesson)
    blocks = ""
    for stage, items in stages.items():
        blocks += f'<section class="roadmap-stage"><h2>{esc(stage)}</h2>'
        for item in items:
            blocks += f'<a href="chapters/{item["id"]}.html"><span>{item["number"]:02d}</span><strong>{esc(item["title"])}</strong><p>{esc(item["subtitle"])}</p></a>'
        blocks += "</section>"
    body = f'<article class="plain"><h1>学习路线图</h1><p class="lead">建议按“入门 → 模型 → 训练 → 系统 → 工程落地”的顺序阅读。已有基础的读者可以直接跳到对应阶段。</p><div class="roadmap-full">{blocks}</div></article>'
    write(SITE / "roadmap.html", shell("学习路线图", "V4 中文重编版学习路线图。", body, active="roadmap"))


def build_concepts(lessons: list[dict]) -> None:
    concept_map: dict[str, dict] = {}
    for lesson in lessons:
        for concept in lesson["concepts"]:
            label = concept["label"]
            entry = concept_map.setdefault(label, {"label": label, "term": concept["term"], "note": concept["note"], "lessons": []})
            entry["lessons"].append({"title": lesson["title"], "url": f'chapters/{lesson["id"]}.html'})
    cards = ""
    for item in sorted(concept_map.values(), key=lambda x: x["label"]):
        links = " ".join(f'<a href="{ref["url"]}">{esc(ref["title"])}</a>' for ref in item["lessons"][:4])
        cards += f'<article class="concept-card"><h2>{esc(item["label"])}</h2><p class="term">{esc(item["term"])}</p><p>{esc(item["note"])}</p><div>{links}</div></article>'
    body = f'<article class="plain wide"><h1>核心概念索引</h1><p class="lead">按学习版章节自动汇总的概念入口。</p><div class="concept-grid">{cards}</div></article>'
    write(SITE / "concepts.html", shell("核心概念索引", "V4 核心概念索引。", body, active="concepts"))


def build_glossary() -> None:
    rows = "".join(f"<tr><td>{esc(zh)}</td><td><code>{esc(en)}</code></td><td>{esc(note)}</td></tr>" for zh, en, note in GLOSSARY)
    body = f'<article class="plain"><h1>术语表</h1><p class="lead">首次出现尽量采用“中文名（English / abbreviation）”，后续保留常用缩写。</p><div class="table-wrap"><table><thead><tr><th>中文</th><th>English / abbreviation</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></article>'
    write(SITE / "glossary.html", shell("术语表", "V4 术语表。", body, active="glossary"))


def build_references(inventory: dict) -> None:
    body = f"""
    <article class="plain">
      <h1>参考资料</h1>
      <p class="lead">V4 是学习版，保留原始来源入口，便于需要逐式核对和深入阅读的读者回到原文。</p>
      <ul class="reference-list">
        <li><a href="{PDF_URL}">原始 arXiv PDF</a></li>
        <li><a href="{ONLINE_STABLE}">V3 结构化中文文档站</a></li>
        <li><a href="assets/data/v4_lessons.json">V4 lesson data</a></li>
      </ul>
      <h2>构建时读取的本地来源</h2>
      <ul>
        <li>PDF bytes: {inventory["pdf_bytes"]}</li>
        <li>source_text.md characters: {inventory["source_text_chars"]}</li>
        <li>document.zh.md characters: {inventory["translated_md_chars"]}</li>
        <li>V3 AST chapters: {inventory["v3_chapters"]}</li>
      </ul>
    </article>
    """
    write(SITE / "references.html", shell("参考资料", "V4 参考资料。", body, active="references"))


def build_about(inventory: dict) -> None:
    body = f"""
    <article class="plain">
      <h1>关于 V4 中文重编版</h1>
      <p class="lead">本页面说明 V4 的定位：它基于原 PDF、提取原文、中文译文和 V3 clean AST，但不是逐字翻译版。</p>
      <section><h2>为什么不是逐字翻译</h2><p>逐字保留 PDF 提取文本会把提取残段、页码、公式损坏和表格错位一起带进网页。V4 选择把内容重新编成学习版，优先保证概念清晰、阅读连贯和复习方便。</p></section>
      <section><h2>如何处理公式和表格</h2><p>公式无法可靠恢复时，V4 使用中文解释和原 PDF 链接；表格无法可靠恢复时，重新整理为教学表格，而不是保留错位表格。</p></section>
      <section><h2>来源读取</h2><p>构建脚本读取了 PDF、source_text.md、document.zh.md 与 clean_chapter_tree.json。V4 页面由重编后的 lesson data 生成。</p></section>
      <section><h2>稳定版</h2><p>稳定逐章结构化版本仍保留在 v3.0.0 与线上主站：<a href="{ONLINE_STABLE}">{ONLINE_STABLE}</a>。</p></section>
    </article>
    """
    write(SITE / "about.html", shell("关于", "说明 V4 是中文重编学习版。", body, active="about"))


def build_search(lessons: list[dict]) -> None:
    index = []
    for lesson in lessons:
        text = " ".join(
            [lesson["title"], lesson["subtitle"], *lesson["objectives"], *(s["title"] + " " + s["body"] for s in lesson["sections"]), *lesson["summary"], *lesson["questions"]]
        )
        index.append({
            "title": lesson["title"],
            "stage": lesson["stage"],
            "url": f'chapters/{lesson["id"]}.html',
            "summary": lesson["subtitle"],
            "text": text,
            "concepts": [c["label"] for c in lesson["concepts"]],
        })
    write(SITE / "assets" / "data" / "search-index.json", json.dumps(index, ensure_ascii=False, indent=2))
    body = """
    <article class="plain search-page">
      <h1>搜索</h1>
      <p class="lead">搜索 V4 中文重编版课程内容、术语和章节标题。</p>
      <div class="search-box"><input id="search-input" type="search" placeholder="输入关键词，例如 RAG、奖励模型、工具调用..." autofocus /><button id="search-button">搜索</button></div>
      <div id="search-status" class="muted"></div>
      <div id="search-results" class="search-results"></div>
    </article>
    <script src="assets/js/search.js"></script>
    """
    write(SITE / "search.html", shell("搜索", "V4 搜索页。", body, active="search"))


def write_assets() -> None:
    css = r"""
:root{--bg:#f6f7f5;--paper:#fff;--ink:#17212b;--muted:#617080;--line:#dfe6e3;--soft:#eef5f4;--accent:#0b7f86;--accent2:#4d5fd7;--warm:#f8f2e8;--shadow:0 18px 45px rgba(37,52,64,.08);--max:920px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Inter","Source Han Sans SC","Microsoft YaHei",Arial,sans-serif;line-height:1.78;letter-spacing:0}.progress{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,var(--accent),var(--accent2));z-index:80}a{color:var(--accent);text-underline-offset:.22em}code{padding:.12em .32em;border:1px solid var(--line);border-radius:5px;background:#f7faf9;font-size:.92em;word-break:break-word}pre{max-width:100%;overflow:auto;padding:14px;border:1px solid var(--line);border-radius:8px;background:#f7faf9}.topbar{position:sticky;top:0;z-index:70;display:flex;align-items:center;gap:24px;min-height:66px;padding:0 28px;border-bottom:1px solid var(--line);background:rgba(246,247,245,.94);backdrop-filter:blur(14px)}.brand{text-decoration:none;color:var(--ink);min-width:310px}.brand strong{display:block;font-size:17px;line-height:1.1}.brand span{display:block;color:var(--muted);font-size:12px}.topnav{display:flex;gap:4px;margin-left:auto}.topnav a{padding:8px 10px;border-radius:6px;color:#30404b;text-decoration:none;font-size:14px}.topnav a.active,.topnav a:hover{background:var(--soft);color:var(--accent)}.menu-button{display:none;width:38px;height:38px;border:1px solid var(--line);border-radius:6px;background:#fff}.menu-button span{display:block;width:18px;height:2px;margin:4px auto;background:var(--ink)}.page-grid{display:block}.main-content{width:min(100%,1180px);margin:0 auto;padding:34px 24px 80px}.hero{min-height:calc(100vh - 110px);display:grid;grid-template-columns:minmax(0,1.35fr) 360px;gap:42px;align-items:center}.hero h1{max-width:760px;margin:0;font-family:Georgia,"Times New Roman","Songti SC",serif;font-size:clamp(42px,7vw,76px);line-height:1.06}.hero-lead{max-width:760px;color:#3f505f;font-size:18px}.hero-search,.search-box{display:flex;gap:8px;max-width:680px;margin-top:24px}input[type=search]{width:100%;min-height:44px;padding:10px 13px;border:1px solid var(--line);border-radius:7px;background:#fff;font:inherit}button,.button{min-height:42px;padding:9px 15px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink);font:inherit;cursor:pointer}button:hover,.button:hover{border-color:var(--accent);color:var(--accent)}.reader-panel,.plain,.lesson-article{background:var(--paper);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow)}.reader-panel{padding:24px}.reader-panel h2{margin-top:0}.band{margin-top:38px}.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.section-head h2,.plain h1,.lesson-header h1{font-family:Georgia,"Times New Roman","Songti SC",serif}.roadmap-mini{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;list-style:none;margin:0;padding:0}.roadmap-mini li,.lesson-card,.roadmap-stage a,.concept-card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px;text-decoration:none;color:var(--ink)}.roadmap-mini span,.lesson-card span,.roadmap-stage span{display:inline-flex;color:var(--accent);font-weight:800;font-size:13px}.roadmap-mini strong,.lesson-card h3{display:block;margin:6px 0;line-height:1.35}.roadmap-mini p,.lesson-card p{margin:0;color:var(--muted);font-size:14px}.lesson-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.lesson-card:hover,.roadmap-stage a:hover,.concept-card:hover{border-color:rgba(11,127,134,.42);box-shadow:0 10px 28px rgba(37,52,64,.07)}.lesson-card em{display:inline-flex;margin-top:12px;color:var(--accent2);font-size:12px;font-style:normal}.plain{max-width:var(--max);margin:0 auto;padding:clamp(24px,5vw,46px)}.plain.wide{max-width:1100px}.lead{color:#455766;font-size:17px}.roadmap-full{display:grid;gap:22px}.roadmap-stage{padding:18px;border-left:4px solid var(--accent);background:#fff;border-radius:8px}.roadmap-stage h2{margin-top:0}.roadmap-stage a{display:block;margin-top:10px}.concept-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.concept-card h2{margin:0}.concept-card .term{color:var(--accent2);font-size:13px}.table-wrap{max-width:100%;overflow:auto}.table-wrap table{min-width:720px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{border:1px solid var(--line);padding:10px 12px;vertical-align:top}th{background:var(--soft);text-align:left}.lesson-page .page-grid{display:grid;grid-template-columns:280px minmax(0,1fr)}.side-nav{position:sticky;top:66px;height:calc(100vh - 66px);overflow:auto;padding:20px 14px;border-right:1px solid var(--line);background:rgba(255,255,255,.62)}.side-title{color:var(--muted);font-weight:800;font-size:12px;margin:0 8px 10px}.chapter-link{display:flex;gap:9px;padding:8px;border-left:2px solid transparent;color:#334550;text-decoration:none;font-size:13px;line-height:1.36}.chapter-link span{min-width:24px;color:var(--muted);font-weight:800}.chapter-link.active,.chapter-link:hover{background:var(--soft);border-left-color:var(--accent);color:var(--accent)}.lesson-page .main-content{max-width:980px;margin:0 auto}.lesson-article{overflow:hidden}.lesson-header{padding:44px clamp(24px,6vw,62px) 28px;background:linear-gradient(135deg,#eff8f8,#fff 62%);border-bottom:1px solid var(--line)}.chapter-number{margin:0 0 10px;color:var(--accent);font-size:13px;font-weight:800}.lesson-header h1{margin:0;font-size:clamp(30px,5vw,48px);line-height:1.14}.lesson-header>p:not(.chapter-number){color:#465866}.source-badges{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.source-badges span{display:inline-flex;padding:4px 8px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted);font-size:12px}.lesson-block{padding:26px clamp(24px,6vw,62px);border-bottom:1px solid var(--line)}.lesson-block h2{margin:0 0 12px;font-size:24px;line-height:1.25}.intro{background:var(--warm)}.check-list li{margin:6px 0}.concept-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;list-style:none;margin:0;padding:0}.concept-list li{padding:12px;border:1px solid #dcd9fb;border-radius:8px;background:#fbfaff}.concept-list strong{display:block;color:var(--accent2)}.concept-list span{display:block;color:var(--muted);font-size:12px}.concept-list p{margin:4px 0 0;font-size:13px}.formula-note{background:#f8fbfb}.topic-list{columns:2}.pager{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:22px clamp(24px,6vw,62px)}.pager a{display:block;padding:14px;border:1px solid var(--line);border-radius:8px;background:var(--soft);text-decoration:none;color:var(--ink)}.pager .next{text-align:right}.search-results{display:grid;gap:12px;margin-top:22px}.search-result{display:block;padding:16px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);text-decoration:none}.search-result span{display:block;color:var(--muted);font-size:13px}.muted{color:var(--muted)}.reference-list li{margin:10px 0}.to-top{position:fixed;right:22px;bottom:22px;opacity:0;pointer-events:none;transition:opacity .18s ease}.to-top.visible{opacity:1;pointer-events:auto}@media (max-width:980px){.topbar{min-height:64px;padding:10px 14px;flex-wrap:wrap}.brand{min-width:0;flex:1}.brand span{display:none}.menu-button{display:block}.topnav{display:none;width:100%;flex-direction:column;margin:0}.topnav.open{display:flex}.hero{min-height:auto;grid-template-columns:1fr}.reader-panel{order:-1}.lesson-grid{grid-template-columns:1fr}.roadmap-mini{grid-template-columns:1fr}.concept-grid{grid-template-columns:1fr}.lesson-page .page-grid{display:block}.side-nav{display:none}.main-content{padding:20px 12px 64px}.concept-list{grid-template-columns:1fr}.pager{grid-template-columns:1fr}.hero-search,.search-box{flex-direction:column}.topic-list{columns:1}}@media print{.topbar,.side-nav,.progress,.to-top,.pager{display:none}.lesson-page .page-grid{display:block}.main-content{padding:0}.lesson-article,.plain{box-shadow:none;border:0}}
"""
    main_js = r"""
(()=>{const topnav=document.getElementById("topnav"),menu=document.getElementById("menu-button"),bar=document.getElementById("progress"),top=document.getElementById("to-top");menu?.addEventListener("click",()=>{const open=topnav.classList.toggle("open");menu.setAttribute("aria-expanded",String(open))});const tick=()=>{const h=document.documentElement;const max=h.scrollHeight-h.clientHeight;const pct=max>0?h.scrollTop/max*100:0;if(bar)bar.style.width=pct+"%";if(top)top.classList.toggle("visible",h.scrollTop>500)};document.addEventListener("scroll",tick,{passive:true});top?.addEventListener("click",()=>scrollTo({top:0,behavior:"smooth"}));tick()})();
"""
    search_js = r"""
(()=>{const input=document.getElementById("search-input"),button=document.getElementById("search-button"),results=document.getElementById("search-results"),status=document.getElementById("search-status");let index=[];const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));function snip(text,q){const clean=String(text||"").replace(/\s+/g," ");const i=clean.toLowerCase().indexOf(q.toLowerCase());const s=Math.max(0,i<0?0:i-48);return clean.slice(s,s+150)+(clean.length>s+150?"...":"")}function run(){const q=input.value.trim();results.innerHTML="";if(!q){status.textContent="请输入关键词。";return}const terms=q.toLowerCase().split(/\s+/).filter(Boolean);const found=index.map(item=>{const hay=`${item.title} ${item.stage} ${item.summary} ${item.text} ${(item.concepts||[]).join(" ")}`.toLowerCase();return{item,score:terms.reduce((n,t)=>n+(hay.includes(t)?1:0),0)}}).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,20);status.textContent=`找到 ${found.length} 条结果。`;results.innerHTML=found.map(({item})=>`<a class="search-result" href="${item.url}"><strong>${esc(item.title)}</strong><span>${esc(item.stage)}</span><p>${esc(snip(item.text,q))}</p></a>`).join("")}fetch("assets/data/search-index.json").then(r=>r.json()).then(data=>{index=data;const q=new URLSearchParams(location.search).get("q");if(q){input.value=q;run()}else status.textContent=`索引已加载，共 ${index.length} 章。`}).catch(()=>{status.textContent="搜索索引加载失败。"});button?.addEventListener("click",run);input?.addEventListener("keydown",e=>{if(e.key==="Enter")run()})})();
"""
    write(SITE / "assets" / "css" / "main.css", css)
    write(SITE / "assets" / "js" / "main.js", main_js)
    write(SITE / "assets" / "js" / "search.js", search_js)


EDITION = "V4.1 Expanded Edition"
EXPANSION_TARGETS = {
    "chapter-01": 3000,
    "chapter-02": 6500,
    "chapter-03": 5600,
    "chapter-04": 3800,
    "chapter-05": 5400,
    "chapter-06": 5600,
    "chapter-07": 5200,
    "chapter-08": 5200,
    "chapter-09": 4300,
    "chapter-10": 3800,
    "chapter-11": 6800,
    "chapter-12": 6400,
    "chapter-13": 4600,
    "chapter-14": 3200,
}

EXTRA_GLOSSARY = [
    ("键值缓存", "KV Cache", "推理时保存历史 token 的 Key/Value 张量，减少解码阶段重复计算。"),
    ("预填充", "Prefill", "推理中一次性处理提示词上下文并建立 KV cache 的阶段。"),
    ("解码", "Decode", "自回归逐 token 生成输出的阶段。"),
    ("高带宽显存", "High Bandwidth Memory / HBM", "GPU 上用于存放权重、激活和 KV cache 的高速显存。"),
    ("张量并行", "Tensor Parallelism", "把单层矩阵计算切分到多个 GPU 上执行的并行方式。"),
    ("流水线并行", "Pipeline Parallelism", "把模型层切成多个阶段，由不同设备流水执行。"),
    ("全分片数据并行", "Fully Sharded Data Parallel / FSDP", "把参数、梯度和优化器状态分片以减少冗余显存。"),
    ("优势函数", "Advantage", "衡量某个动作相对当前策略平均水平好多少的信号。"),
    ("滚动采样", "Rollout", "用当前策略与环境交互生成一段轨迹或回答样本。"),
    ("轨迹缓冲区", "Trajectory Buffer", "保存智能体多步观察、行动、工具调用、反馈和结果的数据结构。"),
    ("ReAct", "Reasoning and Acting", "把思考步骤和行动步骤交替组织的智能体提示与执行范式。"),
    ("STaR", "Self-Taught Reasoner", "通过生成、验证和修正推理过程改进模型的训练方法。"),
    ("重排序", "Reranking", "在检索候选中重新排序，优先保留最相关上下文。"),
    ("护栏", "Guardrails", "限制模型或智能体越权、泄露、危险操作和不合规输出的安全机制。"),
]

EXPANSION_GUIDES = {
    "chapter-01": {
        "priority": "中",
        "omitted": ["Agentic AI 与聊天机器人的边界", "模型能力与系统能力的分工", "全书学习路线"],
        "supplement": [
            ("为什么需要扩展版", [
                "V4.1 Expanded Edition 的目标不是把原 PDF 逐页搬回来，而是在保留 V4 清晰路线的基础上补回关键知识密度。原书覆盖模型、强化学习、系统工程、智能体协议、环境、评估和 UI 框架，简短版适合入门，但不足以支撑系统学习。",
                "因此本版每章都加入更完整的机制解释、方法对比、实践提示和常见误区。读者可以先按 V4.1 学习路径建立全局理解，再回到 V3 结构化文档或原 PDF 做细节核对。"
            ]),
            ("从模型到智能体系统", [
                "智能体式 AI 的核心变化，是把语言模型从“回答器”推进到“执行器”。模型仍然负责理解、生成和推理，但系统还必须提供工具、记忆、环境反馈、权限控制、失败恢复和评估闭环。",
                "这也是本书从 LLM 基础讲到 Agentic AI 系统的原因：没有 token、Transformer、推理和服务化，就无法理解智能体运行成本；没有强化学习和偏好优化，就无法理解智能体如何从反馈中改进行为。"
            ]),
        ],
    },
    "chapter-02": {
        "priority": "高",
        "omitted": ["字符/单词/token 的取舍", "BPE 与词表", "embedding", "Q/K/V 与 multi-head attention", "RoPE", "prefill/decode", "logits 与采样", "KV cache", "FlashAttention"],
        "supplement": [
            ("分词不是小细节", [
                "Token 是语言模型真正看到的离散单位。直接用字符会让序列很长，模型需要处理更多位置；直接用单词又会遇到未登录词、形态变化和跨语言词表膨胀。子词分词把常见片段合并为 token，把罕见词拆成更小片段，在上下文长度、词表规模和泛化能力之间折中。",
                "字节对编码（Byte Pair Encoding / BPE）的直觉是：从最小片段开始，不断合并语料中最常见的相邻片段。这样“tion”“ing”“人工”“智能”等高频片段会变成稳定单位，而罕见词仍能被拆成可处理的片段。词表 vocabulary 决定了模型能输出哪些离散 token，也决定特殊 token、工具调用边界和对话模板如何表达。"
            ]),
            ("Embedding 与 Transformer 输入", [
                "分词器输出 token id 后，embedding 层把离散 id 映射成连续向量。这个向量不是人工定义的词义表，而是在训练中学出的表示：语义、语法、格式、代码符号和特殊控制符都被压进同一个高维空间。",
                "Transformer 接收的是一串 token embedding 加位置信息。每一层会先通过自注意力聚合上下文，再通过前馈网络变换每个位置的表示。最后一个或每个位置的隐藏状态会送入 LM head，得到词表上每个 token 的 logits。"
            ]),
            ("注意力机制的直觉", [
                "Query / Key / Value 可以理解为三种视角：当前位置拿 Query 去询问“我应该关注谁”，历史位置用 Key 提供可匹配的标签，再用 Value 提供真正要汇总的信息。softmax(QK^T / sqrt(d))V 这条简化公式表达的就是相关性加权汇总。",
                "Self-attention 的价值在于，每个 token 都能根据内容动态选择上下文，而不是只看固定窗口。Multi-head attention 则让不同头学习不同关系：一个头可能关注语法依赖，一个头关注实体指代，一个头关注代码括号或工具调用边界。"
            ]),
            ("位置、RoPE 与长上下文", [
                "如果没有位置信息，Transformer 只能看到一袋 token，无法区分“猫追狗”和“狗追猫”。位置编码把顺序注入表示中。RoPE 通过对 Query 和 Key 做位置相关旋转，让注意力分数自然包含相对距离信息，因此在长上下文和外推场景中很常见。",
                "学习 RoPE 时不必先背完整矩阵形式，可以先抓住机制：位置不是被拼接进向量，而是影响注意力匹配本身。两个位置越远，旋转相位差越大，模型就能在注意力计算中感知距离。"
            ]),
            ("推理流水线：prefill 与 decode", [
                "推理通常分为 prefill 和 decode。Prefill 阶段一次性处理用户 prompt，构建所有上下文 token 的 KV cache；decode 阶段每次只生成一个新 token，并把新 token 的 Key/Value 追加到 cache。",
                "生成下一个 token 时，模型先输出 logits，再经过 temperature、top-k、top-p 等采样策略得到实际 token。temperature 越高分布越平，输出更发散；top-k 限制候选数量；top-p 保留累计概率达到阈值的一组候选。"
            ]),
            ("KV Cache 与 FlashAttention", [
                "KV cache 加速的是自回归生成中的重复计算：历史 token 的 Key 和 Value 不必每一步重新计算。它换来的代价是显存消耗随 batch、层数、头数、上下文长度线性增长，因此长上下文服务往往先撞到 KV cache 瓶颈。",
                "FlashAttention 的核心是减少 HBM 读写，而不是近似注意力结果。它把注意力计算分块放进更快的片上存储，并使用在线 softmax 保持数值稳定，从而避免保存完整注意力矩阵。对长序列而言，访存优化往往比单纯增加算力更关键。"
            ]),
        ],
        "table": ("LLM 推理流程速查", ["阶段", "输入", "核心计算", "主要瓶颈"], [
            ["Tokenization", "原始文本", "切分并映射为 token id", "词表、特殊 token、模板一致性"],
            ["Prefill", "prompt token 序列", "并行计算上下文表示并建立 KV cache", "长 prompt 的注意力和显存"],
            ["Decode", "上一步生成 token", "逐 token 更新 KV cache 并输出 logits", "串行依赖和 KV cache 增长"],
            ["Sampling", "logits", "temperature、top-k、top-p 或贪心选择", "质量、多样性和可控性权衡"],
            ["Optimization", "模型与请求批次", "FlashAttention、continuous batching、量化", "吞吐、延迟和显存预算"],
        ]),
    },
    "chapter-03": {
        "priority": "高",
        "omitted": ["GPU/SM/CUDA/Tensor Core", "HBM", "NVLink/PCIe", "batch 与 sequence length", "并行策略", "ZeRO/FSDP", "vLLM/PagedAttention", "throughput/latency", "continuous batching", "speculative decoding"],
        "supplement": [
            ("GPU 为什么适合 LLM", [
                "LLM 的主要计算是大规模矩阵乘法和注意力，这些操作可以拆成大量相似的小计算。GPU 的 SM、CUDA core 和 Tensor Core 正是为这种高并行吞吐设计的。CPU 更适合低延迟、分支复杂、线程数量较少的任务；GPU 则通过成千上万个线程隐藏内存访问延迟。",
                "Tensor Core 对 BF16、FP16、FP8 等低精度矩阵乘法尤其重要。现代训练和推理系统会在精度、吞吐和稳定性之间做选择：训练常用 BF16，推理可能使用 FP16、INT8、INT4 或混合量化。"
            ]),
            ("显存、互联与 KV cache", [
                "HBM 是 LLM 系统最稀缺的资源之一。权重、激活、优化器状态、临时缓冲和 KV cache 都要进入显存。训练时优化器状态和梯度是大头；推理时权重和 KV cache 是大头。batch size、sequence length 和并发数会直接放大 KV cache。",
                "多 GPU 互联决定并行策略的上限。NVLink 的带宽和延迟通常明显优于 PCIe，适合张量并行、流水线并行和频繁同步；如果只能使用 PCIe，就要更谨慎地减少跨卡通信。"
            ]),
            ("并行策略与分片", [
                "数据并行复制模型、切分数据，适合扩大 batch；张量并行切分单层矩阵，解决单卡放不下或算不过来的问题；流水线并行切分层，把不同层放在不同设备上。实际系统常常组合多种并行策略。",
                "ZeRO 和 FSDP 的基本思想是减少冗余：不要让每张卡都保存完整参数、梯度和优化器状态，而是按需分片、通信和重构。它们能显著降低训练显存，但会增加通信、检查点和调试复杂度。"
            ]),
            ("服务化吞吐与延迟", [
                "Serving 的核心不是单请求最快，而是在 SLA 下最大化单位 GPU 的有效吞吐。batching 可以提高吞吐，但会增加排队等待；continuous batching 让已完成请求退出、新请求进入，减少批次尾部浪费。",
                "Speculative decoding 用小模型或草稿模型先生成候选 token，再由大模型并行验证，目标是在不明显牺牲质量的情况下降低解码串行开销。它适合大模型 decode 成本高、草稿模型足够便宜的场景。"
            ]),
        ],
        "table": ("系统优化方法对比", ["方法", "解决的问题", "代价", "适用阶段"], [
            ["张量并行", "单层矩阵计算过大或单卡放不下", "跨卡通信频繁", "训练与推理"],
            ["流水线并行", "层数和参数过多", "气泡开销、调度复杂", "大模型训练"],
            ["FSDP / ZeRO", "参数、梯度、优化器状态冗余", "通信和检查点复杂", "训练"],
            ["PagedAttention", "KV cache 碎片和高并发显存浪费", "运行时调度更复杂", "推理服务"],
            ["Continuous batching", "请求长度不齐导致吞吐浪费", "调度器实现复杂", "在线服务"],
            ["Speculative decoding", "decode 串行瓶颈", "需要草稿模型和验证逻辑", "推理加速"],
        ]),
    },
    "chapter-04": {
        "priority": "中",
        "omitted": ["MDP", "policy/reward/value/advantage", "trajectory/rollout", "on-policy/off-policy", "policy gradient"],
        "supplement": [
            ("从监督学习到强化学习", [
                "监督学习学习的是输入到标签的映射；强化学习学习的是在状态中选择动作以最大化长期回报。对 LLM 来说，token 生成可以看成一连串动作，整段回答的质量或任务是否完成则提供奖励。",
                "马尔可夫决策过程（MDP）把问题拆成状态、动作、转移、奖励和折扣。语言模型场景中，状态通常是 prompt 加已生成 token，动作是下一个 token 或工具调用，奖励可能来自人类偏好、规则验证器或任务结果。"
            ]),
            ("价值、优势与轨迹", [
                "Value 估计从当前状态出发的长期收益；advantage 衡量某个动作比平均选择好多少。策略梯度方法常用 advantage 给更新加权：好于预期的动作提高概率，差于预期的动作降低概率。",
                "Trajectory 或 rollout 是智能体与环境交互产生的序列。对聊天模型，它可能是一段回答；对智能体，它可能包含多轮观察、工具调用、错误恢复和最终结果。长期任务的难点在于 credit assignment：到底是哪一步导致成功或失败。"
            ]),
            ("On-policy 与 off-policy", [
                "On-policy 方法使用当前策略生成的数据更新当前策略，分布匹配更好但采样成本高；off-policy 方法可以复用旧策略或日志数据，样本效率更高但分布偏移更难处理。PPO 偏 on-policy，DPO 更接近离线偏好学习。",
                "在 LLM 训练中，KL 约束、参考模型和偏好数据质量共同决定稳定性。强化学习不是简单“给奖励就会变好”，奖励设计不当会鼓励模型钻空子，甚至损害原本的语言能力。"
            ]),
        ],
    },
    "chapter-05": {
        "priority": "高",
        "omitted": ["SFT", "RLHF pipeline", "reward model", "chosen/rejected", "KL", "数据模板", "训练稳定性"],
        "supplement": [
            ("SFT 解决起点问题", [
                "监督微调（SFT）让基础模型学会遵循指令、使用对话格式、输出安全且有帮助的回答。它通常使用人工示范、合成示范或专家轨迹。SFT 的质量决定后续对齐训练的上限：如果模型连任务格式都不稳定，RLHF 很难只靠奖励把行为纠正回来。",
                "SFT 不是简单堆数据。聊天模板、system/user/assistant 边界、completion-only loss、特殊 token、拒答样式和工具调用格式都会影响模型学到的行为。"
            ]),
            ("RLHF 的完整流水线", [
                "RLHF 通常分为四步：先做 SFT；对同一 prompt 采样多个候选；收集人类偏好形成 chosen/rejected 对；训练奖励模型，再用 PPO 等方法优化策略。奖励模型把“哪个回答更好”变成可微的标量信号。",
                "KL 约束是 RLHF 的安全绳。它限制新策略不要离 SFT 或参考模型太远，避免模型为了奖励模型的漏洞牺牲流畅性、事实性或安全性。KL 太强会学不动，太弱又可能 reward hacking。"
            ]),
            ("数据与稳定性", [
                "偏好数据需要覆盖真实任务、难例、边界条件和安全场景。只用容易样本会让模型在 benchmark 上好看，在生产环境中脆弱；只用单一风格偏好会让模型过拟合某种回答模板。",
                "从 SFT 到 RLHF 的关键不是“多一步强化学习”，而是把行为目标从模仿示范转向优化偏好。PPO、DPO、GRPO 等方法都是围绕同一个问题展开：如何把偏好信号稳定地注入语言模型。"
            ]),
        ],
    },
    "chapter-06": {
        "priority": "高",
        "omitted": ["clipping", "advantage", "KL", "rollout buffer", "value head", "entropy", "失败模式"],
        "supplement": [
            ("PPO 为什么需要裁剪", [
                "普通策略梯度可能因为一次高噪声更新把策略推得太远，语言模型中表现为回答突然变短、重复、格式崩坏或过度迎合奖励模型。PPO 的裁剪目标限制新旧策略概率比，避免单次更新过猛。",
                "简化理解：如果新策略只是稍微提高好动作概率，就允许更新；如果概率比已经超过安全范围，就裁剪收益，不再继续鼓励更大的偏移。这个机制用一阶优化近似了 TRPO 的 trust region 思想。"
            ]),
            ("PPO 在 RLHF 中的组件", [
                "语言模型 PPO 通常需要策略模型、参考模型、奖励模型和价值头。策略模型生成回答；奖励模型评分；价值头估计未来收益；参考模型提供 KL 约束。正因为组件多，PPO 的显存和工程复杂度都很高。",
                "Rollout buffer 保存 prompt、生成 token、log probability、奖励、value、advantage 和 mask。对 LLM 来说，EOS、padding、completion-only 区间和 KL 计算必须处理一致，否则训练信号会错位。"
            ]),
            ("稳定性与失败模式", [
                "PPO 的关键超参数包括学习率、clip range、KL 系数、batch size、rollout 长度、奖励归一化和 entropy bonus。奖励尺度变化会直接影响 advantage，进而影响更新幅度。",
                "常见失败包括奖励黑客、长度偏置、模式坍缩、过度拒答、KL 爆炸和价值函数不稳定。实际训练时需要同时监控 reward、KL、entropy、response length、win rate 和人工抽检样本。"
            ]),
        ],
    },
    "chapter-07": {
        "priority": "高",
        "omitted": ["DPO 推导直觉", "implicit reward", "chosen/rejected logprob", "beta", "PPO vs DPO", "数据边界"],
        "supplement": [
            ("DPO 想简化什么", [
                "DPO 的动机是绕过显式奖励模型和复杂 PPO 循环。它利用 RLHF 目标在 KL 正则下的最优策略形式，把偏好学习改写成一个监督式损失：提高 chosen 相对 rejected 的概率，同时保留参考模型约束。",
                "DPO 仍然需要高质量偏好对。每条样本通常包含 prompt、chosen response 和 rejected response。训练时比较当前模型与参考模型在两条回答上的 log probability 差异，鼓励当前模型更偏向 chosen。"
            ]),
            ("DPO 与 PPO 的差别", [
                "PPO 可以在线采样并利用奖励模型反馈，探索能力更强，但系统复杂；DPO 更像离线偏好优化，流程简洁、显存压力小、实现更接近 SFT。它适合偏好对清晰、任务分布稳定的场景。",
                "DPO 的 beta 控制偏离参考模型的幅度。beta 太小可能更新弱，beta 太大可能过度拟合偏好数据。偏好对如果噪声大、差异太小或来自旧模型分布，DPO 的收益会下降。"
            ]),
            ("训练与排错", [
                "DPO 训练需要注意序列级 log probability 的计算：通常只对 assistant completion 部分计入损失，prompt 不应被当作模型需要偏好的内容。长度差异也会影响 logprob，需要结合任务做归一化或抽检。",
                "如果训练后模型变得冗长、模板化或安全性下降，问题常常在偏好数据而不是公式。应检查 rejected 是否真差、chosen 是否有统一风格偏置，以及数据是否覆盖拒答、事实性和多轮上下文。"
            ]),
        ],
    },
    "chapter-08": {
        "priority": "高",
        "omitted": ["group sampling", "relative advantage", "verifiable reward", "reasoning models", "memory saving", "variance"],
        "supplement": [
            ("GRPO 的核心直觉", [
                "GRPO 为同一个 prompt 采样一组候选回答，用组内相对表现估计优势，而不是依赖单独价值网络。这样可以减少价值模型显存和训练复杂度，尤其适合大模型推理任务。",
                "如果一组回答中只有少数通过验证器，那么通过者相对组均值有正优势，失败者有负优势。模型学习的是“在同题候选中哪些行为更好”，这比绝对奖励更稳定。"
            ]),
            ("为什么适合推理任务", [
                "数学、代码、格式验证和工具任务常有可验证奖励：答案对不对、测试是否通过、工具结果是否满足约束。GRPO 可以对同一题多采样，利用这些二值或规则奖励构建训练信号。",
                "推理模型训练常需要长链条和多样探索。组大小越大，越可能包含高质量候选，但采样成本也越高。温度、组大小、奖励函数和 KL 控制共同决定训练质量。"
            ]),
            ("实践风险", [
                "GRPO 并不自动解决奖励设计。格式奖励过强会让模型过度关注形式；答案奖励过稀会导致大部分样本没有梯度；组内样本太相似会降低相对比较价值。",
                "工程上要监控 pass rate、组内方差、长度、KL 和重复模式。如果模型只学到固定解题模板，说明多样性压力或奖励覆盖不足。"
            ]),
        ],
    },
    "chapter-09": {
        "priority": "高",
        "omitted": ["Online vs Offline DPO", "KTO 非配对反馈", "IPO 有界偏好", "ORPO 合并 SFT", "Best-of-N 成本", "选择建议"],
        "supplement": [
            ("Online DPO 与 Offline DPO", [
                "Offline DPO 使用固定偏好数据，训练稳定、成本低，但数据可能来自旧模型分布。随着策略更新，模型生成的回答会离训练数据越来越远，损失优化的分布和线上行为出现偏移。",
                "Online DPO 让当前策略持续采样新候选，再用奖励模型、规则或人工反馈构造偏好对。它更贴近当前模型分布，但引入采样成本、奖励模型偏差和安全控制问题。"
            ]),
            ("KTO、IPO、ORPO 的动机", [
                "KTO 面向非配对反馈：很多产品只有点赞/点踩、通过/失败，而没有同一 prompt 下的 chosen/rejected 对。KTO 借鉴 Kahneman-Tversky 对收益和损失不对称的直觉，把单样本好坏反馈转成偏好优化信号。",
                "IPO 强调有界偏好，避免模型把 chosen 与 rejected 的差距无限拉大；ORPO 则把 odds ratio 偏好项合并进 SFT 目标，减少参考模型和多阶段训练成本。"
            ]),
            ("Best-of-N 的作用与局限", [
                "Best-of-N 通过多采样后选择最高分候选提升推理质量，也可以用来构造训练数据。它简单直接，但成本随 N 线性增长，而且奖励模型偏差会被放大：如果评审偏爱冗长回答，Best-of-N 会更偏向冗长。",
                "选择方法时先看数据：有高质量偏好对用 DPO/IPO；只有单样本反馈考虑 KTO；想简化流水线评估 ORPO；任务可验证且需要探索时考虑 GRPO/PPO；只想提升少量高价值请求可用 Best-of-N。"
            ]),
        ],
    },
    "chapter-10": {
        "priority": "中",
        "omitted": ["reward model", "pairwise ranking", "chosen/rejected", "reward hacking", "judge model", "AI feedback"],
        "supplement": [
            ("奖励模型是什么", [
                "奖励模型把 prompt 和候选回答映射为质量分数，是人类偏好和强化学习目标之间的桥梁。典型做法是在预训练 LLM 上加一个标量头，输入 prompt-response 序列，输出一个 reward。",
                "Pairwise ranking 常用 Bradley-Terry 形式：如果 chosen 的奖励高于 rejected，那么 chosen 被偏好的概率更高。训练目标不是让奖励有绝对单位，而是让排序与偏好一致。"
            ]),
            ("数据质量与 judge model", [
                "Preference data 的核心字段是 prompt、chosen 和 rejected。chosen 不一定完美，rejected 也不一定完全错误；它们只表达相对偏好。标注标准不一致会让奖励模型学到混乱信号。",
                "AI feedback 和 judge model 可以降低标注成本，但会继承评审模型的偏差。生产中常把规则评估、AI judge、人类抽检和对抗样本结合起来，而不是完全依赖单一奖励来源。"
            ]),
            ("奖励黑客与过优化", [
                "Reward hacking 指模型找到提高奖励分数但不真正改善用户价值的方式，例如变长、套模板、过度自信或迎合评审偏好。Reward overoptimization 则是训练越久奖励越高，但人类评价反而下降。",
                "缓解方法包括限制 KL、校准奖励、混合人工评估、监控长度和安全指标、保留 held-out 偏好集，以及定期检查高奖励低质量样本。"
            ]),
        ],
    },
    "chapter-11": {
        "priority": "高",
        "omitted": ["Agent vs Chatbot", "trajectory buffer", "action/observation/state/memory", "tool use", "self-correction", "ReAct", "STaR", "RAG over experiences", "credit assignment", "agent evaluation", "safety guardrails", "training pipeline"],
        "supplement": [
            ("从聊天机器人到智能体", [
                "聊天机器人主要优化单轮或多轮对话质量；智能体要在环境中行动，调用工具，观察结果，再决定下一步。两者的评估对象不同：聊天机器人评估回答，智能体评估策略和任务完成率。",
                "Agentic AI 的状态不只是对话上下文，还包括工具结果、文件系统、浏览器状态、记忆、计划和未完成任务。动作也不只是生成 token，而可能是调用 API、运行代码、检索资料、写文件或请求人工确认。"
            ]),
            ("轨迹缓冲区与经验", [
                "Trajectory buffer 保存智能体执行任务的全过程：目标、观察、思考、行动、工具输入、工具输出、错误、修正和最终结果。与传统 RL 的数值 replay buffer 不同，智能体轨迹通常是文本和结构化事件混合体。",
                "成功轨迹可以用于 SFT 或 few-shot 检索；失败轨迹可以用于反思、自我修正和偏好数据构造。关键不是只保存最终答案，而是保存每一步为什么发生、环境如何反馈、智能体如何调整。"
            ]),
            ("ReAct、Reflection 与 STaR", [
                "ReAct 把 reasoning 和 acting 交替组织：模型先说明下一步思路，再调用工具，读取观察结果后继续。它让智能体的中间状态更可检查，也方便把失败点定位到具体行动。",
                "Reflection 和 self-correction 要求智能体在失败后生成批评或修正计划，再把改进后的轨迹加入训练或记忆。STaR 类方法通过生成推理、验证答案、保留成功或修正失败来提升推理能力。"
            ]),
            ("RAG over Experiences", [
                "经验检索不一定要更新模型权重。系统可以把过去成功轨迹向量化，遇到新任务时检索相似经验，把关键步骤作为上下文示范。这是一种面向智能体的 RAG：检索的不只是知识片段，而是可复用的行动模式。",
                "这种方法低风险、易回滚，但依赖经验库质量。过时经验、错误工具调用和泄露敏感信息的轨迹都可能被重新注入上下文，因此需要清洗、权限标签和过期策略。"
            ]),
            ("长程任务和 credit assignment", [
                "智能体训练最难的是长程信用分配。任务失败可能源于一开始理解错目标，也可能源于中途工具参数错误、检索结果误读、权限不足或最终验证缺失。只给最终 0/1 奖励很稀疏，难以指出哪一步该改。",
                "工程上常结合过程奖励、规则验证器、人工回放、日志切片和轨迹级偏好。训练 pipeline 通常包括任务采样、轨迹执行、结果验证、失败分类、数据入库、SFT/RL 更新和离线/在线评估。"
            ]),
            ("安全护栏与应用场景", [
                "软件工程智能体、研究智能体和生产力 copilot 都需要不同护栏。代码智能体要限制文件和命令权限；研究智能体要保留引用和证据；办公 copilot 要防止越权读取、误发邮件和泄露隐私。",
                "智能体越自主，越需要明确权限、可观测日志、人工确认点、沙箱和回滚机制。训练提升能力只是第一步，部署时的安全边界同样是系统能力的一部分。"
            ]),
        ],
    },
    "chapter-12": {
        "priority": "高",
        "omitted": ["RAG 流程", "embedding retrieval", "chunking", "reranking", "context window", "memory types", "tool/function calling", "planning/execution loop", "failure recovery", "hallucination control"],
        "supplement": [
            ("RAG 的基本流程", [
                "检索增强生成（RAG）把外部知识引入上下文：先把文档切块并向量化，用户问题到来时检索相关 chunk，必要时 rerank，再把证据放入 prompt 让模型回答。它不是让模型“记住”知识，而是让模型在生成时看到证据。",
                "Chunking 决定检索粒度。块太小会丢上下文，块太大又会引入噪声。常见做法是按标题、段落、代码单元或语义边界切分，并保留来源、时间、权限和层级 metadata。"
            ]),
            ("记忆类型", [
                "短期记忆通常是当前上下文窗口内的对话、计划和工具结果；长期记忆是跨会话保存的用户偏好、项目状态、经验轨迹或知识库。长期记忆必须有写入策略、更新策略和遗忘策略。",
                "智能体记忆和 RAG 的关系很近：RAG 检索事实知识，经验记忆检索过去行动模式，用户记忆检索偏好和长期目标。三者都需要权限、去重、过期和冲突处理。"
            ]),
            ("工具调用与执行循环", [
                "Function calling 把模型输出约束为可解析的工具名和参数，降低自由文本调用的歧义。工具描述要写清输入、输出、副作用、权限和失败条件，否则模型会误用工具。",
                "典型执行循环是：理解目标，制定计划，选择工具，执行，观察结果，判断是否继续或修复。失败恢复包括重试、换工具、缩小问题、请求人工确认和回滚副作用。"
            ]),
            ("幻觉控制", [
                "RAG 可以降低事实幻觉，但不能自动保证正确。模型可能忽略证据、误读证据或把多个来源拼错。需要引用、答案-证据一致性检查、低置信拒答和检索失败时的降级策略。",
                "对高风险任务，工具结果和检索证据应作为可审计对象进入日志。不要只记录最终回答，还要记录检索 query、候选、rerank 分数、使用的上下文和工具返回。"
            ]),
        ],
    },
    "chapter-13": {
        "priority": "高",
        "omitted": ["LLM eval", "agent eval", "benchmark 局限", "human eval", "automatic judge", "safety alignment", "red teaming", "guardrails", "monitoring", "cost/latency/reliability", "feedback loop"],
        "supplement": [
            ("LLM 与智能体评估不同", [
                "LLM evaluation 常看单次回答质量：事实性、指令遵循、风格、安全性和偏好胜率。Agent evaluation 还要看任务完成率、步骤效率、工具使用正确性、恢复能力和长期稳定性。",
                "Benchmark 有价值，但有局限。固定题集容易被过拟合，自动 judge 会有偏差，离线任务不能完全代表生产环境。评估应组合 benchmark、人类评审、真实任务回放和线上监控。"
            ]),
            ("安全、红队与护栏", [
                "Safety alignment 不只是拒答有害内容。智能体还要防 prompt injection、越权工具调用、敏感信息泄露、错误写操作、供应链攻击和不可逆副作用。",
                "Red teaming 应覆盖模型输出、检索内容、工具参数、权限边界和多步组合攻击。Guardrails 包括输入过滤、工具 allowlist、权限确认、输出审计、速率限制和人工审批。"
            ]),
            ("部署与反馈闭环", [
                "生产部署要同时优化质量、成本、延迟和可靠性。高质量模型可能成本高，低延迟系统可能牺牲上下文长度，强护栏可能降低完成率。需要按任务分层：高风险任务更重安全，低风险任务更重速度和成本。",
                "监控指标应包括请求量、延迟、token 成本、工具失败率、检索命中率、用户修正率、人工升级率和安全事件。生产反馈进入数据构造和评估集，形成持续改进闭环。"
            ]),
        ],
    },
    "chapter-14": {
        "priority": "中",
        "omitted": ["全书复盘", "学习路线", "后续方向"],
        "supplement": [
            ("把三条线合在一起", [
                "全书可以压缩为三条主线：模型线解释 LLM 如何生成和推理；训练线解释 SFT、RLHF、PPO、DPO、GRPO 和奖励模型如何塑造行为；系统线解释 RAG、记忆、工具、环境、评估和部署如何把模型变成可用智能体。",
                "V4.1 的扩写版适合按路线学习，也适合按角色跳读：算法读者重点看第 4-10 章，系统读者重点看第 3、11-13 章，产品和评估读者重点看第 1、12、13 章。"
            ]),
            ("下一步怎么学", [
                "如果要深入算法，建议从 policy gradient、KL 正则、偏好建模和 verifiable reward 开始；如果要做工程落地，建议实现一个小型 RAG + tool calling 智能体，并建立轨迹日志和评估集。",
                "最重要的是把方法放回系统：没有好的数据，DPO 不会神奇变好；没有可靠环境，智能体训练无法闭环；没有监控和权限，部署越强的智能体风险越大。"
            ]),
        ],
    },
}

EXTRA_EXPANDED_SECTIONS = {
    "chapter-02": [
        ("从 token 到一次完整生成", [
            "一次 LLM 生成可以拆成六个稳定步骤：用户文本先被分词器切成 token id；embedding 层把 id 转成向量；Transformer 层反复做注意力和前馈变换；LM head 把隐藏状态投影到词表维度；logits 经过温度、top-k、top-p 等策略采样；新 token 再追加回上下文，进入下一轮 decode。理解这条流水线后，很多优化方法就不再孤立：KV Cache 优化的是历史上下文复用，FlashAttention 优化的是注意力访存，采样策略影响的是最后一步的输出多样性。",
            "Prefill 阶段通常吞吐高但一次性消耗显存，因为它要处理整段 prompt 并建立所有位置的 Key/Value；decode 阶段每步只生成一个 token，算术量看似较小，却因为循环次数多、批次动态变化、KV cache 持续增长而成为服务延迟的核心。工程上常把首 token 延迟和每 token 延迟分开观察，前者反映 prompt 处理和排队，后者反映持续生成效率。"
        ]),
        ("采样参数如何影响输出", [
            "Logits 是模型对词表中每个 token 的未归一化分数。Temperature 会改变分布尖锐程度：较低温度让高概率 token 更占优势，适合事实性和格式化任务；较高温度增加多样性，适合创意和探索。Top-k 只保留分数最高的 k 个候选，top-p 则保留累计概率达到阈值的一组候选。二者都不是让模型“更聪明”，而是在质量、稳定性和多样性之间选择。",
            "在智能体系统中，采样参数还会影响工具调用和计划稳定性。过高温度可能让行动序列发散，过低温度又可能在错误路线中重复。实践中常对不同阶段使用不同策略：规划阶段略微保留探索，执行工具调用时更保守，最终回答阶段再根据任务类型调整。"
        ]),
    ],
    "chapter-03": [
        ("显存预算：权重、激活与 KV Cache", [
            "部署 LLM 时，显存主要被三类对象占用：模型权重、计算过程中的激活，以及推理阶段不断增长的 KV Cache。权重大小大致由参数量和精度决定，例如 70B 模型用 FP16 仅权重就需要约 140GB；量化可以降低权重占用，但不会自动解决 KV Cache 的增长。训练时还要额外保存梯度、优化器状态和激活，显存压力远高于纯推理。",
            "KV Cache 的规模与 batch size、层数、注意力头数、head dimension 和 sequence length 近似线性相关。长上下文、多并发和多候选采样会同时推高它。很多线上服务并不是被矩阵乘法算力限制，而是被 HBM 容量、HBM 带宽和 cache 管理效率限制。因此，估算显存预算时必须把 prompt 长度、最大输出长度和并发分布一起放进去。"
        ]),
        ("并行策略如何选择", [
            "数据并行适合多副本处理不同 batch，通信主要发生在梯度同步或参数更新；张量并行把单层矩阵切到多张卡上，能承载更大的层，但每层都需要高频通信；流水线并行按层切分模型，适合模型很深时降低单卡权重压力，但会引入 pipeline bubble；FSDP / ZeRO 则把参数、梯度和优化器状态分片，重点降低训练显存占用。",
            "推理服务和训练的选择不同。推理通常更关注延迟、吞吐和 KV Cache 管理，倾向用张量并行、continuous batching、PagedAttention 和 prefix caching；训练更关注优化器状态、激活检查点和跨卡梯度同步。NVLink 带宽高、延迟低，适合重通信并行；PCIe 更容易成为瓶颈，需要更保守地切分模型。"
        ]),
        ("吞吐与延迟不是同一个目标", [
            "Throughput 关心单位时间处理多少 token 或请求，latency 关心单个用户等待多久。增大 batch 往往提高 GPU 利用率，却可能让短请求等待长请求；continuous batching 通过在 decode 过程中动态加入新请求，缓解传统静态批处理的浪费。服务系统需要同时监控排队时间、首 token 延迟、平均每 token 延迟、超时率和 GPU 利用率。",
            "Speculative decoding 用小模型或草稿模型先生成候选 token，再让大模型一次验证多个候选；如果接受率高，就能减少大模型前向次数。它的收益取决于草稿模型质量、验证成本和任务分布。对于格式严格或工具调用密集任务，接受率可能下降；对于普通文本续写，收益更明显。"
        ]),
    ],
    "chapter-05": [
        ("SFT 的作用边界", [
            "监督微调（SFT）最重要的作用是让基础模型学会指令格式、回答风格、任务模板和安全边界。它把原本只会续写文本的模型，塑造成能理解用户意图、遵循对话角色、按格式输出的助手。SFT 数据的质量通常比数量更关键：高质量示范会让模型学到清晰的任务分解，低质量示范则会固化啰嗦、幻觉或过度拒答。",
            "SFT 也有边界。它不能很好表达“两个回答哪个更好”的偏好差异，也难以处理只有最终结果奖励的任务。更重要的是，SFT 会把示范答案当成唯一标签，而真实用户偏好往往是一组排序和权衡。因此 RLHF、DPO、GRPO 等方法会在 SFT 之后继续塑造模型行为。"
        ]),
        ("RLHF 的四段流水线", [
            "典型 RLHF 可以拆成四段：先用 SFT 得到可用的初始策略；再为同一 prompt 采样多个回答并收集人类偏好，形成 chosen / rejected 样本；随后训练奖励模型，让它给候选回答打分；最后用 PPO 等强化学习方法优化策略，同时用 KL 约束防止模型偏离参考策略过远。每一段都可能成为瓶颈。",
            "奖励模型不是客观真理，它只是偏好数据的近似器。偏好标注如果不一致、任务说明不清或样本分布过窄，奖励模型会学到错误捷径。PPO 阶段如果过度追逐奖励分数，就可能出现 reward hacking：模型生成看似高分但对用户无用、冗长或规避评价器弱点的回答。"
        ]),
        ("从数据模板到训练稳定性", [
            "聊天模板、系统提示、工具调用格式和特殊 token 必须在 SFT、奖励模型训练和策略优化中保持一致。模板不一致会让 KL、logprob 和偏好损失失去可比性，尤其在多轮对话和工具调用任务中更明显。",
            "稳定训练常依赖几个朴素做法：先保证 SFT 基线足够好；偏好数据覆盖真实任务；奖励模型留出验证集并检查长度偏置；PPO 或 DPO 训练时监控 KL、胜率、拒答率、长度和人工样本；上线后用真实失败案例回流，而不是只看离线 benchmark。"
        ]),
    ],
    "chapter-06": [
        ("PPO 的目标函数直觉", [
            "PPO 试图做一件克制的事：让策略朝更高奖励方向更新，但每次更新不能太猛。它比较新策略和旧策略对同一动作的概率比值，如果优势为正，就希望提高该动作概率；如果优势为负，就希望降低概率。Clipping 机制把概率比限制在一个区间内，避免单个 batch 把策略推得过远。",
            "在 LLM 中，一个动作通常是一个 token，整段回答由许多 token 动作组成。PPO 会根据奖励模型或规则奖励得到整段回报，再通过价值函数和 GAE 把优势分配到 token 级别。这个分配并不完美：真正关键的语义决策可能跨越多个 token，所以训练需要足够多样的样本和稳定的 KL 约束。"
        ]),
        ("Rollout Buffer 为什么重要", [
            "PPO 是 on-policy 方法，训练数据应来自当前或非常接近当前的策略。Rollout buffer 保存一批刚生成的轨迹：prompt、生成 token、logprob、奖励、value、mask 和优势估计。完成若干个小批量更新后，这批数据就会过期，因为策略已经改变，概率比和 clipping 假设不再可靠。",
            "这解释了 PPO 为什么昂贵：每一轮都要重新生成、重新打分、重新估计优势。对于 RLHF，生成阶段常占用大量墙钟时间；因此工程系统会用 vLLM、PagedAttention、prefix sharing 和独立生成集群来提高 rollout 速度。"
        ]),
        ("PPO 的稳定性检查", [
            "训练 PPO 时，不能只看奖励上升。还要看 KL 是否失控、输出长度是否异常增长、策略熵是否突然坍缩、价值函数解释方差是否恶化、拒答率和格式错误率是否变化。奖励上升但人工胜率下降，通常说明模型在利用奖励模型漏洞。",
            "常见修复包括降低学习率、减小 clip range、提高 KL 惩罚、改进奖励模型、过滤异常长样本、重新平衡 prompt 分布，以及把过程奖励和规则验证加入评价。PPO 的价值不在于“万能强化学习”，而在于提供一套可控的策略更新框架。"
        ]),
    ],
    "chapter-07": [
        ("DPO 如何绕开奖励模型", [
            "DPO 的出发点是：如果我们已经有 chosen / rejected 偏好对，就不一定非要显式训练一个奖励模型再跑 PPO。它把偏好关系转化为策略相对于参考模型的 logprob 差异，让 chosen 回答相对 rejected 回答更可能，同时通过参考模型保持更新幅度受控。",
            "直觉上，DPO 在问：当前策略相对于参考策略，是否更偏向人类选择的回答？如果是，损失变小；如果策略反而提高了 rejected 的概率，损失变大。这个过程像监督学习一样稳定、便宜，不需要在线 rollout 和价值函数，但它依赖偏好数据覆盖目标分布。"
        ]),
        ("DPO 与 PPO 的差别", [
            "PPO 需要生成新样本、奖励模型打分、价值函数估计和 on-policy 更新，计算成本高但可以利用在线环境奖励。DPO 主要使用离线偏好数据，训练流程简单、稳定、易扩展，但对数据新鲜度和覆盖面更敏感。若模型上线后的任务分布与偏好数据差异很大，DPO 可能学不到真正需要的行为。",
            "PPO 更像“在环境中试错并受约束地改进”，DPO 更像“从比较样本中直接学习偏好边界”。在实践中二者并不互斥：可以用 SFT 建基线，用 DPO 做低成本偏好对齐，再对可验证任务或复杂智能体任务使用 RL 方法。"
        ]),
        ("DPO 的失败模式", [
            "第一类失败是偏好数据本身不可靠：chosen 只是更长、更礼貌或更像标注规范，而不是真的更有用。模型会学习这些表面相关性。第二类失败是 beta 等超参数不合适：约束太强学不动，约束太弱又会远离参考模型。第三类失败是多轮和工具任务的偏好粒度太粗，整段 chosen / rejected 无法告诉模型哪一步导致成功或失败。",
            "因此，DPO 数据应尽量包含困难负样本、真实失败样本和多样任务；训练后不仅看偏好准确率，还要看事实性、长度、拒答、格式、工具调用和人工胜率。"
        ]),
    ],
    "chapter-08": [
        ("GRPO 的群组相对优势", [
            "GRPO 常用于推理和可验证任务。它会对同一个 prompt 采样一组候选回答，并在组内比较它们的奖励。这样不必训练单独的 value head，也能得到相对优势：比同组平均更好的回答提高概率，比同组平均差的回答降低概率。",
            "这种设计适合数学、代码、逻辑题等可以自动判分的场景，因为同一问题的多个候选可以形成清晰对比。它也减少了价值模型带来的显存和训练复杂度，使大模型 RL 更容易扩展。"
        ]),
        ("GRPO 与 PPO、DPO 的关系", [
            "和 PPO 一样，GRPO 仍然通过采样生成候选并根据奖励更新策略，因此更接近在线强化学习；和 DPO 不同，它不只依赖固定偏好对，而是可以在训练过程中持续产生新样本。与 PPO 相比，GRPO 省掉 value head，使用组内相对归一化来估计优势，减少了价值函数误差。",
            "它的代价是每个 prompt 需要生成多个候选，采样成本较高；组内奖励如果过于稀疏或同质，优势信号会变弱。实践中常配合规则验证器、格式检查、长度控制和 KL 约束，避免模型只追求可验证答案而牺牲可读性。"
        ]),
        ("训练稳定性和数据构造", [
            "GRPO 的关键不是公式本身，而是奖励和采样设计。候选数量太少，组内比较噪声大；候选数量太多，生成成本上升。奖励只看最终答案时，模型可能学会猜答案或输出不可读推理；加入过程奖励或格式奖励可以改善，但也会引入新的 hacking 风险。",
            "高质量 prompt 应覆盖不同难度、不同解法和不同错误类型。对于代码任务，奖励可以来自单元测试；对于数学题，可以来自答案校验器；对于开放问答，则需要更谨慎的 judge model 或人工评审。"
        ]),
    ],
    "chapter-10": [
        ("奖励模型学到的是什么", [
            "奖励模型（Reward Model）把 prompt 和回答映射为一个标量分数。它通常不是判断绝对真理，而是近似“在给定标注规范下，人类更喜欢哪个回答”。Pairwise ranking 是常见训练方式：给定 chosen 和 rejected，模型学习让 chosen 分数高于 rejected。",
            "这个分数会驱动 PPO 或作为评估信号，因此它的偏差会被放大。若标注者偏好长答案，奖励模型可能奖励冗长；若训练集中错误答案也写得很自信，模型可能奖励自信语气；若安全样本过多，模型可能过度拒答。"
        ]),
        ("数据质量比模型结构更重要", [
            "构造偏好数据时要明确任务、标注准则和负样本来源。Rejected 不应只是随机差答案，最好包含真实模型容易犯的错误：事实幻觉、漏步骤、格式不符、工具调用错误、过度拒答、越权操作等。Chosen 也不应只有一种风格，否则模型会把风格误当质量。",
            "AI feedback 和 judge model 可以降低成本，但需要校准。自动 judge 容易受提示措辞、答案长度和表面格式影响；高风险任务仍需要人工抽检。奖励模型训练后要检查长度相关性、领域偏差、胜率曲线和对抗样本，而不是只看验证损失。"
        ]),
        ("奖励过优化与防护", [
            "Reward overoptimization 指策略持续提高奖励模型分数，但真实质量不再提高甚至下降。它通常发生在奖励模型覆盖不足、PPO 更新过强或评估指标单一时。防护方法包括 KL 约束、早停、奖励裁剪、独立验证集、人工评审和多指标监控。",
            "在 DPO / GRPO 中，奖励模型的角色会变化，但偏好数据和评价信号仍然重要。DPO 把偏好隐式写进损失，GRPO 常用规则奖励或 judge 分数。无论形式如何，奖励信号都必须接受审计。"
        ]),
    ],
}

EXTRA_EXPANDED_SECTIONS["chapter-03"].extend([
    ("生产部署的实用检查表", [
        "一个可上线的 LLM 服务通常需要先回答几组问题：模型权重是否能单卡容纳；目标并发下 KV Cache 是否会撑满 HBM；prompt 和输出长度的 P95 / P99 是多少；是否需要张量并行；是否能用量化降低带宽压力；是否需要 prefix caching；请求调度是否能承受长短请求混合。只有把这些数字放在一起，才知道瓶颈是在算力、显存容量、显存带宽、跨卡通信还是队列调度。",
        "实践中常用分层策略：短上下文、低风险请求走小模型或高吞吐实例；长上下文、复杂推理请求走更大模型并限制并发；工具调用任务把模型推理和外部 API 延迟分开监控；高价值任务保留人工复核或重试路径。系统设计的目标不是让单次推理最快，而是在质量、成本、延迟和可靠性之间找到可持续平衡。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-04"] = [
    ("从 RL 基础到 LLM 训练", [
        "把 LLM 放进强化学习框架时，状态可以是 prompt、系统消息、历史对话和已生成 token；动作可以是下一个 token、一个工具调用或一个高层计划步骤；奖励可以来自人类偏好、自动验证器、单元测试、规则检查或环境结果。这个映射让 RL 概念能用于语言模型，但也带来新难点：动作空间巨大、奖励稀疏、轨迹很长，而且同一个语义决策会跨越多个 token。",
        "因此，LLM 强化学习很少直接照搬传统控制任务。它通常会加入参考模型、KL 约束、偏好数据、奖励模型、格式规则和离线评估。理解这些工程补丁背后的 RL 概念，比背诵某个算法公式更重要。"
    ]),
]

EXTRA_EXPANDED_SECTIONS["chapter-05"].extend([
    ("数据构造决定对齐上限", [
        "从 SFT 到 RLHF 的核心资产不是单个算法，而是数据管线。SFT 需要高质量示范回答，偏好优化需要覆盖真实用户分布的比较样本，奖励模型需要一致的标注规范，线上反馈还要能回流到新的评估集。若数据只覆盖简单问答，模型在长任务、工具调用和安全边界上仍会脆弱。",
        "一条健康的数据管线会保留 prompt 来源、任务类型、候选生成模型、标注者判断、拒绝原因、长度、语言、工具调用日志和最终质量标签。这样才能在模型退化时定位原因：是任务分布变了、标注规则漂移、奖励模型偏了，还是策略训练过度优化。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("PPO 在 RLHF 中的完整闭环", [
        "一次 RLHF/PPO 迭代通常包括：从 prompt 池抽样；当前策略生成回答；奖励模型或规则系统打分；参考模型计算 KL；价值头估计每个位置的 value；用 GAE 计算优势；再用 clipped objective 更新策略和价值头。更新结束后，这批 rollout 基本作废，下一轮要重新生成。",
        "这条闭环把模型训练、推理服务和数据调度绑在一起。生成慢会拖垮训练，奖励模型不稳会污染梯度，KL 设置不当会导致模型要么学不动、要么偏离参考策略。PPO 的工程难点正是这些模块之间的耦合。"
    ]),
    ("为什么 clipping 能稳定更新", [
        "策略梯度本质上会鼓励高优势动作、抑制低优势动作，但如果新策略一次性把某些 token 概率放大很多，训练会变得不稳定。PPO 的 clipped ratio 把这种放大限制在一个小范围内：优势为正时，超过上界的收益不再增加；优势为负时，低于下界的收益不再继续鼓励。这样它近似实现了“只走可信的一小步”。",
        "Clipping 不是唯一约束。RLHF 中还常用 KL penalty，把新策略拉回参考模型附近，防止语言能力和安全行为被奖励模型牵着跑。实践中 clipping、KL、学习率、batch size、优势归一化和奖励缩放要一起调。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 损失的简化理解", [
        "DPO 可以用一句话理解：让策略相对于参考模型，更偏向 chosen，而不是 rejected。它关心的是两个回答的相对 logprob 差，而不是单个回答的绝对分数。参考模型提供一个锚点，避免策略单纯把所有 chosen 概率推高到不合理程度。",
        "Beta 控制偏好约束强度。Beta 太小，策略可能变化过大；beta 太大，模型学到的偏好信号又很弱。实际训练中会同时观察偏好准确率、验证胜率、KL、长度分布和人工样本，而不是只看 DPO loss。"
    ]),
    ("什么时候不用 DPO", [
        "如果任务需要在环境中探索，例如代码智能体要调用工具、修复错误、根据测试反馈调整，固定偏好对往往不够。DPO 很适合把已收集的比较数据转成稳定训练信号，却不擅长从新环境反馈中主动发现策略。此时 PPO、GRPO 或其他在线方法更合适。",
        "另外，当偏好数据质量很差、chosen/rejected 差异不清、或 rejected 只是随机坏样本时，DPO 会学到浅层风格而非能力。高质量 hard negative 和真实失败样本，是 DPO 能否提升模型的关键。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("组内比较为何适合推理任务", [
        "在数学、代码和逻辑推理任务中，同一个 prompt 往往可以采样出多个候选，有的完全正确，有的中间步骤正确但答案错，有的格式错。GRPO 利用这种组内差异，不需要先构造成固定的 chosen/rejected 对，也不需要训练单独 value head。只要奖励函数能区分好坏，组内相对优势就能提供学习信号。",
        "组内归一化还让不同题目的奖励尺度更可比。某些题整体很难，候选分数都低；某些题整体容易，候选分数都高。用同组平均作为参照，可以让模型关注“在这道题的候选里谁更好”，而不是被跨题分数尺度扰动。"
    ]),
    ("GRPO 的工程代价", [
        "GRPO 的代价主要在生成侧。每个 prompt 采样多个回答会显著增加 token 生成量，也会放大 KV Cache 和调度压力。训练系统通常要把生成、奖励计算和参数更新拆成独立组件，并用高吞吐推理后端减少 rollout 成本。",
        "另一个代价是奖励设计。若只奖励最终答案，模型可能学会输出最短答案而省略推理；若奖励推理过程，又可能学会迎合格式。实践中要把正确性、格式、长度、安全和可读性放进同一套监控，而不是让单一 reward 主导全部更新。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-03"].extend([
    ("系统性能调优的常见误区", [
        "第一个误区是只看峰值 FLOPS。LLM 推理里很多时间花在读写权重、KV Cache 和中间张量上，算力没有吃满并不一定是内核写得差，也可能是 batch 太小、序列太长、HBM 带宽不足或调度碎片太多。第二个误区是只看平均延迟。线上用户体验往往由 P95 / P99 决定，少量超长请求就能拖慢整个批次。",
        "第三个误区是把量化当作无损万能药。权重量化能降低显存和带宽压力，但不同层、不同任务、不同采样策略对精度更敏感；KV Cache 量化也会影响长上下文质量。合理做法是按任务建立离线评估集和线上监控，在质量退化可接受的前提下逐步压缩。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-05"].extend([
    ("为什么 RLHF 仍然需要 SFT", [
        "即使最终要做 PPO、DPO 或 GRPO，SFT 仍然是重要起点。没有 SFT 的基础策略可能不会遵循对话格式，不知道何时停止，也不会稳定调用工具。强化学习在这样的策略上会浪费大量样本，还容易把奖励模型的局部偏好放大成奇怪行为。",
        "好的 SFT 像给模型铺好轨道：它先学会基本语言、任务格式、安全规范和回答结构；后续偏好优化再微调轨道方向。若 SFT 太弱，RL 阶段要同时学习能力和偏好，训练会不稳定；若 SFT 过强且数据单一，后续优化又可能被模板化行为限制。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("价值函数、优势与奖励放置", [
        "PPO 需要知道一个 token 动作到底比平均选择好多少，这就是 advantage。Value head 估计从当前状态继续生成的期望收益，实际回报和 value 的差异形成优势信号。若奖励只在回答末尾出现，优势要沿着整段序列向前传播，长回答会让信用分配变得稀薄；若奖励过于密集，又可能鼓励模型迎合过程指标。",
        "GAE 用一个参数在偏差和方差之间折中。更接近 Monte Carlo 的估计更忠实于真实回报，但方差大；更依赖 value 的估计更平滑，但若 value head 错了会有系统偏差。LLM 训练里常要配合优势归一化、奖励归一化和长度控制，避免少数极端样本主导更新。"
    ]),
    ("PPO 失败时先看什么", [
        "如果奖励上升但人工质量下降，先检查奖励模型是否被钻空子；如果 KL 快速升高，说明策略偏离参考模型过快；如果输出越来越长，可能是奖励或标注偏好长度；如果 entropy 很快下降，模型可能过早收敛到单一模式；如果 value loss 持续异常，优势估计会不可信。",
        "修复顺序通常是先收紧更新：降学习率、提高 KL、缩小 clip range、减少 epoch；再修奖励和数据：加入 hard negative、长度惩罚、格式检查、人工抽检；最后才考虑换算法。PPO 的调参不是魔法，而是围绕分布漂移、奖励偏差和信用分配三类问题排查。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("偏好对的粒度问题", [
        "DPO 的训练样本通常是一整个 chosen 回答和一个 rejected 回答，但真实偏好往往只来自其中几个关键片段。比如 rejected 可能前半段推理正确，只在最后算错；chosen 可能答案正确但解释冗长。整段级别的偏好会把全部 token 都推向同一方向，带来噪声。",
        "改进方法包括构造更接近真实错误的负样本、把多轮任务拆成步骤级比较、保留标注理由、对长度和格式做归一化，并在验证集中单独评估事实性、推理、简洁度和安全。DPO 简化了训练流程，但没有消除数据设计难题。"
    ]),
    ("Online DPO 的折中位置", [
        "Offline DPO 使用固定偏好数据，便宜稳定，但数据会随着策略变化变旧。Online DPO 在训练过程中用当前策略生成新候选，再用人类、规则或 judge model 产生偏好信号，然后继续用 DPO 风格目标更新。它试图在 PPO 的在线探索和 DPO 的稳定优化之间折中。",
        "这种方法仍然要面对 judge 可靠性、采样成本和反馈延迟。若自动 judge 偏差大，在线生成只会更快放大奖励漏洞；若采样太少，模型探索不足；若反馈太慢，训练循环难以扩展。因此 Online DPO 更像系统工程方案，而不只是一个损失函数替换。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("GRPO 在智能体任务中的潜力", [
        "当智能体执行同一任务时，可以采样多条轨迹：有的调用正确工具但总结错误，有的路径更短，有的恢复了失败，有的越权或循环。GRPO 的组内比较思想也能用于这类轨迹，只要奖励系统能评价最终结果、步骤成本和安全边界。",
        "不过智能体轨迹比单段答案更复杂。奖励不仅要看最终是否成功，还要看工具参数是否安全、是否泄露敏感信息、是否重复无效操作、是否遵守权限。组内相对优势能提供方向，但必须配合轨迹日志、环境回放和人工审计。"
    ]),
    ("与可验证奖励的关系", [
        "Verifiable reward 指可以由程序或环境自动判定的奖励，例如数学答案、代码单元测试、格式校验、数据库查询结果或网页任务完成状态。GRPO 与这类奖励天然适配，因为同一 prompt 的多个候选可以快速得到分数。",
        "可验证奖励也有边界。测试覆盖不全会鼓励模型只通过公开样例；格式校验不能保证内容正确；环境成功率可能忽略安全和可解释性。因此扩展到真实智能体时，GRPO 往往需要多奖励组合，而不是单一正确/错误信号。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-03"].extend([
    ("一个部署容量估算例子", [
        "假设要部署一个中等规模对话模型，首先要估算权重占用，再估算每个并发请求的上下文和输出会带来多少缓存。短问答场景中，权重可能是主要显存项；长文档问答中，缓存会随着上下文长度迅速膨胀；多候选生成或智能体反复尝试时，同一个用户任务也可能占用多条生成序列。容量规划不能只看模型参数量，还要把真实请求分布、最大上下文、输出上限和重试策略一起算进去。",
        "如果系统延迟高，排查顺序通常是：先看请求是否在队列里等待；再看首 token 延迟是否来自预填充；然后看解码阶段每 token 延迟；最后看跨卡通信、缓存碎片和外部工具调用。这样能避免把所有问题都归咎于模型太大。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-05"].extend([
    ("从偏好样本看训练目标", [
        "一条偏好样本不只是 chosen 和 rejected 两个字符串。它背后还有任务说明、用户意图、标注准则和比较理由。若标注者选择 chosen 是因为它更准确，那么训练目标应推动事实性；若是因为格式更清楚，就应推动结构化表达；若只是因为更长，模型可能学到错误偏好。因此，偏好数据最好保留理由标签，便于后续分析模型到底学会了什么。",
        "RLHF 的难点在于偏好是多目标的：有用、真实、无害、简洁、礼貌、可执行往往互相拉扯。一个回答可能更安全但不够有用，也可能更直接但风险更高。训练系统需要把这些目标拆成评价维度，而不是把所有东西压成一个无法解释的分数。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("PPO 与语言能力保持", [
        "PPO 训练如果只追逐任务奖励，模型可能忘记原本的通用语言能力。比如在数学奖励上训练太久，模型可能变得冗长、模板化，甚至在普通对话中也输出推理痕迹。参考模型和 KL 约束的作用，就是让新策略在获得任务收益的同时，不要离开原始语言分布太远。",
        "这也是为什么 RLHF 实验要保留通用能力回归测试：摘要、问答、代码、中文表达、安全拒答和格式遵循都要检查。只在目标 benchmark 上变好，不代表模型整体可用。对产品系统而言，PPO 的收益必须覆盖它带来的成本、复杂性和潜在退化。"
    ]),
    ("奖励尺度和长度偏差", [
        "奖励分数的尺度会影响 PPO 更新强度。若奖励范围很大，优势估计会放大，策略更新可能过猛；若奖励范围太小，模型学不动。常见做法包括奖励归一化、裁剪、减去基线，以及把长度惩罚或格式惩罚单独监控。",
        "长度偏差尤其常见。若标注者偏好详细解释，奖励模型可能把长答案当成高质量；PPO 随后会进一步拉长输出。解决办法不是简单限制最大长度，而是构造同样长度但质量不同的比较样本，或者在评估中分离准确性、简洁性和覆盖度。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 的工程优势", [
        "DPO 最大的工程优势是流程简单。它不需要在线生成 rollout，不需要训练 value head，也不需要在每轮迭代中调用奖励模型。训练形式接近普通监督微调，因此更容易扩展到大数据、更容易复现实验，也更适合在已有偏好数据上快速迭代。",
        "这种简单性让 DPO 成为很多团队的首选偏好优化方法：先用 SFT 建立基础助手，再用 DPO 吸收高质量比较数据，最后用人工评估和线上反馈判断是否还需要更昂贵的在线强化学习。它降低了对齐训练门槛，但也要求团队对数据质量更负责。"
    ]),
    ("DPO 评估不能只看偏好准确率", [
        "偏好准确率衡量模型是否能区分验证集里的 chosen 和 rejected，但它不一定代表用户体验。模型可能靠长度、格式、礼貌套话或常见模板赢得偏好，而不是解决任务。评估应加入真实任务成功率、事实核查、拒答合理性、长上下文稳定性和多轮一致性。",
        "对于工具调用和智能体任务，DPO 还要检查行动正确性。一个回答文本看起来更好，不代表工具参数安全、执行顺序正确或环境结果达标。若偏好数据没有包含轨迹级信号，DPO 的改进会停留在表面表达。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("组大小、奖励噪声和训练成本", [
        "组大小越大，组内相对比较越稳定，但生成成本也越高。小组大小适合快速实验，大组大小更适合奖励稀疏、答案差异大的推理任务。若奖励函数噪声很大，增加组大小只能部分缓解；更根本的是改进验证器、清理题目和分层统计不同错误类型。",
        "训练成本还来自奖励计算。代码任务要跑测试，网页任务要驱动环境，复杂问答要调用 judge model。生成和奖励都很贵时，系统需要缓存中间结果、限制最大尝试次数、对难题分层采样，并把失败轨迹保留下来做后续分析。"
    ]),
    ("从 GRPO 走向更通用的偏好优化", [
        "GRPO 展示了一个重要方向：不一定要为每个状态训练准确的 value function，只要能构造相对比较，也能推动策略改进。这个思想可以扩展到排序奖励、列表偏好、过程奖励和多候选筛选。它把训练从“预测一个绝对分数”转向“在一组候选中识别更好行为”。",
        "但相对比较也会受候选集合影响。如果一组候选都很差，最好的那个也未必值得学习；如果一组候选都很好，差异可能只是风格。高质量采样策略应混合容易题、困难题、边界题和真实失败题，让相对优势真正反映能力改进。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-03"].extend([
    ("把系统指标翻译成产品指标", [
        "工程指标最终要落到产品体验上：首 token 延迟影响用户是否觉得系统有响应；每 token 延迟影响长回答等待感；吞吐影响成本；超时和重试影响可靠性；显存利用率影响容量规划。一个成熟服务会把这些指标按任务类型拆开，而不是用单一平均值概括所有流量。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("PPO 与数据新鲜度", [
        "PPO 的 on-policy 特性意味着数据新鲜度非常重要。旧策略生成的轨迹不能无限复用，因为新策略对同一 token 的概率已经改变，概率比会失真，clipping 也失去意义。为了减少浪费，系统会在同一批 rollout 上做有限个 epoch，但超过这个范围就要重新采样。",
        "这让 PPO 的训练节奏像一个流水线：生成、打分、估值、更新、同步权重，再生成。任何环节拖慢都会影响整体效率。权重同步太慢会让生成策略和训练策略不一致，奖励服务太慢会让 GPU 等待，数据队列设计不当会造成样本分布偏移。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("从 DPO 到偏好优化家族", [
        "DPO 之后出现了许多变体，它们通常围绕三个问题展开：怎样处理偏好强度，怎样降低长度和格式偏差，怎样让训练目标更符合真实人类选择。IPO 强调有界偏好，避免把偏好概率推到极端；ORPO 尝试把偏好优化并入监督训练目标；KTO 则面向非配对反馈。",
        "这些方法不是简单谁替代谁，而是适合不同数据条件。若有高质量成对偏好，DPO 是强基线；若只有好/坏反馈，KTO 更自然；若希望少一次训练阶段，ORPO 有吸引力；若偏好标签噪声大，强调有界目标的方法可能更稳。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("GRPO 的常见失败模式", [
        "第一类失败是奖励太稀疏：一组候选都得零分，模型不知道该往哪里改。第二类失败是奖励太容易被投机：模型学会输出固定格式或猜测答案，而不是提升推理能力。第三类失败是候选缺乏多样性：组内回答高度相似，相对优势没有足够信息。第四类失败是 KL 约束太弱，模型为了可验证奖励牺牲通用表达。",
        "对应修复包括增加候选多样性、分层采样难题、加入过程检查、保留参考模型约束、混合通用指令数据，并用人工样本审计高分回答。GRPO 的优势在于把推理训练做得更可扩展，但它仍然需要严谨的数据和评估系统。"
    ]),
    ("与后续智能体训练的连接", [
        "在智能体训练中，组内比较可以从单段答案扩展到整条任务轨迹。同一个目标可以有多种执行路线：少量工具调用快速完成、反复试错后完成、错误调用后恢复、或看似完成但违反约束。若能把这些轨迹放在同一组里比较，模型就能学习更高层的策略偏好，而不只是下一个 token 的局部概率。",
        "这也是 GRPO 与 Agentic AI 的连接点：未来的优化对象不只是回答文本，而是包含观察、行动、工具、记忆和环境反馈的完整行为序列。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-03"].extend([
    ("本章收束", [
        "系统基础章节的核心结论是：LLM 服务不是单纯调用模型，而是一套围绕显存、带宽、并发、调度和可靠性的工程系统。理解硬件和服务化约束，才能解释后续 PPO、GRPO 与智能体训练为什么总是被生成成本和环境反馈速度限制。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("何时选择 PPO", [
        "当任务有在线环境反馈、奖励可以持续生成、并且需要策略主动探索时，PPO 仍然有价值。例如工具调用智能体、代码修复、可交互环境和复杂多步任务，都可能需要模型在新轨迹中试错。若只有固定偏好数据，DPO 往往更便宜；若有可验证答案且希望多候选比较，GRPO 可能更合适。",
        "选择 PPO 前要确认团队能承受它的系统复杂度：高吞吐生成、奖励服务、参考模型、价值头、日志追踪、失败样本分析和多指标评估缺一不可。没有这些基础设施，PPO 容易变成昂贵且不可解释的训练实验。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 的实践落地顺序", [
        "实践中可以按四步落地 DPO：先整理 SFT 基线和对话模板；再构造覆盖真实任务的偏好对，保证 chosen 和 rejected 差异有意义；然后小规模训练并观察 KL、长度、拒答和人工样本；最后再扩大数据和模型规模。这个顺序能尽早发现数据偏差，避免在大规模训练后才发现模型只是学会了表面风格。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("GRPO 的实践落地顺序", [
        "落地 GRPO 时，先从可验证任务开始，例如数学、代码或格式明确的问题；再确定每个 prompt 的候选数量、奖励函数和 KL 约束；随后监控组内奖励方差、通过率、输出长度、格式错误和人工样本质量。只有当奖励可靠、候选有差异、系统能承受生成成本时，GRPO 的优势才会显现。",
        "如果奖励函数还不成熟，可以先用 Best-of-N 或离线重排序收集失败样本，再进入训练。这样能把问题拆开：先验证奖励是否能选出好答案，再验证策略是否能通过训练更常生成好答案。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("复习判断：PPO 是否适合当前问题", [
        "可以用一个简单判断：如果你有稳定的离线偏好数据，先考虑 DPO；如果你有可验证奖励且能为同一题生成多候选，考虑 GRPO；如果任务必须在当前环境中探索，并且奖励只能从新轨迹中获得，再考虑 PPO。PPO 的优势是能利用在线反馈，代价是训练链路长、调参复杂、排障成本高。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("复习判断：DPO 的关键问题", [
        "读完 DPO 后应能回答三个问题：偏好对是否可信，参考模型是否合适，训练后行为是否真的改善。若这三个问题没有证据，DPO loss 下降并不等于对齐成功。DPO 的工程美感在于简单，但它的成败仍然取决于偏好数据和评估闭环。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("复习判断：GRPO 的关键问题", [
        "读完 GRPO 后应能判断：奖励是否可验证，组内候选是否有足够差异，相对优势是否能反映真正能力，生成成本是否可接受。若奖励不可靠或候选过于同质，GRPO 只会把噪声训练得更稳定；若奖励清晰、候选多样，它就能成为推理模型和智能体轨迹优化的有力工具。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("本章小提醒", [
        "学习 PPO 时不要把注意力只放在裁剪公式上。真正决定训练质量的是整套闭环：样本是否来自当前策略，奖励是否可信，优势是否稳定，参考模型约束是否合适，更新后通用能力是否保持。只要其中一环失控，漂亮的目标函数也无法保证模型变好。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("本章小提醒", [
        "学习 DPO 时要记住，它把复杂的偏好优化压缩成更像监督学习的形式，因此容易上手，也容易被误用。若偏好对本身浅、脏、偏或过时，DPO 会忠实学习这些问题。干净、有解释力、覆盖真实任务的数据，比换一个更新的损失函数更重要。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("本章小提醒", [
        "学习 GRPO 时要把“组”看作训练信号的来源。同一问题下多个候选之间的相对好坏，提供了比单个绝对分数更稳的方向。但这要求候选真的有差异，奖励真的能区分质量，系统真的能承担多候选生成的成本。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("PPO 章节的实践复盘", [
        "真正执行一次 PPO 实验时，建议把每轮训练都记录成可复盘事件：本轮使用哪些提示，策略版本是什么，奖励模型版本是什么，平均奖励、平均长度、平均 KL、胜率和失败样本分别如何变化。这样当模型突然退化时，可以回到具体数据和配置，而不是只面对一条下降曲线。",
        "另外，PPO 的收益通常不是线性的。早期可能很快提升，因为模型学会基本偏好；中期会变慢，因为容易样本已经学完；后期可能因为奖励过优化而退化。合适的停止点往往来自人工评估、回归测试和线上风险，而不是训练损失。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 章节的实践复盘", [
        "做 DPO 实验时，最先要检查的是样本对是否真的表达偏好。一个高质量样本对应该让读者清楚知道 chosen 为什么更好：事实更准确、推理更完整、格式更合规、工具调用更安全，或拒答更合理。如果只是 chosen 更长、语气更像助手，模型就会学习这些浅层信号。",
        "第二个检查是参考模型。参考模型通常是 SFT 后的策略，它决定了 DPO 更新的锚点。若参考模型太弱，DPO 要修正的行为太多；若参考模型已经很强但偏好数据很窄，训练可能过度拟合局部风格。参考模型、偏好数据和目标任务必须匹配。",
        "第三个检查是上线前回归。DPO 可能提升偏好胜率，同时改变拒答率、回答长度、格式稳定性或多轮一致性。只有把这些指标一起看，才能判断它是不是可发布的对齐改进。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-08"].extend([
    ("GRPO 章节的实践复盘", [
        "做 GRPO 实验时，建议先把每个 prompt 的候选、奖励和最终更新样本完整保存。若某道题的组内候选差异很小，训练信号就弱；若奖励最高的候选肉眼看并不好，说明奖励函数需要修；若高分候选都很长或格式类似，说明模型可能在学表面模式。",
        "GRPO 的成功常来自三件事同时成立：任务可以自动验证，候选生成有足够多样性，奖励和人工判断大体一致。缺少任意一项，训练都可能变成放大噪声。它适合推理模型和可验证环境，但不是所有开放式对话任务的默认选择。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("与前后章节的关系", [
        "PPO 承接前一章的 SFT / RLHF 流水线，也为后面的 DPO、GRPO 提供对照。理解 PPO 后，会更容易看清 DPO 为什么要避开奖励模型和在线采样，也会更容易理解 GRPO 为什么要用组内相对优势替代价值函数。换句话说，PPO 是理解偏好优化家族的参照系：它功能完整、反馈在线、表达能力强，但成本高、系统复杂、稳定性要求严。",
        "在智能体训练中，PPO 的思想仍然重要，因为很多任务必须通过环境反馈学习。即使最终不直接使用 PPO，也需要借用它对轨迹、奖励、优势、参考约束和策略漂移的分析框架。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("与前后章节的关系", [
        "DPO 位于 SFT 和在线强化学习之间。它比 SFT 更能利用偏好比较，比 PPO 更便宜稳定，但也比 GRPO 更依赖固定数据。理解 DPO 后，可以把许多偏好优化方法看成在同一个问题上做不同折中：如何在不破坏参考模型能力的前提下，让策略更偏向人类或环境认为更好的回答。",
        "后续的 KTO、IPO、ORPO 和 Online DPO 都可以从这个视角理解：有的方法改变反馈形式，有的方法改变目标约束，有的方法改变训练阶段，有的方法把离线偏好和在线采样混合起来。DPO 是进入这个家族的最清晰入口。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-06"].extend([
    ("一句话复盘", [
        "PPO 的核心不是让模型追逐更高分，而是在可信范围内利用新反馈改进策略。只要记住“新鲜轨迹、优势估计、裁剪更新、参考约束、质量回归”这五个关键词，就能把 PPO 放回完整 RLHF 系统中理解。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("案例化理解 DPO", [
        "假设同一个问题有两个回答：回答甲事实准确但表达简洁，回答乙语气热情却包含错误。SFT 会把某个示范答案当作目标继续模仿，而 DPO 会直接利用“甲优于乙”这个比较关系。它不会先训练一个奖励模型给甲和乙分别打分，而是调整策略，使模型相对于参考模型更愿意生成甲这类回答、更少生成乙这类回答。",
        "再看一个多轮任务：用户要求修改代码，chosen 回答先解释风险，再给出最小修改，并提醒测试；rejected 回答直接大改结构，还遗漏边界情况。DPO 可以从这种偏好对中学习“少改、可测、解释关键风险”的倾向。但如果 rejected 只是语气差而不是技术差，模型学到的也会偏向语气。样本设计决定了 DPO 学会的是能力还是表面风格。",
        "因此，DPO 数据最好覆盖多种失败形态：事实错误、推理跳步、格式不符、过度冗长、拒答不当、工具参数危险、代码不可运行、引用不可靠。每类失败都应有清楚的 chosen 对照。这样训练出来的模型才会在真实场景中更稳，而不是只在验证集上更会选择漂亮答案。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 最后的学习抓手", [
        "把 DPO 记成一个数据问题会更稳：它需要清楚的比较、可信的参考、适度的更新和多维度评估。只要这四件事成立，DPO 就能以较低成本吸收偏好；如果其中任何一件缺失，训练曲线再漂亮也需要谨慎解释。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 与真实产品反馈", [
        "真实产品里的反馈并不总是成对偏好。用户可能只点赞、点踩、追问、复制、放弃、改写问题，或者在任务失败后离开。要把这些信号用于 DPO，通常需要先转化为比较样本：同一意图下成功回答优于失败回答，被用户追问修正的回答可能劣于一次解决问题的回答，通过人工复核的工具轨迹优于越权或无效轨迹。",
        "这个转换过程需要谨慎。点击和停留时间不一定代表质量，用户沉默也不一定代表满意。生产系统通常会把隐式反馈、人工标注、自动评估和失败日志结合起来，先构造高置信偏好对，再用 DPO 训练。否则模型可能学习用户行为噪声，而不是学习真正有用的回答。",
        "因此，DPO 的长期价值取决于反馈治理：哪些信号可以进训练集，哪些只用于监控，哪些需要人工复核，哪些必须因隐私或安全原因丢弃。偏好优化不是一次训练任务，而是一套持续维护的数据产品。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("DPO 数据集如何分层", [
        "一个实用的 DPO 数据集可以按任务和失败类型分层。任务层面包括知识问答、数学推理、代码修改、摘要、长文档问答、多轮对话和工具调用。失败类型层面包括事实错误、遗漏约束、推理跳步、格式不符、输出过长、拒答不当、安全边界错误和工具参数错误。分层的意义是让训练后评估能定位改进来自哪里，也能发现某些能力是否退化。",
        "如果所有偏好样本都混在一起，模型可能只学习最高频的浅层模式。例如数据里大量 chosen 都更长，模型会倾向扩写；大量 rejected 都语气生硬，模型会倾向礼貌套话；大量安全样本都以拒答为佳，模型会提高拒答率。分层采样和分层报告可以降低这些偏差，让 DPO 更接近真实对齐。",
        "评估时也要按层看结果。总胜率提升可能掩盖代码任务下降，平均长度正常可能掩盖长文档任务过短，安全拒答提升可能掩盖有用性下降。DPO 适合快速迭代，但每轮迭代都应留下清楚的数据版本、模型版本和分层指标，方便后续回滚和比较。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("最终收束", [
        "DPO 的学习重点可以收成一句话：用比较数据直接塑造策略偏好，同时用参考模型约束更新幅度。它不是万能对齐算法，却是理解现代偏好优化最好的起点。"
    ]),
])

EXTRA_EXPANDED_SECTIONS["chapter-07"].extend([
    ("补充提示", [
        "在实际项目中，DPO 常作为第一轮偏好优化基线，用来验证数据质量、训练稳定性和评价体系是否可靠。"
    ]),
])

TITLE_FIXES = {
    "分词 / 分词 / 分词 / 标记化": "分词与标记化",
    "在线数据保护官": "在线 DPO",
    "ORPO：赔率比偏好优化": "ORPO：优势比偏好优化",
}

BAD_TEXT_PATTERNS = [
    "公式内容已由 OCR 清洗", "锟斤拷", "���", "□", "\ufffd", "数据保护官",
    "Action-Value Function", "Advantage Function", "expected return", "following π", "Don’t wait",
    "Eliminates KV", "using the block table", "The block table", "final sequence length",
]


def normalize_text(text: str) -> str:
    text = html.unescape(str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    replacements = {
        "政策": "策略",
        "奖励模式": "奖励模型",
        "客服人员": "智能体",
        "数据保护官": "DPO",
        "冰冷模型": "策略模型",
        "优势比偏好优化": "赔率比偏好优化（ORPO）",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def clean_title(title: str) -> str:
    title = normalize_text(title)
    return TITLE_FIXES.get(title, title)


def is_useful_paragraph(text: str) -> bool:
    text = normalize_text(text)
    if len(text) < 55 or len(text) > 900:
        return False
    if any(pattern in text for pattern in BAD_TEXT_PATTERNS):
        return False
    if re.fullmatch(r"(第[一二三四五六七八九十0-9]+章|第一章|第二章|第三章|LLM架构与优化 方法)", text):
        return False
    if text.startswith(("图 ", "表 ", "Figure ", "Table ")):
        return False
    ascii_letters = len(re.findall(r"[A-Za-z]", text))
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    if ascii_letters > max(80, han * 1.2):
        return False
    return True


def selected_source_sections(ast_by_id: dict[str, dict], source_ids: list[str], needed_chars: int) -> list[dict]:
    sections: list[dict] = []
    used: set[str] = set()
    total = 0
    for source_id in source_ids:
        chapter = ast_by_id[source_id]
        for sec in chapter.get("sections", []):
            title = clean_title(sec.get("title", "原书主题"))
            paras: list[str] = []
            for block in sec.get("blocks", []):
                if block.get("type") != "paragraph":
                    continue
                para = normalize_text(block.get("text", ""))
                if not is_useful_paragraph(para) or para in used:
                    continue
                used.add(para)
                paras.append(para)
                if sum(len(p) for p in paras) > 780:
                    break
            if paras:
                body = " ".join(paras)
                sections.append({
                    "title": f"原书主题重编：{title}",
                    "body": body,
                    "source": source_id,
                })
                total += len(body)
            if total >= needed_chars:
                return sections
    return sections


def supplement_sections(slug: str) -> list[dict]:
    guide = EXPANSION_GUIDES.get(slug, {})
    out = []
    for title, paragraphs in guide.get("supplement", []):
        out.append({"title": title, "body": "\n\n".join(paragraphs), "source": "v4.1"})
    for title, paragraphs in EXTRA_EXPANDED_SECTIONS.get(slug, []):
        out.append({"title": title, "body": "\n\n".join(paragraphs), "source": "v4.1-expanded"})
    return out


def merge_table(blueprint: dict) -> tuple[str, list[str], list[list[str]]]:
    guide_table = EXPANSION_GUIDES.get(blueprint["slug"], {}).get("table")
    return guide_table or blueprint["table"]


def expanded_concepts(ast_by_id: dict[str, dict], source_ids: list[str], slug: str) -> list[dict]:
    concepts = concepts_for_sources(ast_by_id, source_ids)
    keyword_notes = {
        "chapter-02": [("键值缓存", "KV Cache", "保存历史 Key/Value 的推理缓存。"), ("FlashAttention", "FlashAttention", "降低注意力 HBM 读写的精确注意力实现。")],
        "chapter-03": [("高带宽显存", "HBM", "GPU 高速显存。"), ("PagedAttention", "PagedAttention", "分页管理 KV cache 的推理机制。")],
        "chapter-11": [("轨迹缓冲区", "Trajectory Buffer", "保存智能体多步经验的数据结构。"), ("ReAct", "ReAct", "交替组织思考和行动的智能体范式。")],
        "chapter-12": [("检索增强生成", "RAG", "检索证据后再生成答案。"), ("重排序", "Reranking", "对检索候选进行二次排序。")],
    }
    seen = {c["label"] for c in concepts}
    for label, term, note in keyword_notes.get(slug, []):
        if label not in seen:
            concepts.append({"label": label, "term": term, "note": note})
            seen.add(label)
    return concepts[:10]


def build_lessons(ast: dict, inventory: dict) -> list[dict]:
    ast_by_id = {ch["id"]: ch for ch in ast["chapters"]}
    lessons: list[dict] = []
    old_lengths: dict[str, int] = {}
    for index, blueprint in enumerate(LESSON_BLUEPRINTS, start=1):
        source_ids = blueprint["sources"]
        source_chapters = [ast_by_id[sid] for sid in source_ids]
        merged_text = "\n".join(text_from_blocks(ch) for ch in source_chapters)
        term_counter = Counter(re.findall(r"[A-Za-z][A-Za-z0-9+\-]*|[\u4e00-\u9fff]{2,}", merged_text))
        base_sections = [{"title": title, "body": body, "source": "v4"} for title, body in blueprint["sections"]]
        extras = supplement_sections(blueprint["slug"])
        current_chars = sum(len(s["body"]) for s in base_sections + extras)
        target = EXPANSION_TARGETS.get(blueprint["slug"], 3000)
        needed_chars = max(0, target - current_chars)
        source_sections = selected_source_sections(ast_by_id, source_ids, needed_chars) if needed_chars else []
        sections = base_sections + extras + source_sections
        table = merge_table(blueprint)
        old_file = REPO / "v4" / "chapters" / f"{blueprint['slug']}.html"
        old_len = 0
        if old_file.exists():
            old_text = re.sub(r"<[^>]+>", " ", old_file.read_text(encoding="utf-8", errors="ignore"))
            old_len = len(re.findall(r"[\u4e00-\u9fff]", old_text))
        old_lengths[blueprint["slug"]] = old_len
        body_text = " ".join(s["title"] + " " + s["body"] for s in sections)
        lesson = {
            "number": index,
            "id": blueprint["slug"],
            "title": blueprint["title"],
            "subtitle": blueprint["subtitle"],
            "stage": blueprint["stage"],
            "edition": EDITION,
            "sources": source_ids,
            "source_titles": [ch["title"] for ch in source_chapters],
            "source_topics": source_topics(ast_by_id, source_ids),
            "objectives": blueprint["objectives"],
            "concepts": expanded_concepts(ast_by_id, source_ids, blueprint["slug"]),
            "sections": sections,
            "table": {"title": table[0], "headers": table[1], "rows": table[2]},
            "formula": blueprint["formula"],
            "summary": blueprint["summary"],
            "questions": blueprint["questions"],
            "reading": blueprint["reading"],
            "keywords": [word for word, _ in term_counter.most_common(18)],
            "source_inventory": inventory,
            "target_chars": target,
            "old_length": old_len,
            "char_count": len(re.findall(r"[\u4e00-\u9fff]", body_text)),
            "omitted_topics": EXPANSION_GUIDES.get(blueprint["slug"], {}).get("omitted", []),
            "priority": EXPANSION_GUIDES.get(blueprint["slug"], {}).get("priority", "中"),
        }
        lessons.append(lesson)
    return lessons


def paragraphs_html(body: str) -> str:
    parts = [part.strip() for part in re.split(r"\n{2,}", body or "") if part.strip()]
    return "".join(f"<p>{esc(part)}</p>" for part in parts)


def render_table(table: dict) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in table["headers"])
    rows = "".join("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in table["rows"])
    return f'<section class="lesson-block"><h2>关键图表 / 表格：{esc(table["title"])}</h2><div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>'


def build_chapters(lessons: list[dict]) -> None:
    for idx, lesson in enumerate(lessons):
        prev_link = f'<a href="{lessons[idx-1]["id"]}.html">上一章：{esc(lessons[idx-1]["title"])}</a>' if idx else "<span></span>"
        next_link = f'<a class="next" href="{lessons[idx+1]["id"]}.html">下一章：{esc(lessons[idx+1]["title"])}</a>' if idx + 1 < len(lessons) else "<span></span>"
        section_html = "".join(
            f'<section class="lesson-block"><h2>{esc(section["title"])}</h2>{paragraphs_html(section["body"])}</section>'
            for section in lesson["sections"]
        )
        concept_html = concept_chips(lesson["concepts"])
        source_badges = "".join(f"<span>{esc(title)}</span>" for title in lesson["source_titles"])
        topics = "".join(f"<li>{esc(topic)}</li>" for topic in lesson["source_topics"][:10])
        coverage = "".join(f"<li>{esc(topic)}</li>" for topic in lesson.get("omitted_topics", []))
        body = f"""
        <article class="lesson-article expanded">
          <header class="lesson-header">
            <p class="chapter-number">第 {lesson["number"]:02d} 章 · {esc(lesson["stage"])} · {EDITION}</p>
            <h1>{esc(lesson["title"])}</h1>
            <p>{esc(lesson["subtitle"])}</p>
            <div class="source-badges">{source_badges}</div>
          </header>
          <section class="lesson-block intro"><h2>本章导读</h2><p>本章是 V4.1 扩写版内容：在 V4 预览版清晰学习路径的基础上，补入更多来自原 PDF、V3 clean AST 与完整中文译文的知识点，并清理文本提取噪声、损坏公式和页码干扰。</p></section>
          <section class="lesson-block"><h2>学习目标</h2><ul class="check-list">{"".join(f"<li>{esc(item)}</li>" for item in lesson["objectives"])}</ul></section>
          <section class="lesson-block"><h2>核心概念</h2><ul class="concept-list">{concept_html}</ul></section>
          <section class="lesson-block"><h2>本章补充覆盖</h2><ul class="topic-list">{coverage}</ul></section>
          {section_html}
          {render_table(lesson["table"])}
          <section class="lesson-block formula-note"><h2>公式 / 算法解释</h2><p>{esc(lesson["formula"])}</p><p class="muted">需要逐式核对时，请参考原 PDF：<a href="{PDF_URL}">{PDF_URL}</a></p></section>
          <section class="lesson-block"><h2>来自原文的主题线索</h2><ul class="topic-list">{topics}</ul></section>
          <section class="lesson-block"><h2>实践提示</h2><ul><li>先确认数据形态，再选择训练或系统方案。</li><li>把质量、成本、延迟和安全作为同一套设计约束，而不是事后补丁。</li><li>关键实验要保留输入、输出、配置、评估和失败样本，便于复盘。</li></ul></section>
          <section class="lesson-block"><h2>常见误区</h2><ul><li>把算法名字当作万能解法，而忽略数据和系统约束。</li><li>只看离线指标，不检查真实任务中的失败模式。</li><li>忽视模板、特殊 token、工具边界和权限控制等工程细节。</li></ul></section>
          <section class="lesson-block"><h2>与其他章节的关系</h2><p>本章内容会在后续章节中继续连接到训练目标、系统服务化、智能体轨迹、检索记忆或部署评估。阅读时建议把概念放回全书路线图中理解。</p></section>
          <section class="lesson-block"><h2>小结</h2><ul>{"".join(f"<li>{esc(item)}</li>" for item in lesson["summary"])}</ul></section>
          <section class="lesson-block"><h2>思考题</h2><ol>{"".join(f"<li>{esc(item)}</li>" for item in lesson["questions"])}</ol></section>
          <section class="lesson-block"><h2>延伸阅读</h2><ul>{"".join(f"<li>{esc(item)}</li>" for item in lesson["reading"])}</ul></section>
          <nav class="pager">{prev_link}{next_link}</nav>
        </article>
        """
        write(SITE / "chapters" / f"{lesson['id']}.html", shell(lesson["title"], lesson["subtitle"], body, base="../", active="roadmap", lessons=lessons, active_chapter=lesson["id"], article=True))


def build_home(lessons: list[dict]) -> None:
    cards = card_grid(lessons)
    roadmap = "".join(
        f'<li><span>{lesson["number"]:02d}</span><strong>{esc(lesson["title"])}</strong><p>{esc(lesson["subtitle"])}</p></li>'
        for lesson in lessons
    )
    coverage = "".join(
        f'<li><strong>{esc(lesson["title"])}</strong><span>{lesson["char_count"]} 中文字符</span><p>{esc("、".join(lesson.get("omitted_topics", [])[:4]))}</p></li>'
        for lesson in lessons
    )
    body = f"""
    <section class="hero">
      <div>
        <p class="chapter-number">{EDITION}</p>
        <h1>智能体式 AI 中文重编版</h1>
        <p class="hero-lead">相比 V4 preview，本版增加了更多原书内容覆盖，把简短学习版扩展为更完整的中文重编教材。它仍然不是逐字翻译，而是围绕学习路径、机制理解和工程实践重新组织。</p>
        <form class="hero-search" action="search.html"><input type="search" name="q" placeholder="搜索：RoPE、KV Cache、PPO、ReAct、PagedAttention..." /><button>搜索</button></form>
        <p><a class="button" href="chapters/chapter-01.html">开始阅读 V4.1</a> <a class="button" href="{PDF_URL}">原 PDF</a></p>
      </div>
      <aside class="reader-panel">
        <h2>全书内容覆盖</h2>
        <p>V4.1 按 14 个学习章节覆盖 LLM 基础、系统服务化、强化学习、偏好优化、奖励模型、智能体训练、RAG、记忆、工具、安全和部署。</p>
        <ul><li>重点章节扩写到 5000+ 中文字符。</li><li>搜索索引重建，覆盖新增术语。</li><li>保留 V3 根站点，V4.1 继续位于 /v4/。</li></ul>
      </aside>
    </section>
    <section class="band">
      <div class="section-head"><h2>学习路径</h2><a href="roadmap.html">查看完整路线图</a></div>
      <ol class="roadmap-mini">{roadmap}</ol>
    </section>
    <section class="band">
      <div class="section-head"><h2>扩写覆盖说明</h2><a href="concepts.html">核心概念索引</a></div>
      <div class="lesson-grid">{coverage}</div>
    </section>
    <section class="band">
      <div class="section-head"><h2>章节卡片</h2><a href="concepts.html">核心概念索引</a></div>
      <div class="lesson-grid">{cards}</div>
    </section>
    """
    write(SITE / "index.html", shell("智能体式 AI 中文重编版", "V4.1 Expanded Edition：扩写后的中文重编学习版。", body, active="home"))


def build_search(lessons: list[dict]) -> None:
    index = []
    for lesson in lessons:
        text = " ".join(
            [lesson["title"], lesson["subtitle"], *lesson["objectives"], *(s["title"] + " " + s["body"] for s in lesson["sections"]), *lesson["summary"], *lesson["questions"], *lesson.get("omitted_topics", [])]
        )
        index.append({
            "title": lesson["title"],
            "stage": lesson["stage"],
            "url": f'chapters/{lesson["id"]}.html',
            "summary": lesson["subtitle"],
            "text": text,
            "concepts": [c["label"] for c in lesson["concepts"]],
        })
    write(SITE / "assets" / "data" / "search-index.json", json.dumps(index, ensure_ascii=False, indent=2))
    body = """
    <article class="plain search-page">
      <h1>搜索</h1>
      <p class="lead">搜索 V4.1 Expanded Edition 的课程内容、术语和章节标题。</p>
      <div class="search-box"><input id="search-input" type="search" placeholder="输入关键词，例如 RoPE、KV Cache、PPO、ReAct..." autofocus /><button id="search-button">搜索</button></div>
      <div id="search-status" class="muted"></div>
      <div id="search-results" class="search-results"></div>
    </article>
    <script src="assets/js/search.js"></script>
    """
    write(SITE / "search.html", shell("搜索", "V4.1 搜索页。", body, active="search"))


def build_glossary() -> None:
    merged = GLOSSARY + [item for item in EXTRA_GLOSSARY if item[0] not in {g[0] for g in GLOSSARY}]
    rows = "".join(f"<tr><td>{esc(zh)}</td><td><code>{esc(en)}</code></td><td>{esc(note)}</td></tr>" for zh, en, note in merged)
    body = f'<article class="plain"><h1>术语表</h1><p class="lead">V4.1 扩展了推理、系统、偏好优化和智能体训练相关术语。首次出现尽量采用“中文名（English / abbreviation）”。</p><div class="table-wrap"><table><thead><tr><th>中文</th><th>English / abbreviation</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></article>'
    write(SITE / "glossary.html", shell("术语表", "V4.1 术语表。", body, active="glossary"))


def build_about(inventory: dict) -> None:
    body = f"""
    <article class="plain">
      <h1>关于 V4.1 Expanded Edition</h1>
      <p class="lead">V4.1 基于原 PDF、提取原文、中文译文和 V3 clean AST，对 V4 preview 进行内容扩写。它不是逐字翻译版，而是更完整的中文重编教材版。</p>
      <section><h2>扩写原则</h2><p>优先覆盖原书重要知识点，同时保持章节结构、学习路径和网页阅读体验。公式无法可靠恢复时使用简化公式和中文解释；表格无法可靠恢复时重做为教学表格。</p></section>
      <section><h2>与 V3 的关系</h2><p>V3 更接近原文结构，适合查找完整来源；V4.1 更像中文教材，适合系统学习。稳定根站仍为 V3，V4.1 继续发布在 /v4/。</p></section>
      <section><h2>来源读取</h2><p>构建脚本读取 PDF、source_text.md、document.zh.md 与 clean_chapter_tree.json。V4.1 页面由扩写后的 lesson data 生成。</p></section>
      <section><h2>稳定版</h2><p>稳定逐章结构化版本仍保留在 v3.0.0 与线上主站：<a href="{ONLINE_STABLE}">{ONLINE_STABLE}</a>。</p></section>
    </article>
    """
    write(SITE / "about.html", shell("关于", "说明 V4.1 是中文重编扩写版。", body, active="about"))


def build_references(inventory: dict) -> None:
    body = f"""
    <article class="plain">
      <h1>参考资料</h1>
      <p class="lead">V4.1 是扩写学习版，保留原始来源入口，便于逐式核对和深入阅读。</p>
      <ul class="reference-list">
        <li><a href="{PDF_URL}">原始 arXiv PDF</a></li>
        <li><a href="{ONLINE_STABLE}">V3 结构化中文文档站</a></li>
        <li><a href="assets/data/v4_lessons.json">V4.1 lesson data</a></li>
      </ul>
      <h2>构建时读取的本地来源</h2>
      <ul>
        <li>PDF bytes: {inventory["pdf_bytes"]}</li>
        <li>source_text.md characters: {inventory["source_text_chars"]}</li>
        <li>document.zh.md characters: {inventory["translated_md_chars"]}</li>
        <li>V3 AST chapters: {inventory["v3_chapters"]}</li>
      </ul>
    </article>
    """
    write(SITE / "references.html", shell("参考资料", "V4.1 参考资料。", body, active="references"))


def write_expansion_metadata(lessons: list[dict], inventory: dict) -> None:
    payload = {
        "schema": "v4_1_expanded_metrics",
        "edition": EDITION,
        "lessons": [
            {
                "id": lesson["id"],
                "title": lesson["title"],
                "old_length": lesson["old_length"],
                "new_length": lesson["char_count"],
                "target_chars": lesson["target_chars"],
                "priority": lesson["priority"],
                "sources": lesson["sources"],
                "added_topics": lesson.get("omitted_topics", []),
            }
            for lesson in lessons
        ],
        "source_inventory": inventory,
    }
    write(SITE / "assets" / "data" / "v4_expansion_metrics.json", json.dumps(payload, ensure_ascii=False, indent=2))
    rows = []
    for lesson in lessons:
        rows.append(
            "| {title} | {old} | {sources} | {omitted} | {sections} | {features} | {priority} |".format(
                title=lesson["title"],
                old=lesson["old_length"],
                sources=", ".join(lesson["sources"]),
                omitted="、".join(lesson.get("omitted_topics", [])[:8]),
                sections="、".join([s["title"] for s in lesson["sections"][:8]]),
                features="公式解释、表格、案例/实践提示",
                priority=lesson["priority"],
            )
        )
    report = "# V4 Content Gap Analysis\n\n| V4 当前章节标题 | V4 当前大致字数 | 对应原书 / V3 章节来源 | 原书中被遗漏的重要主题 | 应补充的小节 | 是否涉及公式、表格、图、算法、案例 | 扩写优先级 |\n|---|---:|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
    report_path = ROOT / "report" / "v4_content_gap_analysis.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")


def build_all() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    ast, inventory = load_sources()
    lessons = build_lessons(ast, inventory)
    write(SITE / "assets" / "data" / "v4_lessons.json", json.dumps({"schema": "v4_1_expanded_lessons", "title": TITLE, "edition": EDITION, "lessons": lessons, "source_inventory": inventory}, ensure_ascii=False, indent=2))
    build_home(lessons)
    build_chapters(lessons)
    build_roadmap(lessons)
    build_concepts(lessons)
    build_glossary()
    build_references(inventory)
    build_about(inventory)
    build_search(lessons)
    write_assets()
    write_expansion_metadata(lessons, inventory)
    print(json.dumps({"status": "ok", "chapters": len(lessons), "output": str(SITE)}, ensure_ascii=False))


if __name__ == "__main__":
    build_all()
