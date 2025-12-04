# Evaluation Suite for Spatially-Grounded Document Retrieval

This evaluation suite benchmarks the **Patch-to-Region Relevance Propagation** method against baselines on the BBox-DocVQA dataset.

## Overview

The evaluation compares three primary conditions:

| Condition | Description |
|-----------|-------------|
| **Hybrid** | Top-k regions by patch-to-region relevance score (our method) |
| **Page-only** | Full page OCR text (no filtering) |
| **OCR-only (BM25)** | Top-k regions by BM25 similarity (sparse baseline) |
| **OCR-only (Dense)** | Top-k regions by embedding similarity (dense baseline) |

## Metrics

| Metric | Description |
|--------|-------------|
| **ANLS** | Average Normalized Levenshtein Similarity (answer quality) |
| **IoU@1** | IoU between top-1 region and ground truth bbox |
| **IoU@k** | IoU between union of top-k regions and ground truth |
| **Precision@5** | Fraction of top-5 regions overlapping GT (IoU > 0.5) |
| **Recall** | Fraction of GT area covered by retrieved regions |
| **Hit Rate** | 1 if any region overlaps GT, else 0 |
| **Tokens** | Context token count (efficiency) |
| **Latency** | End-to-end processing time |

## Installation

```bash
cd eval
pip install -r requirements.txt
```

## Dataset Setup

### Automatic Download

The evaluation suite can automatically download datasets:

```bash
# Download BBox-DocVQA (or fallback to DocVQA if not yet released)
python -m eval.download bbox-docvqa

# Download standard DocVQA validation set
python -m eval.download docvqa-val

# Create synthetic dataset for testing
python -m eval.download --synthetic 100

# List available datasets
python -m eval.download --list
```

Datasets are automatically downloaded when running the benchmark if not present:

```bash
# This will auto-download if data/bbox-docvqa doesn't exist
python -m eval.benchmark --dataset data/bbox-docvqa
```

### Manual Setup

Alternatively, download and organize the dataset manually:

```
data/bbox-docvqa/
    images/
        doc_001.png
        doc_002.png
        ...
    annotations.json
    ocr/  (optional, pre-extracted)
        doc_001.json
        doc_002.json
        ...
```

### Annotations Format

```json
[
  {
    "sample_id": "unique_id",
    "image": "doc_001.png",
    "question": "What is the total amount?",
    "answer": "$1,234.56",
    "bbox": [100, 200, 300, 250]
  }
]
```

### OCR Format (optional)

```json
{
  "regions": [
    {
      "content": "Total: $1,234.56",
      "bbox": [100, 200, 300, 250],
      "label": "text",
      "confidence": 0.95
    }
  ],
  "full_text": "..."
}
```

## Usage

### Running the Benchmark

```bash
# Full benchmark with all conditions
python -m eval.benchmark --dataset data/bbox-docvqa

# Quick test with subset
python -m eval.benchmark --dataset data/bbox-docvqa --n-samples 50

# Specific conditions only
python -m eval.benchmark --conditions hybrid page_only --aggregations max

# Custom ColPali URL
python -m eval.benchmark --colpali-url http://colpali:8001
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset` | `data/bbox-docvqa` | Path to dataset |
| `--n-samples` | All | Number of samples to evaluate |
| `--colpali-url` | `http://localhost:8001` | ColPali service URL |
| `--llm-model` | `gpt-4o-mini` | LLM for answer generation |
| `--conditions` | `hybrid page_only ocr_bm25` | Conditions to evaluate |
| `--aggregations` | `max mean sum` | Aggregation methods |
| `--top-k` | `5` | Number of regions to retrieve |
| `--output-dir` | `eval/results` | Output directory |

### Running Analysis

```bash
# Generate analysis report with plots
python -m eval.analysis eval/results/samples_*.json --output-dir eval/analysis

# Custom comparison settings
python -m eval.analysis results.json --aggregation max --threshold 0.3
```

## Programmatic Usage

```python
import asyncio
from pathlib import Path
from eval.benchmark import Benchmark, BenchmarkConfig

config = BenchmarkConfig(
    dataset_path=Path("data/bbox-docvqa"),
    n_samples=100,
    conditions=["hybrid", "page_only", "ocr_bm25"],
    aggregations=["max", "mean"],
    thresholds=[0.2, 0.3, 0.4],
    top_k=5,
)

benchmark = Benchmark(config)
results = asyncio.run(benchmark.run())

# Print summary
for condition, metrics in results.items():
    print(f"{condition}: ANLS={metrics['anls_mean']:.3f}")
```

### Using Individual Components

```python
from eval.dataset import BBoxDocVQADataset
from eval.metrics import compute_anls, compute_iou
from eval.scoring import RegionScorer
from eval.conditions import HybridContextBuilder

# Load dataset
dataset = BBoxDocVQADataset(Path("data/bbox-docvqa")).load()
sample = dataset[0]

# Score regions
scorer = RegionScorer(colpali_url="http://localhost:8001")
scored_regions = await scorer.score_sample(sample, threshold=0.3, top_k=5)

# Build context
builder = HybridContextBuilder(top_k=5)
context = builder.build_context(sample, sample.question, scored_regions)

# Compute metrics
anls = compute_anls(prediction, sample.answer)
iou = compute_iou(scored_regions[0]["bbox"], sample.ground_truth_bbox)
```

## Output Files

The benchmark generates:

| File | Description |
|------|-------------|
| `aggregated_TIMESTAMP.json` | Mean/std metrics per condition |
| `samples_TIMESTAMP.json` | Per-sample detailed results |
| `results_TIMESTAMP.csv` | CSV for spreadsheet analysis |

## Analysis Output

The analysis generates:

| File | Description |
|------|-------------|
| `analysis_report.md` | Markdown summary with tables |
| `threshold_sensitivity.png` | Metrics vs threshold plots |
| `condition_comparison.png` | Bar chart comparing conditions |
| `efficiency_tradeoff.png` | ANLS vs tokens scatter plot |

## Expected Results

Based on the paper's theoretical analysis:

| Condition | Expected ANLS | Expected Token Reduction |
|-----------|---------------|--------------------------|
| Hybrid (max, t=0.3) | Comparable to page-only | ~5x reduction |
| Page-only | Baseline | 1x (no reduction) |
| OCR-only (BM25) | Lower | ~5x reduction |

## Prerequisites

1. **ColPali Service** running at configured URL
2. **OpenAI API Key** for LLM queries and dense embeddings
3. **Pre-extracted OCR** (or DeepSeek OCR service for on-the-fly extraction)

## Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export COLPALI_URL="http://localhost:8001"
```

## Troubleshooting

### ColPali Connection Failed
Ensure the ColPali service is running and accessible:
```bash
curl http://localhost:8001/health
```

### Missing OCR Regions
If samples have no OCR regions, either:
1. Provide pre-extracted OCR in `data/bbox-docvqa/ocr/`
2. Or use the DeepSeek OCR service for on-the-fly extraction

### Out of Memory
Reduce batch size or use `--n-samples` to limit evaluation scope.
