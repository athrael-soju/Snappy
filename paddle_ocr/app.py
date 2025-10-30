from pathlib import Path
from urllib.request import urlretrieve

from paddleocr import PaddleOCRVL


def ensure_demo_image() -> Path:
    """Download the demo image on first run so local path predictions work."""
    target_dir = Path(__file__).parent / "input"
    target_path = target_dir / "paddleocr_vl_demo.png"

    if not target_path.exists():
        print("Downloading demo image...")
        target_dir.mkdir(parents=True, exist_ok=True)
        urlretrieve(
            "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/paddleocr_vl_demo.png",
            target_path,
        )
    else:
        print("Demo image already exists, skipping download.")

    return target_path


pipeline = PaddleOCRVL(
    vl_rec_backend="vllm-server", vl_rec_server_url="http://127.0.0.1:8118/v1"
)
output = pipeline.predict(str(ensure_demo_image()))
for res in output:
    res.print()
    res.save_to_json(save_path="output")
    res.save_to_markdown(save_path="output")
