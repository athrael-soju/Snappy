"""
Index benchmark dataset into Snappy services.
"""

import asyncio
import hashlib
import logging
import time
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PIL import Image

from benchmarks.dataset import BBoxDocVQADataset
from clients.colpali import ColPaliClient

logger = logging.getLogger(__name__)


def _extract_region_content(raw_text: str) -> Dict[str, List[str]]:
    """
    Extract content for each labeled region from raw OCR output.

    The raw text contains patterns like:
    <|ref|>label<|/ref|><|det|>[[coords]]<|/det|>
    Content here

    Args:
        raw_text: Raw OCR output with grounding references

    Returns:
        Dictionary mapping labels to lists of their content
    """
    import re

    content_map: Dict[str, List[str]] = {}

    if not raw_text:
        return content_map

    # Pattern to match: <|ref|>label<|/ref|><|det|>coords<|/det|>Content
    pattern = r"<\|ref\|>([^<]+)<\|/ref\|><\|det\|>.*?<\|/det\|>\s*(.*?)(?=<\|ref\|>|$)"

    for match in re.finditer(pattern, raw_text, re.DOTALL):
        label = match.group(1).strip()
        content = match.group(2).strip()

        if label and content:
            if label not in content_map:
                content_map[label] = []
            content_map[label].append(content)

    return content_map


