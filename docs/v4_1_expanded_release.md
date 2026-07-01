# V4.1 Expanded Edition Release

## STATUS

PASS

## URLs

- V3 Stable:
  https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/

- V4.1 Expanded Preview:
  https://conanxin.github.io/hitchhikers-guide-agentic-ai-zh/v4/

## Version

v4.1.0-expanded-preview

## Summary

V4.1 expands the previous V4 Chinese learning edition into a fuller rewritten教材版. It keeps the clearer V4 learning structure, but substantially increases chapter coverage using the original PDF, V3 clean AST, extracted source text, and full Chinese translation.

## Content Expansion Highlights

- Chapter 02 expanded: tokenization, BPE, vocabulary, embeddings, Transformer flow, attention, RoPE, prefill/decode, sampling, KV Cache, FlashAttention.
- Chapter 03 expanded: GPU, HBM, NVLink/PCIe, parallelism, FSDP/ZeRO, PagedAttention, serving throughput/latency, batching, speculative decoding.
- Chapter 05-08 expanded: SFT/RLHF, PPO, DPO, GRPO, reward and preference optimization mechanisms.
- Chapter 11 expanded: Agentic AI training, trajectory buffers, ReAct, STaR, self-correction, long-horizon tasks, safety guardrails.
- Chapter 12 expanded: RAG, memory, retrieval, reranking, context windows, tool/function calling, execution loops.

## Quality Gate

- All 14 chapter pages generated.
- Focus chapters pass the 5,000 Chinese-character threshold.
- No detected garbled artifacts, page-number heading pollution, temporary fallback text, large English residuals, or broken internal links.
- Search index rebuilt and covers required technical terms.
- Mobile layout checked locally.

## Relationship Between V3, V4, And V4.1

- V3 remains the stable structured documentation site at the root path.
- V4 introduced the rewritten Chinese learning edition under `/v4/`.
- V4.1 expands that learning edition while keeping the same `/v4/` preview path and preserving V3 at the root.

## Remaining Notes

Some English technical abbreviations, method names, and reference titles remain intentionally preserved.
