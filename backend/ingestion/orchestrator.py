"""Orchestrator for concurrent ingestion pipeline."""

import asyncio
import logging
import os
import tempfile
import time
import uuid
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
import io

from pdf2image import convert_from_path
from qdrant_client import models
from datetime import datetime

import config
from .models import PageData, EmbeddingData, StageType, ProgressEvent
from .sse import sse_manager

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for async operations."""
    
    def __init__(self, rate: float):
        """
        Args:
            rate: Requests per second (0 = no limit)
        """
        self.rate = rate
        self.tokens = rate
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        if self.rate <= 0:
            return
            
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0


def _rasterize_pdf_worker(pdf_path: str, file_id: str, job_id: str, temp_dir: str, thread_count: int) -> List[Dict]:
    """
    Worker function to rasterize PDF pages (CPU-bound).
    Runs in ProcessPoolExecutor.
    
    Returns list of dicts with page info and temp file paths.
    """
    try:
        pages = convert_from_path(pdf_path, thread_count=thread_count)
        results = []
        
        for idx, img in enumerate(pages):
            # Save to temp file
            page_id = f"{file_id}_page_{idx}"
            temp_path = os.path.join(temp_dir, f"{page_id}.png")
            img.save(temp_path, "PNG")
            
            w, h = img.size if hasattr(img, "size") else (None, None)
            results.append({
                "page_index": idx,
                "total_pages": len(pages),
                "temp_path": temp_path,
                "width": w,
                "height": h,
            })
            
        return results
    except Exception as e:
        logger.error(f"Error rasterizing PDF {pdf_path}: {e}")
        raise


class IngestionOrchestrator:
    """Orchestrates concurrent ingestion pipeline with backpressure."""
    
    def __init__(self, qdrant_service, minio_service, embedding_processor, muvera_post=None):
        self.qdrant_service = qdrant_service
        self.minio_service = minio_service
        self.embedding_processor = embedding_processor
        self.muvera_post = muvera_post
        self.process_pool = None
        
    async def initialize(self):
        """Initialize resources."""
        # Create ProcessPoolExecutor for CPU-bound work
        self.process_pool = ProcessPoolExecutor(max_workers=config.IMAGE_WORKERS)
        
    async def shutdown(self):
        """Shutdown resources."""
        if self.process_pool:
            self.process_pool.shutdown(wait=True)
            
    async def ingest_files(
        self,
        job_id: str,
        file_paths: List[str],
        original_filenames: Dict[str, str],
    ) -> str:
        """
        Main entry point for ingestion pipeline.
        
        Args:
            job_id: Unique job identifier
            file_paths: List of temporary file paths
            original_filenames: Map of temp path -> original filename
            
        Returns:
            Success message
        """
        try:
            # Create job temp directory
            job_temp_dir = tempfile.mkdtemp(prefix=f"job_{job_id}_")
            logger.info(f"Job {job_id}: Starting ingestion of {len(file_paths)} files")
            
            # Emit queued event
            await sse_manager.emit_queued(job_id, len(file_paths))
            
            # Ensure collection exists
            self.qdrant_service._create_collection_if_not_exists()
            
            # Process files (parallel or sequential based on config)
            if config.ENABLE_PARALLEL_FILES and len(file_paths) > 1:
                total_pages = await self._process_files_parallel(
                    job_id, file_paths, original_filenames, job_temp_dir
                )
            else:
                total_pages = await self._process_files_sequential(
                    job_id, file_paths, original_filenames, job_temp_dir
                )
                
            # Emit completion
            await sse_manager.emit_completed(job_id, total_pages)
            logger.info(f"Job {job_id}: Completed successfully ({total_pages} pages)")
            
            return f"Indexed {total_pages} pages from {len(file_paths)} files"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id}: Failed with error: {error_msg}")
            await sse_manager.emit_error(job_id, error_msg)
            raise
        finally:
            # Cleanup temp directory
            try:
                import shutil
                if os.path.exists(job_temp_dir):
                    shutil.rmtree(job_temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {job_temp_dir}: {e}")
                
    async def _process_files_parallel(
        self,
        job_id: str,
        file_paths: List[str],
        original_filenames: Dict[str, str],
        job_temp_dir: str,
    ) -> int:
        """Process multiple files in parallel."""
        max_parallel = config.MAX_PARALLEL_FILES
        semaphore = asyncio.Semaphore(max_parallel)
        total_pages = 0
        
        async def process_one_file(file_path: str):
            nonlocal total_pages
            async with semaphore:
                pages = await self._process_single_file(
                    job_id, file_path, original_filenames[file_path], job_temp_dir
                )
                total_pages += pages
                
        tasks = [process_one_file(fp) for fp in file_paths]
        await asyncio.gather(*tasks)
        return total_pages
        
    async def _process_files_sequential(
        self,
        job_id: str,
        file_paths: List[str],
        original_filenames: Dict[str, str],
        job_temp_dir: str,
    ) -> int:
        """Process files one at a time."""
        total_pages = 0
        for file_path in file_paths:
            pages = await self._process_single_file(
                job_id, file_path, original_filenames[file_path], job_temp_dir
            )
            total_pages += pages
        return total_pages
        
    async def _process_single_file(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        job_temp_dir: str,
    ) -> int:
        """
        Process a single file through the pipeline stages.
        
        Returns number of pages processed.
        """
        file_id = str(uuid.uuid4())
        logger.info(f"Job {job_id}, File {file_id}: Processing {filename}")
        
        # Emit intake event
        await sse_manager.emit_intake(job_id, file_id, filename)
        
        # Stage 1: Rasterize PDF (CPU-bound, ProcessPool)
        page_data_list = await self._stage_rasterize(
            job_id, file_id, file_path, filename, job_temp_dir
        )
        
        if not page_data_list:
            logger.warning(f"Job {job_id}, File {file_id}: No pages extracted")
            return 0
            
        total_pages = len(page_data_list)
        
        # Create queues for pipeline stages
        page_batch_size = config.PAGE_BATCH_SIZE
        max_batches = config.MAX_CONCURRENT_PAGE_BATCHES
        
        storage_queue = asyncio.Queue(maxsize=max_batches * 2)
        embed_queue = asyncio.Queue(maxsize=max_batches * 2)
        index_queue = asyncio.Queue(maxsize=max_batches * 2)
        
        # Shared progress tracker - counts completed pages
        completed_pages = {"count": 0}
        progress_lock = asyncio.Lock()
        
        async def increment_progress():
            """Increment completed pages and emit progress."""
            async with progress_lock:
                completed_pages["count"] += 1
                percent = int((completed_pages["count"] / total_pages) * 100)
                # Emit a generic progress event with current completion
                await sse_manager.emit(ProgressEvent(
                    job_id=job_id,
                    stage=StageType.INDEX,  # Use index as the main stage
                    file_id=file_id,
                    counts={"done": completed_pages["count"], "total": total_pages, "percent": percent},
                    message=f"Processing: {completed_pages['count']}/{total_pages} pages"
                ))
        
        # Launch pipeline stages concurrently
        # Order: rasterize (done) -> storage (get URLs) -> embeddings -> indexing
        producer_task = asyncio.create_task(
            self._producer_stage(storage_queue, page_data_list, page_batch_size)
        )
        storage_task = asyncio.create_task(
            self._storage_stage(job_id, file_id, storage_queue, embed_queue, total_pages)
        )
        embed_task = asyncio.create_task(
            self._embedding_stage(job_id, file_id, embed_queue, index_queue, total_pages)
        )
        index_task = asyncio.create_task(
            self._indexing_stage(job_id, file_id, index_queue, total_pages, increment_progress)
        )
        
        # Wait for all stages to complete
        await asyncio.gather(producer_task, embed_task, index_task, storage_task)
        
        logger.info(f"Job {job_id}, File {file_id}: Completed {total_pages} pages")
        return total_pages
        
    async def _stage_rasterize(
        self,
        job_id: str,
        file_id: str,
        file_path: str,
        filename: str,
        job_temp_dir: str,
    ) -> List[PageData]:
        """Stage 1: Rasterize PDF to images (CPU-bound)."""
        try:
            # Get file size
            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                file_size = None
                
            # Run rasterization in process pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.process_pool,
                _rasterize_pdf_worker,
                file_path,
                file_id,
                job_id,
                job_temp_dir,
                config.WORKER_THREADS,
            )
            
            # Convert results to PageData objects
            page_data_list = []
            for result in results:
                page_data = PageData(
                    job_id=job_id,
                    file_id=file_id,
                    page_index=result["page_index"],
                    total_pages=result["total_pages"],
                    image_path=result["temp_path"],
                    filename=filename,
                    file_size_bytes=file_size,
                    page_width_px=result["width"],
                    page_height_px=result["height"],
                )
                page_data_list.append(page_data)
                
            logger.info(f"Job {job_id}, File {file_id}: Rasterized {len(page_data_list)} pages")
            return page_data_list
            
        except Exception as e:
            logger.error(f"Job {job_id}, File {file_id}: Rasterization failed: {e}")
            raise
            
    async def _producer_stage(
        self,
        output_queue: asyncio.Queue,
        page_data_list: List[PageData],
        batch_size: int,
    ):
        """Producer: emit page batches to queue."""
        for i in range(0, len(page_data_list), batch_size):
            batch = page_data_list[i:i + batch_size]
            await output_queue.put(batch)
        await output_queue.put(None)  # Sentinel
        
    async def _storage_stage(
        self,
        job_id: str,
        file_id: str,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        total_pages: int,
    ):
        """Stage 2: Upload images to MinIO and get URLs (I/O-bound)."""
        semaphore = asyncio.Semaphore(config.STORAGE_WORKERS)
        
        async def store_batch(batch: List[PageData]):
            async with semaphore:
                # Load images and prepare for upload
                images = []
                doc_ids = []
                for page_data in batch:
                    img = Image.open(page_data.image_path)
                    images.append(img)
                    # Generate document ID now
                    doc_id = str(uuid.uuid4())
                    doc_ids.append(doc_id)
                    page_data.document_id = doc_id  # Store for later use
                    
                # Upload to MinIO with retries
                for attempt in range(config.MAX_RETRIES + 1):
                    try:
                        loop = asyncio.get_event_loop()
                        image_url_dict = await loop.run_in_executor(
                            None,
                            self.minio_service.store_images_batch,
                            images,
                            doc_ids,
                            config.MINIO_IMAGE_FMT,
                            config.MINIO_MAX_CONCURRENCY,
                        )
                        break
                    except Exception as e:
                        if attempt >= config.MAX_RETRIES:
                            logger.error(f"MinIO upload failed after {attempt} retries: {e}")
                            raise
                        wait_time = config.RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(f"MinIO upload attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        
                # Attach image URLs to page data
                for i, page_data in enumerate(batch):
                    doc_id = doc_ids[i]
                    if doc_id in image_url_dict:
                        page_data.image_url = image_url_dict[doc_id]
                    else:
                        raise Exception(f"Failed to get URL for document {doc_id}")
                        
                await output_queue.put(batch)
                
        while True:
            batch = await input_queue.get()
            if batch is None:  # Sentinel
                break
            await store_batch(batch)
            
        await output_queue.put(None)  # Sentinel
        
    async def _embedding_stage(
        self,
        job_id: str,
        file_id: str,
        input_queue: asyncio.Queue,
        output_queue: asyncio.Queue,
        total_pages: int,
    ):
        """Stage 3: Generate embeddings (I/O-bound with rate limiting)."""
        semaphore = asyncio.Semaphore(config.EMBED_WORKERS)
        rate_limiter = RateLimiter(config.EMBEDDING_RPS)
        
        async def process_batch(batch: List[PageData]):
            async with semaphore:
                await rate_limiter.acquire()
                
                # Load images from temp files
                images = []
                for page_data in batch:
                    img = Image.open(page_data.image_path)
                    images.append(img)
                    
                # Generate embeddings with retries
                for attempt in range(config.MAX_RETRIES + 1):
                    try:
                        # Call embedding processor (sync function, but fast enough)
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None,
                            self.embedding_processor.embed_and_mean_pool_batch,
                            images,
                        )
                        original_batch, pooled_rows_batch, pooled_cols_batch = result
                        break
                    except Exception as e:
                        if attempt >= config.MAX_RETRIES:
                            logger.error(f"Embedding failed after {attempt} retries: {e}")
                            raise
                        wait_time = config.RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        
                # Create EmbeddingData objects
                embedding_data_list = []
                for i, page_data in enumerate(batch):
                    embedding_data = EmbeddingData(
                        page_data=page_data,
                        original_embedding=original_batch[i],
                        pooled_rows=pooled_rows_batch[i] if config.QDRANT_MEAN_POOLING_ENABLED else None,
                        pooled_cols=pooled_cols_batch[i] if config.QDRANT_MEAN_POOLING_ENABLED else None,
                    )
                    embedding_data_list.append(embedding_data)
                    
                await output_queue.put(embedding_data_list)
                
        tasks = []
        while True:
            batch = await input_queue.get()
            if batch is None:  # Sentinel
                break
            tasks.append(asyncio.create_task(process_batch(batch)))
            
        # Wait for all embedding tasks
        await asyncio.gather(*tasks)
        await output_queue.put(None)  # Sentinel
        
    async def _indexing_stage(
        self,
        job_id: str,
        file_id: str,
        input_queue: asyncio.Queue,
        total_pages: int,
        increment_progress,
    ):
        """Stage 4: Index embeddings to Qdrant (I/O-bound)."""
        semaphore = asyncio.Semaphore(config.INDEX_WORKERS)
        
        # Accumulate embeddings for batching
        accumulator = []
        batch_size = config.VECTOR_DB_BATCH_SIZE
        
        async def upsert_batch(embeddings: List[EmbeddingData]):
            async with semaphore:
                # Build points
                points = []
                for emb_data in embeddings:
                    # Use document ID that was set in storage stage
                    doc_id = emb_data.page_data.document_id
                    
                    # Build vectors dict
                    vectors = {"original": emb_data.original_embedding}
                    if config.QDRANT_MEAN_POOLING_ENABLED and emb_data.pooled_rows and emb_data.pooled_cols:
                        vectors["mean_pooling_rows"] = emb_data.pooled_rows
                        vectors["mean_pooling_columns"] = emb_data.pooled_cols
                        
                    # Compute MUVERA FDE if enabled
                    if self.muvera_post and self.muvera_post.enabled:
                        try:
                            fde = self.muvera_post.process_document(emb_data.original_embedding)
                            if fde is not None:
                                vectors["muvera_fde"] = fde
                        except Exception as e:
                            logger.warning(f"MUVERA FDE failed for {doc_id}: {e}")
                            
                    # Build payload with image URL from storage stage
                    payload = {
                        "document_id": doc_id,
                        "image_url": emb_data.page_data.image_url,
                        "indexed_at": datetime.now().isoformat() + "Z",
                        **emb_data.page_data.to_metadata(),
                    }
                    
                    point = models.PointStruct(
                        id=doc_id,
                        vector=vectors,
                        payload=payload,
                    )
                    points.append(point)
                    
                # Upsert with retries
                for attempt in range(config.MAX_RETRIES + 1):
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            self.qdrant_service.service.upsert,
                            self.qdrant_service.collection_name,
                            points,
                        )
                        break
                    except Exception as e:
                        if attempt >= config.MAX_RETRIES:
                            logger.error(f"Upsert failed after {attempt} retries: {e}")
                            raise
                        wait_time = config.RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(f"Upsert attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                
                # After successful upsert, increment progress for each page in the batch
                for _ in embeddings:
                    await increment_progress()
                
        while True:
            batch = await input_queue.get()
            if batch is None:  # Sentinel
                # Flush remaining
                if accumulator:
                    await upsert_batch(accumulator)
                break
                
            accumulator.extend(batch)
            
            # Upsert when we have enough
            while len(accumulator) >= batch_size:
                to_upsert = accumulator[:batch_size]
                accumulator = accumulator[batch_size:]
                await upsert_batch(to_upsert)
