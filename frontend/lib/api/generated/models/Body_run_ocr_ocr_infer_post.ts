/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Body_run_ocr_ocr_infer_post = {
    /**
     * Image to process.
     */
    image: Blob;
    /**
     * OCR mode / task preset.
     */
    mode?: ('plain_ocr' | 'markdown' | 'tables_csv' | 'tables_md' | 'kv_json' | 'figure_chart' | 'find_ref' | 'layout_map' | 'pii_redact' | 'multilingual' | 'describe' | 'freeform' | null);
    /**
     * Profile preset controlling default sizing.
     */
    profile?: ('gundam' | 'tiny' | 'small' | 'base' | 'large' | null);
    /**
     * Custom prompt for freeform mode.
     */
    prompt?: (string | null);
    /**
     * Force grounding boxes regardless of selected mode.
     */
    grounding?: (boolean | null);
    /**
     * Request an additional descriptive caption.
     */
    include_caption?: (boolean | null);
    /**
     * Term to highlight for 'find_ref' mode.
     */
    find_term?: (string | null);
    /**
     * JSON schema used by 'kv_json' mode. Provide raw JSON text.
     */
    kv_schema?: (string | null);
    /**
     * Base resize dimension passed to the OCR service (allowed values: 512, 640, 1024, 1280).
     */
    base_size?: (number | null);
    /**
     * Image input size passed to the OCR service (allowed values: 512, 640, 1024, 1280).
     */
    image_size?: (number | null);
    /**
     * Enable crop mode during preprocessing.
     */
    crop_mode?: (boolean | null);
    /**
     * Run compression diagnostics without saving artifacts.
     */
    test_compress?: (boolean | null);
    /**
     * Return markdown-formatted output from the OCR service.
     */
    return_markdown?: (boolean | null);
    /**
     * Include base64-encoded figure crops extracted by the OCR service.
     */
    return_figures?: (boolean | null);
};

