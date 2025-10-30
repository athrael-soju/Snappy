import { OcrService } from '@/lib/api/generated'
import type { OCRExtractionResponse, OCRHealthResponse } from '@/lib/api/generated'
import { schemas } from '@/lib/api/zod'

const extractionSchema = schemas.OCRExtractionResponse
const healthSchema = schemas.OCRHealthResponse

export async function getOcrHealth(): Promise<OCRHealthResponse> {
    const raw = await OcrService.healthOcrHealthGet()
    const parsed = healthSchema.safeParse(raw)
    if (!parsed.success) {
        throw new Error('Invalid OCR health payload')
    }
    return parsed.data
}

export async function getOcrInfo(): Promise<Record<string, unknown>> {
    const raw = await OcrService.infoOcrInfoGet()
    if (!raw || typeof raw !== 'object') {
        return {}
    }
    return raw
}

export async function extractOcrDocument(file: File | Blob): Promise<OCRExtractionResponse> {
    const raw = await OcrService.extractDocumentOcrExtractPost({ file })
    const parsed = extractionSchema.safeParse(raw)
    if (!parsed.success) {
        throw new Error('Invalid OCR extraction payload')
    }
    return parsed.data
}
