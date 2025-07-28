# ColPali with Qdrant Integration

This updated version of the ColPali demo now uses Qdrant vector database for persistent storage instead of keeping embeddings in memory.

## Key Changes

### 1. Qdrant Integration
- **Persistent Storage**: Document embeddings are now stored in Qdrant, providing persistence across app restarts
- **Mean Pooling Strategy**: Implements the mean pooling strategy from the reference implementation for better performance
- **Multi-vector Storage**: Stores original embeddings plus row and column mean-pooled versions

### 2. Enhanced Features
- **Better Search**: Uses Qdrant's optimized vector search with cosine similarity
- **Scalability**: Can handle larger document collections without memory constraints
- **Persistence**: Indexed documents remain available after app restart

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for GPU acceleration)
- Python 3.8+

### Running with Docker Compose

1. **Start Qdrant and the App**:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - Qdrant vector database on port 6333
   - ColPali app on port 7860

2. **Access the Application**:
   - Open your browser to `http://localhost:7860`
   - Qdrant dashboard available at `http://localhost:6333/dashboard`

### Running Locally

1. **Start Qdrant Container**:
   ```bash
   docker run -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant:latest
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the App**:
   ```bash
   python app.py
   ```

## Usage

### Indexing Documents
1. Upload a PDF file using the interface
2. Click "🔄 Index documents" 
3. The app will:
   - Convert PDF pages to images
   - Generate embeddings with mean pooling
   - Store in Qdrant with metadata

### Searching Documents
1. Enter your search query
2. Adjust the number of results (k)
3. Click "🔍 Search"
4. Results show relevant pages with similarity scores

## Technical Details

### Mean Pooling Strategy
The implementation follows the reference code and applies mean pooling in two dimensions:
- **Row pooling**: Averages embeddings across image width
- **Column pooling**: Averages embeddings across image height
- **Original**: Keeps full multi-vector embeddings

### Qdrant Collection Structure
```python
vectors_config = {
    "original": VectorParams(size=128, distance=COSINE, multivector=True),
    "mean_pooling_columns": VectorParams(size=128, distance=COSINE, multivector=True),
    "mean_pooling_rows": VectorParams(size=128, distance=COSINE, multivector=True)
}
```

### Benefits
- **Memory Efficiency**: Large document collections don't consume RAM
- **Persistence**: Indexed documents survive app restarts
- **Performance**: Qdrant's optimized search algorithms
- **Scalability**: Can handle thousands of documents
- **Flexibility**: Multiple vector representations for different search strategies

## Troubleshooting

### Qdrant Connection Issues
- Ensure Qdrant container is running: `docker ps`
- Check Qdrant logs: `docker logs qdrant-container`
- Verify port 6333 is accessible

### GPU Issues
- Ensure NVIDIA Docker runtime is installed
- Check GPU availability: `nvidia-smi`
- Modify docker-compose.yml if using different GPU setup

### Memory Issues
- Reduce batch size in qdrant_manager.py if needed
- Monitor GPU memory usage during indexing
