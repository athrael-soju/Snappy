from typing import Any, Dict, Optional

from pydantic import BaseModel, computed_field


class SearchItem(BaseModel):
    """Search result item with image data and metadata."""

    # Image data - inline base64 (preferred) or URL (legacy)
    image_data: Optional[str] = None  # Base64-encoded image (thumbnail)
    image_mime_type: Optional[str] = None  # MIME type for data URI
    image_url: Optional[str] = None  # Legacy: URL for external storage

    # Metadata
    label: Optional[str] = None
    payload: Dict[str, Any]
    score: Optional[float] = None

    # OCR data - inline (preferred) or URL (legacy)
    ocr_text: Optional[str] = None  # Extracted text
    ocr_markdown: Optional[str] = None  # Markdown-formatted OCR
    json_url: Optional[str] = None  # Legacy: OCR JSON URL

    @computed_field
    @property
    def image_data_uri(self) -> Optional[str]:
        """Return data URI for direct use in img src."""
        if self.image_data and self.image_mime_type:
            return f"data:{self.image_mime_type};base64,{self.image_data}"
        return None

    @computed_field
    @property
    def has_inline_image(self) -> bool:
        """Check if this result has inline image data."""
        return self.image_data is not None
