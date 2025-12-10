# BBox-DocVQA Mini Benchmark

Lightweight runner to sanity-check spatial grounding with ColPali patch scores and DeepSeek OCR bounding boxes.

## Prerequisites

- DeepSeek OCR service running (defaults to `DEEPSEEK_OCR_URL` or `http://localhost:8200`)
- ColPali service running (defaults from `config.COLPALI_URL`)
- Dataset snapshot extracted under `benchmarks/.eval_cache/datasets--Yuwh07--BBox_DocVQA_Bench/snapshots/*/BBox_DocVQA_Bench.jsonl`

## Quick start

Run from the `backend/` directory:

```bash
python benchmarks/run_bbox_docvqa.py --limit 10 --method adaptive
```

## Flags

**Dataset & filtering:**
- `--dataset-root`: override the detected dataset snapshot path
- `--limit`: number of samples to evaluate (default: 0 = no limit)
- `--filter-docs`: filter to specific doc names (e.g., `--filter-docs 2406.05299 2411.15797`)
- `--filter-samples`: filter to specific sample IDs, 0-indexed (e.g., `--filter-samples 0 5 10`)

**Scoring & thresholding:**
- `--method`: `adaptive` (mean+std), `percentile`, `max`, or `none` (no threshold)
- `--percentile`: percentile value when using `percentile` method (default: 80)
- `--top-k`: cap number of regions returned per page
- `--aggregation`: token aggregation for heatmap: `max` (MaxSim), `mean`, or `sum` (default: max)
- `--region-scoring`: `weighted_avg` (IoU-weighted) or `max` (default: weighted_avg)
- `--min-overlap`: minimum IoU overlap with a patch to count toward region scoring (default: 0)
- `--hit-iou`: IoU threshold for counting a prediction as a "hit" (default: 0.5)

**DeepSeek OCR:**
- `--deepseek-url`: base URL override
- `--deepseek-mode`: OCR mode (e.g., `Gundam`, `Tiny`)
- `--deepseek-task`: OCR task (e.g., `markdown`, `plain_ocr`, `locate`)

**Output & visualization:**
- `--output-dir`: directory to write benchmark results (default: `benchmarks/runs`)
- `--visualize`: save per-sample overlays (GT=green, OCR=blue, Pred=magenta)
- `--visualize-limit`: cap number of visualizations (default: no limit; use 0 for none)

## Output

Results are written to `benchmarks/runs/bbox_docvqa_benchmark_<timestamp>/`:
- `summary.json`: aggregate metrics and per-sample results
- `progress.md`: live-updating markdown report with hit/miss tracking and token stats
- `visualizations/`: per-sample overlay images (if `--visualize` enabled)

The summary includes `detection_summary` (OCR region overlap with GT) and `token_summary` (selected vs full OCR vs full image tokens).
