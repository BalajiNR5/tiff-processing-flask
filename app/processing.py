# processing.py
import numpy as np
from PIL import Image
import os
import time
import warnings

Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

TILE_SIZE = 128  # smaller tiles → higher-res heatmap

progress_dict = {}  # job_id -> progress percentage
heatmap_dict = {}   # job_id -> full file path

def process_tiff_background(file_path: str, job_id: str):
    """
    Memory-safe TIFF processing with proper heatmap saving.
    """
    print(f"[JOB {job_id}] Started processing")
    progress_dict[job_id] = 1

    try:
        with Image.open(file_path) as img:
            img = img.convert("L")
            orig_width, orig_height = img.size

            max_dim = 4000
            if max(orig_width, orig_height) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                print(f"[JOB {job_id}] Image downscaled to {img.size[0]}x{img.size[1]}")

            os.makedirs("tmp", exist_ok=True)

            width, height = img.size
            tiles_y = (height + TILE_SIZE - 1) // TILE_SIZE
            tiles_x = (width + TILE_SIZE - 1) // TILE_SIZE
            heatmap_array = np.zeros((tiles_y, tiles_x), dtype=np.float32)

            for ty, y in enumerate(range(0, height, TILE_SIZE)):
                for tx, x in enumerate(range(0, width, TILE_SIZE)):
                    box = (x, y, min(x + TILE_SIZE, width), min(y + TILE_SIZE, height))
                    tile = img.crop(box)
                    tile_np = np.array(tile, dtype=np.uint8)
                    heatmap_array[ty, tx] = float(tile_np.mean())
                    del tile_np
                    del tile
                    progress_dict[job_id] = max(1, int((ty * tiles_x + tx + 1) / (tiles_x * tiles_y) * 100))
                    time.sleep(0.001)

            # Normalize and resize heatmap to match original image
            heatmap_normalized = ((heatmap_array - heatmap_array.min()) /
                                  (heatmap_array.ptp() + 1e-5) * 255).astype(np.uint8)
            heatmap_img = Image.fromarray(heatmap_normalized)
            heatmap_img = heatmap_img.resize((width, height), Image.BICUBIC)

            heatmap_path = os.path.join("tmp", f"{job_id}_heatmap.png")
            heatmap_img.save(heatmap_path)
            heatmap_dict[job_id] = os.path.abspath(heatmap_path)  # **absolute path is safer**

            print(f"[JOB {job_id}] Heatmap saved at {heatmap_dict[job_id]}")
            progress_dict[job_id] = 100

    except Exception as e:
        print(f"[JOB {job_id}] ERROR: {e}")
        progress_dict[job_id] = -1

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
