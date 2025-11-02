#!/bin/bash
# DeepSeek-OCR Local GPU Setup Script
# This script sets up the correct PyTorch version for RTX 5090 compatibility

set -e

echo "🚀 Setting up DeepSeek-OCR with proper GPU support..."

# Check if we're in WSL
# if [[ ! -f /proc/version ]] || ! grep -q Microsoft /proc/version; then
#     echo "❌ This script should be run in WSL for GPU compatibility"
#     exit 1
# fi

# Check if venv exists
if [[ ! -d ".venv" ]]; then
    echo "📦 Creating Python virtual environment..."
    uv venv

    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

echo "📥 Installing PyTorch 2.7.0 with CUDA 12.8 support..."
uv pip install --upgrade pip
uv pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

echo "📚 Installing other requirements..."
uv pip install -r requirements.txt

# Install specific flash-attn version compatible with torch 2.7.0
echo "📦 Installing flash-attn compatible with PyTorch 2.7.0..."
uv pip install "./tmp/flash_attn-2.7.4.post1+cu129torch2.7.0-cp312-cp312-linux_x86_64.whl"


echo "🔧 Setting environment variables for GPU..."
export USE_GPU=true
export DEEPSEEK_BASE_SIZE=1024
export DEEPSEEK_IMAGE_SIZE=640
export SERVICE_API_KEY=dev-key-change-in-production
export REQUIRE_API_KEY=false
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0;"

echo "✅ Setup complete! Starting DeepSeek-OCR server..."
echo "🌐 Server will be available at: http://localhost:7860"
echo "📖 API docs available at: http://localhost:7860/docs"
echo ""

# Start the server
uvicorn app:app --host 0.0.0.0 --port 7860 --reload