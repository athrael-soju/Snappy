"""
OCR utilities shared between Snappy core and benchmarks.
"""

import re
from typing import Dict, List


def extract_region_content(raw_text: str) -> Dict[str, List[str]]:
    """
    Extract content for each labeled region from raw OCR output.

    The raw text contains patterns like:
    <|ref|>label<|/ref|><|det|>[[coords]]<|/det|>
    Content here

    This function parses the grounding markers and extracts the content
    associated with each labeled region.

    Args:
        raw_text: Raw OCR output with grounding references

    Returns:
        Dictionary mapping labels to lists of their content
    """
    content_map: Dict[str, List[str]] = {}

    if not raw_text:
        return content_map

    # Pattern to match: <|ref|>label<|/ref|><|det|>coords<|/det|>Content
    # This captures the label and the content following it
    pattern = (
        r"<\|ref\|>([^<]+)<\|/ref\|><\|det\|>.*?<\|/det\|>\s*(.*?)(?=<\|ref\|>|$)"
    )

    matches = re.findall(pattern, raw_text, re.DOTALL)

    for label, content in matches:
        label = label.strip()
        content = content.strip()

        if label not in content_map:
            content_map[label] = []

        # Clean the content - remove any remaining grounding markers
        content = re.sub(r"<\|[^|]+\|>", "", content)
        content = content.strip()

        if content:
            content_map[label].append(content)

    return content_map
