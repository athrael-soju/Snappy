# 1. Introduction

Retrieval-augmented generation (RAG) has emerged as the dominant paradigm for grounding large language models in external knowledge, enabling factual responses without costly retraining. The effectiveness of RAG systems hinges on a fundamental requirement: retrieving *precisely relevant* context while minimizing noise. For text corpora, this challenge is well-studied. Dense retrievers identify semantically similar passages, and chunking strategies control context granularity. However, document collections present a fundamentally harder problem.

Documents are not sequences of tokens but *spatially-organized visual artifacts*. A single page may contain heterogeneous elements (tables, figures, equations, headers, footnotes), each carrying distinct semantic content at different spatial locations. When a user queries "What was the Q3 revenue?", the answer likely resides in a specific table cell, not spread across the entire page. Yet current retrieval systems operate at the wrong granularity.

**The Page-Level Retrieval Problem.** Vision-language models (VLMs) such as ColPali [1] have achieved state-of-the-art performance on document retrieval benchmarks by embedding document pages directly as images. These models leverage late interaction mechanisms, computing fine-grained similarity between query tokens and visual patches. This approach elegantly sidesteps OCR errors and preserves layout semantics. However, ColPali and its variants return *entire pages* as retrieval units. For RAG applications, this is problematic: feeding a full page into a language model's context window introduces irrelevant content, increases latency, inflates costs, and, critically, dilutes the signal that the model must attend to. The retrieval system knows *which page* contains the answer but not *where on the page*.

**The Structured Extraction Gap.** Conversely, OCR-based pipelines such as DeepSeek-OCR [2] extract text with precise bounding box coordinates, enabling structured representations of document content. Tables become rows and columns; figures receive captions; headers define hierarchy. This structural fidelity is invaluable for downstream processing. Yet OCR systems lack *semantic grounding*. They cannot assess which extracted regions are relevant to a given query. A page with twenty OCR regions offers no ranking mechanism; all regions are treated as equally plausible candidates.

**Our Insight.** We observe that these paradigms are complementary. ColPali's patch-level similarity scores encode *where* on a page the model attends when processing a query. This information is computed but discarded when returning page-level results. OCR systems know *what* content exists and *where* it is located, but not *why* it matters. By unifying these signals, we can achieve region-level retrieval: returning only the document regions that are both structurally coherent (via OCR) and semantically relevant (via VLM attention).

**Contributions.** This paper presents a hybrid architecture for spatially-grounded document retrieval:

1. **Coordinate Mapping Formalism.** We formalize the mathematical correspondence between vision transformer patch grids and OCR bounding boxes, enabling spatial alignment between heterogeneous representations (§3.2).

2. **Relevance Propagation via Interpretability Maps.** We repurpose ColPali's late interaction mechanism to generate per-query-token similarity heatmaps, then propagate these scores to OCR regions through patch-region intersection (§3.3).

3. **Two-Stage Retrieval Architecture.** We introduce a mean-pooling strategy that compresses patch embeddings along spatial axes, enabling efficient candidate retrieval before full-resolution reranking (§3.4).

4. **Theoretical Analysis.** We establish bounds on localization precision as a function of patch resolution and analyze information-theoretic tradeoffs in the pooling stage (§4).

5. **Open Implementation.** We release Snappy, a complete system implementing this architecture with ColPali, DeepSeek-OCR, and Qdrant vector search, demonstrating practical applicability (§5).

Our experiments on [benchmark TBD] show that region-level retrieval improves downstream RAG answer quality by [X]% while reducing context length by [Y]%, validating the hypothesis that retrieval granularity directly impacts generation fidelity.

## References

[1] Faysse, M., et al. "ColPali: Efficient Document Retrieval with Vision Language Models." arXiv preprint arXiv:2407.01449 (2024).

[2] [DeepSeek-OCR reference TBD]
