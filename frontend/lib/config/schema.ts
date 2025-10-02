/**
 * Configuration schema for runtime settings.
 * Defines all configurable environment variables with their types, defaults, and metadata.
 */

export interface ConfigSetting {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select" | "password";
  options?: string[];
  default: string;
  description: string;
  min?: number;
  max?: number;
  step?: number;
  depends_on?: {
    key: string;
    value: boolean;
  };
}

export interface ConfigCategory {
  name: string;
  description: string;
  order: number;
  icon: string;
  settings: ConfigSetting[];
}

export interface ConfigSchema {
  [categoryKey: string]: ConfigCategory;
}

export const CONFIG_SCHEMA: ConfigSchema = {
  application: {
    order: 1,
    icon: "settings",
    name: "Application",
    description: "Core application settings",
    settings: [
      {
        key: "LOG_LEVEL",
        label: "Log Level",
        type: "select",
        options: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default: "INFO",
        description: "Logging verbosity level"
      },
      {
        key: "ALLOWED_ORIGINS",
        label: "Allowed CORS Origins",
        type: "text",
        default: "*",
        description: "Comma-separated list of allowed origins, or * for all"
      }
    ]
  },
  processing: {
    order: 2,
    icon: "cpu",
    name: "Processing",
    description: "Document processing and indexing settings",
    settings: [
      {
        key: "DEFAULT_TOP_K",
        label: "Default Top K Results",
        type: "number",
        min: 1,
        max: 100,
        default: "5",
        description: "Default number of search results to return"
      },
      {
        key: "MAX_TOKENS",
        label: "Max Tokens",
        type: "number",
        min: 100,
        max: 4096,
        default: "500",
        description: "Maximum tokens for text generation"
      },
      {
        key: "BATCH_SIZE",
        label: "Batch Size",
        type: "number",
        min: 1,
        max: 128,
        default: "12",
        description: "Number of documents to process in parallel"
      },
      {
        key: "WORKER_THREADS",
        label: "Worker Threads",
        type: "number",
        min: 1,
        max: 32,
        default: "8",
        description: "Number of worker threads for processing"
      },
      {
        key: "ENABLE_PIPELINE_INDEXING",
        label: "Enable Pipeline Indexing",
        type: "boolean",
        default: "True",
        description: "Enable parallel pipeline indexing"
      },
      {
        key: "MAX_CONCURRENT_BATCHES",
        label: "Max Concurrent Batches",
        type: "number",
        min: 1,
        max: 10,
        default: "3",
        description: "Maximum number of concurrent batches"
      }
    ]
  },
  colpali: {
    order: 3,
    icon: "brain",
    name: "Embedding Model",
    description: "ColPali embedding model configuration",
    settings: [
      {
        key: "COLPALI_MODE",
        label: "Processing Mode",
        type: "select",
        options: ["cpu", "gpu"],
        default: "gpu",
        description: "Use CPU or GPU for embeddings"
      },
      {
        key: "COLPALI_CPU_URL",
        label: "CPU Service URL",
        type: "text",
        default: "http://localhost:7001",
        description: "URL for CPU-based ColPali service"
      },
      {
        key: "COLPALI_GPU_URL",
        label: "GPU Service URL",
        type: "text",
        default: "http://localhost:7002",
        description: "URL for GPU-based ColPali service"
      },
      {
        key: "COLPALI_API_TIMEOUT",
        label: "API Timeout (seconds)",
        type: "number",
        min: 10,
        max: 600,
        default: "300",
        description: "Request timeout for ColPali API"
      }
    ]
  },
  qdrant: {
    order: 4,
    icon: "database",
    name: "Vector Database",
    description: "Qdrant vector store and retrieval settings",
    settings: [
      {
        key: "QDRANT_URL",
        label: "Qdrant URL",
        type: "text",
        default: "http://localhost:6333",
        description: "URL for Qdrant vector database"
      },
      {
        key: "QDRANT_COLLECTION_NAME",
        label: "Collection Name",
        type: "text",
        default: "documents",
        description: "Name of the Qdrant collection"
      },
      {
        key: "QDRANT_SEARCH_LIMIT",
        label: "Search Limit",
        type: "number",
        min: 1,
        max: 1000,
        default: "20",
        description: "Maximum results from vector search"
      },
      {
        key: "QDRANT_PREFETCH_LIMIT",
        label: "Prefetch Limit",
        type: "number",
        min: 10,
        max: 1000,
        default: "200",
        description: "Number of candidates to prefetch"
      },
      {
        key: "QDRANT_ON_DISK",
        label: "Store Vectors on Disk",
        type: "boolean",
        default: "True",
        description: "Store vectors on disk instead of RAM"
      },
      {
        key: "QDRANT_ON_DISK_PAYLOAD",
        label: "Store Payload on Disk",
        type: "boolean",
        default: "True",
        description: "Store payload data on disk"
      },
      {
        key: "QDRANT_USE_BINARY",
        label: "Use Binary Quantization",
        type: "boolean",
        default: "False",
        description: "Enable binary quantization for vectors"
      },
      {
        key: "QDRANT_BINARY_ALWAYS_RAM",
        label: "Keep Binary Vectors in RAM",
        type: "boolean",
        default: "True",
        description: "Always keep binary vectors in RAM"
      },
      {
        key: "QDRANT_SEARCH_ENABLE_QUANT",
        label: "Enable Quantization in Search",
        type: "boolean",
        default: "False",
        description: "Enable quantization during search"
      },
      {
        key: "QDRANT_SEARCH_RESCORE",
        label: "Enable Rescoring",
        type: "boolean",
        default: "True",
        description: "Rescore results with full precision"
      },
      {
        key: "QDRANT_SEARCH_OVERSAMPLING",
        label: "Search Oversampling",
        type: "number",
        min: 1.0,
        max: 10.0,
        step: 0.1,
        default: "2.0",
        description: "Oversampling factor for search"
      },
      {
        key: "QDRANT_MEAN_POOLING_ENABLED",
        label: "Enable Mean Pooling",
        type: "boolean",
        default: "False",
        description: "Use mean pooling for embeddings"
      },
      {
        key: "MUVERA_ENABLED",
        label: "Enable MUVERA",
        type: "boolean",
        default: "False",
        description: "Multi-Vector Embedding Retrieval Augmentation for faster initial retrieval"
      },
      {
        key: "MUVERA_K_SIM",
        label: "K Similarity",
        type: "number",
        min: 1,
        max: 20,
        default: "6",
        description: "Number of similar vectors to consider",
        depends_on: { key: "MUVERA_ENABLED", value: true }
      },
      {
        key: "MUVERA_DIM_PROJ",
        label: "Projection Dimension",
        type: "number",
        min: 8,
        max: 128,
        default: "32",
        description: "Dimensionality of projection space",
        depends_on: { key: "MUVERA_ENABLED", value: true }
      },
      {
        key: "MUVERA_R_REPS",
        label: "Repetitions",
        type: "number",
        min: 1,
        max: 100,
        default: "20",
        description: "Number of repetitions",
        depends_on: { key: "MUVERA_ENABLED", value: true }
      },
      {
        key: "MUVERA_RANDOM_SEED",
        label: "Random Seed",
        type: "number",
        min: 0,
        max: 9999,
        default: "42",
        description: "Random seed for reproducibility",
        depends_on: { key: "MUVERA_ENABLED", value: true }
      }
    ]
  },
  storage: {
    order: 5,
    icon: "hard-drive",
    name: "Object Storage",
    description: "MinIO object storage configuration",
    settings: [
      {
        key: "MINIO_URL",
        label: "MinIO URL",
        type: "text",
        default: "http://localhost:9000",
        description: "Internal MinIO service URL"
      },
      {
        key: "MINIO_PUBLIC_URL",
        label: "Public MinIO URL",
        type: "text",
        default: "http://localhost:9000",
        description: "Public-facing MinIO URL"
      },
      {
        key: "MINIO_ACCESS_KEY",
        label: "Access Key",
        type: "password",
        default: "minioadmin",
        description: "MinIO access key (username)"
      },
      {
        key: "MINIO_SECRET_KEY",
        label: "Secret Key",
        type: "password",
        default: "minioadmin",
        description: "MinIO secret key (password)"
      },
      {
        key: "MINIO_BUCKET_NAME",
        label: "Bucket Name",
        type: "text",
        default: "documents",
        description: "Name of the storage bucket"
      },
      {
        key: "MINIO_WORKERS",
        label: "Worker Threads",
        type: "number",
        min: 1,
        max: 32,
        default: "12",
        description: "Number of concurrent upload workers"
      },
      {
        key: "MINIO_RETRIES",
        label: "Retry Attempts",
        type: "number",
        min: 0,
        max: 10,
        default: "3",
        description: "Number of retry attempts on failure"
      },
      {
        key: "MINIO_FAIL_FAST",
        label: "Fail Fast",
        type: "boolean",
        default: "False",
        description: "Stop immediately on first error"
      },
      {
        key: "MINIO_PUBLIC_READ",
        label: "Public Read Access",
        type: "boolean",
        default: "True",
        description: "Allow public read access to files"
      },
      {
        key: "MINIO_IMAGE_FMT",
        label: "Image Format",
        type: "select",
        options: ["JPEG", "PNG", "WEBP"],
        default: "JPEG",
        description: "Image format for stored files"
      },
      {
        key: "MINIO_IMAGE_QUALITY",
        label: "Image Quality",
        type: "number",
        min: 1,
        max: 100,
        default: "75",
        description: "Image compression quality (1-100)"
      }
    ]
  }
};
