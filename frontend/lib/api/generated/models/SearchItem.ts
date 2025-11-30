/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SearchItem = {
    // Image data - inline base64 (preferred) or URL (legacy)
    image_data?: (string | null);
    image_mime_type?: (string | null);
    image_url?: (string | null);
    // Computed field - data URI for direct use in img src
    image_data_uri?: (string | null);
    has_inline_image?: boolean;
    // Metadata
    label?: (string | null);
    payload: Record<string, any>;
    score?: (number | null);
    // OCR data - inline (preferred) or URL (legacy)
    ocr_text?: (string | null);
    ocr_markdown?: (string | null);
    json_url?: (string | null);
};

