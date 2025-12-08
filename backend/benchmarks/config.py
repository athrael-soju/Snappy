"""
Configuration for BBox_DocVQA benchmark.

Defines all configurable parameters for running the benchmark,
including dataset paths, aggregation methods, selection strategies,
evaluation settings, and baseline comparisons.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml


@dataclass
class DatasetConfig:
    """Configuration for the BBox_DocVQA dataset."""

    # Dataset source
    hf_dataset: str = "Yuwh07/BBox_DocVQA_Bench"
    jsonl_path: Optional[str] = None
    images_dir: Optional[str] = None
    split: str = "train"  # HuggingFace dataset only has train split

    # Filtering
    filter_single_page: bool = True
    categories: Optional[List[str]] = None  # SPSBB, SPMBB, MPMBB
    region_types: Optional[List[str]] = None  # Text, Image, Table
    domains: Optional[List[str]] = None

    # Sampling
    max_samples: Optional[int] = None
    sample_seed: Optional[int] = 42


@dataclass
class AggregationConfig:
    """Configuration for patch-to-region aggregation."""

    # Aggregation methods to evaluate
    methods: List[str] = field(
        default_factory=lambda: ["max", "mean", "sum", "iou_weighted"]
    )

    # Default method for single-method runs
    default_method: str = "iou_weighted"

    # Token aggregation (for multi-token queries)
    token_aggregation: str = "max"

    # Patch grid dimensions
    grid_x: int = 32
    grid_y: int = 32


@dataclass
class SelectionConfig:
    """Configuration for region selection strategies."""

    # Selection methods to evaluate
    methods: List[str] = field(
        default_factory=lambda: ["top_k", "otsu", "relative"]
    )

    # Default method for single-method runs
    default_method: str = "top_k"

    # Top-k parameters
    top_k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    default_k: int = 5

    # Relative threshold parameters
    relative_thresholds: List[float] = field(
        default_factory=lambda: [0.3, 0.5, 0.7, 0.9]
    )
    default_relative_threshold: float = 0.5

    # Percentile parameters
    percentile_values: List[float] = field(
        default_factory=lambda: [80.0, 90.0, 95.0]
    )


@dataclass
class EvaluationConfig:
    """Configuration for evaluation metrics."""

    # IoU thresholds for hit rate computation
    iou_thresholds: List[float] = field(
        default_factory=lambda: [0.25, 0.5, 0.75]
    )

    # Matching strategies
    matching_strategies: List[str] = field(
        default_factory=lambda: ["any", "coverage", "hungarian"]
    )

    # Primary metric for comparison
    primary_metric: str = "recall"
    primary_iou_threshold: float = 0.5


@dataclass
class BaselineConfig:
    """Configuration for baseline methods."""

    # Baselines to run
    enabled: List[str] = field(
        default_factory=lambda: [
            "random",
            "bm25",
            "cosine",
            "uniform_patches",
            "center_bias",
            "top_left_bias",
        ]
    )

    # Random baseline
    random_seed: int = 42
    random_k: int = 5

    # Text similarity
    bm25_k1: float = 1.5
    bm25_b: float = 0.75


@dataclass
class VisualizationConfig:
    """Configuration for debug visualizations."""

    # Enable visualization generation
    enabled: bool = True

    # Output directory (relative to run folder)
    output_dir: str = "visualizations"

    # Number of samples to visualize
    max_samples: int = 50

    # Which samples to visualize
    visualize_strategy: Literal["random", "worst", "best", "all"] = "worst"

    # Image settings
    dpi: int = 150
    show_scores: bool = True
    show_labels: bool = True
    show_heatmap: bool = True


@dataclass
class OutputConfig:
    """Configuration for benchmark output."""

    # Base directory for all benchmark runs (relative to benchmarks folder)
    base_dir: str = "runs"

    # Run-specific directory (set automatically with timestamp)
    run_dir: str = ""

    # Output formats
    save_json: bool = True
    save_csv: bool = True
    save_summary: bool = True

    # Detailed results
    save_per_sample: bool = False
    save_stratified: bool = True


@dataclass
class ColPaliConfig:
    """Configuration for ColPali service."""

    # Service URL
    url: str = "http://localhost:7000"

    # Timeouts
    timeout: int = 30
    batch_size: int = 8

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class OCRConfig:
    """Configuration for DeepSeek OCR service."""

    # Service URL
    url: str = "http://localhost:8200"

    # Processing settings
    mode: str = "Gundam"
    task: str = "markdown"
    include_grounding: bool = True

    # Timeouts
    timeout: int = 60


@dataclass
class BenchmarkConfig:
    """Complete benchmark configuration."""

    # Sub-configurations
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    baselines: BaselineConfig = field(default_factory=BaselineConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    colpali: ColPaliConfig = field(default_factory=ColPaliConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)

    # Run configuration
    name: str = "bbox_docvqa_benchmark"
    description: str = "Patch-to-Region Relevance Propagation Benchmark"

    # Parallel processing
    num_workers: int = 4

    # Logging
    log_level: str = "INFO"
    log_progress_every: int = 100

    @classmethod
    def from_yaml(cls, path: str) -> "BenchmarkConfig":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkConfig":
        """Create configuration from dictionary."""
        config = cls()

        # Update sub-configurations
        if "dataset" in data:
            config.dataset = DatasetConfig(**data["dataset"])
        if "aggregation" in data:
            config.aggregation = AggregationConfig(**data["aggregation"])
        if "selection" in data:
            config.selection = SelectionConfig(**data["selection"])
        if "evaluation" in data:
            config.evaluation = EvaluationConfig(**data["evaluation"])
        if "baselines" in data:
            config.baselines = BaselineConfig(**data["baselines"])
        if "visualization" in data:
            config.visualization = VisualizationConfig(**data["visualization"])
        if "output" in data:
            config.output = OutputConfig(**data["output"])
        if "colpali" in data:
            config.colpali = ColPaliConfig(**data["colpali"])
        if "ocr" in data:
            config.ocr = OCRConfig(**data["ocr"])

        # Update top-level fields
        for field_name in ["name", "description", "num_workers", "log_level", "log_progress_every"]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "num_workers": self.num_workers,
            "log_level": self.log_level,
            "log_progress_every": self.log_progress_every,
            "dataset": self._dataclass_to_dict(self.dataset),
            "aggregation": self._dataclass_to_dict(self.aggregation),
            "selection": self._dataclass_to_dict(self.selection),
            "evaluation": self._dataclass_to_dict(self.evaluation),
            "baselines": self._dataclass_to_dict(self.baselines),
            "visualization": self._dataclass_to_dict(self.visualization),
            "output": self._dataclass_to_dict(self.output),
            "colpali": self._dataclass_to_dict(self.colpali),
            "ocr": self._dataclass_to_dict(self.ocr),
        }

    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert a dataclass to dictionary."""
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            if value is not None:
                result[field_name] = value
        return result

    def save_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


