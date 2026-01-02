import requests
import time
import sys
import numpy as np
from PIL import Image
import os

def create_tiff(filename="test_image.tiff"):
    # Create a random image
    arr = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    img = Image.fromarray(arr)
    img.save(filename)
    print(f"Created {filename}")

def test_flow():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Check server (GET /)
    print("Checking server status...")
    try:
        resp = requests.get(base_url + "/")
        if resp.status_code == 200:
            print("Server running")
        else:
            print(f"Server check failed: {resp.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("Server is not answering. Is it running?")
        return

    # 2. Upload
    create_tiff("test_image.tiff")
    print("Uploading TIFF...")
    # Use absolute path or relative? Relative is fine if cwd is correct.
    files = {'file': open('test_image.tiff', 'rb')}
    try:
        resp = requests.post(base_url + "/process", files=files)
        if resp.status_code != 200:
             print(f"Upload failed: {resp.text}")
             return
        data = resp.json()
        job_id = data.get('job_id')
        print(f"TIFF uploaded, job_id: {job_id}")
    except Exception as e:
        print(f"Upload error: {e}")
        return

    # 3. Poll
    print(f"Polling status for job {job_id}...")
    status = "pending"
    while status != "completed" and status != "error":
        time.sleep(1)
        resp = requests.get(f"{base_url}/status/{job_id}")
        if resp.status_code != 200:
             print(f"Status check failed: {resp.status_code}")
             break
        status = resp.json().get('status')
        progress = resp.json().get('progress')
        print(f"Status: {status}, Progress: {progress}%")
        if status == 'error':
             print("Processing failed")
             return

    if status == 'completed':
        print("Processing completed")

        # 4. Download
        print("Downloading heatmap...")
        resp = requests.get(f"{base_url}/heatmap/{job_id}")
        if resp.status_code == 200:
            with open("heatmap.png", "wb") as f:
                f.write(resp.content)
            print("Heatmap downloaded")
        else:
            print(f"Download failed: {resp.status_code}")

if __name__ == "__main__":
    test_flow()