async def index_benchmark_dataset(
    dataset_name: str,
    cache_dir: str,
    max_docs: Optional[int],
    categories: Optional[List[str]],
    collection_name: str,
    colpali_url: str,
    qdrant_url: str,
    duckdb_url: str,
    minio_url: str,
    deepseek_ocr_url: str,
) -> Dict[str, Any]:
    """
    Index benchmark dataset into Snappy services.

    Args:
        dataset_name: HuggingFace dataset name
        cache_dir: Cache directory for dataset
        max_docs: Maximum documents to index
        categories: Filter by categories
        collection_name: Qdrant collection name
        colpali_url: ColPali service URL
        qdrant_url: Qdrant service URL
        duckdb_url: DuckDB service URL
        minio_url: MinIO service URL
        deepseek_ocr_url: DeepSeek OCR service URL

    Returns:
        Dict with indexing statistics
    """
    start_time = time.time()

    # Load dataset
    logger.info(f"Loading dataset {dataset_name}...")
    dataset = BBoxDocVQADataset(
        dataset_name=dataset_name,
        cache_dir=cache_dir,
    )
    dataset.load(max_samples=None, categories=categories)

    logger.info(f"Dataset loaded with {len(dataset)} samples")

    # Get the images zip path
    cache_path = Path(cache_dir)
    zip_path = None
    for snapshot_dir in (cache_path / f"datasets--{dataset_name.replace('/', '--')}" / "snapshots").glob("*"):
        potential_zip = snapshot_dir / "BBox_DocVQA_Bench_Images.zip"
        if potential_zip.exists():
            zip_path = potential_zip
            break

    if not zip_path:
        raise RuntimeError(f"Could not find images zip in {cache_dir}")

    logger.info(f"Found images zip at {zip_path}")

    # Prepare documents for indexing by grouping samples by document
    logger.info("Preparing documents for indexing...")
    docs = {}

    for sample in dataset:
        doc_key = f"{sample.category}/{sample.doc_name}"
        if doc_key not in docs:
            docs[doc_key] = {
                "doc_name": sample.doc_name,
                "category": sample.category,
                "pages": set(),
            }

        # Collect unique pages
        for page_num in sample.evidence_pages:
            docs[doc_key]["pages"].add(page_num)

    logger.info(f"Found {len(docs)} unique documents")

    # Load images from zip and prepare for indexing
    documents_to_index = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for doc_key, doc_info in docs.items():
            if max_docs and len(documents_to_index) >= max_docs:
                break

            doc_name = doc_info["doc_name"]
            category = doc_info["category"]
            doc_pages = []

            for page_num in sorted(doc_info["pages"]):
                # Load image from zip
                image_path = f"{category}/{doc_name}/{doc_name}_{page_num}.png"
                try:
                    with zip_ref.open(image_path) as img_file:
                        image_data = img_file.read()
                        doc_pages.append((image_data, page_num))
                except KeyError:
                    logger.warning(f"Image not found in zip: {image_path}")
                    continue

            if doc_pages:
                documents_to_index.append({
                    "doc_name": doc_name,
                    "category": category,
                    "pages": doc_pages,
                })

    logger.info(f"Prepared {len(documents_to_index)} documents for indexing with {sum(len(d['pages']) for d in documents_to_index)} total pages")

    # Clear existing data before indexing
    logger.info("Clearing existing data...")

    # Clear Qdrant collection
    logger.info(f"Deleting Qdrant collection '{collection_name}' if it exists...")
    try:
        delete_response = requests.delete(f"{qdrant_url}/collections/{collection_name}", timeout=30)
        if delete_response.status_code == 200:
            logger.info(f"Deleted existing collection '{collection_name}'")
        elif delete_response.status_code == 404:
            logger.info(f"Collection '{collection_name}' does not exist, skipping deletion")
        else:
            delete_response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to delete Qdrant collection: {e}")

    # Clear DuckDB tables
    logger.info("Clearing DuckDB tables...")
    try:
        clear_response = requests.post(f"{duckdb_url}/maintenance/clear", timeout=30)
        clear_response.raise_for_status()
        logger.info("Cleared DuckDB tables successfully")
    except Exception as e:
        logger.warning(f"Failed to clear DuckDB tables: {e}")

    # Ensure Qdrant collection exists with correct vector size
    logger.info(f"Creating Qdrant collection '{collection_name}'...")

    # Get a sample embedding to determine vector size
    logger.info("Getting sample embedding to determine vector size...")
    sample_doc = documents_to_index[0]
    sample_image_data = sample_doc["pages"][0][0]

    from PIL import Image
    from io import BytesIO
    sample_image = Image.open(BytesIO(sample_image_data))

    colpali_client = ColPaliClient(base_url=colpali_url, timeout=60)
    sample_embedding_result = await asyncio.to_thread(colpali_client.embed_images, [sample_image])
    sample_embedding = sample_embedding_result[0]["embedding"]

    import numpy as np
    # Use mean pooling to get single vector size
    sample_pooled = np.mean([np.array(v) for v in sample_embedding], axis=0).tolist()
    vector_size = len(sample_pooled)

    logger.info(f"Determined vector size: {vector_size} (pooled from {len(sample_embedding)} vectors of {len(sample_embedding[0])} dims each)")

    # Create the collection
    create_response = requests.put(
        f"{qdrant_url}/collections/{collection_name}",
        json={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            }
        },
        timeout=30,
    )
    create_response.raise_for_status()
    logger.info(f"Collection '{collection_name}' created successfully with size {vector_size}")

    # Index documents
    indexed_count = 0
    total_pages = 0

    for doc in documents_to_index:
        doc_name = doc["doc_name"]
        category = doc["category"]
        pages = doc["pages"]

        logger.info(f"Indexing {category}/{doc_name} ({len(pages)} pages)...")

        try:
            # Index each page
            for page_data, page_num in pages:
                await _index_page(
                    doc_name=f"{category}_{doc_name}",
                    page_num=page_num,
                    image_data=page_data,
                    collection_name=collection_name,
                    colpali_url=colpali_url,
                    qdrant_url=qdrant_url,
                    duckdb_url=duckdb_url,
                    minio_url=minio_url,
                    deepseek_ocr_url=deepseek_ocr_url,
                )
                total_pages += 1

            indexed_count += 1
            logger.info(f"Successfully indexed {category}/{doc_name}")

        except Exception as e:
            logger.error(f"Failed to index {category}/{doc_name}: {e}")
            continue

    total_time = time.time() - start_time

    return {
        "indexed_count": indexed_count,
        "total_pages": total_pages,
        "total_time": total_time,
    }