def get_default_config() -> BenchmarkConfig:
    """Get default benchmark configuration."""
    return BenchmarkConfig()


def create_ablation_configs() -> Dict[str, BenchmarkConfig]:
    """
    Create configurations for ablation studies.

    Returns dictionary mapping ablation name to config.
    """
    configs = {}

    # Base config
    base = get_default_config()

    # Ablation: Aggregation methods
    for method in ["max", "mean", "sum", "iou_weighted"]:
        config = get_default_config()
        config.name = f"ablation_aggregation_{method}"
        config.aggregation.methods = [method]
        config.aggregation.default_method = method
        configs[f"agg_{method}"] = config

    # Ablation: Selection strategies
    for method in ["top_k", "otsu", "elbow", "gap", "relative"]:
        config = get_default_config()
        config.name = f"ablation_selection_{method}"
        config.selection.methods = [method]
        config.selection.default_method = method
        configs[f"sel_{method}"] = config

    # Ablation: Top-k values
    for k in [1, 3, 5, 10, 20]:
        config = get_default_config()
        config.name = f"ablation_top_k_{k}"
        config.selection.methods = ["top_k"]
        config.selection.default_k = k
        configs[f"top_k_{k}"] = config

    # Ablation: IoU thresholds
    for thresh in [0.25, 0.5, 0.75]:
        config = get_default_config()
        config.name = f"ablation_iou_{thresh}"
        config.evaluation.primary_iou_threshold = thresh
        configs[f"iou_{thresh}"] = config

    # Ablation: By category
    for category in ["SPSBB", "SPMBB", "MPMBB"]:
        config = get_default_config()
        config.name = f"ablation_category_{category}"
        config.dataset.categories = [category]
        configs[f"cat_{category}"] = config

    # Ablation: By region type
    for region_type in ["Text", "Image", "Table"]:
        config = get_default_config()
        config.name = f"ablation_region_{region_type}"
        config.dataset.region_types = [region_type]
        configs[f"region_{region_type}"] = config

    return configs


# Example YAML configuration template
EXAMPLE_CONFIG_YAML = """
# BBox_DocVQA Benchmark Configuration
name: bbox_docvqa_benchmark
description: Patch-to-Region Relevance Propagation Benchmark

# Dataset settings
dataset:
  hf_dataset: Yuwh07/BBox_DocVQA_Bench
  split: test
  filter_single_page: true
  max_samples: null  # null for all samples

# Patch-to-region aggregation
aggregation:
  methods:
    - max
    - mean
    - sum
    - iou_weighted
  default_method: iou_weighted
  token_aggregation: max
  grid_x: 32
  grid_y: 32

# Region selection
selection:
  methods:
    - top_k
    - otsu
    - relative
  default_method: top_k
  top_k_values: [1, 3, 5, 10]
  default_k: 5
  relative_thresholds: [0.3, 0.5, 0.7, 0.9]

# Evaluation metrics
evaluation:
  iou_thresholds: [0.25, 0.5, 0.75]
  matching_strategies:
    - any
    - coverage
    - hungarian
  primary_metric: recall
  primary_iou_threshold: 0.5

# Baseline methods
baselines:
  enabled:
    - random
    - bm25
    - cosine
    - uniform_patches
  random_seed: 42
  random_k: 5

# Visualization
visualization:
  enabled: true
  output_dir: benchmark_visualizations
  max_samples: 50
  visualize_strategy: worst

# Output
output:
  output_dir: benchmark_results
  save_json: true
  save_csv: true
  save_stratified: true

# Services
colpali:
  url: http://localhost:7000
  timeout: 30
  batch_size: 8

ocr:
  url: http://localhost:8200
  mode: Gundam
  task: markdown
  include_grounding: true

# Execution
num_workers: 4
log_level: INFO
log_progress_every: 100
"""


def save_example_config(path: str = "benchmark_config.yaml") -> None:
    """Save example configuration file."""
    with open(path, "w") as f:
        f.write(EXAMPLE_CONFIG_YAML)
