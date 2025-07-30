import os
import torch
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "documents")

# In Memory Configuration
IN_MEMORY_URL = os.getenv("IN_MEMORY_URL", "http://localhost:6333")
IN_MEMORY_NUM_IMAGES = os.getenv("IN_MEMORY_NUM_IMAGES", "500")
IN_MEMORY_BATCH_SIZE = os.getenv("IN_MEMORY_BATCH_SIZE", "4")
IN_MEMORY_THREADS = os.getenv("IN_MEMORY_THREADS", "4")

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "nomic-ai/colnomic-embed-multimodal-3b")
MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu")

# Storage Configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "qdrant")  # "memory" or "qdrant"

# Application Configuration
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))

# Batch Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
