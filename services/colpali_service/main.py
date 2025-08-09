import torch
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from PIL import Image
import base64
import io
import numpy as np

from core import ColPaliCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global ColPali instance
colpali_core: Optional[ColPaliCore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    global colpali_core
    try:
        logger.info("Initializing ColPali service...")
        colpali_core = ColPaliCore()
        logger.info("ColPali service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ColPali service: {e}")
        raise
    
    yield
    
    # Shutdown (cleanup if needed)
    logger.info("Shutting down ColPali service...")


app = FastAPI(title="ColPali Service", version="1.0.0", lifespan=lifespan)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    model_name: str


class EncodeRequest(BaseModel):
    images: List[str]  # Base64 encoded images
    batch_size: Optional[int] = 4


class EncodeResponse(BaseModel):
    embeddings: List[List[float]]
    shape: List[int]


class EncodeWithPoolingResponse(BaseModel):
    original: List[List[List[float]]]  # Batch of images, each with multiple vectors
    mean_pooling_rows: List[List[List[float]]]  # Batch of pooled embeddings, multivector structure
    mean_pooling_columns: List[List[List[float]]]  # Batch of pooled embeddings, multivector structure
    shapes: Dict[str, List[int]]


class QueryRequest(BaseModel):
    query: str
    max_length: Optional[int] = 50


class QueryResponse(BaseModel):
    embedding: List[float]
    shape: List[int]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if colpali_core is None:
        raise HTTPException(status_code=503, detail="ColPali service not initialized")
    
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        device=colpali_core.get_device(),
        model_name=colpali_core.get_model_name()
    )

@app.post("/encode/images_with_pooling", response_model=EncodeWithPoolingResponse)
async def encode_images_with_pooling(request: EncodeRequest):
    """Encode images with mean pooling - maintains original functionality"""
    if colpali_core is None:
        raise HTTPException(status_code=503, detail="ColPali service not initialized")
    
    try:
        # Decode base64 images to PIL Images
        images = []
        for img_b64 in request.images:
            img_data = base64.b64decode(img_b64)
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        # Encode images with mean pooling
        result = colpali_core.encode_images_with_pooling(images, batch_size=request.batch_size or 4)
        
        return EncodeWithPoolingResponse(
            original=result["original"],
            mean_pooling_rows=result["mean_pooling_rows"],
            mean_pooling_columns=result["mean_pooling_columns"],
            shapes=result["shapes"]
        )
        
    except Exception as e:
        logger.error(f"Error encoding images with pooling: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to encode images with pooling: {str(e)}")


@app.post("/encode/query", response_model=QueryResponse)
async def encode_query(request: QueryRequest):
    """Encode query to embedding"""
    if colpali_core is None:
        raise HTTPException(status_code=503, detail="ColPali service not initialized")
    
    try:
        result = colpali_core.encode_query(request.query, max_length=request.max_length or 50)
        
        # Result already contains embedding list and shape from core.py
        return QueryResponse(embedding=result["embedding"], shape=result["shape"])
        
    except Exception as e:
        logger.error(f"Error encoding query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to encode query: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ColPali Service", "status": "running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
