"""
Configuration schema for Retrieval and Search.

Controls region-level retrieval using interpretability maps.
"""

from typing import Any, Dict

# Schema for Retrieval
SCHEMA: Dict[str, Any] = {
    "retrieval": {
        "description": "Controls retrieval behavior including region-level filtering based on query relevance.",
        "icon": "search",
        "name": "Retrieval & Search",
        "order": 3,
        "settings": [
            {
                "default": 10,
                "description": "Default number of results to return per search query",
                "help_text": "Controls how many document pages are returned by default when no k parameter is specified. "
                "Higher values return more results but may be slower. Lower values return fewer but faster results.",
                "key": "DEFAULT_TOP_K",
                "label": "Default Top K Results",
                "max": 50,
                "min": 1,
                "type": "int",
                "ui_type": "number",
            },
            {
                "default": False,
                "description": "Enable region-level retrieval using interpretability maps",
                "help_text": "When enabled, uses ColPali interpretability maps to filter OCR regions based on query relevance. "
                "Only regions that are relevant to the query (based on attention scores) will be returned, "
                "reducing noise and improving precision. This requires ColPali service to be available and "
                "adds processing overhead for each search with OCR results. "
                "Disable for faster searches when all regions are needed.",
                "key": "ENABLE_REGION_LEVEL_RETRIEVAL",
                "label": "Enable Region-Level Retrieval",
                "type": "bool",
                "ui_type": "boolean",
            },
            {
                "default": 0.3,
                "description": "Minimum relevance score threshold for region filtering (0.0-1.0)",
                "help_text": "Regions with relevance scores below this threshold will be filtered out. "
                "Higher values (e.g., 0.5-0.7) return only highly relevant regions but may miss some content. "
                "Lower values (e.g., 0.1-0.3) return more regions including marginally relevant ones. "
                "Only applies when region-level retrieval is enabled.",
                "key": "REGION_RELEVANCE_THRESHOLD",
                "label": "Region Relevance Threshold",
                "max": 1.0,
                "min": 0.0,
                "step": 0.05,
                "type": "float",
                "ui_type": "number",
                "depends_on": {"key": "ENABLE_REGION_LEVEL_RETRIEVAL", "value": True},
                "ui_indent_level": 1,
            },
            {
                "default": 0,
                "description": "Maximum number of regions to return per page (0 = no limit)",
                "help_text": "Limits the number of regions returned per page after relevance filtering. "
                "Set to 0 for no limit (return all regions above threshold). "
                "Set to a specific number (e.g., 5-10) to return only the top-k most relevant regions. "
                "Only applies when region-level retrieval is enabled.",
                "key": "REGION_TOP_K",
                "label": "Max Regions Per Page",
                "max": 50,
                "min": 0,
                "type": "int",
                "ui_type": "number",
                "depends_on": {"key": "ENABLE_REGION_LEVEL_RETRIEVAL", "value": True},
                "ui_indent_level": 1,
            },
            {
                "default": "iou_weighted",
                "description": "How to aggregate patch scores for each region",
                "help_text": "Controls how patch-level similarity scores are combined into region scores: "
                "'iou_weighted' (recommended) uses IoU-weighted average as described in the paper - "
                "patches are weighted by their spatial overlap with the region, making scores comparable across region sizes. "
                "'max' uses the highest patch score in the region (simple but may favor small regions). "
                "'mean' averages all patch scores in the region.",
                "key": "REGION_SCORE_AGGREGATION",
                "label": "Score Aggregation Method",
                "type": "str",
                "ui_type": "select",
                "options": ["iou_weighted", "max", "mean"],
                "depends_on": {"key": "ENABLE_REGION_LEVEL_RETRIEVAL", "value": True},
                "ui_indent_level": 1,
            },
        ],
    }
}
