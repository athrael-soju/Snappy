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
     * OCR mode (plain_ocr, markdown, tables_csv, etc.).
     */
    mode?: (string | null);
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
     * Base resize dimension used by the OCR service.
     */
    base_size?: (number | null);
    /**
     * Image input size passed to the OCR service.
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
};