async def _index_page(
    doc_name: str,
    page_num: int,
    image_data: bytes,
    collection_name: str,
    colpali_url: str,
    qdrant_url: str,
    duckdb_url: str,
    minio_url: str,
    deepseek_ocr_url: str,
) -> None:
    """Index a single page into Snappy services."""

    # 1. Get ColPali embedding using the client
    logger.debug(f"Getting ColPali embedding for {doc_name} page {page_num}")

    # Load image from bytes
    image = Image.open(BytesIO(image_data))

    # Initialize ColPali client
    colpali_client = ColPaliClient(base_url=colpali_url, timeout=60)

    # Get embedding
    embedding_result = await asyncio.to_thread(colpali_client.embed_images, [image])

    # Extract embedding from result and use mean pooling to get single vector
    embedding = embedding_result[0]["embedding"]

    import numpy as np
    # Use mean pooling across all vectors to get a single 128-dim vector
    pooled_embedding = np.mean([np.array(v) for v in embedding], axis=0).tolist()

    logger.debug(f"Embedding shape: {len(embedding)} vectors of {len(embedding[0])} dims each, pooled to {len(pooled_embedding)} dims")

    # 2. Store in Qdrant
    logger.debug(f"Storing in Qdrant: {doc_name} page {page_num}")

    # Use a hash of doc_name and page_num as ID (Qdrant needs numeric IDs)
    import hashlib
    point_id = int(hashlib.md5(f"{doc_name}_page_{page_num}".encode()).hexdigest()[:16], 16) % (2**63)

    qdrant_response = requests.put(
        f"{qdrant_url}/collections/{collection_name}/points",
        json={
            "points": [
                {
                    "id": point_id,
                    "vector": pooled_embedding,
                    "payload": {
                        "doc_name": doc_name,
                        "page_num": page_num,
                        "image_path": f"{doc_name}/page_{page_num}.png",
                    }
                }
            ]
        },
        timeout=30,
    )
    qdrant_response.raise_for_status()

    # 3. Run OCR
    logger.debug(f"Running OCR for {doc_name} page {page_num}")
    ocr_response = requests.post(
        f"{deepseek_ocr_url}/api/ocr",
        files={"image": ("page.png", image_data, "image/png")},
        data={
            "mode": "Gundam",
            "task": "markdown",
            "include_grounding": "true",
            "include_images": "true",
        },
        timeout=120,
    )
    ocr_response.raise_for_status()
    ocr_result = ocr_response.json()

    # 4. Store OCR text in DuckDB
    if ocr_result.get("text"):
        logger.debug(f"Storing OCR text in DuckDB: {doc_name} page {page_num}")

        page_id = hashlib.md5(f"{doc_name}_page_{page_num}".encode()).hexdigest()
        document_id = hashlib.md5(doc_name.encode()).hexdigest()

        # Convert bounding_boxes to regions format expected by DuckDB
        # Extract content mapping from raw text using the same logic as Snappy's OCR processor
        raw_text = ocr_result.get("raw", "")
        content_map = _extract_region_content(raw_text) if raw_text else {}

        regions = []
        for i, bbox in enumerate(ocr_result.get("bounding_boxes", [])):
            label = bbox.get("label", "unknown")
            region = {
                "id": f"{doc_name}#region-{i+1}",
                "label": label,
                "bbox": [bbox.get("x1"), bbox.get("y1"), bbox.get("x2"), bbox.get("y2")],
            }

            # Add content if available from raw text parsing
            if label in content_map and content_map[label]:
                content_list = content_map[label]
                if content_list:
                    region["content"] = content_list.pop(0)

            regions.append(region)

        duckdb_payload = {
            "provider": "deepseek",
            "version": "1.0",
            "filename": doc_name,
            "page_number": page_num,
            "page_id": page_id,
            "document_id": document_id,
            "text": ocr_result.get("text", ""),
            "markdown": ocr_result.get("markdown", ocr_result.get("text", "")),
            "raw_text": ocr_result.get("raw", ""),
            "regions": regions,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "storage_url": f"minio://{doc_name}/page_{page_num}.png",
            "extracted_images": ocr_result.get("extracted_images", [])
        }

        duckdb_response = requests.post(
            f"{duckdb_url}/ocr/store",
            json=duckdb_payload,
            timeout=30,
        )
        duckdb_response.raise_for_status()
        logger.debug(f"Stored OCR text for {doc_name} page {page_num}")

    logger.info(f"Indexed {doc_name} page {page_num}")
