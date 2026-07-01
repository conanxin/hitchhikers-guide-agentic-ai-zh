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


def build_all() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    ast, inventory = load_sources()
    lessons = build_lessons(ast, inventory)
    write(SITE / "assets" / "data" / "v4_lessons.json", json.dumps({"schema": "v4_learning_lessons", "title": TITLE, "lessons": lessons, "source_inventory": inventory}, ensure_ascii=False, indent=2))
    build_home(lessons)
    build_chapters(lessons)
    build_roadmap(lessons)
    build_concepts(lessons)
    build_glossary()
    build_references(inventory)
    build_about(inventory)
    build_search(lessons)
    write_assets()
    print(json.dumps({"status": "ok", "chapters": len(lessons), "output": str(SITE)}, ensure_ascii=False))


if __name__ == "__main__":
    build_all()
